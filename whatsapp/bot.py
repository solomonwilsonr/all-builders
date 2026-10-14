"""M12 WhatsApp bot logic: what the shopper sent -> SafeShelf API calls -> a short reply in English or Hindi.

No WhatsApp or HTTP code here (that is app.py), so every reply can be tested from plain dicts. The wording rules
match the extension: code picks the words from the API's verdict (red = official recall, amber = reports under
review, green = checked, nothing found); AI findings are always labelled as evidence, never as a ruling; a shop
is never called a scam.
"""
import re
from html import unescape

URL = re.compile(r"https?://[^\s<>\"']+")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")

HAZARD_WORDS = {
    "en": {"fire_burn": "overheating, fire or burns", "electric_shock": "electric shocks", "choking": "choking",
           "chemical": "chemical harm", "mechanical_injury": "injuries", "other": "safety problems"},
    "hi": {"fire_burn": "ज़्यादा गरम होने, आग या जलने", "electric_shock": "बिजली के झटके", "choking": "गला अटकने",
           "chemical": "रासायनिक नुकसान", "mechanical_injury": "चोट", "other": "सुरक्षा समस्याओं"},
}

TEXT = {
    "en": {
        "help": "Send me a product link or a photo of the product or its label. I'll check: Is it safe? Is it real?\n"
                "Reply HINDI for Hindi.",
        "working": "Checking this product. One moment…",
        "unknown": "I couldn't tell which product this is. Try a clearer photo of the label (brand and model "
                   "number), or send the shop link.",
        "red": "⛔ RECALLED. {name} is on an official recall list ({recalls}). Stop using it and follow the "
               "recall instructions.",
        "amber": "⚠️ BE CAREFUL. {n} buyers reported {hazard} with {name}. Under review, not an official recall.",
        "green": "✅ CHECKED. No recall and no hazard reports found for {name} in {reviews} reviews.",
        "not_enough_evidence": "ℹ️ NOT ENOUGH EVIDENCE. Too few reviews of {name} to judge its safety yet. "
                               "No recall found.",
        "under_review_recall": "A recall that may cover it is being checked.",
        "shop_ok": "Shop check: nothing unusual found.",
        "shop": "Shop check: {summary}",
        "hidden": "This page has hidden text aimed at AI assistants. I ignored it.",
        "alternative": "Safer option: {name} ({why}).",
        "footer": "AI findings are evidence for you, not an official ruling.",
        "photo": "From your photo: {name}.",
    },
    "hi": {
        "help": "मुझे किसी प्रोडक्ट का लिंक या उसकी या उसके लेबल की फ़ोटो भेजें। मैं जाँचूँगा: क्या यह सुरक्षित है? "
                "क्या यह असली है?\nEnglish के लिए ENGLISH लिखें।",
        "working": "इस प्रोडक्ट की जाँच कर रहा हूँ। एक पल…",
        "unknown": "मैं पहचान नहीं पाया कि यह कौन सा प्रोडक्ट है। लेबल (ब्रांड और मॉडल नंबर) की साफ़ फ़ोटो या दुकान का "
                   "लिंक भेजें।",
        "red": "⛔ रिकॉल हुआ है। {name} आधिकारिक रिकॉल सूची में है ({recalls})। इसका इस्तेमाल बंद करें और रिकॉल के "
               "निर्देश मानें।",
        "amber": "⚠️ सावधान रहें। {n} खरीदारों ने {name} से {hazard} की शिकायत की है। जाँच चल रही है, यह आधिकारिक "
                 "रिकॉल नहीं है।",
        "green": "✅ जाँच हो गई। {name} के {reviews} रिव्यू में कोई रिकॉल या खतरे की शिकायत नहीं मिली।",
        "not_enough_evidence": "ℹ️ पर्याप्त जानकारी नहीं। {name} की सुरक्षा बताने के लिए अभी बहुत कम रिव्यू हैं। कोई "
                               "रिकॉल नहीं मिला।",
        "under_review_recall": "एक रिकॉल जो इस पर लागू हो सकता है, उसकी जाँच चल रही है।",
        "shop_ok": "दुकान की जाँच: कुछ असामान्य नहीं मिला।",
        "shop": "दुकान की जाँच: {summary}",
        "hidden": "इस पेज में AI के लिए छिपा हुआ टेक्स्ट है। मैंने उसे अनदेखा किया।",
        "alternative": "सुरक्षित विकल्प: {name} ({why})।",
        "footer": "AI की जानकारी आपके लिए सबूत है, आधिकारिक फ़ैसला नहीं।",
        "photo": "आपकी फ़ोटो से: {name}।",
    },
}

# Shop-check reasons, from engine/trust.py summary(), in Hindi. Unknown reasons stay in English.
SHOP_HI = [
    (re.compile(r"photos copied from the genuine product's marketplace listing, on a site that is not a known seller"),
     "फ़ोटो असली प्रोडक्ट की मार्केटप्लेस लिस्टिंग से कॉपी की गई हैं, और यह साइट कोई जाना-माना विक्रेता नहीं है"),
    (re.compile(r"photos copied from the genuine product's official listing, but the seller is not authorised"),
     "फ़ोटो असली प्रोडक्ट की आधिकारिक लिस्टिंग से कॉपी की गई हैं, पर विक्रेता अधिकृत नहीं है"),
    (re.compile(r"price is (\d+)% of the genuine product's lowest (?:marketplace price|price from an authorised seller)"),
     r"कीमत असली प्रोडक्ट की सबसे कम कीमत का \1% है"),
    (re.compile(r"website registered only (\d+) days ago"), r"वेबसाइट सिर्फ़ \1 दिन पहले बनी है"),
    (re.compile(r"specs differ from the genuine model \(([^)]*)\)"), r"स्पेसिफ़िकेशन असली मॉडल से अलग हैं (\1)"),
    (re.compile(r"^Be careful: "), "सावधान: "),
]
HIDDEN_REASON = re.compile(r";? ?the page hides instructions aimed at AI assistants")  # said on its own line


