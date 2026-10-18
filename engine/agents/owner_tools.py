"""Owner-help tools for Shelf Chat: before buying, while using it, and when something goes wrong.

Thin wrappers over engine/assist.py (code rules: compatibility, power setups, symptoms, suitability, repair or
replace, disposal, pressure tactics, report and support-request drafts) and engine/household.py (the household's
products, warranty and return dates, service requests, family sharing). Gemini fills in the arguments from what the
shopper said; the answers come from code. Each call is one step of the run; its result also goes to the screen
(the answer's "assist" field) so drafts can be copied.

The household tools act for the signed-in owner only: the owner comes from the request's X-Owner-Ref header (set by
the API handler, never by the model or the message).
"""
import asyncio
import logging
import time

from google.adk.tools import ToolContext

from engine import assist, household, passport, safety
from engine.agents import runtime

log = logging.getLogger(__name__)


def _done(tool_context: ToolContext, name: str, body: dict, summary: str, started: float) -> dict:
    runtime.current().results[name] = body
    runtime.current().results.setdefault("assist", {})[name] = body
    runtime.step(tool_context.agent_name, name, summary, time.monotonic() - started, None, body)
    return body


def _market(tool_context: ToolContext, market: str) -> str:
    return market or tool_context.state.get("market") or "in"  # names and codes: engine/assist.py _market


# ---------- before buying ----------

async def check_compatibility(tool_context: ToolContext, charger_connector: str = "", charger_watts: float = 0,
                              charger_volts: float = 0, charger_amps: float = 0,
                              charger_protocols: list[str] | None = None, device_connector: str = "",
                              device_watts: float = 0, device_volts: float = 0,
                              device_protocols: list[str] | None = None) -> dict:
    """Will this charger work with this device (laptop, phone)? Compares the plug at the device end, the voltage,
    the power (watts) and fast-charge standards (USB PD, PPS, Quick Charge...). Pass only values the shopper or the
    product record gave; leave the rest empty and the answer says what to read on the labels."""
    started = time.monotonic()
    body = assist.compatibility(
        {"connector": charger_connector, "watts": charger_watts, "volts": charger_volts, "amps": charger_amps,
         "protocols": charger_protocols or []},
        {"connector": device_connector, "watts": device_watts, "volts": device_volts,
         "protocols": device_protocols or []})
    return _done(tool_context, "check_compatibility", body, f"Compatibility: {body['verdict']}", started)


async def check_power_setup(tool_context: ToolContext, appliances: list[dict], chain: list[dict],
                            market: str = "") -> dict:
    """Is this plug setup safe? appliances: [{name, watts, amps, volts}] all plugged into the chain. chain: the parts
    between them and the wall, in order: [{kind: extension | adapter | cable, name, rated_watts, rated_amps,
    rated_volts}]. Finds overloads, daisy-chained boards, heaters on boards and voltage mismatches. market: in, jp,
    au, nz, sg..."""
    started = time.monotonic()
    body = assist.setup(appliances, chain, _market(tool_context, market))
    return _done(tool_context, "check_power_setup", body, f"Power setup: {body['verdict']}", started)


async def check_suitability(product_id: str, tool_context: ToolContext, children_under_3: bool = False,
                            children: bool = False, pets: bool = False, allergies: list[str] | None = None,
                            accessibility: list[str] | None = None, product_description: str = "") -> dict:
    """Does this product suit this household? Weighs what the shopper said (young children, pets, allergies,
    accessibility needs such as low vision or limited grip) against the product's hazard reports and listing text.
    product_description: what the shopper said about the product (materials, batteries, parts), in their words."""
    started = time.monotonic()
    hazards, text, category = [], "", None
    if product_id and product_id.lower() not in ("unmatched", "unknown"):
        try:
            record = await asyncio.to_thread(safety.safety, product_id)
            hazards = [f.get("hazard_type") for f in record.get("ai_findings") or [] if f.get("hazard_type")]
            runtime.saw(record)
            product = await asyncio.to_thread(passport.product, product_id)
            category = product.get("category")
            text = " ".join(str(v) for v in (product.get("brand"), product.get("model"), product.get("attributes"),
                                             *(row.get("title") for row in product.get("listings") or [])) if v)
        except Exception as error:  # noqa: BLE001  unknown product: the shopper's own details still get an answer
            log.info("suitability record for %s unavailable: %s", product_id, type(error).__name__)
    link = runtime.current().results.get("checkLink") or {}
    text = " ".join(t for t in (text, link.get("title") or "", product_description) if t)
    body = assist.suitability({"children_under_3": children_under_3, "children": children, "pets": pets,
                               "allergies": allergies or [], "accessibility": accessibility or []},
                              hazards, text, category)
    return _done(tool_context, "check_suitability", body, f"Suitability: {len(body['concerns'])} concerns", started)


