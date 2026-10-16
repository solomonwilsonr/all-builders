"""Live investigation of any product, seen before or not (plan v2.2 workstreams A, B, C, J; POST /v1/investigations).

    investigate(request) -> answer      quick: official sources in parallel, verification, code verdict (seconds)
    start(request)       -> job         deep: the same plus browser-only sources, as a durable job

Steps: market -> identity (read-only: a listing never becomes a product here) -> source plan -> parallel retrieval ->
dedupe -> per record: authenticity, claim support, exact-scope check -> contradictions -> hazard signals with
independent-observation counting -> coverage by country -> deterministic outcome -> what would change it -> snapshot.
"""
import logging
import re
import threading
import time
import typing
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from engine import active, assessments, locales, plain, region_policy
from engine.evidence_verification import (
    POLICY_VERSION,
    adjudicator,
    contradictions,
    corroboration,
    identity_scope,
    source_check,
)
from engine.evidence_verification.claims import ClaimType, EvidenceClaim, claim_id, verification_status
from engine.normalize import norm_brand
from engine.sources import coverage, planner, registry
from engine.sources.base import SourceQuery

log = logging.getLogger(__name__)
MIN_REVIEWS = 20
CLAIM_TYPES = set(typing.get_args(ClaimType))
PRODUCT_FIELDS = ("product_id", "brand", "model", "gtin", "batch", "category", "title", "local_identifiers", "key",
                  "market", "identity_source", "identity_agent")
HAZARD_FIELDS = ("hazard_type", "mechanism", "severity", "independent_reports", "independent_groups", "with_photos",
                 "first_seen", "trend", "evidence_ids")
_jobs = ThreadPoolExecutor(max_workers=2, thread_name_prefix="investigation")
_memory_jobs: dict[str, dict] = {}  # when there is no database: jobs live as long as this instance
_lock = threading.Lock()


def new_id(prefix: str = "INV-") -> str:
    from engine import store
    return store.short_id(prefix, str(time.time_ns()))


# --- identity --------------------------------------------------------------------------------------------------

def product_from(request: dict) -> dict:
    """Who is this product? The caller's own fields win (a confirmed label read, or a business's catalogue), then a
    stored product, then what the listing's title says. Read-only."""
    listing = {k: request.get(k) for k in ("url", "title", "brand", "model", "gtin", "page_text", "currency")
               if request.get(k)}
    product = {"product_id": request.get("product_id"), "brand": request.get("brand"), "model": request.get("model"),
               "gtin": request.get("gtin"), "batch": request.get("batch"), "category": request.get("category"),
               "title": request.get("title")}
    if product["product_id"]:
        try:
            from engine import store
            fp = store.latest_fingerprint(product["product_id"]) or {}
            for k in ("brand", "model", "gtin", "category"):
                product[k] = product[k] or fp.get(k)
        except Exception as error:  # noqa: BLE001
            log.debug("no stored product: %s", type(error).__name__)
    if listing and not (product["brand"] and product["model"]):
        from engine import identity
        fp = identity.fingerprint(listing)
        product["model"] = product["model"] or title_model(listing) or fp.get("model")
        for k in ("gtin", "category"):
            product[k] = product[k] or fp.get(k)
        product["brand"] = product["brand"] or title_brand(listing)
    product["identity_source"] = "given" if request.get("model") else "listing text (code)" if product["model"] else None
    if listing and not product["model"] and not request.get("no_agents"):
        # Code found no model number: the identity agent reads the listing, and only quotes found on the page count.
        from engine.agents import identity_agent
        read = identity_agent.read({**listing, "label_text": request.get("label_text")})
        for k in ("brand", "model", "batch"):
            product[k] = product[k] or read.get(k)
        if read.get("model"):
            product["identity_source"] = f"identity agent (quoted: \"{read['quotes']['model']}\")"
        product["identity_agent"] = {k: read.get(k) for k in ("verified", "rejected", "quotes", "model_version",
                                                                "evidence_id")} if read else None
    ids = locales.local_identifiers(" ".join(str(request.get(k) or "") for k in ("title", "page_text", "label_text")))
    product["local_identifiers"] = {**ids, **(request.get("local_identifiers") or {})}
    if not product["gtin"] and ids.get("gtin"):
        product["gtin"] = ids["gtin"][0]
    product["key"] = "|".join([norm_brand(product["brand"]), locales.comparable_model(product["model"]),
                               (request.get("market") or "").upper()])
    return product


