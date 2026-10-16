"""Complaint drafts for a shopper who already bought it (POST /v1/after-purchase): a refund request to the marketplace
and a complaint to the regulator (India's National Consumer Helpline, Australia's ACCC, Japan's CAA and 188 hotline,
and the others in JAPAC), already filled in with SafeShelf's evidence.

    drafts(answer, purchase) -> [{kind, to, how, subject, body, language, fill_in, evidence}, ...]

Rules: written by code from the investigation, never by Gemini, so a draft never claims more than the code decided
("recalled in the US" is never written as "recalled here"). Nothing is sent: the shopper copies the draft, fills in
the [brackets] and sends it themselves. No personal details are stored; the shopper adds their own.
"""
from datetime import UTC, datetime
from urllib.parse import urlparse

from engine import plain

# Where a JAPAC shopper complains, by market: the regulator's own channels, in the order to try them.
REGULATORS = {
    "IN": {"name": "National Consumer Helpline (Department of Consumer Affairs)", "language": "en",
           "how": ["Call 1915 (toll-free)", "WhatsApp 8800001915", "File online at https://consumerhelpline.gov.in/",
                   "If it isn't resolved, file a case with the consumer commission at https://edaakhil.nic.in/"],
           "url": "https://consumerhelpline.gov.in/",
           "note": "The helpline passes product-safety complaints to the Central Consumer Protection Authority (CCPA). "
                   "If the label shows an ISI mark, add the BIS R-number: BIS can check whether it is genuine."},
    "AU": {"name": "ACCC Product Safety Australia", "language": "en",
           "how": ["Report an unsafe product at https://www.productsafety.gov.au/",
                   "For a refund dispute, contact your state or territory consumer protection agency"],
           "url": "https://www.productsafety.gov.au/",
           "note": "Under the Australian Consumer Law, an unsafe product is a major failure: you can choose a refund "
                   "or a replacement."},
    "JP": {"name": "消費者庁 (Consumer Affairs Agency) / 消費者ホットライン 188", "language": "ja",
           "how": ["消費者ホットライン 188 に電話する (Call 188: your local consumer affairs centre)",
                   "製品事故は消費者庁へ: https://www.caa.go.jp/"],
           "url": "https://www.caa.go.jp/",
           "note": "188 connects you to your local consumer affairs centre (消費生活センター), which helps with refunds "
                   "and passes product accidents to the Consumer Affairs Agency."},
    "SG": {"name": "Consumer Product Safety Office (CPSO), Enterprise Singapore", "language": "en",
           "how": ["Report an unsafe product at https://www.consumerproductsafety.gov.sg/",
                   "For a refund dispute, contact CASE at https://www.case.org.sg/"],
           "url": "https://www.consumerproductsafety.gov.sg/", "note": ""},
    "NZ": {"name": "Product Safety New Zealand (MBIE)", "language": "en",
           "how": ["Report an unsafe product at https://www.productsafety.govt.nz/"],
           "url": "https://www.productsafety.govt.nz/",
           "note": "Under the Consumer Guarantees Act, goods must be safe; you can ask the seller to put it right."},
    "KR": {"name": "1372 Consumer Counseling Center (Korea Consumer Agency)", "language": "en",
           "how": ["Call 1372", "File online at https://www.1372.go.kr/"], "url": "https://www.1372.go.kr/", "note": ""},
    "US": {"name": "U.S. Consumer Product Safety Commission (SaferProducts.gov)", "language": "en",
           "how": ["Report at https://www.saferproducts.gov/"], "url": "https://www.saferproducts.gov/", "note": ""},
}
# Where to ask for a refund, by shop.
SHOPS = [
    ("amazon.in", "Amazon.in", "https://www.amazon.in/gp/help/customer/contact-us", "en"),
    ("flipkart.com", "Flipkart", "https://www.flipkart.com/helpcentre", "en"),
    ("amazon.co.jp", "Amazon.co.jp", "https://www.amazon.co.jp/gp/help/customer/contact-us", "ja"),
    ("amazon.com.au", "Amazon.com.au", "https://www.amazon.com.au/gp/help/customer/contact-us", "en"),
    ("amazon.sg", "Amazon.sg", "https://www.amazon.sg/gp/help/customer/contact-us", "en"),
    ("amazon.com", "Amazon.com", "https://www.amazon.com/gp/help/customer/contact-us", "en"),
]
FILL_IN = ["[your name]", "[order number]", "[date you bought it]"]
NOTHING_SENT = "A draft for you to check and send yourself. SafeShelf has not sent anything."


