"""api_handler.py with stand-ins for Person A's engine modules: no Google calls, no database."""
import asyncio
import sys
import types as pytypes

import pytest
from fastapi import HTTPException


@pytest.fixture()
def handler(monkeypatch):
    calls = []

    def module(name, **attrs):
        m = pytypes.ModuleType(name)
        m.__dict__.update(attrs)
        return m

    class Models:
        def generate_content(self, model, contents, config):
            calls.append(model)
            if model == "busy":
                raise RuntimeError("503")
            return pytypes.SimpleNamespace(text="The price matches [EV-1F3B0227] [EV-FAKE1].")

    fake_gemini = module("engine.gemini", client=lambda: pytypes.SimpleNamespace(models=Models()))
    fake_safety = module("engine.safety", safety=lambda pid: {"verdict": "not_enough_evidence", "evidence_ids": ["EV-1F3B0227"]})
    fake_identity = module("engine.identity", relationships=lambda pid: (_ for _ in ()).throw(KeyError(pid)))  # unreadable part
    fake_marks = module("engine.marks", certifications=lambda pid: {"certifications": []})
    engine = module("engine", gemini=fake_gemini, safety=fake_safety, identity=fake_identity, marks=fake_marks)
    for name, mod in (("engine", engine), ("engine.gemini", fake_gemini), ("engine.safety", fake_safety), ("engine.identity", fake_identity), ("engine.marks", fake_marks)):
        monkeypatch.setitem(sys.modules, name, mod)
    sys.modules.pop("api_handler", None)
    import api_handler

    monkeypatch.setattr(api_handler, "CHAT_MODELS", ["busy", "ok"])
    return api_handler, calls


class Req:
    def __init__(self, body):
        self._body = body

    async def json(self):
        return self._body


def run(h, body):
    return asyncio.run(h.start_agent_session(Req(body), {}))


def test_answers_with_only_real_evidence_ids_and_skips_a_busy_model(handler):
    h, calls = handler
    out = run(h, {"mode": "chat", "product_id": "SS-P-1", "message": "Is it genuine?", "language": "en", "session_id": "s1"})
    assert calls == ["busy", "ok"]
    assert out["messages"][0]["evidence_ids"] == ["EV-1F3B0227"]  # EV-FAKE1 is not in the evidence
    assert "[" not in out["messages"][0]["text"] and out["session_id"] == "s1"


def test_unmatched_product_uses_only_the_check_result(handler):
    h, _ = handler
    out = run(h, {"mode": "chat", "product_id": "unmatched", "message": "Why?", "context": {"evidence_ids": ["EV-1F3B0227"]}, "history": [{"role": "user", "text": "hi"}]})
    assert out["messages"][0]["evidence_ids"] == ["EV-1F3B0227"]


def test_every_model_busy_gives_a_clear_503(handler, monkeypatch):
    h, _ = handler
    monkeypatch.setattr(h, "CHAT_MODELS", ["busy"])
    with pytest.raises(HTTPException) as err:
        run(h, {"mode": "chat", "product_id": "x", "message": "hi"})
    assert err.value.status_code == 503 and "busy" in err.value.detail


def test_investigate_and_empty_messages_are_rejected(handler):
    h, _ = handler
    with pytest.raises(HTTPException) as a:
        run(h, {"mode": "investigate", "product_id": "x"})
    with pytest.raises(HTTPException) as b:
        run(h, {"mode": "chat", "product_id": "x", "message": " "})
    assert (a.value.status_code, b.value.status_code) == (501, 422)
