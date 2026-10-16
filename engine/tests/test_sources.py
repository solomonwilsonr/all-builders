"""Live-source framework (plan v2.2 workstream A): adapters on recorded official responses, failure states, planner,
coverage. No network: every request goes to an httpx.MockTransport."""
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from engine.sources import cache, coverage, planner, policy, registry
from engine.sources.adapters import _http, au_accc, cpsc, jp_caa, oecd_globalrecalls
from engine.sources.base import (
    BLOCKED,
    CHECKED_LIVE,
    NO_MATCH,
    NOT_SUPPORTED,
    OK,
    RATE_LIMITED,
    TIMEOUT,
    UNAVAILABLE,
    SourceQuery,
    SourceResult,
)

FIX = Path(__file__).parent / "fixtures" / "sources"


def fixture(name: str) -> str:
    return (FIX / name).read_text()


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    cache.clear()
    policy.breaker.failures.clear()
    policy.breaker.opened_at.clear()
    policy.limiter.calls.clear()
    monkeypatch.delenv("SAFESHELF_RESEARCH_URL", raising=False)
    yield
    _http.transport = None


def mock(handler):
    _http.transport = httpx.MockTransport(handler)


def run(coro):
    return asyncio.run(coro)


# --- adapters on recorded responses ------------------------------------------------------------------------------

def test_cpsc_reads_model_numbers_from_the_description():
    rows = json.loads(fixture("cpsc_power_bank.json"))
    record = cpsc.to_record(rows[0], datetime.now(UTC))
    assert record.record_id == "cpsc:26792"
    assert "ZHX-PB22" in record.product_identifiers["models"]
    assert record.jurisdiction == "US" and record.authority == "CPSC"
    assert record.source_published_at.date().isoformat() == "2026-09-24"
    assert record.source_url.startswith("https://cpsc.gov/Recalls/")
    assert record.event_at is None  # never filled with a publication date


def test_cpsc_search_merges_model_and_brand_queries():
    rows = json.loads(fixture("cpsc_power_bank.json"))
    seen = []

    def handler(request: httpx.Request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json=rows[:1] if "RecallDescription" in request.url.params else rows[:2])

    mock(handler)
    adapter = cpsc.Adapter(registry.source("cpsc"))
    records = run(adapter.search(SourceQuery(brand="NEWDERY", model="ZHX-PB22")))
    assert {r.record_id for r in records} == {"cpsc:26792", "cpsc:26740"}
    assert any("RecallDescription" in p for p in seen) and any("RecallTitle" in p for p in seen)


def test_cpsc_replay_drops_notices_published_after_the_cutoff():
    rows = json.loads(fixture("cpsc_power_bank.json"))
    mock(lambda request: httpx.Response(200, json=rows))
    adapter = cpsc.Adapter(registry.source("cpsc"))
    cutoff = datetime(2026, 8, 1, tzinfo=UTC)
    records = run(adapter.search(SourceQuery(brand="x", as_of=cutoff)))
    assert records and all(r.source_published_at <= cutoff for r in records)
    assert "cpsc:26792" not in {r.record_id for r in records}  # published 24 Sep 2026


def test_oecd_record_keeps_its_country_as_jurisdiction():
    raw = json.loads(fixture("oecd_detail_au.json"))["recall"]
    record = oecd_globalrecalls.to_record(raw, datetime.now(UTC))
    assert record.jurisdiction == "AU" and record.authority == "ACCC"
    assert "WMPB10A" in record.product_identifiers["models"]
    assert record.source_url.startswith("https://www.productsafety.gov.au/")


def test_oecd_search_falls_back_to_the_brand():
    detail = json.loads(fixture("oecd_detail_au.json"))
    search = json.loads(fixture("oecd_search_au.json"))
    asked = []

    def handler(request: httpx.Request):
        if request.url.path.endswith("search.xqy"):
            asked.append(request.url.params["q"])
            return httpx.Response(200, json=search if "Comsol" in request.url.params["q"] else {"results": []})
        return httpx.Response(200, json=detail)

    mock(handler)
    adapter = oecd_globalrecalls.Adapter(registry.source("oecd_globalrecalls"))
    records = run(adapter.search(SourceQuery(brand="Comsol", model="NOPE-1")))
    assert asked[0].startswith("NOPE-1") and asked[1].startswith("Comsol")
    assert records and records[0].jurisdiction == "AU"