async def explain_pressure_tactics(tactics: list[str], tool_context: ToolContext, quotes: list[str] | None = None,
                                   market: str = "") -> dict:
    """Explains selling-pressure tactics the shopper describes or pasted (countdown_timer, low_stock, social_proof,
    preselected_extras, hidden_subscription, drip_pricing, fake_discount, confirmshaming, forced_account, nagging,
    bait_and_switch), with what to do about each. quotes: the shop's words, in the same order."""
    started = time.monotonic()
    quotes = quotes or []
    body = assist.pressure([{"tactic": t, "quote": quotes[i] if i < len(quotes) else ""}
                            for i, t in enumerate(tactics or [])], _market(tool_context, market))
    return _done(tool_context, "explain_pressure_tactics", body, f"{len(body['tactics'])} pressure tactics", started)


# ---------- something is wrong ----------

async def guide_symptoms(symptoms: list[str], tool_context: ToolContext, product_kind: str = "",
                         market: str = "") -> dict:
    """What to do now when a product seems wrong. symptoms, any of: smoke_or_flame, sparks, hissing_or_popping,
    burning_smell, swelling, leaking, very_hot, melted_or_scorched, shock_or_tingle, damaged_cable, cracked_case,
    chemical_smell, buzzing, warm, not_working, error_code. product_kind: charger, power bank, laptop, heater...
    Returns the urgency and safe steps (never testing the product)."""
    started = time.monotonic()
    body = assist.symptoms(symptoms, product_kind, _market(tool_context, market))
    return _done(tool_context, "guide_symptoms", body, f"Symptoms: {body['urgency']}", started)


async def _item(tool_context: ToolContext, item_id: str) -> dict:
    if not item_id:
        return {}
    try:
        rows = await asyncio.to_thread(household.items, tool_context.state.get("tenant") or "public",
                                       tool_context.state.get("owner"))
    except Exception:  # noqa: BLE001  no household list: the shopper's own details still work
        return {}
    return next((r for r in rows["items"] if r["item_id"] == item_id), {})


async def repair_or_replace(tool_context: ToolContext, product_kind: str = "", household_item_id: str = "",
                            recalled: bool = False, safety_symptom: bool = False, within_return: bool = False,
                            under_warranty: bool = False, repair_quote: float = 0,
                            replacement_price: float = 0) -> dict:
    """Repair, replace, return or claim the warranty? With household_item_id the return and warranty dates come from
    the household list. safety_symptom: it overheated, swelled, sparked, leaked or gave a shock."""
    started = time.monotonic()
    item = await _item(tool_context, household_item_id)
    left = item.get("status") or {}
    body = assist.repair_or_replace({
        "kind": product_kind or item.get("category") or item.get("name") or "", "recalled": recalled,
        "safety_symptom": safety_symptom,
        "within_return": within_return or (left.get("return", {}).get("days_left", -1) >= 0),
        "under_warranty": under_warranty or (left.get("warranty", {}).get("days_left", -1) >= 0),
        "repair_quote": repair_quote, "replacement_price": replacement_price or item.get("price")})
    return _done(tool_context, "repair_or_replace", body, f"Repair or replace: {body['advice']}", started)


async def find_disposal(tool_context: ToolContext, item: str = "", damaged: bool = False, market: str = "") -> dict:
    """Where to take an old battery, charger or appliance (official battery and e-waste collection for the market),
    and how to prepare it. damaged: swollen, leaking or burnt."""
    started = time.monotonic()
    body = assist.disposal(_market(tool_context, market), item, damaged)
    return _done(tool_context, "find_disposal", body, f"Disposal options: {len(body['options'])}", started)


async def write_incident_report(tool_context: ToolContext, product: str = "", brand: str = "", model: str = "",
                                bought_from: str = "", bought_on: str = "", happened_on: str = "",
                                what_happened: str = "", symptoms: list[str] | None = None, injury: str = "",
                                damage: str = "", photos: int = 0, did_since: str = "", market: str = "") -> dict:
    """Turns what happened into a clear safety report (model, purchase date, symptoms, photos) for SafeShelf, the
    brand or the regulator. Missing details are left as [fill in]. Nothing is sent."""
    started = time.monotonic()
    body = assist.incident_report({
        "product": product, "brand": brand, "model": model, "bought_from": bought_from, "bought_on": bought_on,
        "happened_on": happened_on, "what_happened": what_happened, "symptoms": symptoms or [], "injury": injury,
        "damage": damage, "photos": photos, "did_since": did_since, "market": _market(tool_context, market)})
    return _done(tool_context, "write_incident_report", body, f"Incident report: {len(body['missing'])} to fill in",
                 started)


