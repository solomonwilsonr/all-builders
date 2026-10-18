"""Builds the SafeShelf test shops (shops/public/): three fictional storefronts carrying the eight test products from
the judges' page, as real web pages the SafeShelf extension can check in any Chrome, including the judges' page's
real cloud browser.

Each product page is the same listing as its test page (web/samples/presets.json: title, price, seller, page text),
and names that listing's address in <link rel="canonical">, so the live API checks exactly what the test page
recorded. Each page carries a "How to test this page" guide; the shops' home page has the full guide.

The guide sits outside <main>: the extension reads only the block around the product title (plus hidden text, for
the prompt-injection test), so the expected answer shown to people is never sent with the check.

    python3 shops/build.py        # or: make shops (builds, then serves on :8091)
"""
import html
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "public"
PRESETS = HERE.parent / "web" / "samples" / "presets.json"
JUDGES = "https://shelf2026-3656b.web.app"

SHOPS = {
    "kaimono": {"name": "Kaimono Ichiba", "local": "買い物市場", "market": "Japan", "tag": "Japan's everyday marketplace"},
    "haatbox": {"name": "Haatbox", "local": "", "market": "India", "tag": "Everything, delivered across India"},
    "megadealz24": {"name": "MegaDealz24", "local": "", "market": "India", "tag": "MEGA SALE · up to 90% OFF · TODAY ONLY"},
}

