"""Owner help: the before-buying, while-using and when-something-goes-wrong answers Shelf Chat gives.

    compatibility(charger, device)             will this charger work with my laptop / phone?
    setup(appliances, chain, market)           appliance + extension board + adapter + cable: are the ratings safe?
    symptoms(found, kind, market)              it smells, swells, leaks or gets hot: what to do now (never "test it")
    suitability(household, hazards, text, ...) children, allergies, pets, accessibility, against this product's evidence
    repair_or_replace(situation)               recall remedy, return, warranty service, qualified repair or replace
    disposal(market, item)                     official battery and e-waste collection, never household waste
    pressure(tactics, market)                  countdown timers, pre-ticked extras, hidden subscriptions explained
    incident_report(fields) / support_request(fields)   a clear report and a warranty or support request to copy

Every answer is written by code from the numbers the shopper (or the product record) gave; Gemini only fills in the
arguments and explains the result. A value nobody gave is "not known", never assumed: the answer then says what to
read on the label. Nothing here sends anything: drafts are for the shopper to copy and send themselves.
"""
import re
from datetime import date

from engine import complaints, region

LABEL = "Guidance from SafeShelf's code rules on the details you gave - not a test of the product or legal advice"
VOLTS = {"in": 230, "jp": 100, "au": 230, "nz": 230, "sg": 230, "my": 240, "id": 230, "th": 220, "ph": 220, "vn": 220}
EMERGENCY = {"in": "112 (fire 101)", "jp": "119", "au": "000", "nz": "111", "sg": "995", "my": "999", "id": "112",
             "th": "199 (fire)", "ph": "911", "vn": "114 (fire)"}
NO_TESTING = ("Don't test it to see if it happens again: don't plug it back in, charge it, open it or press on it.")