SPACED_MODEL = re.compile(r"\b[A-Z]{3,6} \d{2,5}[A-Z]?\b(?! ?(?:mAh|W|V|A|L|kg|mm|cm|GB|TB|Hz|ml|VAC|litres?|liters?|"
                          r"inch|in\b|ft|pcs|Ampere))")
UNIT_AFTER = re.compile(r"^\d+(?:MAH|W|V|A|L)$", re.IGNORECASE)


def title_model(listing: dict) -> str | None:
    """The model code as written in the listing (hyphens kept: regulators' search boxes need "ZHX-PB22", not
    "ZHXPB22"): the page's "Model number" row, else the first code-like word of the title, Japanese titles included."""
    from engine.normalize import MODEL_TOKEN, N_IN_ONE, NOT_MODELS, labelled_model, norm_model
    from engine.sources.normalizer import NOT_MODEL, TOKEN
    labelled = labelled_model(listing.get("page_text") or "")
    title = N_IN_ONE.sub(" ", locales.fold(listing.get("title") or ""))
    from engine.sources.normalizer import models_in
    marked = models_in(title)  # "型番 DE-C38-10000BK", "Model: X100": a code the title itself labels comes first
    if marked and not labelled:
        return marked[0]
    # "V-Guard VSDI 100 Digital": a capitalised code and a number written apart are one model ("VSDI 100").
    spaced = [m for m in SPACED_MODEL.findall(title) if not UNIT_AFTER.match(m.split()[-1])]
    for token in spaced + MODEL_TOKEN.findall(title) + TOKEN.findall(title):
        code = norm_model(token)
        if labelled and code == labelled:
            return token
        if len(code) >= 4 and not NOT_MODELS.match(code) and not NOT_MODEL.match(token) and \
                re.search(r"[A-Z]", code) and re.search(r"\d", code):
            return None if labelled else token
    return labelled or None


def title_brand(listing: dict) -> str | None:
    """The brand the listing claims, unless it's only a generic first word of the title ("New", "65W")."""
    from engine import page_safety, trust
    brand = trust.listing_brand(listing)
    return page_safety.searchable_brand(listing, brand) or None


# --- verification ----------------------------------------------------------------------------------------------

def dedupe(results) -> list[dict]:
    """One record per official record ID; the live copy wins over a stored one, identifiers are merged."""
    best: dict[str, dict] = {}
    for result in results:
        for record in result.records:
            r = record.to_dict()
            old = best.get(r["record_id"])
            if old is None or (old["mode"] != "live" and r["mode"] == "live"):
                if old:
                    for k in ("models", "gtins", "batches", "brands"):
                        r["product_identifiers"][k] = list(dict.fromkeys(
                            r["product_identifiers"].get(k, []) + old["product_identifiers"].get(k, [])))
                    r["also_from"] = sorted(set(old.get("also_from", [])) | {old["source"]})
                best[r["record_id"]] = r
            else:
                for k in ("models", "gtins", "batches", "brands"):
                    old["product_identifiers"][k] = list(dict.fromkeys(
                        old["product_identifiers"].get(k, []) + r["product_identifiers"].get(k, [])))
                old["also_from"] = sorted(set(old.get("also_from", [])) | {r["source"]})
    return list(best.values())