def shop_of(url: str | None) -> tuple[str, str | None, str]:
    host = (urlparse(url or "").hostname or "").lower()
    for ending, name, help_url, lang in SHOPS:
        if host == ending or host.endswith("." + ending):
            return name, help_url, lang
    return ("the seller" if not host else host.removeprefix("www.")), None, "en"


def facts(answer: dict) -> dict:
    """What every draft says, in plain words, from the code's outcome."""
    product = answer.get("product") or {}
    p = answer.get("plain") or {}
    lead = answer.get("lead_record") or {}
    match = next((m for m in answer.get("matches") or [] if m.get("record_id") == lead.get("record_id")), lead)
    risk = plain.hazard_of(f"{match.get('hazard') or ''} {match.get('title') or ''}")
    if risk == "a safety risk" and answer.get("hazards"):
        risk = plain.hazard_of(answer["hazards"][0].get("mechanism"))
    market = (answer.get("market") or "").upper()
    basis = answer.get("basis") or answer.get("outcome")
    name = " ".join(x for x in (product.get("brand"), product.get("model")) if x) or product.get("title") or \
        "this product"
    where, here = plain.country(match.get("jurisdiction")), plain.country(market) if market else "my country"
    record = (f"{match.get('authority')} notice {match.get('record_id')}"
              f"{' of ' + match['published'] if match.get('published') else ''}: {match.get('url')}"
              if match.get("url") else None)
    if basis == "confirmed_recall":
        claim = f"The {name} has been officially recalled in {here} because of {risk} ({record})."
        ask = "a full refund, as the recall provides"
    elif basis == "recalled_abroad_same_model":
        claim = (f"The same model ({name}) has been officially recalled in {where} because of {risk} ({record}). "
                 f"It has not been recalled in {here}, so please confirm whether the unit sold to me is affected.")
        ask = "confirmation that my unit is not affected, or a refund if it is"
    elif basis == "local_recall_batch_unknown":
        claim = (f"Some units of the {name} have been recalled in {here} because of {risk} ({record}). My unit's "
                 "batch/serial number is [batch or serial number from the label].")
        ask = "a refund if my unit is in the recalled range"
    elif answer.get("hazards") or basis in ("substantiated_hazard_signal", "hazard_reports"):
        h = (answer.get("hazards") or [{}])[0]
        n = h.get("independent_groups") or h.get("independent_reports")
        claim = (f"Other buyers report {risk} with the {name}"
                 f"{f' ({n} independent reports)' if n else ''}. It has not been officially recalled.")
        ask = "a refund or replacement, because the product does not seem safe"
    else:
        claim = (f"I have a safety concern about the {name}. SafeShelf found no official recall for it "
                 f"({answer.get('coverage', {}).get('summary') or 'checked official recall lists'}).")
        ask = "a refund or replacement"
    return {"name": name, "claim": claim, "ask": ask, "risk": risk, "record": record, "market": market,
            "title": p.get("title"), "investigation_id": answer.get("investigation_id"),
            "checked": (answer.get("retrieved_at") or datetime.now(UTC).isoformat())[:10],
            "evidence": [{"label": f"{m.get('authority')} {m.get('record_id')}", "url": m["url"]}
                         for m in (answer.get("matches") or []) if m.get("url") and m.get("tier") == "exact"][:3]}