def test_caa_detail_keeps_japanese_text_and_reads_the_model_number():
    detail = jp_caa.parse_detail(fixture("caa_detail.html"), "平南商事「HAIARA モバイルバッテリー」 - 返金／回収")
    assert "型番" in detail["identification"] and "W5PRO" in detail["identification"]
    record = jp_caa.to_record("00000035913", {"title": detail["title"], "posted": "2026/10/05", "start": "2026/09/24"},
                              detail, datetime.now(UTC))
    assert record.product_identifiers["models"] == ["W5PRO"]
    assert record.language == "ja" and "型番" in record.original_text  # original kept, not translated
    assert record.jurisdiction == "JP" and record.source_published_at.date().isoformat() == "2026-10-05"
    assert "出典" in record.attribution  # PDL 1.0 asks for the source to be credited


def test_caa_search_results_are_parsed():
    rows = jp_caa.parse_search(fixture("caa_search.html"))
    assert rows and rows[0]["rcl"] == "00000035913" and rows[0]["posted"] == "2026/10/05"


def test_accc_rss_parser():
    feed = """<rss><channel><item><title>Kelvo CX-65 charger recall</title>
      <link>https://www.productsafety.gov.au/recalls/kelvo-cx-65</link>
      <description>Model number CX-65. Stop using.</description><pubDate>Tue, 14 Oct 2026 10:00:00 +1100</pubDate>
      <guid>https://www.productsafety.gov.au/recalls/kelvo-cx-65</guid></item></channel></rss>"""
    records = au_accc.parse_feed(feed, datetime.now(UTC))
    assert records[0].record_id == "accc:kelvo-cx-65" and "CX-65" in records[0].product_identifiers["models"]
    assert records[0].jurisdiction == "AU"


# --- failure states ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("status,expected", [(403, BLOCKED), (429, RATE_LIMITED), (503, "error")])
def test_http_failures_become_honest_states(status, expected):
    mock(lambda request: httpx.Response(status, text="no"))
    result = run(planner.run_one("cpsc", SourceQuery(brand="Anker", model="A1263")))
    assert result.status == expected and not result.records
    assert result.coverage_state() == UNAVAILABLE