def verify(product: dict, records: list[dict], market: str | None, found_contradictions: list[dict]) -> list[dict]:
    retracted = contradictions.retracted_records(found_contradictions)
    excluded = contradictions.excluded_records(found_contradictions)
    matches = []
    for r in records:
        scope = identity_scope.check(product, r, market)
        if scope["tier"] == "none":
            continue
        auth, auth_why = source_check.authenticity(r)
        lead_claim = next((c for c in r["claims"] if c["claim_type"] == "affected_models"), r["claims"][0]
                          if r["claims"] else {"excerpt": r["title"]})
        support = source_check.supports(lead_claim.get("excerpt") or "", r)
        matches.append({
            "record_id": r["record_id"], "source": r["source"], "authority": r["authority"], "title": r["title"],
            "url": r["source_url"], "jurisdiction": r["jurisdiction"], "record_type": r["record_type"],
            "published": (r["source_published_at"] or "")[:10] or None, "retrieved_at": r["retrieved_at"],
            "mode": r["mode"], "language": r["language"], "hazard": r["hazard"][:300], "remedy": r["remedy"][:300],
            "models_named": r["product_identifiers"].get("models", [])[:12],
            "batch_limits": r["product_identifiers"].get("batches", [])[:3],
            "tier": scope["tier"], "scope": scope["scope"], "local": scope["local"], "reasons": scope["reasons"],
            "would_change": scope["would_change"], "authenticity": auth, "authenticity_reason": auth_why,
            "support": support, "retracted": r["record_id"] in retracted, "excluded": r["record_id"] in excluded,
            "attribution": r.get("attribution"), "also_from": r.get("also_from", []),
            "original_text": r["original_text"][:600] if r["language"] != "en" else None,
            "places": region_policy.places(market, r)})
    order = adjudicator.TIER_RANK
    return sorted(matches, key=lambda m: (order.index(m["tier"]), not m["local"], m["published"] or ""))


def build_claims(product: dict, records: list[dict], matches: list[dict]) -> list[dict]:
    by_id = {r["record_id"]: r for r in records}
    out = []
    for m in matches:
        r = by_id[m["record_id"]]
        for c in r["claims"]:
            support = source_check.supports(c.get("excerpt") or "", r)
            claim = EvidenceClaim(
                claim_id=claim_id(r["record_id"], c["claim_type"], c["text"]),
                claim_type=c["claim_type"] if c["claim_type"] in CLAIM_TYPES else "recall",
                claim_text=c["text"][:1000], product_id=product.get("product_id"),
                model=product.get("model"), batch_scope=r["product_identifiers"].get("batches", [])[:3],
                jurisdiction=r["jurisdiction"], source_registry_id=r["source"], source_record_id=r["record_id"],
                source_url=r["source_url"], source_type=r["record_type"], source_document_hash=r["raw_payload_hash"],
                source_excerpt=(c.get("excerpt") or "")[:500], source_language=r["language"],
                license_policy_id=r["source"], attribution=r.get("attribution") or "",
                event_at=r["event_at"], source_published_at=r["source_published_at"],
                source_updated_at=r["source_updated_at"], retrieved_at=r["retrieved_at"],
                extraction_method=c.get("extraction_method") or "code (engine/sources/normalizer.py)",
                source_authenticity_status=m["authenticity"], claim_support_status=support,
                product_match_tier=m["tier"], identity_scope_status=m["scope"],
                verification_status=verification_status(m["authenticity"], support, m["tier"], m["scope"],
                                                        m["retracted"], m["excluded"]),
                review_status="pending" if m["tier"] in ("variant", "suspected_rebrand", "family_named") or
                (m["tier"] == "exact" and not m["local"]) else "not_required",
                is_local=m["local"])
            out.append(claim.public())
    return out


def hazards_for(product: dict, request: dict) -> tuple[list[dict], int, list[dict], list[dict]]:
    """Radar findings for a stored product (or the page's own reviews), each with its independent-observation count.
    Returns (findings, reviews_checked, observation_groups, reviews_for_contradictions)."""
    if request.get("skip_reviews"):
        return [], 0, [], []
    body = None
    try:
        if product.get("product_id"):
            from engine import safety
            body = safety.safety(product["product_id"], assess=False)
        elif request.get("reviews") and (request.get("url") or request.get("title")):
            from engine import page_safety
            fields = ("url", "title", "reviews", "brand", "price", "currency")
            body = page_safety.listing_safety({k: request.get(k) for k in fields if request.get(k)})
    except Exception as error:  # noqa: BLE001  no reviews is a limitation, not a failure
        log.info("no hazard signals: %s", type(error).__name__)
    if not body:
        return [], 0, [], []
    findings, groups, texts = hazard_groups(body.get("ai_findings", []))
    return findings, body.get("reviews_checked", 0), groups, texts


