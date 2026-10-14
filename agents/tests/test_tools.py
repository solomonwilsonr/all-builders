"""Offline checks: the tools read from the mock API and the evidence-ID filter works. No Gemini needed."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "api"))
from app.main import app as api_app  # noqa: E402

from safeshelf_agents import tools  # noqa: E402


@pytest.fixture(autouse=True)
def api(monkeypatch):
    monkeypatch.setattr(tools, "ALLOW_MOCK", True)  # offline tests use the repo's example answers on purpose
    client = TestClient(api_app)
    monkeypatch.setattr(tools.httpx, "get", lambda url, headers=None, timeout=None: client.get(url.replace(tools.API_BASE, "")))


def test_safety_tool_returns_evidence_ids():
    out = tools.get_safety("SS-P-10291")
    assert out["ai_findings"][0]["evidence_ids"]


def test_every_tool_answers_from_the_api():
    for fn in tools.ALL_TOOLS:
        assert "error" not in fn("SS-P-10291"), fn.__name__


def test_agent_builds_without_a_key():
    from safeshelf_agents.shelf_chat import agent

    assert agent.name == "shelf_chat"


def test_context_holds_all_evidence_ids():
    import asyncio

    from safeshelf_agents.shelf_chat import _context

    text, seen = asyncio.run(_context("SS-P-10291"))
    assert {"EV-201", "EV-207"} <= seen and "alternatives" in text


def test_busy_model_falls_back_and_fake_citations_are_dropped(monkeypatch):
    import asyncio

    from google.genai import errors

    from safeshelf_agents import shelf_chat

    tried = []

    async def fake_run(model, session_id, prompt):
        tried.append(model)
        if model == "m1":
            raise errors.ServerError(503, {"error": {"message": "busy"}}, None)
        return "Be careful [EV-201] [EV-999]."

    monkeypatch.setattr(shelf_chat, "_run", fake_run)
    monkeypatch.setattr(shelf_chat, "MODELS", ["m1", "m2"])
    shelf_chat._cooling.clear()
    out = asyncio.run(shelf_chat.ask("SS-P-10291", "Is it safe?"))
    assert tried == ["m1", "m2"]
    tried.clear()
    asyncio.run(shelf_chat.ask("SS-P-10291", "Again?"))
    assert tried[0] == "m2"  # m1 failed a moment ago, so it is skipped
    assert out["messages"][0]["evidence_ids"] == ["EV-201"]  # EV-999 was never in the evidence
    assert "[" not in out["messages"][0]["text"]  # citations are shown separately


def test_slow_model_is_raced_by_the_next_one(monkeypatch):
    import asyncio

    from safeshelf_agents import shelf_chat

    async def fake_run(model, session_id, prompt):
        await asyncio.sleep(5 if model == "slow" else 0.01)
        return f"answer from {model}"

    monkeypatch.setattr(shelf_chat, "_run", fake_run)
    monkeypatch.setattr(shelf_chat, "HEDGE_AFTER", 0.05)
    out = asyncio.run(shelf_chat._race(["slow", "fast"], "s", "p"))
    assert out == "answer from fast"  # did not wait for the slow model


def test_follow_up_prompt_carries_the_check_result_and_earlier_turns(monkeypatch):
    import asyncio

    from safeshelf_agents import shelf_chat

    seen_prompt = {}

    async def fake_run(model, session_id, prompt):
        seen_prompt["p"] = prompt
        return "The price could not be verified [EV-67CA94E3] [EV-201]."

    monkeypatch.setattr(shelf_chat, "_run", fake_run)
    monkeypatch.setattr(shelf_chat, "MODELS", ["m"])
    ctx = {"summary": "Not enough evidence yet", "real": {"lines": ["Could not verify price"]}, "evidence_ids": ["EV-201"]}
    out = asyncio.run(shelf_chat.ask("unmatched", "why?", "en", "s1", ctx, [{"role": "user", "text": "Is it real?"}, {"role": "bot", "text": "Not sure."}]))
    p = seen_prompt["p"]
    assert "Could not verify price" in p and "Shopper: Is it real?" in p and "SafeShelf: Not sure." in p
    assert out["messages"][0]["evidence_ids"] == ["EV-201"]  # only IDs present in the check result are kept


def test_example_answers_never_reach_the_model(monkeypatch):
    monkeypatch.setattr(tools, "ALLOW_MOCK", False)  # real behaviour: the in-process API answers with mock data here
    assert tools.get_safety("SS-P-10291") == {"unavailable": "no real data for this yet"}
