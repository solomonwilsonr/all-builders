"""gemini.structured: a slow model is not waited out; a backup starts and the first good answer wins."""
import time
import types as pytypes

import pytest

from engine import gemini


@pytest.fixture()
def fake(monkeypatch):
    monkeypatch.setattr(gemini, "HEDGE_AFTER_S", 0.2)
    monkeypatch.setattr(gemini, "_cooling", {})
    calls = []

    def attempt(model, prompt, schema, timeout_s):
        calls.append(model)
        if model == "slow":
            time.sleep(3)
        if model == "broken":
            raise RuntimeError("503")
        return pytypes.SimpleNamespace(usage_metadata=None), {"answer": model}

    monkeypatch.setattr(gemini, "_attempt", attempt)
    return calls


def test_a_slow_model_is_not_waited_out(fake):
    started = time.monotonic()
    out = gemini.structured("p", {}, models=["slow", "fast"], timeout_s=1)  # hedge after max(0.2, 0.25 s)
    assert out["model"] == "fast" and time.monotonic() - started < 1.5
    assert gemini._cooling.get("slow")  # the slow model goes last next time


def test_a_failing_model_falls_through_at_once(fake):
    out = gemini.structured("p", {}, models=["broken", "fast"], timeout_s=30)
    assert out["model"] == "fast" and fake == ["broken", "fast"]


def test_every_model_failing_is_an_error(fake):
    with pytest.raises(RuntimeError):
        gemini.structured("p", {}, models=["broken"], timeout_s=1)
