"""Every endpoint in contracts/openapi.yaml must have a mock and be served by the API."""
import json
import re

import pytest
from fastapi.testclient import TestClient

from app.main import CONTRACTS_DIR, app, spec

client = TestClient(app)

OPERATIONS = [
    (path, method, op)
    for path, methods in spec["paths"].items()
    for method, op in methods.items()
]

# Minimal valid request bodies, by operationId.
BODIES = {
    "identifyProduct": {"url": "https://example-deals-store.test/65w-charger"},
    "findDuplicates": {"product_id": "SS-P-10291"},
    "trustCheck": {"url": "https://example-deals-store.test/65w-charger"},
    "listingSafetyCheck": {"url": "https://www.amazon.in/dp/B0DT3HZQ5K", "title": "JETech Case",
                           "reviews": [{"text": "Fits well, clear after a month.", "rating": 5}]},
    "listingReviewVerdict": {"url": "https://www.amazon.in/dp/B0DT3HZQ5K", "title": "JETech Case",
                             "rating_summary": {"average": 4.1, "count": 3412,
                                                "distribution": {"5": 58, "4": 18, "3": 8, "2": 5, "1": 11}},
                             "reviews": [{"text": "Fits well, clear after a month.", "rating": 5}]},
    "listingPriceBenchmark": {"url": "https://www.amazon.in/dp/B0DT3HZQ5K", "title": "60W USB-C Charger", "price": 299, "currency": "INR"},
    "listingClaimsCheck": {"url": "https://www.amazon.in/dp/B0DT3HZQ5K", "title": "60W USB-C Charger", "price": 299, "currency": "INR"},
    "listingAge": {"url": "https://www.amazon.in/dp/B0DT3HZQ5K", "first_available": "5 October 2026"},
    "listingOfficialSeller": {"url": "https://www.amazon.in/dp/B0DT3HZQ5K", "title": "boAt Airdopes", "seller": "Random Traders", "page_text": "Brand\tboAt"},
    "createReport": {"product_id": "SS-P-10291", "description": "Port melted"},
    "addShelfItem": {"product_id": "SS-P-10291"},
    "catalogScan": {"csv_url": "gs://safeshelf-demo/catalog.csv"},
    "startAgentSession": {"mode": "chat", "product_id": "SS-P-10291"},
    "askSupport": {"question": "How many free checks do I get?"},
}


def fill(path: str) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: {"product_id": "SS-P-20019"}.get(m.group(1), "SS-I-0001"), path)


@pytest.mark.parametrize("path,method,op", OPERATIONS, ids=[op["operationId"] for _, _, op in OPERATIONS])
def test_endpoint_serves_its_mock(path, method, op):
    mock_file = CONTRACTS_DIR / "mock" / op["x-mock"]
    assert mock_file.exists(), f"missing mock {mock_file.name}"
    expected_status = int(next(iter(op["responses"])))

    response = client.request(method.upper(), fill(path), json=BODIES.get(op["operationId"]))

    assert response.status_code == expected_status
    assert response.headers["X-SafeShelf-Source"] == "mock"
    body = response.json()
    if "{product_id}" in path and "product_id" in body:
        assert body["product_id"] == "SS-P-20019"


def test_every_mock_file_is_used():
    used = {op["x-mock"] for _, _, op in OPERATIONS}
    on_disk = {p.name for p in (CONTRACTS_DIR / "mock").glob("*.json")}
    assert on_disk == used


def test_demo_ids_are_consistent():
    demo = json.loads((CONTRACTS_DIR / "demo_products.json").read_text())
    assert "SS-P-10291" in {p["product_id"] for p in demo["products"]}


def test_health():
    assert client.get("/health").json()["ok"] is True


def test_docs_show_contract_with_examples():
    doc = client.get("/openapi.json").json()
    op = doc["paths"]["/v1/products/identify"]["post"]
    assert "requestBody" in op
    assert op["responses"]["200"]["content"]["application/json"]["example"]


def test_mcp_lists_tools_and_answers_from_the_api():
    headers = {"accept": "application/json, text/event-stream"}
    with TestClient(app) as mcp_client:  # the MCP session manager runs in the app's lifespan
        tools = mcp_client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {t["name"] for t in tools.json()["result"]["tools"]}
        assert {"identify_product", "product_safety", "check_listing", "safer_alternatives"} <= names
        call = mcp_client.post("/mcp", headers=headers, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "safer_alternatives", "arguments": {"product_id": "SS-P-20019"}}})
        assert json.loads(call.json()["result"]["content"][0]["text"])["product_id"] == "SS-P-20019"


def test_limiter_per_caller_and_per_day():
    from app.main import Limiter

    lim = Limiter(per_minute=2, per_day=3)
    assert lim.check("a", 0) is None and lim.check("a", 1) is None
    assert "a minute" in lim.check("a", 2)          # third in the same minute
    assert lim.check("b", 3) is None                # other callers unaffected
    assert lim.check("a", 70) is not None and "daily" in lim.check("a", 70)  # window cleared, day cap of 3 hit
    assert lim.check("a", 86_400 * 2) is None        # a new day starts over


def test_a_screenshot_fits_and_refusals_carry_cors_headers():
    """A phone screenshot (1.6 MB) for the chat was refused with no CORS header: the browser said "Failed to fetch"."""
    origin = {"Origin": "http://localhost:8090"}
    screenshot = {"mode": "chat", "product_id": "SS-P-10291", "image": "data:image/png;base64," + "A" * 2_000_000}
    assert client.post("/v1/agent/sessions", json=screenshot, headers=origin).status_code != 413
    too_big = client.post("/v1/agent/sessions", content=b"x" * 9_500_000,
                          headers={**origin, "content-type": "application/json"})
    assert too_big.status_code == 413 and "at most 9 MB" in too_big.json()["detail"]
    assert too_big.headers["access-control-allow-origin"] == "*"
    big_listing = client.post("/v1/listings/trust-check", content=b"x" * 1_500_000,
                              headers={**origin, "content-type": "application/json"})
    assert big_listing.status_code == 413 and big_listing.headers["access-control-allow-origin"] == "*"
