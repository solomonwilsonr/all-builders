"""Shelf Chat handler with stand-ins for Gemini and the data: no Google calls, no database."""
import types as pytypes

import pytest
from fastapi import HTTPException

from engine import chat, chat_core


@pytest.fixture()
def models(monkeypatch):
    tried = []

    class Models:
        def generate_content(self, model, contents, config):
            tried.append(model)
            if model == "busy":
                raise RuntimeError("503")
            return pytypes.SimpleNamespace(text="Two fire reports [EV-1F3B0227] [EV-FAKE1].", usage_metadata=None)

    monkeypatch.setattr(chat.gemini, "client", lambda: pytypes.SimpleNamespace(models=Models()))
    monkeypatch.setattr(chat.safety, "safety", lambda pid: {"verdict": "amber", "evidence_ids": ["EV-1F3B0227"]})
    monkeypatch.setattr(chat.identity, "relationships", lambda pid: (_ for _ in ()).throw(KeyError(pid)))
    monkeypatch.setattr(chat.marks, "certifications", lambda pid: {"certifications": []})
    monkeypatch.setattr(chat, "CHAT_MODELS", ["busy", "good"])
    return tried


def test_answer_keeps_only_real_evidence_ids_and_falls_back(models):
    out = chat.answer({"mode": "chat", "product_id": "SS-P-10291", "message": "Is it safe?", "language": "hi"})
    msg = out["messages"][0]
    assert models == ["busy", "good"]
    assert msg["evidence_ids"] == ["EV-1F3B0227"]  # the invented ID is dropped
    assert "[" not in msg["text"] and out["language"] == "hi"


def test_unmatched_product_reads_no_evidence(models, monkeypatch):
    monkeypatch.setattr(chat.safety, "safety", lambda pid: pytest.fail("no evidence lookup for an unmatched listing"))
    out = chat.answer({"mode": "chat", "product_id": "unmatched", "message": "Is it genuine?"})
    assert out["messages"][0]["evidence_ids"] == []


def test_bad_requests():
    with pytest.raises(HTTPException) as e:
        chat.answer({"mode": "investigate", "message": "x"})
    assert e.value.status_code == 501
    with pytest.raises(HTTPException) as e:
        chat.answer({"mode": "chat", "message": "  "})
    assert e.value.status_code == 422


def test_all_models_busy(models, monkeypatch):
    monkeypatch.setattr(chat, "CHAT_MODELS", ["busy"])
    with pytest.raises(HTTPException) as e:
        chat.answer({"mode": "chat", "product_id": "SS-P-10291", "message": "hi"})
    assert e.value.status_code == 503


def test_reply_language_follows_the_picker_or_the_script_of_the_question():
    assert chat_core.language("ta") == "ta" and chat_core.language("xx") == "en" and chat_core.language(None) == "en"
    assert chat_core.language("en", "இது பாதுகாப்பானதா?") == "ta"
    assert chat_core.language("en", "これは安全ですか？") == "ja"
    assert chat_core.language("ja", "安全吗") == "ja" and chat_core.language("en", "这个安全吗") == "zh-Hans"
    assert chat_core.language("mr", "हे सुरक्षित आहे का?") == "mr" and chat_core.language("en", "क्या यह सुरक्षित है?") == "hi"
    assert chat_core.language("en", "Sản phẩm này có an toàn không?") == "vi"
    assert chat_core.language("id", "Apakah ini aman?") == "id"  # Latin-script languages come from the picker
    assert chat_core.language("en", "Is the 65W model safe?") == "en"
    assert "Reply language: Thai" in chat_core.prepare("unmatched", "ปลอดภัยไหม", "th", "{}", None, None)[0]