def _num(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


BY_NAME = {name.lower().removeprefix("the "): code for code, name in region.NAMES.items()}


def _market(market: str | None) -> str:
    """A market code (in, jp, au...) from a code or a country name, the way a model may pass it; India if unknown."""
    key = (market or "").strip().lower().removeprefix("the ")
    return key if key in region.NAMES else BY_NAME.get(key, "in")


# ---------- compatibility checker ----------

CONNECTORS = [(re.compile(pattern, re.IGNORECASE), code) for pattern, code in (
    (r"usb[\s_-]*c|type[\s_-]*c", "usb_c"), (r"lightning", "lightning"), (r"micro[\s_-]*usb", "micro_usb"),
    (r"usb[\s_-]*a\b|type[\s_-]*a", "usb_a"), (r"magsafe", "magsafe"),
    (r"barrel|dc[\s_-]*jack|round pin|\d\.\d\s*x\s*\d", "barrel"))]
PROTOCOLS = [(re.compile(pattern, re.IGNORECASE), code) for pattern, code in (
    (r"\bpps\b", "pps"), (r"\bpd\b|power[\s_-]*delivery", "usb_pd"), (r"quick[\s_-]*charge|\bqc\b", "quick_charge"),
    (r"warp|dash|supervooc|vooc", "vooc_warp"), (r"super[\s_-]*fast", "samsung_sfc"))]


def connector(text: str | None) -> str | None:
    """The plug at the device end, as a code: usb_c, lightning, micro_usb, usb_a, magsafe, barrel, or the text."""
    if not text:
        return None
    return next((code for pattern, code in CONNECTORS if pattern.search(text)), text.strip().lower())


def protocols(values) -> set[str]:
    text = " ".join(values) if isinstance(values, list | tuple | set) else str(values or "")
    found = {code for pattern, code in PROTOCOLS if pattern.search(text)}
    return found | ({"usb_pd"} if "pps" in found else set())


def compatibility(charger: dict, device: dict) -> dict:
    """charger: {connector, watts, volts, amps, protocols}; device: {connector, watts (what it needs), volts, protocols}.
    -> {verdict: works | works_slowly | wont_work | dont_use | not_enough_info, reasons, check_on_label}"""
    reasons, read = [], []
    plug_c, plug_d = connector(charger.get("connector")), connector(device.get("connector"))
    volts_c, volts_d = _num(charger.get("volts")), _num(device.get("volts"))
    watts_c = _num(charger.get("watts")) or ((volts_c or 0) * (_num(charger.get("amps")) or 0)) or None
    watts_d = _num(device.get("watts")) or ((volts_d or 0) * (_num(device.get("amps")) or 0)) or None
    proto_c, proto_d = protocols(charger.get("protocols")), protocols(device.get("protocols"))
    usb = {plug_c, plug_d} <= {"usb_c", "usb_a", "lightning", "micro_usb", None} and "barrel" not in (plug_c, plug_d)
    verdict = "works"

    if plug_c and plug_d and plug_c != plug_d:
        verdict = "wont_work"
        reasons.append(f"The plug doesn't fit: the charger's cable ends in {plug_c.replace('_', '-')}, the device "
                       f"takes {plug_d.replace('_', '-')}. Use the right cable, not a plug adapter on a power cable.")
    elif not (plug_c and plug_d):
        read.append("the plug type at the device end (USB-C, Lightning, barrel...)")

    if not usb:  # barrel and brand plugs: the voltage is fixed, so it must match the device exactly
        if volts_c and volts_d and abs(volts_c - volts_d) / volts_d > 0.05:
            verdict = "dont_use"
            reasons.append(f"Wrong voltage: the charger gives {volts_c:g} V, the device needs {volts_d:g} V. A "
                           "fixed-voltage plug at the wrong voltage can damage the device or overheat.")
        elif not (volts_c and volts_d):
            read.append("the voltage: OUTPUT on the charger and INPUT on the device (for example 19.5V)")
    elif volts_d and volts_d > 5.5 and "usb_pd" in proto_d and "usb_pd" not in proto_c and proto_c:
        verdict = "wont_work" if verdict == "works" else verdict
        reasons.append(f"The device charges at {volts_d:g} V over USB Power Delivery, which this charger doesn't list.")

    if watts_c and watts_d:
        if watts_c >= watts_d:
            reasons.append(f"Enough power: {watts_c:g} W for a device that needs {watts_d:g} W.")
        elif not usb:
            verdict = "dont_use"
            reasons.append(f"Too little power: {watts_c:g} W for a device that needs {watts_d:g} W. A fixed-voltage "
                           "adapter run past its rating can overheat.")
        elif watts_c >= 0.6 * watts_d:
            verdict = verdict if verdict in ("wont_work", "dont_use") else "works_slowly"
            reasons.append(f"It charges, slower: {watts_c:g} W for a device that needs {watts_d:g} W (a laptop may "
                           "still drain while you use it hard).")
        else:
            verdict = verdict if verdict == "dont_use" else "wont_work"
            reasons.append(f"Probably too little power: {watts_c:g} W for a device that needs {watts_d:g} W. A "
                           "laptop may not charge at all; a phone charges very slowly.")
    else:
        read.append("the power: OUTPUT watts on the charger (or volts x amps) and what the device needs")

    if verdict in ("works", "works_slowly") and proto_d - proto_c and proto_c:
        reasons.append("Fast charging won't work: the device's fast-charge standard ("
                       + ", ".join(sorted(p.replace("_", " ") for p in proto_d - proto_c))
                       + ") isn't on the charger, so it charges at normal speed.")
    if verdict == "works" and read:
        verdict = "not_enough_info"
    return {"verdict": verdict, "reasons": reasons, "check_on_label": read,
            "tip": "Use a charger with your market's safety mark (BIS in India, PSE in Japan, RCM in Australia) from "
                   "the brand or an authorised seller; very cheap copies are a common cause of charger fires.",
            "label": LABEL}


# ---------- accessory (socket chain) checks ----------

HIGH_LOAD = re.compile(r"heater|kettle|iron|geyser|water heater|air ?con|\bac\b|microwave|oven|induction|hob|"
                       r"hair ?dryer|toaster|fryer|washing machine|dryer|fridge|refrigerator|radiator", re.IGNORECASE)


def setup(appliances: list[dict], chain: list[dict], market: str | None = None) -> dict:
    """appliances: [{name, watts, amps, volts}] all on the chain; chain: [{kind: extension | adapter | cable | socket,
    name, rated_watts, rated_amps, rated_volts}] from the appliance to the wall.
    -> {verdict: ok | close_to_limit | unsafe | not_enough_info, load_watts, problems, check_on_label}"""
    m = _market(market)
    mains = VOLTS.get(m, 230)
    problems, read, verdict = [], [], "ok"
    load, unknown_load = 0.0, []
    for a in appliances or []:
        w = _num(a.get("watts")) or ((_num(a.get("amps")) or 0) * mains) or None
        if w:
            load += w
        else:
            unknown_load.append(a.get("name") or "an appliance")
        dev_volts = _num(a.get("volts"))
        if dev_volts and abs(dev_volts - mains) / mains > 0.15:
            verdict = "unsafe"
            problems.append(f"{a.get('name') or 'The appliance'} is made for {dev_volts:g} V; mains here is {mains} V. "
                            "A plug adapter doesn't change the voltage: use it only if its label says a range like "
                            "100-240V, otherwise it needs a voltage converter.")
    if unknown_load:
        read.append(f"the watts (W) on the label of {', '.join(unknown_load)}")
    heavy = [a.get("name") for a in appliances or [] if HIGH_LOAD.search(a.get("name") or "")
             or (_num(a.get("watts")) or 0) >= 1500]
    boards = [c for c in chain or [] if (c.get("kind") or "").lower() in ("extension", "power strip", "board")]
    if len(boards) >= 2:
        verdict = "unsafe"
        problems.append("Extension boards plugged into each other (daisy-chained): every board adds a weak point and "
                        "the total load goes through the first one. Use one board, plugged into the wall.")
    if heavy and any((c.get("kind") or "").lower() in ("extension", "power strip", "board", "adapter") for c in chain or []):
        verdict = "unsafe"
        problems.append(f"{', '.join(n for n in heavy if n)} draws a lot of power: plug it straight into a wall "
                        "socket, not an extension board or adapter.")
    if m == "in" and load > 6 * mains:
        problems.append(f"{load:g} W needs a 16 A socket in India: don't run it through a 6 A plug, adapter or board.")
    for c in chain or []:
        name = c.get("name") or c.get("kind") or "a part of the setup"
        rating = _num(c.get("rated_watts")) or ((_num(c.get("rated_amps")) or 0) * (_num(c.get("rated_volts")) or mains)) or None
        if not rating:
            read.append(f"the rating printed on {name} (for example 10A 250V, or 2400W max)")
            continue
        if load > rating:
            verdict = "unsafe"
            problems.append(f"{name} is overloaded: {load:g} W through a part rated {rating:g} W. It can overheat and "
                            "start a fire.")
        elif load > 0.8 * rating and verdict == "ok":
            verdict = "close_to_limit"
            problems.append(f"{name} is close to its limit ({load:g} W of {rating:g} W): fine for a short time, not "
                            "for long or unattended use.")
    if verdict == "ok" and read:
        verdict = "not_enough_info"
    return {"verdict": verdict, "load_watts": load or None, "mains_volts": mains, "problems": problems,
            "check_on_label": read, "label": LABEL}


# ---------- something is wrong with it ----------

SYMPTOMS = {
    "smoke_or_flame": ("emergency", "smoke or flames"), "sparks": ("emergency", "sparks"),
    "hissing_or_popping": ("emergency", "hissing or popping from a battery"),
    "burning_smell": ("stop", "a burning smell"), "swelling": ("stop", "swelling or a bulging case"),
    "leaking": ("stop", "leaking liquid"), "very_hot": ("stop", "too hot to hold"),
    "melted_or_scorched": ("stop", "melting or scorch marks"), "shock_or_tingle": ("stop", "a shock or tingle"),
    "damaged_cable": ("stop", "a damaged or frayed cable"), "cracked_case": ("stop", "a cracked case"),
    "chemical_smell": ("stop", "a chemical smell"), "buzzing": ("watch", "buzzing or crackling"),
    "warm": ("watch", "getting warm"), "not_working": ("watch", "it stopped working"),
    "error_code": ("watch", "an error code"),
}
URGENCY = ["watch", "stop", "emergency"]
BATTERY = re.compile(r"battery|power ?bank|phone|laptop|tablet|e-?bike|scooter|vape|earbud|watch|charger", re.IGNORECASE)


def symptoms(found: list[str], kind: str | None = None, market: str | None = None) -> dict:
    """found: SYMPTOMS keys. -> {urgency: emergency | stop | watch, steps, after, ...}. Safe observations only."""
    known = [s for s in found or [] if s in SYMPTOMS]
    urgency = max((SYMPTOMS[s][0] for s in known), key=URGENCY.index, default="watch")
    battery = bool(BATTERY.search(kind or ""))
    m = _market(market)
    steps = []
    if urgency == "emergency":
        steps += ["Keep away from it and get people and pets out of the room.",
                  (f"If anything is burning, call the fire service ({EMERGENCY.get(m, '112')}). Don't use water on an "
                  "electrical or battery fire."),
                  ("Only if you can do it without touching the product: switch it off at the wall socket or the main "
                  "switch.")]
    elif urgency == "stop":
        steps += [("Stop using it now. Switch it off at the wall socket, then unplug it, only if the plug isn't hot or "
                  "damaged."),
                  ("If it is cool enough to move, put it on a hard surface that can't burn (tile, concrete), away from "
                  "curtains, bedding and anything flammable, and leave it there.")]
        if "swelling" in known or (battery and urgency != "watch"):
            steps.append("A swollen or overheating battery can catch fire: don't press, puncture, charge or bin it.")
        if "leaking" in known or "chemical_smell" in known:
            steps.append("Don't touch the liquid; open a window, wash any skin it touched with water, and keep "
                         "children and pets away.")
        if "shock_or_tingle" in known:
            steps.append("Don't touch it again until it is unplugged at the wall; if someone was hurt by a shock, "
                         "get medical advice.")
    else:
        steps += [("You can keep an eye on it: chargers and laptops get warm while charging, but they should never be "
                  "too hot to hold."),
                  ("Charge it on a hard surface, not on a bed or sofa, and not unattended or overnight until you know "
                  "what's going on."),
                  "Stop using it straight away if it gets very hot, smells of burning, swells, sparks or leaks."]
        if "error_code" in known or "not_working" in known:
            steps.append("Look the error up in the manual (send SafeShelf the manual as a PDF and ask about it).")
    steps.append(NO_TESTING)
    after = ["Take photos of it and any damage, and keep the product, box and receipt: they are evidence.",
             "Check your warranty and return dates (SafeShelf can find them if the product is in your household list).",
             "Report what happened so other buyers are warned; SafeShelf can write the report for you."]
    return {"urgency": urgency, "symptoms": [SYMPTOMS[s][1] for s in known], "steps": steps, "after": after,
            "emergency_number": EMERGENCY.get(m, "112") if urgency == "emergency" else None, "label": LABEL}


# ---------- personal suitability ----------

BUTTON_CELL = re.compile(r"button (cell|battery)|coin (cell|battery)|\bcr ?20(16|25|32)\b|\blr ?44\b", re.IGNORECASE)


def suitability(household: dict, hazard_types: list[str], product_text: str, category: str | None = None) -> dict:
    """household: {children_under_3, children, pets, allergies: [...], accessibility: [...]} as the shopper said;
    hazard_types: from the product's evidence; product_text: its title, attributes and listing text.
    -> {concerns: [{for, concern, from: evidence | listing | general}], no_evidence: [...]}"""
    text = f"{product_text or ''} {category or ''}"
    hazards = set(hazard_types or [])
    concerns, unknown = [], []

    def add(who, concern, source):
        concerns.append({"for": who, "concern": concern, "from": source})

    kids = household.get("children_under_3") or household.get("children")
    if household.get("children_under_3"):
        if "choking" in hazards:
            add("children under 3", "Buyers report small or detachable parts: keep it away from under-3s.", "evidence")
        elif re.search(r"toy|baby|infant|teether|rattle", text, re.IGNORECASE):
            unknown.append("whether its parts are small enough to choke on: check the age label (0-3 warning)")
    if kids and BUTTON_CELL.search(text):
        add("children", "It uses a button or coin battery: a swallowed one can burn through a child's throat within "
                        "hours. The battery cover must be screwed shut; if one is swallowed, go to a hospital now.",
            "listing")
    if kids and hazards & {"fire_burn", "electric_shock"}:
        add("children", "Buyers report heat or shock problems: keep it out of children's reach and don't leave it "
                        "charging unattended.", "evidence")
    if kids and "chemical" in hazards:
        add("children", "Buyers report leaks or chemical smells: store it out of reach.", "evidence")
    if household.get("pets") and re.search(r"cable|cord|charger|battery|wire", text, re.IGNORECASE):
        add("pets", "Pets chew cables and batteries: keep cords out of reach and unplug it when not in use.", "general")
    for allergen in household.get("allergies") or []:
        if allergen and re.search(rf"\b{re.escape(allergen)}", text, re.IGNORECASE):
            add(f"{allergen} allergy", f"The listing mentions {allergen}.", "listing")
        elif allergen:
            unknown.append(f"whether it contains {allergen}: SafeShelf has no material or ingredient list showing "
                           "it, so check the label or ask the brand")
    for need in household.get("accessibility") or []:
        unknown.append(f"how well it suits {need}: the listing and reviews SafeShelf read don't say; check the "
                       "controls, display and alerts in the manual or ask the seller")
    if "skin" in " ".join(household.get("allergies") or []).lower() and "chemical" in hazards:
        add("skin allergies", "Buyers report irritation or chemical smells.", "evidence")
    return {"concerns": concerns, "no_evidence": unknown,
            "note": "Only what the evidence and the listing say; nothing found is not a promise it suits you.",
            "label": LABEL}


# ---------- repair, replace, dispose ----------

SEALED = re.compile(r"charger|power ?bank|adapter|battery|earbud|vape|bulb|cable", re.IGNORECASE)


def repair_or_replace(s: dict) -> dict:
    """s: {recalled, safety_symptom, within_return, under_warranty, repair_quote, replacement_price, kind, age_years}.
    -> {advice, options: [{option, why}]} in the order to try them."""
    options = []
    kind = s.get("kind") or ""
    if s.get("recalled"):
        options.append({"option": "recall remedy", "why": "It is recalled: the brand must fix, replace or refund it "
                        "free. Don't repair it yourself or sell it on."})
    if s.get("within_return"):
        options.append({"option": "return or replacement from the seller", "why": "You are still inside the return "
                        "window: that is the quickest way, and it costs nothing."})
    if s.get("under_warranty"):
        options.append({"option": "warranty service", "why": "It is under warranty: use the brand's authorised "
                        "service centre. Opening it or a third-party repair can void the warranty."})
    quote, price = _num(s.get("repair_quote")), _num(s.get("replacement_price"))
    if s.get("safety_symptom") and SEALED.search(kind):
        options.append({"option": "replace it", "why": "It overheated, swelled, sparked or leaked, and a sealed item "
                        "like this can't be repaired safely. Buy a certified replacement and dispose of this one."})
    elif quote and price and quote > 0.5 * price:
        options.append({"option": "replace it", "why": f"The repair ({quote:g}) costs more than half a new one "
                        f"({price:g})."})
    else:
        options.append({"option": "qualified repair", "why": "Use the brand's authorised service centre or a "
                        "qualified technician" + (" (it had a safety problem, so not a general repair shop)"
                                                  if s.get("safety_symptom") else "") + "."})
        if not (quote and price):
            options[-1]["why"] += " Ask for a quote and compare it with a new one: over half the price, replace it."
    options.append({"option": "dispose of the old one safely", "why": "If you replace it, take it to an e-waste or "
                    "battery collection point, never household waste."})
    return {"advice": options[0]["option"], "options": options,
            "never": "Don't repair mains wiring or lithium batteries yourself.", "label": LABEL}


DISPOSAL = {
    "in": [("The brand's e-waste take-back", ("Brands must collect their old products under India's E-Waste "
            "(Management) Rules 2022 and Battery Waste Management Rules 2022; the take-back number is on the brand's "
            "website.")), ("A CPCB-authorised e-waste recycler or collection centre",
            "The Central Pollution Control Board lists them by state at https://cpcb.nic.in/"),
           ("Your city's e-waste drive or collection point", "Many municipal corporations run e-waste bins and drives.")],
    "jp": [("JBRC collection box (small rechargeable batteries)", ("At electronics and home-centre stores; find one at "
            "https://www.jbrc.com/")), ("Small home appliance recycling (小型家電リサイクル)", ("Your city's collection "
            "boxes or the retailer; check your municipality's rules.")),
           ("Home Appliance Recycling Law items", ("TVs, fridges, washing machines and air conditioners go back through "
            "the retailer, for a recycling fee."))],
    "au": [("B-cycle battery drop-off", ("Free battery drop-off at many supermarkets and hardware stores: "
            "https://bcycle.com.au/")), ("MobileMuster (phones and their batteries and chargers)",
            "https://www.mobilemuster.com.au/"), ("Recycling Near You (Planet Ark)", ("Search e-waste options near you: "
            "https://recyclingnearyou.com.au/"))],
    "nz": [("Your council's e-waste and battery drop-off", ("Search your council's website for e-waste or battery "
            "recycling.")), ("Retailer and brand take-back schemes", ("Many electronics stores take back batteries and "
            "small electronics."))],
    "sg": [("ALBA e-waste bins", "Free bins for batteries, bulbs and small electronics: https://alba-ewaste.sg/"),
           ("Retailer one-for-one take-back", ("Large retailers must take back an old appliance when delivering a new "
            "one (NEA's e-waste scheme)."))],
}
GENERIC_DISPOSAL = [("The brand's or retailer's take-back", "Ask the brand or the shop you bought it from."),
                    ("Your local council's e-waste or hazardous-waste collection", "Search your city's website.")]


def disposal(market: str | None, item: str | None = None, damaged: bool = False) -> dict:
    m = _market(market)
    lithium = bool(BATTERY.search(item or ""))
    prepare = [("Never put batteries or electronics in household waste or recycling bins: crushed lithium batteries "
               "start fires in garbage trucks and depots.")]
    if lithium:
        prepare.append("Cover the battery's terminals with tape before you drop it off.")
    if damaged:
        prepare.append("A swollen, leaking or burnt battery is not for a normal drop-off box: keep it in a metal tin "
                       "or on sand outdoors, away from anything that burns, and ask the collection point or your "
                       "council how to hand it over.")
    return {"market": m, "options": [{"where": w, "how": h} for w, h in DISPOSAL.get(m, GENERIC_DISPOSAL)],
            "prepare": prepare, "label": LABEL}


# ---------- purchase-pressure detector ----------

TACTICS = {
    "countdown_timer": ("Countdown timer", "False urgency", ("A clock makes you rush. Deals with a timer often "
                        "restart or come back; check the price again tomorrow before you decide.")),
    "low_stock": ("'Only N left'", "False urgency", ("Low-stock messages push you to buy now. They are often not "
                  "checked by anyone; a real product will usually be restocked.")),
    "social_proof": ("'N people are viewing / bought this'", "False urgency", ("Live-viewer and recent-buyer counts "
                     "are hard to verify; they say nothing about whether the product is safe.")),
    "preselected_extras": ("Pre-ticked extras", "Basket sneaking", ("Insurance, extended warranty, donations or "
                           "add-ons ticked for you. Untick anything you didn't choose and check the total again.")),
    "hidden_subscription": ("Hidden subscription", "Subscription trap", ("'Subscribe & save', a free trial or "
                            "auto-renew that charges you later. Choose one-time purchase, and note how to cancel.")),
    "drip_pricing": ("Fees added late", "Drip pricing", ("Delivery, handling or convenience fees that appear only at "
                     "checkout. Compare the final total, not the first price.")),
    "fake_discount": ("Inflated 'was' price", "False urgency / misleading price", ("A big struck-through price makes "
                      "the discount look larger. Compare with the brand's own store or another shop.")),
    "confirmshaming": ("Guilt-trip button", "Confirm shaming", ("A 'No, I don't want to save money' button. It's "
                       "just a no; you can click it.")),
    "forced_account": ("Forced sign-up", "Forced action", ("You must make an account, share contacts or install an "
                       "app to continue. You can usually check out as a guest or buy elsewhere.")),
    "nagging": ("Repeated pop-ups", "Nagging", "Pop-ups that keep asking. Close them; they don't change the deal."),
    "bait_and_switch": ("Different product than advertised", "Bait and switch", ("The product, variant or seller "
                        "changed from what was advertised. Check the model number and seller before you pay.")),
}


def pressure(found: list[dict], market: str | None = None) -> dict:
    """found: [{tactic, quote}] that Gemini read off the screenshot (quote = the text exactly as shown).
    -> {tactics: [{tactic, name, explanation, quote}], note}"""
    out = []
    for f in found or []:
        key = f.get("tactic")
        if key in TACTICS and not any(o["tactic"] == key for o in out):
            name, india, explain = TACTICS[key]
            out.append({"tactic": key, "name": name, "explanation": explain, "quote": (f.get("quote") or "")[:160],
                        **({"india_rule": f"'{india}' is a dark pattern under India's CCPA Guidelines for Prevention "
                                          "and Regulation of Dark Patterns, 2023"} if _market(market) == "in" else {})})
    return {"tactics": out,
            "note": "Pressure tactics are about the shop's selling, not the product's safety; take your time." if out
            else "No pressure tactics were visible on this screen.", "label": LABEL}


# ---------- reports to copy ----------

FILL = "[fill in]"


def _when(value) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value) if value else FILL