def language(text: str, current: str = "en") -> str:
    """Hindi when the shopper writes Devanagari or asks for it; ENGLISH switches back."""
    words = text.strip().lower()
    if words in ("hindi", "हिंदी", "हिन्दी"):
        return "hi"
    if words == "english":
        return "en"
    return "hi" if DEVANAGARI.search(text) else current


def parse(message: dict) -> dict:
    """A WhatsApp Cloud API message -> {kind: link|photo|help|switch, ...}."""
    kind = message.get("type")
    if kind == "image":
        return {"kind": "photo", "media_id": message["image"]["id"], "caption": message["image"].get("caption", "")}
    text = (message.get("text") or {}).get("body", "") if kind == "text" else ""
    found = URL.search(text)
    if found:
        return {"kind": "link", "url": found.group(0).rstrip(").,"), "text": text}
    if text.strip().lower() in ("hindi", "हिंदी", "हिन्दी", "english"):
        return {"kind": "switch", "text": text}
    return {"kind": "help", "text": text}


def listing_from_html(url: str, html: str) -> dict:
    """What a shop page says about itself: title, price, photos and its visible text (hidden-text check)."""
    def meta(name: str) -> str | None:
        m = re.search(rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]*content=["\']([^"\']+)', html, re.IGNORECASE) \
            or re.search(rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']{re.escape(name)}["\']', html, re.IGNORECASE)
        return unescape(m.group(1)).strip() if m else None
    page_title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = meta("og:title") or (unescape(page_title.group(1)).strip() if page_title else None)
    price = meta("product:price:amount") or meta("og:price:amount")
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))).strip()
    listing = {"url": url, "title": title, "page_text": text[:8000],
               "image_urls": [u for u in [meta("og:image")] if u],
               "currency": meta("product:price:currency") or meta("og:price:currency")}
    if price:
        try:
            listing["price"] = float(price.replace(",", ""))
        except ValueError:
            pass
    return {k: v for k, v in listing.items() if v}


def product_name(identity: dict, lang: str = "en") -> str:
    return " ".join(x for x in (identity.get("brand"), identity.get("model")) if x) or \
        ("यह प्रोडक्ट" if lang == "hi" else "this product")


def shop_line(trust: dict, lang: str) -> str | None:
    if not trust:
        return None
    summary = HIDDEN_REASON.sub("", trust.get("summary") or "")
    if not summary.lower().startswith("be careful") or summary.strip() in ("Be careful:", "Be careful: ."):
        return TEXT[lang]["shop_ok"]
    if lang == "hi":
        for pattern, hindi in SHOP_HI:
            summary = pattern.sub(hindi, summary)
        summary = summary.removesuffix(".") + "।"
    return TEXT[lang]["shop"].format(summary=summary)


def reply(identity: dict, safety: dict, lang: str = "en", trust: dict | None = None,
          alternatives: dict | None = None, from_photo: bool = False) -> str:
    """The message text. Code picks every word from the API answers; nothing here is generated."""
    t, name = TEXT[lang], product_name(identity, lang)
    lines = [t["photo"].format(name=name)] if from_photo else []
    verdict = safety.get("verdict")
    status = safety.get("official_status") or {}
    if verdict == "red":
        lines.append(t["red"].format(name=name, recalls=", ".join(status.get("recall_ids") or [])))
    elif verdict == "amber":
        top = (safety.get("ai_findings") or [{}])[0]
        lines.append(t["amber"].format(n=top.get("independent_reports", 0), name=name,
                                       hazard=HAZARD_WORDS[lang].get(top.get("hazard_type"), HAZARD_WORDS[lang]["other"])))
    elif verdict == "green":
        lines.append(t["green"].format(name=name, reviews=safety.get("reviews_checked", 0)))
    else:
        lines.append(t["not_enough_evidence"].format(name=name))
    if status.get("recall_ids_under_review") and verdict != "red":
        lines.append(t["under_review_recall"])
    shop = shop_line(trust or {}, lang)
    if shop:
        lines.append(shop)
    if trust and trust.get("hidden_instructions_found"):
        lines.append(t["hidden"])
    best = ((alternatives or {}).get("alternatives") or [None])[0]
    if best and verdict in ("red", "amber"):
        why = f"0 hazard reports in {best['reviews_read']} reviews" if lang == "en" else \
            f"{best['reviews_read']} रिव्यू में 0 खतरे की शिकायत"
        lines.append(t["alternative"].format(name=f"{best['brand']} {best['model']}".strip(), why=why))
    lines.append(t["footer"])
    return "\n\n".join(lines)


def voice_text(text: str) -> str:
    """What the voice note says: the reply without symbols and without the footer's small print."""
    spoken = re.sub(r"[⛔⚠️✅ℹ️]", "", text)
    return spoken.replace("\n\n", " ").strip()