# What each page shows beyond the recorded listing. Nothing here contradicts the listing; reviews appear only where
# they match the recorded answer (the melting reports, and the control's ordinary reviews).
PAGES = {
    "recall_jp": {
        "art": "powerbank", "brand": "HAIARA", "rating": (4.1, "326件の評価"),
        "about": ["大容量10000mAh、スマートフォン約2回分", "USB-C入出力・USB-A出力の2台同時充電", "薄型・軽量 約198g、残量LED表示"],
        "specs": [("Brand", "HAIARA"), ("Model Number", "W5PRO"), ("Capacity", "10000mAh"), ("Ports", "USB-C ×1, USB-A ×1"), ("Country of origin", "China")],
        "delivery": "明日お届け · 送料無料", "reviews": [],
    },
    "recall": {
        "art": "powerbank", "brand": "Anker", "rating": (4.3, "2,140 ratings"),
        "about": ["10000mAh, charges most phones more than twice", "PowerIQ and VoltageBoost for fast charging", "Compact: about the size of a deck of cards"],
        "specs": [("Brand", "Anker"), ("Model Number", "A1263"), ("Capacity", "10000mAh"), ("Output", "5V 2.4A"), ("Country of origin", "China")],
        "delivery": "FREE delivery by Thursday", "reviews": [],
    },
    "fake": {
        "art": "charger", "brand": "Kelvo", "rating": (4.9, "52 ratings"), "mrp": 2999,
        "about": ["100% ORIGINAL Kelvo product guaranteed", "65W Super Fast charging for all phones and laptops", "Limited stock at this price, order now!!"],
        "specs": [("Brand", "Kelvo"), ("Model", "CX-65"), ("Output", "65 W"), ("Certification", "BIS verified")],
        "delivery": "Prepaid orders only (UPI). No returns on sale items.", "reviews": [],
    },
    "mark": {
        "art": "charger", "brand": "VoltNova", "rating": (4.2, "418 ratings"), "label": "BIS R-41097318",
        "about": ["65W GaN: charges a laptop and a phone together", "Two USB-C ports, foldable pins", "BIS registered (IS 13252)"],
        "specs": [("Brand", "VoltNova"), ("Model Number", "VN-65PD"), ("Output", "65 W"), ("Ports", "2 × USB-C"), ("Certification", "BIS R-41097318"), ("Country of origin", "China")],
        "delivery": "FREE delivery by Friday", "reviews": [],
    },
    "hazard": {
        "art": "charger", "brand": "Kelvo", "rating": (3.4, "1,284 ratings"), "label": "BIS R-41097318",
        "about": ["65W fast charging for laptops and phones", "Two USB-C ports", "Compact travel size"],
        "specs": [("Brand", "Kelvo"), ("Model Number", "CX-65"), ("Output", "65 W (20V 3.25A)"), ("Ports", "2 × USB-C"), ("Certification", "BIS R-41097318"), ("Country of origin", "China")],
        "delivery": "FREE delivery by Wednesday",
        "reviews": [
            (1, "Port got very hot and melted", "Used it for two weeks. The USB-C port overheated during charging and there is a burn mark now. Stopped using it.", "2026-08-02"),
            (1, "Smells of burning", "Charger smelled burnt after an hour with my laptop. Scary. Unplugged immediately.", "2026-08-19"),
            (2, "Hot to touch", "Gets hotter than my old charger. Returning it.", "2026-09-03"),
            (5, "Works great", "Charges my laptop fast. Compact. No issues so far.", "2026-09-10"),
            (4, "Good value", "Does what it says. A bit warm but fine.", "2026-09-21"),
        ],
    },
    "unknown": {
        "art": "kettle", "brand": "Zorvana", "rating": None,
        "about": ["1.2Lの大容量、約3分で沸騰", "空だき防止・自動電源オフ", "コードレスで注ぎやすい"],
        "specs": [("Brand", "Zorvana"), ("Model Number", "KT-12"), ("Capacity", "1.2L"), ("Power", "1200W")],
        "delivery": "3〜5日以内に発送", "reviews": [],
    },
    "janod": {
        "art": "table", "brand": "Janod", "rating": None,
        "about": ["Wooden activity table for toddlers: beads, gears, a maze and a bell", "Non-slip feet, water-based paints, FSC-certified wood", "From 1 year old"],
        "specs": [("Brand", "Janod"), ("Model Number", "J04402"), ("Material", "Wood"), ("Age range", "12 months and up")],
        "delivery": "Delivery 26–28 Oct", "reviews": [],
    },
    "clean": {
        "art": "charger", "brand": "SafeVolt", "rating": (4.5, "24 ratings"),
        "about": ["65W USB-C, two ports", "Fixed pins, over-temperature cut-off", "Two-year warranty"],
        "specs": [("Brand", "SafeVolt"), ("Model Number", "SV-65"), ("Output", "65 W"), ("Ports", "2 × USB-C"), ("Safety", "Over-temperature cut-off"), ("Country of origin", "India")],
        "delivery": "FREE delivery by Thursday",
        "reviews": [
            (5, "Fast and stays cool", "Charges my laptop and phone together. Barely warm after a long session.", "2026-07-14"),
            (4, "Solid build", "Feels well made. The cable could be longer, but the charger itself is great.", "2026-08-05"),
            (5, "Exactly as described", "65W as promised, works with my MacBook and my Pixel.", "2026-08-30"),
            (4, "Good value", "Cheaper than the brand-name ones and has worked fine for a month.", "2026-09-18"),
        ],
    },
}

TONES = {"red": "Don't buy", "amber": "Be careful", "green": "No problems found", "unknown": "Not enough evidence"}
SHIELD = ('<svg class="ss-mark" viewBox="0 0 32 32" role="img" aria-label="SafeShelf"><path d="M4 8a6 6 0 0 1 6-6h12a6 6 0 0 1 6 6v8c0 7-5.5 12-12 14C9.5 28 4 23 4 16z" fill="#0271E4"/>'
          '<path d="m10.5 16 4 4 7-8" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')
e = html.escape


def money(amount, currency):
    sym = {"INR": "₹", "JPY": "¥"}.get(currency, currency + " ")
    return f"{sym}{amount:,.0f}"


