"""Build the API docs data (site/api-endpoints.json) from the contract, so site/api.html never drifts from it.

    python3 web/build_api_docs.py

Every operation in contracts/openapi.yaml, grouped the way a builder reaches for them, with its parameters, a
request example and the example answer from contracts/mock/ (trimmed). Run by `make deploy-web`.
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = yaml.safe_load((ROOT / "contracts" / "openapi.yaml").read_text())
OUT = Path(__file__).parent / "site" / "api-endpoints.json"
MAX_LINES = 40

# (group id, title, blurb, test on path and operationId). First match wins, so the order matters.
GROUPS = [
    ("check", "Check a listing", "Start here: a listing URL or the page's own data in, an answer with its evidence out.",
     lambda p, o: p.startswith(("/v1/listings/", "/v1/agent/", "/v1/investigations")) or p == "/v1/products/identify"),
    ("product", "Product record", "Everything SafeShelf knows about one product, by the product_id that identify returns.",
     lambda p, o: p.startswith("/v1/products/")),
    ("recalls", "Recalls and early warnings", "Official notices from 12 countries, and the signals that come before them.",
     lambda p, o: p.startswith(("/v1/recalls", "/v1/sources", "/v1/cross-border", "/v1/radar", "/v1/incidents"))),
    ("shopper", "For shoppers", "Camera, voice, saved products and what to do after buying.",
     lambda p, o: p.startswith(("/v1/camera", "/v1/voice", "/v1/watchlists", "/v1/household", "/v1/shelf",
                                "/v1/after-purchase", "/v1/support")) or p == "/v1/reports"),
    ("review", "People in the loop", "A person decides every consequential finding. These need a reviewer key.",
     lambda p, o: p.startswith(("/v1/identity", "/v1/reports/", "/v1/reviews", "/v1/cases"))),
    ("platform", "Marketplaces and developers", "Catalog scans, signed webhooks and your own usage.",
     lambda p, o: p.startswith(("/v1/catalog", "/v1/webhooks", "/v1/developer"))),
    ("proof", "Proof and audit", "Benchmarks, red-team rounds, evidence records and the step-by-step trace.",
     lambda p, o: True),
]
# Calls a visitor may run from the page: read-only and not metered against the AI-check limit (or cheap and cached).
RUNNABLE = {"getSafety", "getCertifications", "getProduct", "getHistory", "getAlternatives", "getRelationships",
            "getOwnerGuidance", "getCaseFile", "getTimeline", "getCrossBorder", "getSupplyChain", "listRecalls",
            "getRecall", "getSourcesHealth", "getRadarCandidates", "getCrossBorderCandidates", "getIncidentSignals",
            "getRedteamRounds", "getBenchResults", "getBenchRuns", "getBenchEvidence", "trustCheck"}
REVIEWER = {"identityFeedback", "reviewReport", "getReviewQueue", "decideReview", "transitionCase"}
INTERNAL = {"recheckWatchlists"}
DEVELOPER = {"getDeveloperUsage", "createWebhook", "catalogScan"}
# Demo values for path parameters, so a Run works as it stands.
PATH_DEFAULTS = {"product_id": "SS-P-10291", "recall_id": "", "investigation_id": "", "report_id": "",
                 "case_id": "", "watchlist_id": "", "item_id": ""}
SAMPLE = {"url": "https://example-deals-store.test/65w-charger", "title": "65W Super Fast Charger - Kelvo CX-65 Original",
          "price": 299, "currency": "INR", "seller": "MegaDealz24", "product_id": "SS-P-10291", "language": "en",
          "mode": "investigate", "message": "Is this charger safe to buy?", "country": "IN"}


def resolve(node: dict) -> dict:
    """Follow a $ref (#/components/...) to its target."""
    seen = 0
    while isinstance(node, dict) and "$ref" in node and seen < 10:
        target = SPEC
        for part in node["$ref"].lstrip("#/").split("/"):
            target = target[part]
        node, seen = target, seen + 1
    return node


def sample_body(schema: dict, depth: int = 0) -> object:
    """A small request example from the schema: its own example, else the required and common fields."""
    schema = resolve(schema)
    if "example" in schema:
        return schema["example"]
    if schema.get("type") == "array":
        return [sample_body(schema.get("items") or {}, depth + 1)]
    props = schema.get("properties") or {}
    if not props or depth > 1:
        return {"string": "text", "number": 1, "integer": 1, "boolean": True}.get(schema.get("type"), {})
    keep = [k for k in props if k in (schema.get("required") or []) or k in SAMPLE] or list(props)[:3]
    out = {}
    for key in keep[:6]:
        prop = resolve(props[key])
        if key in SAMPLE:
            out[key] = SAMPLE[key]
        elif "enum" in prop:
            out[key] = prop["enum"][0]
        elif "default" in prop:
            out[key] = prop["default"]
        else:
            out[key] = sample_body(prop, depth + 1)
    return out


def trimmed(value: object) -> str:
    lines = json.dumps(value, indent=2, ensure_ascii=False).splitlines()
    return "\n".join(lines[:MAX_LINES] + (["  …"] if len(lines) > MAX_LINES else []))


def mock_example(name: str | None) -> tuple[str, object]:
    if not name or not (ROOT / "contracts" / "mock" / name).exists():
        return "", None
    body = json.loads((ROOT / "contracts" / "mock" / name).read_text())
    return trimmed(body), body


def first_id(body: object, key: str) -> str:
    """An id from the example answer (a recall_id from the recall list, say), for a Run that works."""
    if isinstance(body, dict):
        if isinstance(body.get(key), str):
            return body[key]
        values = body.values()
    elif isinstance(body, list):
        values = body
    else:
        return ""
    for v in values:
        if found := first_id(v, key):
            return found
    return ""


def main() -> None:
    groups = {g[0]: {"id": g[0], "title": g[1], "blurb": g[2], "ops": []} for g in GROUPS}
    examples = {}
    for path, ops in SPEC["paths"].items():
        for method, op in ops.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            example, body = mock_example(op.get("x-mock"))
            examples[op["operationId"]] = body
            params = []
            for raw in op.get("parameters") or []:
                p = resolve(raw)
                params.append({"name": p["name"], "in": p["in"], "required": bool(p.get("required")),
                               "description": (p.get("description") or "").strip()})
            request = None
            if content := (op.get("requestBody") or {}).get("content", {}).get("application/json"):
                request = sample_body(content.get("schema") or {})
                if op["operationId"] == "trustCheck":
                    request = {k: SAMPLE[k] for k in ("url", "title", "price", "currency", "seller")}
            oid = op["operationId"]
            access = ("reviewer key" if oid in REVIEWER else "internal key" if oid in INTERNAL
                      else "developer key" if oid in DEVELOPER else "public")
            entry = {"id": oid, "method": method.upper(), "path": path, "summary": op.get("summary") or "",
                     "description": (op.get("description") or "").strip().split("\n\n")[0],
                     "params": params, "request": request, "example": example, "access": access,
                     "runnable": oid in RUNNABLE}
            group = next(g[0] for g in GROUPS if g[3](path, op))
            groups[group]["ops"].append(entry)
    # Fill path ids from other examples so Run works: the recall list names a recall, and so on.
    sources = {"recall_id": "listRecalls", "investigation_id": "getInvestigation", "case_id": "getReviewQueue"}
    defaults = dict(PATH_DEFAULTS)
    for key, oid in sources.items():
        defaults[key] = first_id(examples.get(oid), key) or defaults[key]
    for g in groups.values():
        for op in g["ops"]:
            for p in op["params"]:
                if p["in"] == "path":
                    p["default"] = defaults.get(p["name"], "")
    data = {"title": SPEC["info"]["title"], "version": SPEC["info"]["version"],
            "count": sum(len(g["ops"]) for g in groups.values()), "groups": list(groups.values())}
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"{OUT.relative_to(ROOT)}: {data['count']} operations, {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
