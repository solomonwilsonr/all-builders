"""Real handlers the API registers (api/app/main.py REAL_HANDLERS) when MOCK=0 and DATABASE_URL is set."""
import json
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from engine import (
    after_purchase,
    camera,
    case_file,
    cases,
    catalog,
    claims_check,
    crossborder,
    evidence,
    gemini,
    hazard_discovery,
    household,
    identity,
    incidents,
    investigation,
    marks,
    official_seller,
    owner,
    page_safety,
    passport,
    point_and_ask,
    price_benchmark,
    recall_catalog,
    redteam,
    review_verdict,
    reviews,
    safety,
    supply_chain,
    support,
    tenancy,
    trace,
    trust,
    voice,
    watch,
    webhooks,
)
from engine import (
    listing_age as listing_age_module,
)
from engine.agents import handler as agent_handler
from engine.sources import health as source_health

log = logging.getLogger(__name__)


async def identify_product(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    if not any(listing.get(k) for k in ("url", "title", "page_text", "image_urls")):
        raise HTTPException(status_code=422, detail="Give at least a url, title, page_text or image_urls")
    return await run_in_threadpool(identity.identify, listing)


async def find_duplicates(request: Request, params: dict[str, Any]) -> dict:
    body = await request.json()
    try:
        return await run_in_threadpool(identity.duplicates, body["product_id"], bool(body.get("refresh")))
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None


async def get_relationships(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(identity.relationships, params["product_id"])


async def get_safety(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(safety.safety, params["product_id"])
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None


async def get_certifications(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(marks.certifications, params["product_id"])
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None


async def trust_check(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    if not any(listing.get(k) for k in ("url", "title", "page_text", "image_urls")):
        raise HTTPException(status_code=422, detail="Give at least a url, title, page_text or image_urls")
    return await run_in_threadpool(trust.trust_check, listing)


async def listing_safety_check(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    if not any(listing.get(k) for k in ("url", "title")):
        raise HTTPException(status_code=422, detail="Give at least a url or title")
    return await run_in_threadpool(page_safety.listing_safety, listing)


async def listing_price_benchmark(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    if not any(listing.get(k) for k in ("url", "title")):
        raise HTTPException(status_code=422, detail="Give at least a url or title")
    def run() -> dict:
        refs, kind = price_benchmark.references_for(listing, gemini.grounded)
        return price_benchmark.benchmark(listing, refs, kind)
    return await run_in_threadpool(run)


async def listing_age(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    return await run_in_threadpool(listing_age_module.assess, listing)  # plain rules on a date: no Gemini, no database


async def listing_official_seller(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    return await run_in_threadpool(official_seller.assess, listing)  # plain rules on the registry: no Gemini, no database


async def listing_claims_check(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    if not any(listing.get(k) for k in ("url", "title")):
        raise HTTPException(status_code=422, detail="Give at least a url or title")
    return await run_in_threadpool(claims_check.check, listing, gemini.grounded)


async def listing_review_verdict(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    if not any(listing.get(k) for k in ("url", "title")):
        raise HTTPException(status_code=422, detail="Give at least a url or title")
    return await run_in_threadpool(review_verdict.review_verdict, listing)


async def get_evidence(request: Request, params: dict[str, Any]) -> list[dict]:
    ids = request.query_params.get("ids") or ""
    if not ids.strip():
        raise HTTPException(status_code=422, detail="Give ids, e.g. ?ids=EV-1F3B0227,EV-08E9C38D")
    return await run_in_threadpool(evidence.lookup, ids)


def by_product(fn):
    """GET /v1/products/{product_id}/... handler: unknown product -> 404."""
    async def handler(request: Request, params: dict[str, Any]) -> dict:
        try:
            return await run_in_threadpool(fn, params["product_id"])
        except KeyError as missing:
            raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None
    return handler


async def create_report(request: Request, params: dict[str, Any]) -> dict:
    body = await request.json()
    if not body.get("product_id") or not body.get("description"):
        raise HTTPException(status_code=422, detail="Give a product_id and a description")
    try:
        # The reporter is stored only as a hash (Firebase uid or WhatsApp number from the calling screen or bot).
        return await run_in_threadpool(passport.create_report, body, request.headers.get("x-reporter-ref"))
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None


async def bench_results(request: Request, params: dict[str, Any]) -> dict:
    return passport.bench_results()


async def get_trace(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(trace.get_trace, params["investigation_id"])
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown investigation {missing}") from None


def traced(operation_id: str, handler):
    """With an X-Investigation-Id header, the answer is also recorded as a step of that investigation."""
    async def wrapper(request: Request, params: dict[str, Any]) -> dict:
        investigation_id = request.headers.get("x-investigation-id")
        if not investigation_id:
            return await handler(request, params)
        if not trace.VALID_ID.match(investigation_id):
            raise HTTPException(status_code=422, detail="X-Investigation-Id: letters, digits and ._:- only")
        calls = gemini.track()  # copied into the worker thread by run_in_threadpool
        started = time.monotonic()
        body = await handler(request, params)
        await run_in_threadpool(trace.record, investigation_id, operation_id, time.monotonic() - started, calls, body)
        return body
    return wrapper


async def list_recalls(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(recall_catalog.search, dict(request.query_params))
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem)) from None


async def get_recall(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(recall_catalog.recall, params["recall_id"])
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown recall {missing}") from None


async def catalog_scan(request: Request, params: dict[str, Any]) -> dict:
    body = await request.json()
    try:
        return await run_in_threadpool(catalog.scan, body)
    except ValueError as problem:  # missing or unreadable CSV, no title column
        raise HTTPException(status_code=422, detail=str(problem)) from None


# --- plan v2.2: live investigations, sources, watchlists, review, enterprise ---------------------------------------

BENCH = Path(__file__).resolve().parents[1] / "bench"
INVESTIGATION_FIELDS = ("url", "title", "brand", "model", "gtin", "batch", "product_id", "market", "currency", "depth",
                        "reviews", "as_of", "page_text", "category", "local_identifiers")


def who(request: Request) -> tenancy.Caller:
    """The caller, resolved once per request by tenant_guard (public when no key)."""
    return getattr(request.state, "caller", None) or tenancy.Caller()


def need(request: Request, scope: str) -> tenancy.Caller:
    caller = who(request)
    try:
        tenancy.require(caller, scope)
    except PermissionError as problem:
        raise HTTPException(status_code=403, detail=str(problem)) from None
    return caller


async def body_of(request: Request) -> dict:
    try:
        body = await request.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def bad_request(fn):
    """ValueError -> 422 and KeyError -> 404, so engine modules can stay free of HTTP."""
    async def handler(request: Request, params: dict[str, Any]):
        try:
            return await fn(request, params)
        except ValueError as problem:
            raise HTTPException(status_code=422, detail=str(problem)) from None
        except KeyError as missing:
            raise HTTPException(status_code=404, detail=f"Not found: {missing}") from None
        except RuntimeError as problem:  # a feature not configured on this server
            raise HTTPException(status_code=503, detail=str(problem)) from None
    return handler


@bad_request
async def create_investigation(request: Request, params: dict[str, Any]) -> dict:
    body = await body_of(request)
    if body.get("image"):
        raise ValueError("send label photos to POST /v1/camera/label first, then investigate the confirmed fields")
    req = {k: body[k] for k in INVESTIGATION_FIELDS if body.get(k) not in (None, "", [])}
    if not any(req.get(k) for k in ("url", "title", "brand", "model", "gtin", "product_id")):
        raise ValueError("Give at least a url, title, brand, model, gtin or product_id")
    caller = who(request)
    key = request.headers.get("idempotency-key")
    stored = await run_in_threadpool(tenancy.idempotent, caller, key, req) if key else None
    if stored:
        return stored
    if req.get("depth") == "deep":
        answer = await run_in_threadpool(investigation.start, req, caller.tenant_id)
    else:
        answer = await run_in_threadpool(investigation.investigate, req, None, caller.tenant_id)
        await run_in_threadpool(webhooks.emit, caller.tenant_id, "investigation.complete",
                                {k: answer.get(k) for k in ("investigation_id", "outcome", "headline", "market",
                                                            "product", "snapshot_id")})
    if key:
        await run_in_threadpool(tenancy.remember, caller, key, req, answer)
    return answer


@bad_request
async def get_investigation(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(investigation.get, params["investigation_id"], who(request).tenant_id)


@bad_request
async def get_investigation_sources(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(investigation.sources, params["investigation_id"], who(request).tenant_id)


async def get_sources_health(request: Request, params: dict[str, Any]) -> dict:
    return source_health.report()


@bad_request
async def recheck_product(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(investigation.investigate, {"product_id": params["product_id"]}, None,
                                   who(request).tenant_id)


@bad_request
async def read_label(request: Request, params: dict[str, Any]) -> dict:
    body = await body_of(request)
    return await run_in_threadpool(camera.read_label, body.get("image") or "")


@bad_request
async def point_ask(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(point_and_ask.ask, await body_of(request), who(request).tenant_id)


@bad_request
async def speak_verdict(request: Request, params: dict[str, Any]) -> dict:
    body = await body_of(request)
    return await run_in_threadpool(voice.spoken, body, body.get("language"))


@bad_request
async def after_purchase_guide(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(after_purchase.guide, await body_of(request), who(request).tenant_id)


@bad_request
async def report_incident(request: Request, params: dict[str, Any]) -> dict:
    # The reporter is kept only as a hash (the calling screen's user id, like POST /v1/reports).
    return await run_in_threadpool(incidents.report, await body_of(request), request.headers.get("x-reporter-ref"))


async def incident_signals(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(incidents.signals, request.query_params.get("market"))


async def redteam_rounds(request: Request, params: dict[str, Any]) -> dict:
    return redteam.saved()


@bad_request
async def redteam_round(request: Request, params: dict[str, Any]) -> dict:
    body = await body_of(request)
    return await run_in_threadpool(redteam.live_round, body.get("attack") or "", body.get("market") or "US")


def owner_caller(request: Request) -> tenancy.Caller:
    caller = who(request)
    if not caller.owner_ref:
        raise HTTPException(status_code=422, detail="Send X-Owner-Ref (the screen's user id; only a hash is kept)")
    return caller


@bad_request
async def create_watchlist(request: Request, params: dict[str, Any]) -> dict:
    caller = owner_caller(request)
    return await run_in_threadpool(watch.create, caller.tenant_id, caller.owner_ref, await body_of(request))


@bad_request
async def list_watchlists(request: Request, params: dict[str, Any]) -> dict:
    caller = owner_caller(request)
    out = await run_in_threadpool(watch.items, caller.tenant_id, caller.owner_ref)
    out["notifications"] = await run_in_threadpool(watch.notifications, caller.tenant_id, caller.owner_ref)
    return out


@bad_request
async def delete_watchlist(request: Request, params: dict[str, Any]) -> dict:
    caller = owner_caller(request)
    return await run_in_threadpool(watch.delete, caller.tenant_id, caller.owner_ref, params["watchlist_id"])


@bad_request
async def add_household_item(request: Request, params: dict[str, Any]) -> dict:
    caller = owner_caller(request)
    return await run_in_threadpool(household.add, caller.tenant_id, caller.owner_ref, await body_of(request))


@bad_request
async def list_household_items(request: Request, params: dict[str, Any]) -> dict:
    caller = owner_caller(request)
    return await run_in_threadpool(household.items, caller.tenant_id, caller.owner_ref,
                                   request.query_params.get("search"))


@bad_request
async def delete_household_item(request: Request, params: dict[str, Any]) -> dict:
    caller = owner_caller(request)
    return await run_in_threadpool(household.delete, caller.tenant_id, caller.owner_ref, params["item_id"])


@bad_request
async def recheck_watchlists(request: Request, params: dict[str, Any]) -> dict:
    body = await body_of(request)
    token = os.environ.get("SAFESHELF_RECHECK_TOKEN")
    if not (who(request).is_admin or (token and secrets.compare_digest(str(body.get("token") or ""), token))):
        raise HTTPException(status_code=403, detail="Needs the internal key or the re-check token")
    out = await run_in_threadpool(watch.recheck, max(1, min(int(body.get("limit") or 20), 100)))
    try:  # the same daily job reminds owners of return windows and warranties about to end
        out |= await run_in_threadpool(household.remind)
    except Exception as error:  # noqa: BLE001  the household tables may not be migrated yet
        log.warning("household reminders failed: %s", type(error).__name__)
    return out


@bad_request
async def identity_feedback(request: Request, params: dict[str, Any]) -> dict:
    caller = need(request, "reviewer")
    body = await body_of(request)
    return await run_in_threadpool(identity.feedback, body.get("source_id") or "", body.get("target_id") or "",
                                   body.get("label") or "", reviewer_ref(request, caller), body.get("rationale") or "",
                                   body.get("market"))


def reviewer_ref(request: Request, caller: tenancy.Caller) -> str:
    return caller.owner_ref or f"{caller.tenant_id}:reviewer"


@bad_request
async def review_report(request: Request, params: dict[str, Any]) -> dict:
    caller = need(request, "reviewer")
    return await run_in_threadpool(reviews.review_report, caller.tenant_id, reviewer_ref(request, caller),
                                   params["report_id"], await body_of(request))


@bad_request
async def get_review_queue(request: Request, params: dict[str, Any]) -> dict:
    caller = need(request, "reviewer")
    return await run_in_threadpool(reviews.queue, caller.tenant_id, request.query_params.get("state") or "open")


@bad_request
async def decide_review(request: Request, params: dict[str, Any]) -> dict:
    caller = need(request, "reviewer")
    return await run_in_threadpool(reviews.decide, caller.tenant_id, reviewer_ref(request, caller),
                                   params["case_id"], await body_of(request))


@bad_request
async def get_case(request: Request, params: dict[str, Any]) -> dict:
    need(request, "reviewer")
    return await run_in_threadpool(cases.case, params["case_id"])


@bad_request
async def transition_case(request: Request, params: dict[str, Any]) -> dict:
    caller = need(request, "reviewer")
    body = await body_of(request)
    ref = reviewer_ref(request, caller)
    out = await run_in_threadpool(cases.transition, params["case_id"], body.get("to") or "", ref,
                                  body.get("rationale") or "", caller.tenant_id)
    if body.get("action"):
        out["action"] = await run_in_threadpool(cases.prepare_action, params["case_id"], body["action"], ref)
    return out


async def radar_candidates(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(hazard_discovery.candidates)


async def cross_border_candidates(request: Request, params: dict[str, Any]) -> dict:
    found = await run_in_threadpool(crossborder.candidates)
    return {"candidates": found, "total": len(found),
            "note": "Same model code in notices from two countries; tier exact = same company named. Each needs a "
                    "person to check before it is used as a finding."}


@bad_request
async def product_cross_border(request: Request, params: dict[str, Any]) -> dict:
    matches = await run_in_threadpool(crossborder.for_product, params["product_id"])
    return {"product_id": params["product_id"], "matches": matches,
            "note": "A foreign notice is a signal for this market, never a local confirmed recall."}


@bad_request
async def developer_usage(request: Request, params: dict[str, Any]) -> dict:
    caller = need(request, "developer")
    return await run_in_threadpool(tenancy.usage, caller)


@bad_request
async def create_webhook(request: Request, params: dict[str, Any]) -> dict:
    caller = need(request, "developer")
    body = await body_of(request)
    return await run_in_threadpool(webhooks.create, caller.tenant_id, body.get("url") or "", body.get("events") or [])



@bad_request
async def support_ask(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(support.ask, await body_of(request))

async def bench_runs(request: Request, params: dict[str, Any]) -> dict:
    runs = []
    for path in sorted((BENCH / "runs").glob("*.json"), reverse=True):
        try:
            run = json.loads(path.read_text())
        except ValueError:
            continue
        runs.append({k: run.get(k) for k in ("run_id", "benchmark", "created_at", "policy_version", "summary")}
                    | {"path": f"bench/runs/{path.name}"})
    return {"runs": runs}


async def bench_evidence(request: Request, params: dict[str, Any]) -> dict:
    path = BENCH / "evidence_results.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No evidence benchmark run yet (make bench-evidence)")
    return json.loads(path.read_text())


def tenant_guard(operation_id: str, handler):
    """Every engine call: resolve the tenant from X-API-Key (401 for an unknown key), apply the tenant's shared rate
    limit (Postgres, all instances), and meter the call for that tenant's usage report."""
    async def wrapper(request: Request, params: dict[str, Any]):
        try:
            caller = await run_in_threadpool(tenancy.caller, request.headers)
        except PermissionError as problem:
            raise HTTPException(status_code=401, detail=str(problem)) from None
        except Exception:  # noqa: BLE001  tenancy tables missing: treat as public
            caller = tenancy.Caller(owner_ref=tenancy.owner_hash(request.headers.get("x-owner-ref")))
        request.state.caller = caller
        if caller.tenant_id != tenancy.PUBLIC:
            reason = await run_in_threadpool(tenancy.allow, caller, operation_id)
            if reason:
                raise HTTPException(status_code=429, detail=reason, headers={"Retry-After": "60"})
        status = 200
        try:
            return await handler(request, params)
        except HTTPException as problem:
            status = problem.status_code
            raise
        finally:
            if caller.tenant_id != tenancy.PUBLIC:
                await run_in_threadpool(tenancy.meter, caller, operation_id, status)
    return wrapper


HANDLERS = {
    "identifyProduct": identify_product,
    "findDuplicates": find_duplicates,
    "getRelationships": get_relationships,
    "getSafety": get_safety,
    "getCertifications": get_certifications,
    "trustCheck": trust_check,
    "listingSafetyCheck": listing_safety_check,
    "listingReviewVerdict": listing_review_verdict,
    "listingPriceBenchmark": listing_price_benchmark,
    "listingClaimsCheck": listing_claims_check,
    "listingAge": listing_age,
    "listingOfficialSeller": listing_official_seller,
    "getProduct": by_product(passport.product),
    "getHistory": by_product(passport.history),
    "getAlternatives": by_product(passport.alternatives),
    "getCaseFile": by_product(case_file.case_file),
    "getOwnerGuidance": by_product(owner.owner_guidance),
    "createReport": create_report,
    "getBenchResults": bench_results,
    "startAgentSession": agent_handler.start_agent_session,
    "getEvidence": get_evidence,
    "catalogScan": catalog_scan,
    "listRecalls": list_recalls,
    "getRecall": get_recall,
    "createInvestigation": create_investigation,
    "getInvestigation": get_investigation,
    "getInvestigationSources": get_investigation_sources,
    "getSourcesHealth": get_sources_health,
    "recheckProduct": recheck_product,
    "getTimeline": by_product(passport.timeline),
    "getSupplyChain": by_product(supply_chain.build),
    "getCrossBorder": product_cross_border,
    "readLabel": read_label,
    "createWatchlist": create_watchlist,
    "listWatchlists": list_watchlists,
    "deleteWatchlist": delete_watchlist,
    "recheckWatchlists": recheck_watchlists,
    "addHouseholdItem": add_household_item,
    "listHouseholdItems": list_household_items,
    "deleteHouseholdItem": delete_household_item,
    "identityFeedback": identity_feedback,
    "reviewReport": review_report,
    "getReviewQueue": get_review_queue,
    "decideReview": decide_review,
    "getCase": get_case,
    "transitionCase": transition_case,
    "getRadarCandidates": radar_candidates,
    "getCrossBorderCandidates": cross_border_candidates,
    "getDeveloperUsage": developer_usage,
    "createWebhook": create_webhook,
    "getBenchRuns": bench_runs,
    "getBenchEvidence": bench_evidence,
    "pointAndAsk": point_ask,
    "speakVerdict": speak_verdict,
    "afterPurchase": after_purchase_guide,
    "reportIncident": report_incident,
    "getIncidentSignals": incident_signals,
    "getRedteamRounds": redteam_rounds,
    "runRedteamRound": redteam_round,
    "askSupport": support_ask,
}
HANDLERS = {op: tenant_guard(op, traced(op, handler)) for op, handler in HANDLERS.items()}
HANDLERS["getTrace"] = tenant_guard("getTrace", get_trace)
