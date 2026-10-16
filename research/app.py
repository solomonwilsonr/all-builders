"""Research Agent service (M9): POST /research runs the headless browser on official recall sites.

Its own Cloud Run service, because Chromium is too big for the API. The API calls it with a shared token
(Secret Manager: research-token); nothing else should. See browser.py for what the agent does and may not do.
"""
import hmac
import os

import browser
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

TOKEN = os.environ.get("RESEARCH_TOKEN", "")
app = FastAPI(title="SafeShelf Research Agent")


class ResearchRequest(BaseModel):
    brand: str = ""
    model: str = ""
    kind: str = ""
    sources: list[str] | None = None
    mode: str = "scripted"  # or "computer_use", or "browser_use" (open-source browser-use agent)


@app.post("/research")
async def research(req: ResearchRequest, x_research_token: str = Header(default="")) -> dict:
    if TOKEN and not hmac.compare_digest(x_research_token, TOKEN):
        raise HTTPException(status_code=401, detail="Missing or wrong X-Research-Token")
    if not (req.brand or req.model):
        raise HTTPException(status_code=422, detail="Give a brand and a model number")
    mode = req.mode if req.mode in ("computer_use", "browser_use") else "scripted"
    return await browser.research(req.brand[:80], req.model[:80], req.sources, mode,
                                  budget_s=240 if mode in ("computer_use", "browser_use") else 160)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "sources": sorted(browser.SOURCES)}