def art(kind, view, title, label="", brand=""):
    """Product photos, drawn: front, side and the rating label. Text on the label matches the specifications."""
    name = e(brand or title.split(" ")[0])
    if kind == "powerbank":
        body = ('<rect x="70" y="18" width="100" height="164" rx="18" fill="#f4f6f8" stroke="#2b3440" stroke-width="3"/>'
                '<rect x="102" y="30" width="36" height="6" rx="3" fill="#2b3440"/>'
                '<circle cx="104" cy="160" r="4" fill="#33b864"/><circle cx="120" cy="160" r="4" fill="#33b864"/><circle cx="136" cy="160" r="4" fill="#33b864"/>'
                f'<text x="120" y="104" text-anchor="middle" font-size="15" font-weight="700" fill="#2b3440" font-family="Helvetica, Arial">{name}</text>')
        side = '<rect x="104" y="18" width="32" height="164" rx="10" fill="#e9edf1" stroke="#2b3440" stroke-width="3"/><rect x="113" y="168" width="14" height="5" rx="2" fill="#2b3440"/>'
    elif kind == "kettle":
        body = ('<path d="M74 70h92l-8 104H82z" fill="#f4f6f8" stroke="#2b3440" stroke-width="3" stroke-linejoin="round"/>'
                '<path d="M166 88c26 0 26 52 0 52" fill="none" stroke="#2b3440" stroke-width="6"/><path d="M74 78 50 62" stroke="#2b3440" stroke-width="6" stroke-linecap="round"/>'
                '<rect x="70" y="56" width="100" height="16" rx="6" fill="#2b3440"/><rect x="66" y="174" width="108" height="10" rx="4" fill="#c7cfd8"/>'
                f'<text x="120" y="128" text-anchor="middle" font-size="14" font-weight="700" fill="#2b3440" font-family="Helvetica, Arial">{name}</text>')
        side = body
    elif kind == "table":
        body = ('<rect x="44" y="70" width="152" height="18" rx="6" fill="#e8c9a0" stroke="#2b3440" stroke-width="3"/>'
                '<path d="M58 88v86M182 88v86M80 88v70M160 88v70" stroke="#2b3440" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M70 70V44M100 70V36M130 70V44" stroke="#2b3440" stroke-width="3"/>'
                '<circle cx="70" cy="52" r="7" fill="#e45b4f"/><circle cx="100" cy="46" r="7" fill="#f2b43c"/><circle cx="130" cy="54" r="7" fill="#3c8fd8"/>'
                '<circle cx="164" cy="56" r="10" fill="#c7cfd8" stroke="#2b3440" stroke-width="2"/>'
                f'<text x="120" y="128" text-anchor="middle" font-size="14" font-weight="700" fill="#2b3440" font-family="Helvetica, Arial">{name}</text>')
        side = body
    else:
        body = ('<rect x="58" y="44" width="124" height="124" rx="22" fill="#f4f6f8" stroke="#2b3440" stroke-width="3"/>'
                '<rect x="94" y="76" width="52" height="12" rx="6" fill="#2b3440"/><rect x="94" y="100" width="52" height="12" rx="6" fill="#2b3440"/>'
                '<path d="M100 168v18M140 168v18" stroke="#2b3440" stroke-width="7" stroke-linecap="round"/>'
                f'<text x="120" y="146" text-anchor="middle" font-size="14" font-weight="700" fill="#2b3440" font-family="Helvetica, Arial">{name}</text>')
        side = '<rect x="96" y="44" width="48" height="124" rx="14" fill="#e9edf1" stroke="#2b3440" stroke-width="3"/><path d="M106 168h28" stroke="#2b3440" stroke-width="7" stroke-linecap="round"/>'
    if view == "label":
        lines = [title.split(",")[0][:30], "Ref. J04402 · 12m+" if kind == "table" else "Input: 100-240V~ 50/60Hz", label or "Made in China"]
        text = "".join(f'<text x="34" y="{78 + i * 26}" font-size="{14 if i == 0 else 12}" font-weight="{700 if i == 0 else 400}" fill="#1a1d21" font-family="Helvetica, Arial">{e(t)}</text>' for i, t in enumerate(lines))
        mark = '<rect x="34" y="146" width="44" height="28" fill="none" stroke="#1a1d21" stroke-width="2"/><text x="56" y="165" text-anchor="middle" font-size="12" font-weight="700" font-family="Helvetica, Arial">BIS</text>' if label.startswith("BIS") else ""
        inner = f'<rect x="20" y="40" width="200" height="146" rx="8" fill="#fff" stroke="#c7cfd8" stroke-width="2"/>{text}{mark}'
        what = "Close-up of the rating label"
    else:
        inner = body if view == "front" else side
        what = f"{'Front' if view == 'front' else 'Side'} view"
    return f'<svg viewBox="0 0 240 200" role="img" aria-label="{e(what)} of the {e(title[:60])}"><rect width="240" height="200" fill="#fbfcfd"/>{inner}</svg>'


