"""'I already bought it' (POST /v1/after-purchase): the after-purchase half of SafeShelf, for any listing.

    guide({investigation_id | url/title/brand/model..., purchase: {url, order_id, date, what_happened}})
        -> {situation, headline, say, steps, drafts, case_file: {markdown}, ...}

Before purchase, the check card and the buy-button warning step in; after purchase this says what to do now: stop
using it (or check the label), get the refund or remedy, report it, and dispose of it safely, with a refund request
and a regulator complaint already filled in (engine/complaints.py) and a case file to attach. Every step comes from
the code's outcome; Gemini writes none of it. engine/owner.py does the same for products SafeShelf has stored.
"""
from datetime import UTC, datetime

from engine import complaints, investigation, owner

LISTING_FIELDS = ("url", "title", "brand", "model", "gtin", "batch", "market", "currency", "page_text", "category")
LABEL = "Guidance from official records and SafeShelf's code rules - not a regulatory determination or legal advice"


def _step(title: str, detail: str, **extra) -> dict:
    return {"title": title, "detail": detail, **{k: v for k, v in extra.items() if v}}


def steps_for(answer: dict, f: dict) -> tuple[str, str, list[dict]]:
    basis = answer.get("basis") or answer.get("outcome")
    lead = answer.get("lead_record") or {}
    p = answer.get("plain") or {}
    if basis == "confirmed_recall":
        return "recalled", f"{p.get('title') or 'Recalled'}. Stop using it.", [
            _step("Stop using it now", "Unplug it and put it away from children. Don't throw it away yet: keep it and "
                                       "the receipt until you've claimed the remedy."),
            _step("Claim the recall remedy", "The recall notice says what you get (refund, repair or replacement) and "
                                             "how to claim it.", url=lead.get("url")),
            _step("Ask the shop for a refund", "Use the refund request below. A recalled product is a strong reason "
                                               "for a refund."),
        ]
    if basis in ("recalled_abroad_same_model", "local_recall_batch_unknown", "possible_match"):
        what = "serial or batch number" if basis == "local_recall_batch_unknown" else "model number"
        return "recall_to_check", f"{p.get('title') or 'A recall may cover yours'}. Check your label.", [
            _step(f"Compare the {what} on your label with the recall",
                  f"{f['record'] or 'The recall notice'} lists the affected {what}s. Look on the label, base or box.",
                  url=lead.get("url")),
            _step("Until you know, use it carefully", "Don't charge it or leave it running unattended or overnight. "
                                                      "Stop if it gets hot, smells, swells or sparks."),
            _step("Ask the shop whether yours is affected", "Use the refund request below; it asks them to confirm."),
        ]
    if answer.get("hazards") or basis in ("substantiated_hazard_signal", "hazard_reports"):
        tips = [owner.PRECAUTIONS.get(h.get("hazard_type"), owner.PRECAUTIONS["other"])
                for h in (answer.get("hazards") or [])[:2]]
        return "hazard_reports", "Not recalled, but buyers report safety problems. Check yours.", [
            _step(f"Check yours for {f['risk']}", " ".join(dict.fromkeys(tips)) or owner.PRECAUTIONS["other"]),
            _step("If yours shows the problem, stop using it and ask for a refund",
                  "Use the refund request below while the return window is open. A photo helps."),
        ]
    if basis == "no_matching_notice_found":
        return "no_known_issue", "No recall found for this product. Keep an eye on it.", [
            _step("Nothing to do now", "SafeShelf found no recall. That's not a guarantee: if it overheats, sparks or "
                                       "smells of burning, stop using it and report it."),
        ]
    return "not_enough_evidence", "We can't tell yet. Find the model number on the label.", [
        _step("Read the label", "Find the brand and model number on the label or box, then check again (or point "
                                "your phone's camera at it)."),
    ]


