"""The one HTTP path adapters use: allowlisted hosts only, short timeouts, one retry for transient errors, and honest
failure states (403 and captchas are "blocked": SafeShelf stops there, it never works around a block).

Tests swap `transport` for an httpx.MockTransport, so unit tests never touch the network.
"""
import asyncio

import httpx

from engine.sources import policy
from engine.sources.base import BLOCKED, ERROR, RATE_LIMITED, TIMEOUT, SourceFailure

USER_AGENT = "SafeShelf-research/0.2 (+consumer product safety; read-only)"
transport: httpx.AsyncBaseTransport | None = None  # tests set a MockTransport
CAPTCHA = ("captcha", "verify you are human", "are you a robot", "challenges.cloudflare")


class Base:
    """Shared plumbing: the registry entry, its allowlist and timeout."""

    def __init__(self, entry: dict):
        self.entry = entry
        self.id = entry["id"]
        self.domains = entry.get("domains") or []
        self.timeout = float(entry.get("timeout_s") or 8)

    async def get(self, url: str, params: dict | None = None, data: dict | None = None,
                  method: str = "GET") -> httpx.Response:
        ok, why = policy.allowed_url(url, self.domains)
        if not ok:
            raise SourceFailure(ERROR, f"refused to fetch {url}: {why}")
        attempts = 2
        for attempt in range(1, attempts + 1):
            try:
                async with httpx.AsyncClient(transport=transport, timeout=self.timeout, follow_redirects=True,
                                             headers={"User-Agent": USER_AGENT}) as client:
                    response = await client.request(method, url, params=params, data=data)
                final_ok, why = policy.allowed_url(str(response.url), self.domains)
                if not final_ok:  # a redirect off the official domains is not followed into evidence
                    raise SourceFailure(BLOCKED, f"redirected away from the official site: {why}")
                if response.status_code in (401, 403):
                    raise SourceFailure(BLOCKED, f"the site refused the request ({response.status_code})")
                if response.status_code == 429:
                    raise SourceFailure(RATE_LIMITED, "the site asked SafeShelf to slow down (429)")
                if response.status_code >= 500:
                    if attempt < attempts:
                        await asyncio.sleep(0.4)
                        continue
                    raise SourceFailure(ERROR, f"the site had a server error ({response.status_code})")
                if response.status_code >= 400:
                    raise SourceFailure(ERROR, f"the site answered {response.status_code}")
                head = response.text[:4000].lower() if "html" in response.headers.get("content-type", "") else ""
                if any(sign in head for sign in CAPTCHA):
                    raise SourceFailure(BLOCKED, "the site showed a captcha; a person needs to look")
                return response
            except httpx.TimeoutException:
                if attempt < attempts:
                    continue
                raise SourceFailure(TIMEOUT, f"no answer within {self.timeout:g} s") from None
            except httpx.HTTPError as error:
                if attempt < attempts:
                    await asyncio.sleep(0.4)
                    continue
                raise SourceFailure(ERROR, f"could not reach the site ({type(error).__name__})") from None
        raise SourceFailure(ERROR, "no answer")

    async def json(self, url: str, params: dict | None = None):
        response = await self.get(url, params)
        try:
            return response.json()
        except ValueError:
            raise SourceFailure(ERROR, "the site's answer was not valid JSON") from None

    async def health(self) -> dict:
        return {"source": self.id, "access_status": self.entry["access_status"]}