def stars(n):
    return f'<span class="stars" aria-label="{n} out of 5 stars">{"★" * round(n)}{"☆" * (5 - round(n))}</span>'


def head(title, depth, extra=""):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{e(title)}</title>
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{up}shop.css">
{extra}<script src="{up}shop.js" defer></script>
</head>
"""


def testbar(depth, here=False):
    up = "../" * depth
    how = '<a href="#how-to-test">How to test this page</a>' if here else ""
    return (f'<div class="testbar"><div class="tb-in">{SHIELD}<p><b>SafeShelf test shop</b> <span>A fictional shop for testing the SafeShelf extension. Nothing here is for sale.</span></p>'
            f'<nav aria-label="Test shop"><a href="{up}index.html">All eight test products</a>{how}</nav></div></div>\n')


def shopbar(key, depth):
    s = SHOPS[key]
    up = "../" * depth
    logo = {"kaimono": '<span class="logo-mark" aria-hidden="true"></span>', "haatbox": '<span class="logo-mark" aria-hidden="true"></span>',
            "megadealz24": '<span class="logo-mark" aria-hidden="true"></span>'}[key]
    local = f'<small lang="ja">{s["local"]}</small>' if s["local"] else ""
    cart = "カート" if key == "kaimono" else "Cart"
    search = "何をお探しですか？" if key == "kaimono" else "Search for products, brands and more"
    return (f'<header class="shopbar"><div class="sb-in"><a class="logo" href="{up}#{key}">{logo}<span>{e(s["name"])}{local}</span></a>'
            f'<form class="search" role="search" action="{up}index.html"><label class="sr" for="q">Search {e(s["name"])}</label><input id="q" name="q" type="search" placeholder="{search}"><button type="submit">Search</button></form>'
            f'<span class="cart" data-cart>{cart} <b>0</b></span></div>'
            f'<div class="sb-tag">{e(s["tag"])}</div></header>\n')


def guide(p, i, presets, ctx):
    tone = p["expect"]["overall"][0] if not p.get("control") else "green"
    label = p["expect"]["label"].lstrip("⛔⚠️❔ ️")
    prev, nxt = presets[i - 1], presets[(i + 1) % len(presets)]
    return f"""<aside class="guide" id="how-to-test" aria-labelledby="g-h">
  <p class="g-kicker">Test product {i + 1} of {len(presets)}</p>
  <h2 id="g-h">How to test this page</h2>
  <ol class="g-steps">
    <li><b>Open it in Chrome with SafeShelf.</b> The judges' page's <a href="{JUDGES}/#shop-page" target="_blank" rel="noopener">real browser</a> already has it. In your own Chrome, <a href="{JUDGES}/site/get.html" target="_blank" rel="noopener">add the extension</a> and sign in.</li>
    <li><b>Press the shield <span class="g-check">Check with SafeShelf</span></b> on the right edge of this page. <span class="g-point" aria-hidden="true">→</span></li>
    <li><b>Read the answer</b> and open its evidence. It's a live check on SafeShelf's API, so it takes a few seconds and uses one check.</li>
  </ol>
  <div class="g-expect tone-{tone}"><span>A correct check says</span><b>{e(TONES[tone])}: {e(label)}</b></div>
  <p class="g-what"><b>What this page tests.</b> {e(p["what"])}.</p>
  <details class="g-more"><summary>How the answer is known</summary>
    <p>This page is the same listing as test page {i + 1} on the judges' page. It names that listing's address (<code>{e(p["request"]["listing"]["url"])}</code>), so SafeShelf checks exactly what the recorded run checked.</p>
    <p>No extension? The judges' page has <a href="{JUDGES}/#shop-page" target="_blank" rel="noopener">the instant test page</a> for this product, with the extension running inside it.</p>
  </details>
  <nav class="g-nav" aria-label="Other test products">
    <a href="{ctx(prev)}" rel="prev"><small>Previous</small>{e(prev["name"])}</a>
    <a href="{ctx(nxt)}" rel="next"><small>Next</small>{e(nxt["name"])}</a>
  </nav>
