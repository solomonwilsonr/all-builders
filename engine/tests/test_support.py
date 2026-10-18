"""engine.support: the site's Help chat answers from the site's own sections and never cites one that isn't there."""
import pytest

from engine import gemini, support


@pytest.fixture()
def fake(monkeypatch):
    seen = {}

    def structured(prompt, schema, models=None, timeout_s=30):
        seen["prompt"] = prompt
        return dict(seen.get("reply") or {}, model="fake")

    monkeypatch.setattr(gemini, "structured", structured)
    return seen


def test_the_real_knowledge_file_covers_the_site():
    kb = support.knowledge()
    pages = {c["url"].split("#")[0] for c in kb.values()}
    assert {"index.html", "how.html", "agents.html", "results.html", "team.html", "get.html", "chat.html"} <= pages
    assert any("5 live checks a day" in c["text"] for c in kb.values())


def test_sources_are_only_real_sections_one_per_page_section(fake):
    kb = support.knowledge()
    real = next(c for c in kb.values() if c["title"] == "Signing in, guest checks and limits")
    fake["reply"] = {"answer": "1 check as a guest, 5 a day signed in.", "kind": "answered",
                     "sources": [real["id"], "S9999", real["id"]]}
    out = support.ask({"question": "How many free checks do I get?"})
    assert out["answer"].startswith("1 check")
    assert [s["id"] for s in out["sources"]] == [real["id"]]
    assert out["handoff"] is None and out["model_version"] == "fake"


def test_a_product_check_is_handed_to_eddy(fake):
    fake["reply"] = {"answer": "Eddy on the Chat page checks products.", "kind": "product_check", "sources": []}
    out = support.ask({"question": "is amazon.in/dp/B0CX65SFC safe?"})
    assert out["kind"] == "product_check" and out["handoff"]["url"] == "chat.html"


def test_the_prompt_holds_the_site_and_only_recent_turns(fake):
    fake["reply"] = {"answer": "ok", "kind": "answered", "sources": []}
    history = [{"role": "user", "text": f"turn {n}"} for n in range(10)]
    support.ask({"question": "and on my phone?", "history": history, "language": "हिन्दी"})
    prompt = fake["prompt"]
    assert "[S1]" in prompt and "हिन्दी" in prompt and "and on my phone?" in prompt
    assert "turn 9" in prompt and "turn 3" not in prompt


@pytest.mark.parametrize("body", [{}, {"question": "   "}, {"question": 7}, {"question": "x" * 1001}])
def test_bad_questions_are_refused(fake, body):
    with pytest.raises(ValueError):
        support.ask(body)
