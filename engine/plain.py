"""The answer in everyday words, for shoppers with no safety or legal background (plan v2.2 UX).

    shopper(decision, product, matches, country_rows) -> {title, why, todo, tone, checked: [...]}

Rules: short sentences, no jargon ("notice", "coverage", "potential concern", "stored copy" never appear), say what
to do next, never claim more than the code decided, and always say that "no recall found" is not a guarantee.
Screens (extension, web page, WhatsApp, chat) show this first and keep the technical answer behind "details".
"""
FLAGS = {"IN": "🇮🇳", "JP": "🇯🇵", "AU": "🇦🇺", "SG": "🇸🇬", "NZ": "🇳🇿", "KR": "🇰🇷", "TW": "🇹🇼", "US": "🇺🇸", "EU": "🇪🇺",
         "MY": "🇲🇾", "ID": "🇮🇩", "TH": "🇹🇭", "PH": "🇵🇭", "VN": "🇻🇳"}
SHORT = {"US": "the US", "EU": "Europe", "KR": "South Korea", "AU": "Australia", "JP": "Japan", "IN": "India",
         "SG": "Singapore", "TW": "Taiwan", "NZ": "New Zealand", "MY": "Malaysia", "ID": "Indonesia", "TH": "Thailand",
         "PH": "the Philippines", "VN": "Vietnam"}
HAZARD_WORDS = [
    ("fire", "a fire risk"), ("火災", "a fire risk"), ("発火", "a fire risk"), ("発煙", "a fire risk"),
    ("burn", "a burn risk"), ("やけど", "a burn risk"), ("overheat", "overheating"), ("発熱", "overheating"),
    ("shock", "an electric shock risk"), ("electrocut", "an electric shock risk"), ("感電", "an electric shock risk"),
    ("chok", "a choking risk"), ("窒息", "a choking risk"), ("lacerat", "a cut risk"),
    ("strangul", "a strangulation risk"),
    ("entangle", "a strangulation risk"), ("impact", "an injury risk"), ("fall", "a fall risk"),
    ("chemical", "a chemical risk"), ("lead", "too much lead")]


def country(code: str | None) -> str:
    return SHORT.get((code or "").upper(), code or "another country")


def hazard_of(text: str | None) -> str:
    text = (text or "").lower()
    return next((words for key, words in HAZARD_WORDS if key in text), "a safety risk")


def name_of(product: dict) -> str:
    """'this Anker A1263', or 'this product' when nothing reliable is known."""
    brand, model = (product.get("brand") or "").strip(), (product.get("model") or "").strip()
    if brand and model:
        return f"this {brand} {model}"
    if model:
        return f"model {model}"
    return f"this {brand} product" if brand else "this product"


def checked_list(country_rows: list[dict], matches: list[dict], market: str | None) -> list[dict]:
    """One line per country, in plain words. Countries SafeShelf can't check at all are left out, except the
    shopper's own (which then says why)."""
    worst: dict[str, str] = {}
    rank = {"exact": 4, "variant": 3, "suspected_rebrand": 3, "family_named": 2, "unresolved": 1}
    for m in matches:
        if m.get("excluded") or m.get("retracted") or m.get("tier") not in rank:
            continue
        code = (m.get("jurisdiction") or "").upper()
        if rank[m["tier"]] > rank.get(worst.get(code, ""), 0):
            worst[code] = m["tier"]
    out = []
    for row in country_rows:
        code = row["country"]
        tier = worst.get(code)
        if tier == "exact":
            status, mark = "Recall found for this model", "warn"
        elif tier == "unresolved":
            status, mark = "This brand has recalls – model number needed to check", "maybe"
        elif tier:
            status, mark = "Similar product recalled – check the model", "maybe"
        elif row["state"] in ("checked_live", "checked_cache", "no_matching_notice_found"):
            status, mark = "No recall found", "ok"
        elif row["state"] == "source_unavailable":
            status, mark = "Couldn't check right now", "skip"
        elif row.get("is_market"):
            status, mark = "No official recall list we can read", "skip"
        else:
            continue
        if code == "IN" and mark in ("ok", "skip"):
            status += " (India has no public recall list; we checked government safety orders)"
        out.append({"country": code, "flag": FLAGS.get(code, "🌐"), "name": row.get("name") or country(code),
                    "status": status, "mark": mark, "yours": bool(row.get("is_market"))})
    return out[:8]