def _refund(f: dict, purchase: dict) -> dict:
    shop, help_url, lang = shop_of(purchase.get("url") or purchase.get("listing_url"))
    happened = purchase.get("what_happened") or "[what happened, if anything: overheating, smell, sparks…]"
    body = (f"Hello,\n\nI bought the {f['name']} from you (order {purchase.get('order_id') or '[order number]'}, "
            f"{purchase.get('date') or '[date you bought it]'}).\n\n{f['claim']}\n\n"
            f"What I have seen: {happened}\n\nI have stopped using it. I am asking for {f['ask']}. Please tell me how "
            "to return it safely.\n\n"
            f"Checked with SafeShelf on {f['checked']} (reference {f['investigation_id'] or 'n/a'}).\n\n"
            "Thank you,\n[your name]")
    out = {"kind": "refund_request", "to": shop, "how": [f"Contact {shop} customer service: {help_url}"]
           if help_url else ["Send it to the seller through the shop's contact or returns page"],
           "subject": f"Refund request: {f['name']} - safety recall" if f["record"] else
           f"Refund request: {f['name']} - safety concern",
           "body": body, "language": "en", "fill_in": FILL_IN, "evidence": f["evidence"], "status": NOTHING_SENT}
    if lang == "ja":
        out["translations"] = {"ja": {
            "subject": f"返金のお願い: {f['name']}（安全上の問題）",
            "body": (f"お世話になっております。\n\n注文番号 {purchase.get('order_id') or '[注文番号]'} で購入した "
                     f"{f['name']} について連絡いたします。\n\n{f['claim']}\n\n"
                     "現在は使用を中止しています。返金または安全な返品方法をご案内ください。\n\n"
                     f"SafeShelf で {f['checked']} に確認（参照番号 {f['investigation_id'] or 'なし'}）。\n\n[お名前]"),
            "note": "Japanese written by code from fixed sentences; the recall details stay in English."}}
    return out


def _regulator(f: dict, purchase: dict) -> dict:
    reg = REGULATORS.get(f["market"], REGULATORS["IN"] if not f["market"] else None)
    if reg is None:
        return {"kind": "regulator_complaint", "to": "your country's consumer protection agency", "how": [],
                "subject": "", "body": "", "language": "en", "fill_in": [], "evidence": f["evidence"],
                "status": "SafeShelf has no regulator contact for this country yet."}
    shop, _, _ = shop_of(purchase.get("url") or purchase.get("listing_url"))
    happened = purchase.get("what_happened") or "[what happened: e.g. it overheated while charging; any injury]"
    body = (f"Product: {f['name']}\nBought from: {shop}, order {purchase.get('order_id') or '[order number]'}, on "
            f"{purchase.get('date') or '[date you bought it]'}\nListing: {purchase.get('url') or '[link to the listing]'}"
            f"\n\nWhy I am reporting it: {f['claim']}\n\nWhat happened to me: {happened}\n\n"
            f"Official records: {'; '.join(e['label'] + ' ' + e['url'] for e in f['evidence']) or 'none found'}\n"
            f"Checked with SafeShelf on {f['checked']} (reference {f['investigation_id'] or 'n/a'}). SafeShelf's "
            "result is set by code from official recall lists; it is not a regulator's decision.\n\n"
            f"I would like the regulator to look into this product and the seller.\n\n[your name], [phone or email]")
    out = {"kind": "regulator_complaint", "to": reg["name"], "how": reg["how"], "url": reg["url"],
           "subject": f"Unsafe product report: {f['name']}", "body": body, "language": "en",
           "fill_in": FILL_IN + ["[phone or email]"], "evidence": f["evidence"], "note": reg["note"],
           "status": NOTHING_SENT}
    if reg["language"] == "ja":
        out["translations"] = {"ja": {
            "subject": f"危険な製品の報告: {f['name']}",
            "body": (f"製品: {f['name']}\n購入先: {shop}（注文番号 {purchase.get('order_id') or '[注文番号]'}）\n"
                     f"購入日: {purchase.get('date') or '[購入日]'}\n\n報告の理由: {f['claim']}\n\n"
                     f"起きたこと: {purchase.get('what_happened') or '[例: 充電中に発熱した。けがの有無]'}\n\n"
                     "この製品と販売者について調査をお願いします。\n\n[お名前]・[連絡先]"),
            "note": "Japanese written by code from fixed sentences; the recall details stay in English."}}
    return out


def drafts(answer: dict, purchase: dict | None = None) -> list[dict]:
    purchase = purchase or {}
    f = facts(answer)
    out = [_refund(f, purchase)]
    if answer.get("outcome") != "no_matching_notice_found" or purchase.get("what_happened"):
        out.append(_regulator(f, purchase))
    return out