</aside>
"""


def product_page(p, i, presets):
    key, slug = p["shop"].split("/")
    s, page, l = SHOPS[key], PAGES[p["id"]], p["request"]["listing"]
    ja = key == "kaimono"
    ctx = lambda q: f"../{q['shop']}.html"  # noqa: E731 (links between products, relative to this folder)
    offer = {"@type": "Offer", "price": l["price"], "priceCurrency": l["currency"], "availability": "https://schema.org/InStock"}
    if l.get("seller"):
        offer["seller"] = {"@type": "Organization", "name": l["seller"]}
    model = next((v for k, v in page["specs"] if k.startswith("Model")), "")
    ld = {"@context": "https://schema.org", "@type": "Product", "name": l["title"], "brand": {"@type": "Brand", "name": page["brand"]},
          "model": model, "url": l["url"], "offers": offer}
    extra = (f'<link rel="canonical" href="{e(l["url"])}"><!-- the listing this page stands for: SafeShelf checks this address -->\n'
             f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n')
    views = [("front", "Front"), ("side", "Side"), ("label", "Label")]
    gallery = "".join(f'<figure class="shot{" on" if v == "front" else ""}" data-shot="{v}">{art(page["art"], v, l["title"], page.get("label", ""), page["brand"])}</figure>' for v, _ in views)
    thumbs = "".join(f'<button type="button" class="thumb{" on" if v == "front" else ""}" data-show="{v}" aria-label="Show the {n.lower()} photo">{art(page["art"], v, l["title"], page.get("label", ""), page["brand"])}</button>' for v, n in views)
    rating = ""
    if page["rating"]:
        r, n = page["rating"]
        rating = f'<p class="rating">{stars(r)} <span>{r}</span> <a href="#reviews">{e(n)}</a></p>'
    mrp = ""
    if page.get("mrp"):
        off = round(100 * (1 - l["price"] / page["mrp"]))
        mrp = f'<p class="mrp"><span class="off">-{off}%</span> M.R.P.: <s>{money(page["mrp"], l["currency"])}</s></p>'
    seller = f'<p class="seller">Sold by <span id="seller">{e(l["seller"])}</span></p>' if l.get("seller") else ""
    hidden = ""
    if p["id"] == "fake":
        # the prompt-injection test: invisible to shoppers, read by any AI that takes in the whole page. SafeShelf must ignore it and flag it.
        injected = l["page_text"].split("\n", 2)[2]
        hidden = f'<div class="offscreen" aria-hidden="true">{e(injected)}</div>'
    urgency = ('<div class="urgency"><b>⚡ DEAL ENDS IN <span data-countdown>00:09:59</span></b><span>Only 3 left in stock! 147 people are viewing this.</span></div>'
               if key == "megadealz24" else "")
    about = "".join(f"<li>{e(a)}</li>" for a in page["about"])
    specs = "".join(f'<tr><th scope="row">{e(k)}</th><td>{e(v)}</td></tr>' for k, v in page["specs"])
    tax = "（税込）" if ja else "Inclusive of all taxes"
    btn_cart, btn_buy = ("カートに入れる", "今すぐ買う") if ja else ("Add to cart", "Buy now")
    if page["reviews"]:
        items = "".join(f'<article class="review"><div class="r-meta">{stars(st)}<time datetime="{d}">{d}</time></div><strong>{e(t)}</strong><p>{e(b)}</p></article>'
                        for st, t, b, d in page["reviews"])
        reviews = f'<section class="reviews" id="reviews" aria-labelledby="rv-h"><h2 id="rv-h">Customer reviews</h2>{items}</section>\n'
    else:
        reviews = f'<section class="reviews" id="reviews" aria-labelledby="rv-h"><h2 id="rv-h">Customer reviews</h2><p class="none">{"まだレビューはありません。" if ja else "No written reviews yet."}</p></section>\n'
    crumbs = {"kaimono": "家電 › モバイルバッテリー" if p["id"] == "recall_jp" else "家電 › キッチン家電", "haatbox": "Toys › Baby & toddler › Activity tables" if p["id"] == "janod" else "Electronics › Mobile accessories › Chargers", "megadealz24": "HOT DEALS › Chargers"}[key]
    return (head(f"{l['title']} | {s['name']}", 1, extra)
            + f'<body class="skin-{key}" data-safeshelf-listing-id="{e(p["id"])}">\n'
            + testbar(1, here=True) + shopbar(key, 1)
            + f'<nav class="crumbs" aria-label="Breadcrumb">{e(crumbs)}</nav>\n'
            + f"""<main class="product" id="product">
  <div class="gallery" id="gallery">{gallery}<div class="thumbs">{thumbs}</div></div>
  <div class="info">
    <a class="brand" href="#">{"ブランド: " if ja else "Visit the "}{e(page["brand"])}{"" if ja else " store"}</a>
    <h1 id="title">{e(l["title"])}</h1>
    {rating}
    {urgency}
    <div class="buybox">
      {mrp}<p class="price" id="price">{money(l["price"], l["currency"])}</p><p class="tax">{tax}</p>
      <p class="delivery">{e(page["delivery"])}</p>
      {seller}
      <div class="btns"><button type="button" class="b-cart" data-demo>{btn_cart}</button><button type="button" class="b-buy" data-demo>{btn_buy}</button></div>
    </div>
    <h2 class="about-h">{"商品の説明" if ja else "About this item"}</h2>
    <ul class="about">{about}</ul>
  </div>
  <section class="specs-box" aria-labelledby="sp-h"><h2 id="sp-h">Specifications</h2><table class="specs">{specs}</table>{hidden}</section>