def shopper(decision: dict, product: dict, matches: list[dict], country_rows: list[dict],
            market: str | None) -> dict:
    basis, outcome = decision.get("basis"), decision.get("outcome")
    here = country(market) if market else "your country"
    this = name_of(product)
    lead = next((m for m in matches if m.get("record_id") == (decision.get("lead_record") or {}).get("record_id")),
                decision.get("lead_record") or {})
    there = country(lead.get("jurisdiction"))
    risk = hazard_of(f"{lead.get('hazard') or ''} {lead.get('title') or ''}")
    model = product.get("model")
    n_ok = sum(1 for r in country_rows if r["state"] in ("checked_live", "checked_cache", "no_matching_notice_found"))
    brand = product.get("brand") or "This brand"
    texts = {
        "confirmed_recall": (
            f"Recalled in {here}", "red",
            f"The official safety regulator in {here} has recalled {this} because of {risk}.",
            ("Don't buy it. If you already have one, stop using it and follow the recall steps "
             "(refund, repair or replacement).")),
        "recalled_abroad_same_model": (
            f"Recalled in {there}", "amber",
            (f"The safety regulator in {there} recalled {this} because of {risk}. It hasn't been recalled in {here} "
             "yet, so the version sold here may or may not be affected."),
            (f"Check that the model number on the box or label is exactly {model or 'the same'}. If it is, avoid "
             "buying it, or don't charge or use it unattended until the seller confirms it's safe.")),
        "local_recall_batch_unknown": (
            "Some units are recalled", "amber",
            (f"The safety regulator in {here} recalled some units of {this} because of {risk}, "
             "only certain serial or batch numbers."),
            ("Find the serial or batch number on the product or box and compare it with the recall (link below). "
             "If it matches, stop using it.")),
        "substantiated_hazard_signal": (
            "Buyers report safety problems", "amber",
            f"Several different buyers say {this} caused {risk}. It isn't officially recalled.",
            "Read what the buyers say below before you buy, and consider a safer alternative."),
        "possible_match": (
            "A similar product was recalled", "amber",
            (f"A safety recall mentions {'an' if brand[:1].lower() in 'aeiou' else 'a'} {brand} product like this one "
             "but gives no model number, "
             "so we can't tell if it's this exact one."),
            "Compare the product name and photos with the recall (link below). If you're unsure, ask the seller."),
        "seizure_or_notice": (
            "Officials warn about this type of product", "amber",
            (f"Government officials in {here} have seized or warned about this type of product when it was sold "
             "without the required safety certification."),
            "Make sure the listing or box shows a valid safety mark (in India, the ISI / BIS mark with an R-number)."),
        "hazard_reports": (
            "A few buyers mention a problem", "amber",
            f"Some buyers mention {risk} with {this}. It's not enough to call it unsafe, and it isn't recalled.",
            "Read the reviews below and keep an eye on it if you buy it."),
        "registry_mismatch": (
            "Safety mark doesn't match", "amber",
            "The safety certificate shown on the listing belongs to a different product in the official register.",
            "Ask the seller for the correct certificate, or choose a product whose safety mark checks out."),
        "brand_recalls_model_unknown": (
            "We need the model number", "unknown",
            (f"{brand} has recalled some of its products before. We couldn't see this one's model number, "
             "so we can't tell if it's one of them."),
            "Look for 'Model' in the product details or on the label, then check again."),
        "no_matching_notice_found": (
            "No recalls found", "green",
            f"We checked official safety recall lists in {n_ok} countries and found no recall for {this}.",
            ("That's a good sign, but not a guarantee. Read recent reviews and buy from the brand's official "
             "store if you can.")),
        "insufficient_evidence": (
            "We can't tell yet", "unknown",
            "We couldn't identify this product well enough to check it against official recall lists.",
            "Look for the brand and model number in the product details or on the label, then check again."),
    }
    title, tone, why, todo = texts.get(basis) or texts.get(outcome) or texts["insufficient_evidence"]
    return {"title": title, "tone": tone, "why": why, "todo": todo,
            "checked": checked_list(country_rows, matches, market),
            "link": {"url": lead.get("url"), "label": f"See the official recall ({lead.get('authority')})"}
            if lead.get("url") and outcome != "no_matching_notice_found" else None,
            "note": "Checked by SafeShelf using official government safety lists. This is guidance for shoppers, not "
                    "an official ruling."}
