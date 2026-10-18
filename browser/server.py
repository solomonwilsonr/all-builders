"""A real Chrome with the SafeShelf extension, for "Try it" on the judges' page. Runs on Cloud Run and costs nothing
until a signed-in judge presses "Start a real browser".

One judge per container (Cloud Run --concurrency 1). The whole session is one WebSocket on /session:
  1. the viewer page (/view, noVNC) opens it with the judge's Firebase ID token in the WebSocket protocol header
     ("ss.<token>"), so the token never appears in a request URL or the request log;
  2. the token is verified with Google's library (a real SafeShelf sign-in, for the Firebase project) before anything
     starts;
  3. Chromium starts on a virtual screen with a fresh profile and the real extension, signed in with that token, on the
     SafeShelf test shops (or one test product's page, `?start=`);
  4. the screen is streamed (x11vnc -> this WebSocket -> noVNC) until the judge ends it or SESSION_SECONDS pass;
  5. Chromium, the screen and the profile are deleted.
"""
import asyncio
import contextlib
import json
import logging
import os
import re
import shutil
import socket
import uuid
from pathlib import Path
from urllib.parse import urlparse

from aiohttp import WSMsgType, web
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

PORT = int(os.environ.get("PORT", "8080"))
FIREBASE_PROJECT = os.environ.get("FIREBASE_PROJECT", "shelf2026-3656b")
API_BASE = os.environ.get("API_BASE", "https://safeshelf-api-368488022657.asia-south1.run.app").rstrip("/")
SESSION_SECONDS = int(os.environ.get("SESSION_SECONDS", "300"))
# The SafeShelf test shops (shops/): the seven test products as real pages. A session starts on their home page, or on
# one of their product pages; nothing else can be passed in.
SHOPS_URL = os.environ.get("SHOPS_URL", "https://safeshelf-shops.web.app").rstrip("/")
START_URL = os.environ.get("START_URL", SHOPS_URL + "/")
SHOP_PAGE = re.compile(r"/[a-z0-9-]+/[a-z0-9-]+\.html")
# Pages allowed to put the viewer in a frame and hand it a token (the judges' page, deployed and local)
EMBEDDERS = [o for o in os.environ.get("EMBEDDERS", "https://shelf2026-3656b.web.app,https://shelf2026-3656b.firebaseapp.com,http://localhost:8095").split(",") if o]
DEV_SKIP_AUTH = os.environ.get("DEV_SKIP_AUTH") == "1"  # local testing only; never set on Cloud Run
HERE = Path(__file__).resolve().parent
NOVNC = Path(os.environ.get("NOVNC_DIR", "/usr/share/novnc"))
DISPLAY, VNC_PORT = ":99", 5900
log = logging.getLogger("safeshelf-browser")
logging.basicConfig(level=logging.INFO, format="%(message)s")

busy = False  # one session per container
google_request = google_requests.Request()


def verify(token: str) -> dict:
    """The judge's Firebase sign-in, checked: signature, expiry, and that it is for the SafeShelf project."""
    if DEV_SKIP_AUTH:
        return {"sub": "dev", "email": "dev@localhost", "name": "Local test"}
    claims = id_token.verify_firebase_token(token, google_request, audience=FIREBASE_PROJECT)
    if not claims or not claims.get("sub"):
        raise ValueError("not a SafeShelf sign-in")
    return claims


def write_extension(base: Path, token: str, claims: dict) -> Path:
    """This session's copy of the extension: the real files, signed in with the judge's token, calling the live API."""
    ext = base / "ext"
    shutil.copytree(HERE / "ext", ext)
    (ext / "config.generated.js").write_text(
        "// Written for one remote browser session; not the shipped settings.\n"
        f"export const API_BASE = {json.dumps(API_BASE)};\nexport const SHELF_SYNC = false;\n"
        f"export const SIGNIN_URL = {json.dumps(EMBEDDERS[0] + '/signin.html' if EMBEDDERS else '')};\nexport const FIREBASE_API_KEY = \"\";\n")
    session = {"idToken": token, "email": claims.get("email") or "", "name": claims.get("name") or "",
               "expiresAt": int(claims.get("exp", 0)) * 1000 or 0}
    # A fixed public key gives the extension a fixed ID, so the policy in remote/policy.json can pin its icon to the
    # toolbar (Chromium hides it in the puzzle menu otherwise, and the shops' home page shows no shield).
    manifest = json.loads((ext / "manifest.json").read_text())
    manifest["key"] = (HERE / "remote" / "extension-key.txt").read_text().strip()
    (ext / "manifest.json").write_text(json.dumps(manifest, indent=2))
    template = (HERE / "remote" / "session.js").read_text()
    (ext / "session.js").write_text(template.replace("__SESSION__", json.dumps(session)))
    shutil.copy(HERE / "remote" / "rbac.js", ext / "rbac.js")
    return ext


async def port_open(port: int, seconds: float) -> bool:
    for _ in range(int(seconds * 10)):
        with contextlib.suppress(OSError):
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return True
        await asyncio.sleep(0.1)
    return False