</main>
"""
            + guide(p, i, presets, ctx) + reviews + footer(1) + "</body>\n</html>\n")


def footer(depth):
    up = "../" * depth
    return (f'<footer class="foot"><p>Kaimono Ichiba, Haatbox and MegaDealz24 are fictional shops built to test SafeShelf; nothing here is for sale. '
            f'Kelvo, SafeVolt, VoltNova and Zorvana are made-up brands. The HAIARA, Anker and Janod recalls are real notices from Japan\'s CAA, the US CPSC and Australia\'s ACCC; the Janod listing is a real Amazon.in page.</p>'
            f'<p><a href="{up}index.html">All eight test products</a> · <a href="{JUDGES}" target="_blank" rel="noopener">SafeShelf judges\' page</a></p></footer>\n')


def index_page(presets):
    groups = ""
    for key, s in SHOPS.items():
        cards = ""
        for i, p in enumerate(presets):
            if not p["shop"].startswith(key + "/"):
                continue
            l, page = p["request"]["listing"], PAGES[p["id"]]
            tone = "green" if p.get("control") else p["expect"]["overall"][0]
            cards += (f'<li><a class="pcard" href="{p["shop"]}.html"><span class="pc-art">{art(page["art"], "front", l["title"], brand=page["brand"])}</span>'
                      f'<span class="pc-n">{"✓" if p.get("control") else i + 1}</span><b>{e(p["name"])}</b><small>{e(l["title"])}</small>'
                      f'<span class="pc-price">{money(l["price"], l["currency"])}</span>'
                      f'<span class="pc-exp tone-{tone}">{e(p["expect"]["label"].lstrip("⛔⚠️❔ " + chr(0xfe0f)))}</span></a></li>')
        local = f' <span lang="ja">{s["local"]}</span>' if s["local"] else ""
        groups += (f'<section class="shopgroup sg-{key}" id="{key}" aria-labelledby="h-{key}"><header><span class="sg-logo skin-{key}"><span class="logo-mark" aria-hidden="true"></span></span>'
                   f'<div><h2 id="h-{key}">{e(s["name"])}{local}</h2><p>{e(s["market"])} · {e(s["tag"])}</p></div></header><ul class="pgrid">{cards}</ul></section>\n')
    return (head("SafeShelf test shops", 0) + '<body class="home">\n' + testbar(0)
            + f"""<header class="hero"><div class="hero-in">
  <p class="kicker">SafeShelf test shops</p>
  <h1>Eight shop pages where the right answer is known</h1>
  <p class="lede">Real web pages for the eight test products on the judges' page: a recall in Japan, a US recall sold in India, a fake shop, a borrowed safety mark, melting chargers, a product nobody has data on, a toddler's table recalled abroad and still sold on Amazon.in, and a clean control that must stay quiet.</p>