def _name(f: dict) -> str:
    """Brand, product and model, each once: a saved name often already holds the brand and model."""
    parts: list[str] = []
    for part in (f.get("product"), f.get("brand"), f.get("model")):
        if part and part.lower() not in " ".join(parts).lower():
            parts.insert(0, part) if part == f.get("brand") else parts.append(part)
    return " ".join(parts) or FILL


def incident_report(f: dict) -> dict:
    """A clear, safety-first report of what happened, for SafeShelf, the brand or the regulator.
    f: {product, brand, model, bought_from, bought_on, happened_on, what_happened, symptoms, injury, damage, photos,
    did_since, market}. Missing details become [fill in]; nothing is sent."""
    name = _name(f)
    lines = [f"Product: {name}", f"Model number: {f.get('model') or FILL} (printed on the label or the box)",
             f"Bought from: {f.get('bought_from') or FILL}, on {_when(f.get('bought_on'))}",
             f"When it happened: {_when(f.get('happened_on'))}",
             f"What happened: {f.get('what_happened') or FILL}",
             f"What I noticed: {', '.join(f.get('symptoms') or []) or FILL}",
             f"Injury: {f.get('injury') or 'none'}", f"Damage to property: {f.get('damage') or 'none'}",
             f"Photos: {f.get('photos') or 0} attached" if f.get("photos") else "Photos: [attach photos of the "
             "product, the damage and the label]",
             f"What I did since: {f.get('did_since') or 'Stopped using it and kept it, its box and the receipt.'}"]
    m = _market(f.get("market")).upper()
    regulator = complaints.REGULATORS.get(m)
    return {"title": f"Product safety incident: {name}", "body": "\n".join(lines),
            "missing": [line.split(":")[0] for line in lines if FILL in line],
            "send_to": [{"to": "SafeShelf", "how": "Send it with a photo through 'Report a problem' (POST "
                         "/v1/incidents); similar reports from other buyers are grouped into an early warning."},
                        {"to": "The brand or seller", "how": "Their support page or the order page."}]
            + ([{"to": regulator["name"], "how": regulator["how"][0]}] if regulator else []),
            "note": "Nothing is sent by SafeShelf: copy it, fill in the [brackets] and send it yourself.",
            "label": LABEL}