# --- the investigation -------------------------------------------------------------------------------------------

def query_for(product: dict, market: str | None, as_of: str | None = None) -> SourceQuery:
    return SourceQuery(brand=product.get("brand"), model=product.get("model"), gtin=product.get("gtin"),
                       category=product.get("category"), market_country=market, batch=product.get("batch"),
                       title=product.get("title"), languages=region_policy.languages(market),
                       local_identifiers=product.get("local_identifiers") or {},
                       as_of=datetime.fromisoformat(as_of).replace(tzinfo=UTC) if as_of else None)


def stored_links(product_id: str | None, market: str | None, seen: set[str]) -> list[dict]:
    """Recall links engine/recalls.py already made for a stored product (exact model, or inherited from a verified
    exact twin), as matches the policy can weigh. Locality is decided here, so a CPSC link on an Amazon.in product
    becomes "recalled abroad", not "recalled here"."""
    if not product_id:
        return []
    try:
        from engine import store
        from engine.sources.adapters.stored_notices import jurisdiction, to_record
        rows = store.conn().execute(
            """SELECT DISTINCT r.id, r.authority, r.notice_date, r.title, r.hazard, r.scope_json, r.url
               FROM recall_products p JOIN recalls r ON r.id = p.recall_id
               WHERE p.product_id = %s AND p.match_class = 'exact_model'""", (product_id,)).fetchall()
    except Exception as error:  # noqa: BLE001
        log.debug("no stored links: %s", type(error).__name__)
        return []
    out = []
    for row in rows:
        if row["id"] in seen:
            continue
        r = to_record(row, datetime.now(UTC), "stored_notices").to_dict()
        where = jurisdiction(row)
        scope_status, scope_why = identity_scope.batch_scope({}, r)
        auth, auth_why = source_check.authenticity(r)
        out.append({
            "record_id": r["record_id"], "source": "stored_notices", "authority": r["authority"], "title": r["title"],
            "url": r["source_url"], "jurisdiction": where, "record_type": r["record_type"],
            "published": (r["source_published_at"] or "")[:10] or None, "retrieved_at": r["retrieved_at"],
            "mode": "cache", "language": "en", "hazard": r["hazard"][:300], "remedy": r["remedy"][:300],
            "models_named": r["product_identifiers"].get("models", [])[:12],
            "batch_limits": r["product_identifiers"].get("batches", [])[:3], "tier": "exact", "scope": scope_status,
            "local": region_policy.is_local(where, [where], market),
            "reasons": ["SafeShelf linked this notice to the product by exact model number (or a verified exact twin)"]
            + scope_why, "would_change": [], "authenticity": auth, "authenticity_reason": auth_why,
            "support": "supported", "retracted": False, "excluded": False, "attribution": r.get("attribution"),
            "also_from": [], "original_text": None, "places": region_policy.places(market, r)})
    return out