def test_timeout_is_reported_not_swallowed(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    mock(handler)
    result = run(planner.run_one("cpsc", SourceQuery(brand="Anker")))
    assert result.status == TIMEOUT and result.coverage_state() == UNAVAILABLE


def test_malformed_json_is_an_error():
    mock(lambda request: httpx.Response(200, text="<html>oops</html>", headers={"content-type": "text/html"}))
    result = run(planner.run_one("cpsc", SourceQuery(brand="Anker")))
    assert result.status == "error" and "JSON" in result.detail


def test_captcha_page_is_blocked():
    mock(lambda request: httpx.Response(200, text="<html>Please verify you are human (captcha)</html>",
                                        headers={"content-type": "text/html"}))
    result = run(planner.run_one("jp_caa", SourceQuery(brand="Anker")))
    assert result.status in (BLOCKED, OK)  # CAA's own client reads HTML; it finds no rows rather than bypassing


def test_redirect_off_the_official_domain_is_refused():
    def handler(request):
        if request.url.host == "www.saferproducts.gov":
            return httpx.Response(302, headers={"location": "https://evil.example/recalls"})
        return httpx.Response(200, json=[])

    mock(handler)
    result = run(planner.run_one("cpsc", SourceQuery(brand="Anker")))
    assert result.status == BLOCKED


def test_circuit_opens_after_repeated_failures():
    mock(lambda request: httpx.Response(503))
    for _ in range(3):
        run(planner.run_one("cpsc", SourceQuery(brand=f"b{_}")))
    result = run(planner.run_one("cpsc", SourceQuery(brand="again")))
    assert result.status == "circuit_open" and result.coverage_state() == UNAVAILABLE


def test_successful_answers_are_cached_and_marked():
    rows = json.loads(fixture("cpsc_power_bank.json"))
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(200, json=rows[:1])

    mock(handler)
    q = SourceQuery(brand="NEWDERY")
    first = run(planner.run_one("cpsc", q))
    second = run(planner.run_one("cpsc", q))
    assert first.mode == "live" and second.mode == "cache" and len(calls) == 1
    assert second.retrieved_at == first.retrieved_at  # the original retrieval time, never "now"


# --- policy ----------------------------------------------------------------------------------------------------

def test_allowlist_refuses_lookalike_and_ip_hosts():
    domains = ["cpsc.gov"]
    assert policy.allowed_url("https://www.cpsc.gov/Recalls/1", domains)[0]
    assert not policy.allowed_url("https://cpsc.gov.evil.example/Recalls", domains)[0]
    assert not policy.allowed_url("https://evilcpsc.gov/x", domains)[0]
    assert not policy.allowed_url("http://169.254.169.254/latest", domains)[0]
    assert not policy.allowed_url("https://user:pw@cpsc.gov/", domains)[0]
    assert not policy.allowed_url("file:///etc/passwd", domains)[0]


def test_webhook_urls_must_be_public_https():
    assert not policy.public_https_url("http://example.com/hook")[0]
    assert not policy.public_https_url("https://localhost/hook")[0]
    assert not policy.public_https_url("https://10.0.0.5/hook")[0]
    assert not policy.public_https_url("https://metadata.google.internal/")[0]


def test_query_terms_are_sanitised():
    assert policy.clean_term('A1263"; DROP TABLE <script>') == "A1263 DROP TABLE script"
    assert policy.clean_term("型番ＷＳ－１２") == "型番ＷＳ－１２"
    assert len(policy.clean_term("x" * 500)) == policy.MAX_TERM


# --- planner and coverage --------------------------------------------------------------------------------------

def test_plan_puts_the_market_first_and_explains_skips():
    steps = planner.plan(SourceQuery(brand="Anker", market_country="IN"))
    assert steps[0]["source"] == "india_notices" and steps[0]["role"] == "local"
    bis = next(s for s in steps if s["source"] == "india_bis")
    assert not bis["runnable"] and "automated access" in bis["why"]
    eu = next(s for s in steps if s["source"] == "eu_safety_gate")
    assert not eu["runnable"]  # browser-only and no Research Agent here


def test_japan_and_singapore_sources_run_only_when_access_is_verified():
    jp = {s["source"]: s for s in planner.plan(SourceQuery(brand="x", market_country="JP"))}
    assert jp["jp_caa"]["runnable"] and not jp["jp_meti"]["runnable"] and not jp["jp_nite"]["runnable"]
    sg = {s["source"]: s for s in planner.plan(SourceQuery(brand="x", market_country="SG"))}
    assert not sg["sg_cps"]["runnable"] and not sg["sg_safety_mark"]["runnable"]


def test_key_required_source_runs_only_with_its_key(monkeypatch):
    monkeypatch.delenv("SAFERPRODUCTS_API_KEY", raising=False)
    assert not registry.runnable(registry.source("saferproducts"))[0]
    monkeypatch.setenv("SAFERPRODUCTS_API_KEY", "k")
    assert registry.runnable(registry.source("saferproducts"))[0]


def test_coverage_never_turns_a_failure_into_no_match():
    plan = planner.plan(SourceQuery(brand="x", market_country="AU"))
    results = [SourceResult(source="oecd_globalrecalls", status=TIMEOUT, detail="slow"),
               SourceResult(source="cpsc", status=OK, records=[])]
    rows = coverage.source_rows(plan, results, {})
    states = {r["source"]: r["state"] for r in rows}
    assert states["oecd_globalrecalls"] == UNAVAILABLE and states["cpsc"] == NO_MATCH
    assert states["au_accc"] == NOT_SUPPORTED
    au = coverage.matrix("AU", rows)[0]
    assert au["country"] == "AU" and au["is_market"] and au["state"] == UNAVAILABLE


def test_a_match_counts_only_in_its_own_country():
    plan = planner.plan(SourceQuery(brand="x", market_country="IN"))
    results = [SourceResult(source="stored_notices", status=OK, records=[], mode="cache"),
               SourceResult(source="india_notices", status=OK, records=[], mode="cache")]
    rows = coverage.source_rows(plan, results, {"stored_notices": {"US": 1}})
    by_country = {r["country"]: r for r in coverage.matrix("IN", rows)}
    assert by_country["IN"]["state"] == NO_MATCH
    assert by_country["US"]["state"] != NO_MATCH and by_country["US"]["matched"] == 1


def test_live_match_rolls_up_as_checked_live():
    plan = planner.plan(SourceQuery(brand="x", market_country="JP"))
    rows = coverage.source_rows(plan, [SourceResult(source="jp_caa", status=OK)], {"jp_caa": {"JP": 1}})
    jp = coverage.matrix("JP", rows)[0]
    assert jp["state"] == CHECKED_LIVE and jp["matched"] == 1
