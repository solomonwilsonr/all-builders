"""Research Agent client. The agent itself is a headless browser on Cloud Run (research/, its own service, because
Chromium is too big for the API): it searches official recall sites that have no API, with Gemini reading each page
and choosing what to open, and it stops at captchas and blocks instead of working around them.

What it finds is stored as evidence (source_type "research") so answers can cite it. A match is always "for a person
to confirm": only an exact model number in a stored official notice (engine/recalls.py) makes a product "recalled".
"""
import logging
import os

import requests

from engine import store
from engine.agents import cache

RESEARCH_URL = os.environ.get("SAFESHELF_RESEARCH_URL", "").rstrip("/")
TOKEN = os.environ.get("SAFESHELF_RESEARCH_TOKEN", "")
CACHE_S = 24 * 3600
TIMEOUT_S = int(os.environ.get("SAFESHELF_RESEARCH_TIMEOUT", "150"))
log = logging.getLogger(__name__)


def check(brand: str, model: str, kind: str = "", sources: list[str] | None = None, mode: str = "scripted") -> dict:
    """Official recall sites searched for brand + model. {"skipped": True} when the service is not configured."""
    if not RESEARCH_URL:
        return {"skipped": True, "reason": "the Research Agent service is not configured here"}
    key = f"research:{brand}|{model}|{','.join(sorted(sources or []))}|{mode}".lower()
    cached = cache.get(key)
    if cached:  # recall sites change slowly: one search per model a day
        return {**cached, "from_cache": True}
    response = requests.post(f"{RESEARCH_URL}/research", timeout=TIMEOUT_S,
                             headers={"X-Research-Token": TOKEN} if TOKEN else {},
                             json={"brand": brand, "model": model, "kind": kind, "sources": sources, "mode": mode})
    response.raise_for_status()
    body = response.json()
    for source in body.get("sources", []):
        for match in source.get("matches", []):
            match["evidence_id"] = store.add_evidence(
                "research", match.get("url") or source.get("start_url") or "",
                {"site": source.get("site"), "query": source.get("query"), **match})
    cache.put(key, body, CACHE_S)
    return body


def reasons(body: dict) -> list[tuple[str, list[str]]]:
    out = []
    for s in body.get("sources", []):
        site, model = s.get("site"), body.get("model") or "this model"
        if s.get("status") in ("blocked", "captcha"):
            out.append((f"{site} blocked the automated check ({s['status']}); a person needs to look", []))
            continue
        covering = [m for m in s.get("matches", []) if m.get("covers_this_model") in ("yes", "maybe")]
        for m in covering[:2]:
            line = (f"The Research Agent found a notice on {site} that may cover {model}: \"{m.get('title')}\" "
                    f"({m.get('date') or 'undated'}); for a person to confirm")
            out.append((line, [m.get("evidence_id")]))
        if s.get("status") == "not_found" or (s.get("status") == "found" and not covering):
            out.append((f"No recall notice for {model} on {site} (searched by the Research Agent)", []))
    return out


def summary(body: dict) -> str:
    parts = []
    for s in body.get("sources", []):
        n = len([m for m in s.get("matches", []) if m.get("covers_this_model") in ("yes", "maybe")])
        parts.append(f"{s.get('site')} {s.get('status')}" + (f" ({n} possible match)" if n else ""))
    return "Research Agent: " + ("; ".join(parts) or "no sites searched")