</div></header>
<main class="home-main">
<section class="howto" id="how-to-test" aria-labelledby="h-how">
  <h2 id="h-how">How to use these shops</h2>
  <ol class="ways">
    <li><span class="w-n">1</span><div><h3>In the judges' page real browser</h3><p>On the <a href="{JUDGES}/#shop-page" target="_blank" rel="noopener">judges' page</a>, press <b>Start a real browser</b>. A real Chrome with SafeShelf opens on this page. Pick a product below, or tap <b>Real browser</b> on any product card there.</p></div></li>
    <li><span class="w-n">2</span><div><h3>In your own Chrome</h3><p><a href="{JUDGES}/site/get.html" target="_blank" rel="noopener">Add the SafeShelf extension</a> and sign in, then open any product below.</p></div></li>
    <li><span class="w-n">3</span><div><h3>Press the shield, read the answer</h3><p>On a product page, press the shield button, <b>Check with SafeShelf</b>, on the right edge. Each page has a short guide saying what a correct answer is, so you can tell at once if SafeShelf got it right.</p></div></li>
  </ol>
  <p class="howto-note">These checks run live on SafeShelf's API and use one check each. For instant answers with no extension, use the <a href="{JUDGES}/#shop-page" target="_blank" rel="noopener">test pages</a> on the judges' page: the same eight listings.</p>
</section>
{groups}
<section class="realshops" aria-labelledby="h-real"><h2 id="h-real">Or try a real shop</h2><p>The extension works on real product pages too:</p>
  <p class="rs-links"><a href="https://www.amazon.in/">Amazon.in</a><a href="https://www.flipkart.com/">Flipkart</a><a href="https://www.amazon.co.jp/">Amazon.co.jp</a><a href="https://www.amazon.com.au/">Amazon.com.au</a><a href="https://www.amazon.sg/">Amazon.sg</a></p></section>
</main>
""" + footer(0) + "</body>\n</html>\n")


def main():
    presets = json.loads(PRESETS.read_text())["presets"]
    if OUT.exists():
        shutil.rmtree(OUT)
    for name in ("shop.css", "shop.js", "favicon.svg"):
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(HERE / "static" / name, OUT / name)
    (OUT / "index.html").write_text(index_page(presets))
    for i, p in enumerate(presets):
        path = OUT / f"{p['shop']}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(product_page(p, i, presets))
    (OUT / "404.html").write_text(head("Not found | SafeShelf test shops", 0).replace('href="shop', 'href="/shop').replace('src="shop', 'src="/shop')
                                  + '<body class="home">\n' + testbar(0).replace('href="index.html"', 'href="/"')
                                  + '<main class="home-main"><section class="howto"><h2>That page isn\'t here</h2><p><a href="/">See all eight test products</a>.</p></section></main></body>\n</html>\n')
    print(f"built {len(presets)} product pages and the home page in {OUT.relative_to(HERE.parent)}/")


if __name__ == "__main__":
    main()