async def write_support_request(tool_context: ToolContext, problem: str, household_item_id: str = "",
                                product: str = "", brand: str = "", model: str = "", bought_from: str = "",
                                bought_on: str = "", order_ref: str = "", warranty_until: str = "",
                                request: str = "") -> dict:
    """A warranty claim or support request to the brand or seller, to copy and send. With household_item_id the
    order number, dates and shop come from the household list. request: repair, replacement or refund."""
    started = time.monotonic()
    item = await _item(tool_context, household_item_id)
    body = assist.support_request({
        "product": product or item.get("name"), "brand": brand or item.get("brand"), "model": model or item.get("model"),
        "bought_from": bought_from or item.get("bought_from"), "bought_on": bought_on or item.get("bought_on"),
        "order_ref": order_ref or item.get("order_ref"),
        "warranty_until": warranty_until or item.get("warranty_until"), "problem": problem, "request": request})
    return _done(tool_context, "write_support_request", body, "Support request drafted", started)


# ---------- the household's products ----------

async def _household(tool_context: ToolContext, name: str, fn, *args) -> dict:
    started = time.monotonic()
    try:
        body = await asyncio.to_thread(fn, tool_context.state.get("tenant") or "public",
                                       tool_context.state.get("owner"), *args)
    except ValueError as problem:
        body = {"error": str(problem)}
    except KeyError:
        body = {"error": "That isn't in your household list (or it belongs to someone who shared theirs with you)."}
    except Exception as error:  # noqa: BLE001  the household list is down: the chat says so
        log.warning("household %s failed: %s", name, type(error).__name__)
        body = {"error": "The household list can't be reached right now (a SafeShelf server problem, not the "
                         "shopper's account): ask them to try again later."}
    summary = body["error"] if "error" in body else {
        "add_household_product": "Saved to the household list", "find_household_products":
        f"{len(body.get('items', []))} household products, {len(body.get('due_soon', []))} dates due soon"}.get(
        name, name.replace("_", " ").capitalize())
    return _done(tool_context, name, body, summary, started)


async def add_household_product(name: str, tool_context: ToolContext, brand: str = "", model: str = "",
                                category: str = "", product_id: str = "", bought_from: str = "", order_ref: str = "",
                                bought_on: str = "", price: float = 0, currency: str = "", return_days: int = 0,
                                warranty_months: int = 0, return_by: str = "", warranty_until: str = "",
                                notes: str = "") -> dict:
    """Saves a product the household owns (from the shopper's words or a receipt): its shop, order number, purchase
    date (YYYY-MM-DD) and the return period / warranty, so SafeShelf can track the deadlines. Only when the shopper
    asks to save it."""
    item = {"name": name, "brand": brand, "model": model, "category": category, "product_id": product_id,
            "bought_from": bought_from, "order_ref": order_ref, "bought_on": bought_on, "price": price or None,
            "currency": currency, "return_days": return_days, "warranty_months": warranty_months,
            "return_by": return_by, "warranty_until": warranty_until, "notes": notes}
    return await _household(tool_context, "add_household_product", household.add,
                            {k: v for k, v in item.items() if v not in ("", 0, None)})


async def find_household_products(tool_context: ToolContext, search: str = "") -> dict:
    """The household's products (also those shared by family), with return and warranty days left and what is due
    soon. search: a name, brand, model or kind (charger, battery...)."""
    return await _household(tool_context, "find_household_products", household.items, search or None)


async def log_service_request(item_id: str, kind: str, tool_context: ToolContext, status: str = "open",
                              ref: str = "", note: str = "") -> dict:
    """Records a warranty claim, repair, return or support request on a household product. kind: warranty_claim,
    repair, return, support_request; ref: the ticket or claim number."""
    return await _household(tool_context, "log_service_request", household.log_service, item_id,
                            {"kind": kind, "status": status, "ref": ref, "note": note})


async def remove_household_product(item_id: str, tool_context: ToolContext) -> dict:
    """Removes a product from the household list, only when the shopper asks."""
    return await _household(tool_context, "remove_household_product", household.delete, item_id)


async def share_household(tool_context: ToolContext) -> dict:
    """Creates a one-time invite code so a family member can see this household's products (read-only). Only when
    the shopper asks to share."""
    return await _household(tool_context, "share_household", household.invite)


async def join_household(invite_code: str, tool_context: ToolContext) -> dict:
    """Joins a family member's household with the invite code (HS-...) they shared."""
    return await _household(tool_context, "join_household", household.accept, invite_code)


async def household_sharing(tool_context: ToolContext) -> dict:
    """Who this household is shared with, and which households are shared with this shopper."""
    return await _household(tool_context, "household_sharing", household.members)


async def stop_sharing(invite_code: str, tool_context: ToolContext) -> dict:
    """Ends a household sharing (the owner revokes it, or the member leaves)."""
    return await _household(tool_context, "stop_sharing", household.revoke, invite_code)


OWNER_TOOLS = [check_compatibility, check_power_setup, check_suitability, explain_pressure_tactics, guide_symptoms,
               repair_or_replace, find_disposal, write_incident_report, write_support_request, add_household_product,
               find_household_products, log_service_request, remove_household_product, share_household,
               join_household, household_sharing, stop_sharing]