def support_request(f: dict) -> dict:
    """A warranty claim or support request to the brand or seller. f: {product, brand, model, order_ref, bought_from,
    bought_on, warranty_until, problem, request (repair | replacement | refund), stopped_using}."""
    name = _name(f)
    ask = {"repair": "repair it under warranty", "replacement": "replace it", "refund": "refund me"}.get(
        f.get("request") or "", "repair or replace it under warranty")
    status = " ".join(s for s in (
        "For safety I have stopped using it and kept it, its box and the receipt." if f.get("stopped_using", True)
        else "", f"It is under warranty until {_when(f.get('warranty_until'))}." if f.get("warranty_until") else "") if s)
    body = "\n".join([
        "Hello,", "",
        (f"I bought a {name} from {f.get('bought_from') or FILL} on {_when(f.get('bought_on'))} "
        f"(order number {f.get('order_ref') or FILL})."),
        f"Problem: {f.get('problem') or FILL}", *([status] if status else []),
        f"Please {ask}, and tell me how to send it to you or where to take it.", "",
        "Photos and the receipt are attached.", "", "Thank you,", "[your name and phone number]"])
    return {"subject": f"Warranty/support request: {name}" + (f" (order {f['order_ref']})" if f.get("order_ref") else ""),
            "body": body, "missing": [FILL] if FILL in body else [],
            "note": "Nothing is sent by SafeShelf: copy it, fill in the [brackets] and send it yourself.",
            "label": LABEL}