def case_markdown(answer: dict, f: dict, purchase: dict) -> str:
    """A ready-made case file to attach to a complaint: the result, the official records, what was checked."""
    product = answer.get("product") or {}
    rows = (answer.get("plain") or {}).get("checked") or []
    lines = [f"# SafeShelf case file {answer.get('investigation_id') or ''}".rstrip(), "",
             f"**Product:** {f['name']}" + (f" ({product.get('title')})" if product.get("title") else ""),
             f"**Listing:** {purchase.get('url') or product.get('url') or 'not given'}",
             f"**Checked:** {f['checked']} · **Result (set by code, policy {answer.get('policy_version') or '?'}):** "
             f"{(answer.get('plain') or {}).get('title') or answer.get('outcome')}",
             f"**Why:** {(answer.get('plain') or {}).get('why') or answer.get('headline') or ''}", "",
             "## Official records", ""]
    lines += [f"- {m.get('authority')} {m.get('record_id')} ({m.get('published') or 'undated'}, "
              f"{'this country' if m.get('local') else m.get('jurisdiction')}): {m.get('title')} {m.get('url')}"
              for m in (answer.get("matches") or []) if m.get("tier") in ("exact", "variant") and m.get("url")][:5] \
        or ["- None matched this exact product."]
    lines += ["", "## Where SafeShelf checked", ""]
    lines += [f"- {r['name']}: {r['status']}" for r in rows] or [f"- {answer.get('coverage', {}).get('summary', '')}"]
    for h in (answer.get("hazards") or [])[:3]:
        lines.append(f"- Buyer reports: {h.get('mechanism') or h.get('hazard_type')}, "
                     f"{h.get('independent_groups') or h.get('independent_reports')} independent")
    lines += ["", f"_{LABEL}. No personal details are included; the shopper adds their own._"]
    return "\n".join(lines)


def answer_for(body: dict, tenant_id: str = "public") -> dict:
    if body.get("investigation_id"):
        try:
            answer = investigation.get(body["investigation_id"], tenant_id)
            if answer.get("status") == "complete" or answer.get("outcome"):
                return answer
        except KeyError:
            pass  # expired or from another instance: check again from the listing
    listing = {k: body[k] for k in LISTING_FIELDS if body.get(k)}
    if not any(listing.get(k) for k in ("url", "title", "brand", "model", "gtin")):
        raise ValueError("give investigation_id, or the listing (url, title, brand or model)")
    return investigation.investigate(listing, None, tenant_id)


def guide(body: dict, tenant_id: str = "public") -> dict:
    answer = answer_for(body, tenant_id)
    purchase = {**(body.get("purchase") or {})}
    purchase.setdefault("url", body.get("url") or (answer.get("product") or {}).get("url"))
    f = complaints.facts(answer)
    situation, headline, steps = steps_for(answer, f)
    if situation != "no_known_issue" or purchase.get("what_happened"):
        steps.append(_step("Report it", "Send the regulator complaint below. It is filled in with the official "
                                        "records; add what happened to you."))
    if situation == "recalled":
        steps.append(_step("Dispose of it safely", owner.DISPOSAL))
    steps.append(_step("Save it to My Shelf", "SafeShelf tells you if it is recalled later."))
    say = {"recalled": "Stop using it. Ask the shop for a refund. We've written the request for you.",
           "recall_to_check": "Check the model number on your label. Until you know, don't leave it charging.",
           "hazard_reports": "Check yours for the problem buyers report. If you see it, stop using it.",
           "no_known_issue": "No recall found. If it overheats or sparks, stop using it.",
           "not_enough_evidence": "Find the model number on the label, then check again."}[situation]
    return {
        "investigation_id": answer.get("investigation_id"), "outcome": answer.get("outcome"),
        "basis": answer.get("basis"), "situation": situation, "headline": headline, "say": say,
        "plain": plain_of(answer),
        "steps": [{"n": n, **s} for n, s in enumerate(steps, 1)],
        "drafts": complaints.drafts(answer, purchase),
        "case_file": {"markdown": case_markdown(answer, f, purchase),
                      "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")},
        "label": LABEL,
    }


def plain_of(answer: dict) -> dict | None:
    p = answer.get("plain")
    return {k: p.get(k) for k in ("title", "tone", "why", "todo", "say", "link")} if p else None