def start_page(asked: str) -> str:
    """The page Chrome opens on: a test shop product page if one was asked for, otherwise the start page."""
    path = asked[len(SHOPS_URL):] if asked.startswith(SHOPS_URL + "/") else ""
    return SHOPS_URL + path if SHOP_PAGE.fullmatch(path) else START_URL


async def start_browser(base: Path, ext: Path, url: str = START_URL) -> list[asyncio.subprocess.Process]:
    env = {**os.environ, "DISPLAY": DISPLAY}
    procs = [await asyncio.create_subprocess_exec("Xvfb", DISPLAY, "-screen", "0", "1280x800x24", "-nolisten", "tcp",
                                                  stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)]
    for _ in range(50):
        if Path("/tmp/.X11-unix/X99").exists():
            break
        await asyncio.sleep(0.1)
    procs.append(await asyncio.create_subprocess_exec(
        "chromium", "--no-sandbox", "--test-type", "--disable-dev-shm-usage", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
        "--disable-sync", "--password-store=basic", f"--user-data-dir={base / 'profile'}", f"--load-extension={ext}",
        f"--disable-extensions-except={ext}", "--window-position=0,0", "--window-size=1280,800", "--lang=en-IN", url,
        env=env, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL))
    procs.append(await asyncio.create_subprocess_exec(
        "x11vnc", "-display", DISPLAY, "-rfbport", str(VNC_PORT), "-localhost", "-nopw", "-forever", "-noxdamage", "-quiet",
        env=env, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL))
    if not await port_open(VNC_PORT, 45):
        raise RuntimeError("the screen did not start")  # 45 s: a cold instance (14:03 on 18 Oct) missed 20 s
    return procs


async def stop(procs: list, base: Path) -> None:
    for p in reversed(procs):
        with contextlib.suppress(ProcessLookupError):
            p.kill()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(p.wait(), 5)
    shutil.rmtree(base, ignore_errors=True)
    with contextlib.suppress(FileNotFoundError):
        Path("/tmp/.X11-unix/X99").unlink()
        Path("/tmp/.X99-lock").unlink()


async def session(request: web.Request) -> web.StreamResponse:
    global busy
    # only the viewer page served by this service may open a session
    if urlparse(request.headers.get("Origin", "")).netloc != request.host:
        return web.Response(status=403, text="Open the browser from the SafeShelf page")
    offered = [p.strip() for p in request.headers.get("Sec-WebSocket-Protocol", "").split(",")]
    token = next((p[3:] for p in offered if p.startswith("ss.")), "")
    try:
        claims = verify(token)
    except Exception as err:  # bad, expired or missing token
        log.info(json.dumps({"event": "refused", "why": type(err).__name__}))
        return web.Response(status=401, text="Sign in on the SafeShelf page first")
    if busy:
        return web.Response(status=503, text="This browser is busy")
    busy = True
    sid = uuid.uuid4().hex[:12]
    base = Path(f"/tmp/ss-{sid}")
    procs: list = []
    ws = web.WebSocketResponse(protocols=("binary",), max_msg_size=0, heartbeat=25)
    await ws.prepare(request)
    log.info(json.dumps({"event": "start", "session": sid, "user": claims.get("sub")}))
    try:
        base.mkdir(parents=True)
        procs = await start_browser(base, write_extension(base, token, claims), start_page(request.query.get("start", "")))
        reader, writer = await asyncio.open_connection("127.0.0.1", VNC_PORT)

        async def to_screen():
            async for msg in ws:
                if msg.type == WSMsgType.BINARY:
                    writer.write(msg.data)
                    await writer.drain()
                elif msg.type in (WSMsgType.CLOSE, WSMsgType.ERROR):
                    break

        async def to_viewer():
            while data := await reader.read(65536):
                await ws.send_bytes(data)

        tasks = [asyncio.create_task(t) for t in (to_screen(), to_viewer(), asyncio.sleep(SESSION_SECONDS))]
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in tasks:
            t.cancel()
        writer.close()
    except Exception as err:
        log.info(json.dumps({"event": "failed", "session": sid, "error": str(err)[:200]}))
    finally:
        await ws.close()
        await stop(procs, base)
        busy = False
        log.info(json.dumps({"event": "end", "session": sid}))
    return ws


async def view(_request: web.Request) -> web.Response:
    page = (HERE / "view.html").read_text().replace("__EMBEDDERS__", json.dumps(EMBEDDERS)).replace("__SECONDS__", str(SESSION_SECONDS)) \
        .replace("__SHOPS__", json.dumps(SHOPS_URL))
    # only the SafeShelf pages may frame the viewer
    return web.Response(text=page, content_type="text/html", headers={"Content-Security-Policy": "frame-ancestors " + " ".join(EMBEDDERS)})


async def health(_request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "busy": busy})


app = web.Application()
app.add_routes([web.get("/view", view), web.get("/session", session), web.get("/health", health), web.static("/novnc", NOVNC)])

if __name__ == "__main__":
    web.run_app(app, port=PORT, access_log=None)