def collect(product: dict, market: str | None, depth: str = "quick", as_of: str | None = None,
            review_texts: list[dict] | None = None, only: list[str] | None = None) -> dict:
    """Sources -> dedupe -> contradictions -> scope-checked matches -> coverage. JSON-safe (pipeline state)."""
    query = query_for(product, market, as_of)
    if query.brand or query.model or query.gtin:
        retrieved = planner.investigate(query, depth, only)
    else:
        retrieved = {"plan": planner.plan(query, depth), "results": []}
    if only:  # a baseline run (e.g. stored copy only): the other sources are reported as not consulted
        retrieved["plan"] = [s for s in retrieved["plan"] if s["source"] in only]
    records = dedupe(retrieved["results"])
    found = contradictions.find(product, records, review_texts or [])
    matches = verify(product, records, market, found)
    matches += stored_links(product.get("product_id"), market, {m["record_id"] for m in matches})
    matched: dict[str, dict[str, int]] = {}
    for m in matches:
        if m["tier"] not in ("lookalike", "unresolved") and not m["excluded"]:  # brand-only: not a notice for this product
            for source in [m["source"], *m.get("also_from", [])]:
                by_country = matched.setdefault(source, {})
                by_country[m["jurisdiction"]] = by_country.get(m["jurisdiction"], 0) + 1
    source_rows = coverage.source_rows(retrieved["plan"], retrieved["results"], matched)
    country_rows = coverage.matrix(market, source_rows)
    statuses = [r.status for r in retrieved["results"]]
    modes = {r.mode for r in retrieved["results"] if r.ok}
    local_skipped = any(not p["runnable"] and p["role"] == "local" for p in retrieved["plan"])
    failed = any(s != "ok" for s in statuses)
    source_mode = "partial" if failed or local_skipped else "live" if "live" in modes else "cache" if modes else "none"
    return {"market": market, "market_name": registry.market_name(market) if market else "your country",
            "product": {k: product.get(k) for k in PRODUCT_FIELDS},
            "records": records, "matches": matches, "contradictions": found, "source_rows": source_rows,
            "country_rows": country_rows, "source_mode": source_mode, "depth": depth,
            "query_keys": [query.key()],
            "query": {"brand": query.brand, "model": query.model, "gtin": query.gtin, "market": market, "depth": depth,
                      "as_of": as_of}}


def adjudicate(collected: dict, hazards: list[dict], reviews_checked: int, registry_issues: list[dict] | None = None,
               as_of: str | None = None) -> dict:
    product, market = collected["product"], collected["market"]
    decision = adjudicator.decide(market, collected["market_name"], product, collected["matches"], hazards,
                                  collected["country_rows"], reviews_checked, MIN_REVIEWS, registry_issues, as_of)
    decision["what_would_change"] = active.plan(decision, product, collected["country_rows"], collected["depth"],
                                                collected["matches"])
    decision["coverage"] = {"countries": collected["country_rows"], "sources": collected["source_rows"],
                            "summary": coverage.summary_line(collected["country_rows"])}
    decision["source_mode"] = collected["source_mode"]
    decision["rules"] = region_policy.rules(market)
    decision["plain"] = plain.shopper(decision, product, collected["matches"], collected["country_rows"], market)
    return decision


def hazard_groups(findings: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Each radar finding with its independent-observation count (copies and shared photos count once)."""
    from engine import store
    out, groups, texts = [], [], []
    for f in findings:
        observations = []
        for eid in f.get("evidence_ids", [])[:40]:
            try:
                content = store.evidence_content(eid) if str(eid).startswith("EV-") else {}
            except Exception:  # noqa: BLE001
                content = {}
            observations.append({"id": eid, "text": content.get("text") or "", "date": content.get("date"),
                                 "image_hashes": content.get("image_hashes") or []})
            texts.append({"evidence_id": eid, "text": content.get("text") or ""})
        found = corroboration.group(observations) if any(o["text"] for o in observations) else []
        groups += found
        out.append({**f, "independent_groups": len(found) if found else f.get("independent_reports", 0)})
    return out, groups, texts


def investigate(request: dict, investigation_id: str | None = None, tenant_id: str = "public") -> dict:
    started = time.monotonic()
    investigation_id = investigation_id or new_id()
    market = region_policy.market_of(request.get("url"), request.get("currency"), request.get("market"))
    request = {**request, "market": market}
    product = product_from(request)
    product["market"] = market
    depth = "deep" if request.get("depth") == "deep" else "quick"
    as_of = request.get("as_of")
    hazards, reviews_checked, groups, review_texts = hazards_for(product, request)
    collected = collect(product, market, depth, as_of, review_texts, request.get("only_sources"))
    decision = adjudicate(collected, hazards, reviews_checked, request.get("registry_issues"), as_of)
    matches = collected["matches"]
    claims = build_claims(product, collected["records"], [m for m in matches if m["tier"] != "lookalike"][:12])
    answer = {
        "investigation_id": investigation_id, "status": "complete", "job_status": "complete", "tenant_id": tenant_id,
        "market": market, "market_name": collected["market_name"], "depth": depth, "product": collected["product"],
        **decision,
        "matches": matches[:15], "claims": claims, "contradictions": collected["contradictions"][:10],
        "hazards": [{k: h.get(k) for k in HAZARD_FIELDS} for h in hazards],
        "observation_groups": groups[:50], "reviews_checked": reviews_checked,
        "retrieved_at": datetime.now(UTC).isoformat(), "seconds": round(time.monotonic() - started, 2),
        "evidence_ids": [h for f in hazards for h in f.get("evidence_ids", [])][:20],
        "source_links": [{"record_id": m["record_id"], "url": m["url"], "authority": m["authority"]}
                         for m in matches[:10] if m["url"]],
        "query": collected["query"], "query_keys": collected["query_keys"],
        "model_versions": {"policy": POLICY_VERSION, "sources": "engine.sources/0.2"},
        "label": "Outcome set by code from official sources; AI only read and explained them. Not a regulator's "
                 "determination.",
    }
    answer["snapshot_id"] = assessments.save_snapshot(answer)
    return answer


# --- durable jobs ------------------------------------------------------------------------------------------------

def start(request: dict, tenant_id: str = "public") -> dict:
    """A deep investigation as a job: recorded first, run in the background, polled with GET /v1/investigations/{id}."""
    job_id = new_id()
    assessments.create_job(job_id, tenant_id, request)
    with _lock:
        _memory_jobs[job_id] = {"status": "queued", "tenant_id": tenant_id}

    def run():
        assessments.update_job(job_id, "running")
        with _lock:
            _memory_jobs[job_id]["status"] = "running"
        try:
            answer = investigate(request, job_id, tenant_id)
            assessments.update_job(job_id, "complete", answer.get("snapshot_id"))
            with _lock:
                _memory_jobs[job_id] = {"status": "complete", "tenant_id": tenant_id, "answer": answer}
        except Exception as error:  # noqa: BLE001
            log.warning("investigation job %s failed: %s", job_id, type(error).__name__)
            assessments.update_job(job_id, "failed", error=type(error).__name__)
            with _lock:
                _memory_jobs[job_id] = {"status": "failed", "tenant_id": tenant_id, "error": type(error).__name__}

    _jobs.submit(run)
    return {"investigation_id": job_id, "status": "queued", "job_status": "queued",
            "poll": f"/v1/investigations/{job_id}",
            "note": "Deep checks search browser-only sources too; this usually takes 30-90 seconds."}


def get(investigation_id: str, tenant_id: str = "public") -> dict:
    with _lock:
        mem = _memory_jobs.get(investigation_id)
    if mem and mem.get("tenant_id") not in (tenant_id, "public") and tenant_id != "admin":
        raise KeyError(investigation_id)
    if mem and mem.get("answer"):
        return mem["answer"]
    try:
        row = assessments.job(investigation_id)
    except Exception:  # noqa: BLE001
        row = None
    if row:
        if row["tenant_id"] not in (tenant_id, "public") and tenant_id != "admin":
            raise KeyError(investigation_id)
        if row["status"] == "complete" and row.get("output"):
            return row["output"]
        return {"investigation_id": investigation_id, "status": row["status"], "job_status": row["status"],
                "error": row.get("error")}
    if mem:
        return {"investigation_id": investigation_id, "status": mem["status"], "job_status": mem["status"],
                "error": mem.get("error")}
    try:
        snaps = assessments.snapshots(investigation_id)
    except Exception:  # noqa: BLE001
        snaps = []
    if snaps:
        out = snaps[0]["output"]
        if out.get("tenant_id") not in (tenant_id, "public") and tenant_id != "admin":
            raise KeyError(investigation_id)
        return out
    raise KeyError(investigation_id)


def sources(investigation_id: str, tenant_id: str = "public") -> dict:
    answer = get(investigation_id, tenant_id)
    if answer.get("status") != "complete":
        return {"investigation_id": investigation_id, "status": answer.get("status"), "sources": []}
    return {"investigation_id": investigation_id, "market": answer.get("market"),
            "coverage": answer.get("coverage"), "matches": answer.get("matches"), "claims": answer.get("claims"),
            "retrieved_at": answer.get("retrieved_at"), "source_mode": answer.get("source_mode")}
