"""Shelf Chat (the Concierge) and the Safer Alternative Finder: ADK agents that read stored evidence through tools.

The Concierge decides which evidence to read (safety, copies, marks, history, exact quotes) and, for "show me a
safer one", hands over to the Safer Alternative Finder (an AgentTool). Answers may cite only evidence IDs some tool
returned in this request. If every model fails, the one-call chat (engine/chat.py) answers instead.
"""
import asyncio
import json
import logging

from fastapi import HTTPException
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

from engine import chat, chat_core, gemini, safety
from engine.agents import cache, guard, links, pipeline, runtime, screenshot, tools

log = logging.getLogger(__name__)

HOW_TO_WORK = """

How you work:
- The message names the product_id and already includes its stored safety record (recall status, hazard reports
  with evidence IDs, safety marks). Answer from it directly when it answers the question: no tool call needed.
  Call tools only for what it does not contain, usually one: get_safety (only if the record is missing),
  get_relationships (copies, rebrands, look-alikes), get_certifications (safety marks against registries),
  get_history (what changed and linked recalls), get_product (brand, model, specs). Call get_evidence (the exact
  quote behind an evidence ID) only when the shopper asks for the reviews' own words or the photos. Call the tools
  you need together in one turn, not one after another.
- For "is there a safer one / what should I buy instead / which genuine twin is cheapest", call find_safer_alternative.
- For "draft a refund request" or "what do I tell the seller", write a short message the shopper can copy and send
  themselves, citing only the evidence; you never send anything.
- If product_id is "unmatched", there is no stored evidence: do not call tools, answer from the check result.
- If the message contains a product link (http...), call check_link with it FIRST and answer about THAT product,
  not the product_id in the message. Say what it is (name, price), the two colours (safety, is it real) and the
  main reasons, citing evidence IDs. If the link can't be read, say so."""

ALTERNATIVE_INSTRUCTION = """You are SafeShelf's Safer Alternative Finder. Given a product_id, call get_alternatives,
and when it helps, get_relationships, to recommend at most two products to buy instead.
Rules: only products get_alternatives returned; say why each is safer in SafeShelf's terms (no official recall, N hazard
reports in M reviews read, authorised seller) and its price. A genuine twin means only an exact model or a verified
rebrand; never call a look-alike the same product. No reviews read is not proof of safety: say so. Never promise
safety. Cite the evidence IDs the tools returned in [brackets]. If there is no alternative, say so plainly.
Reply in at most 4 short sentences."""


SEND_MORE = ("suggest sending a screenshot of the product page (or opening it with the SafeShelf extension on a "
             "computer), which SafeShelf reads without visiting the shop")
NOTES = {
    "partial": "The shop showed SafeShelf's server only part of this page (no price or reviews), so price and reviews "
               f"were not checked. Say so, and {SEND_MORE}.",
    "none": "The page could not be opened, so only the link itself was checked. Say so, ask for the product's brand "
            f"and model number, and {SEND_MORE}.",
    "message": "The page could not be opened (shops often block servers), so SafeShelf checked the product by the "
               "name in the shopper's message: recalls and safety marks were searched by that name, but price, seller "
               f"and reviews were not checked. Say so, and {SEND_MORE}.",
    "link": "The page could not be opened (shops often block servers), so SafeShelf checked the product by the name "
            "in the link itself: recalls and safety marks were searched by that name, but price, seller and reviews "
            f"were not checked. Say so, and {SEND_MORE}.",
    "screenshot": "SafeShelf read this from the shopper's image, not from the shop's page: only what was visible was "
                  "checked (reviews_on_page says how many reviews). Say so in a few words.",
}


async def investigate_listing(listing: dict, page: str, language: str, page_evidence: dict | None = None,
                              note: str | None = None) -> dict:
    """The full investigation of a listing the chat got from a link or an image, as the chat's check result."""
    found = await pipeline.investigate({"listing": listing, "product_id": "unmatched", "language": language,
                                        **({"page_evidence": page_evidence} if page_evidence else {})})
    link = {"url": listing.get("url"), "title": listing.get("title"), "brand": listing.get("brand"),
            "price": listing.get("price"), "currency": listing.get("currency"), "page_read": page,
            "name_from": note if note in ("message", "link") else None,  # the page unread: where the name came from
            "reviews_on_page": len(listing.get("reviews", [])), "product_id": found.get("product_id"),
            # what the page's buyers said, lowest stars first, so follow-up questions can be answered from it
            "reviews": [{"rating": r.get("rating"), "title": r.get("title"), "text": (r.get("text") or "")[:400]}
                        for r in sorted(listing.get("reviews", []), key=lambda r: r.get("rating") or 5)[:10]],
            "verdict": found.get("verdict"), "investigation_id": found.get("investigation_id")}
    runtime.current().results["checkLink"] = link
    note = NOTES.get(note or page)
    return {**link, "summary": found["messages"][0]["text"], "label": found.get("label"), **({"note": note} if note else {})}


async def check_link(url: str, tool_context: ToolContext) -> dict:
    """Checks the product page behind a link the shopper pasted: reads the page (title, price, seller, reviews), then
    runs SafeShelf's full investigation of it: is it safe (recalls, hazard reports), is it real (price, seller, website,
    hidden AI instructions). Returns the product, the colours set by code and the reasons with evidence IDs."""
    import time
    started = time.monotonic()
    listing = cache.get("link:" + links.clean(url))
    try:
        if listing is None:
            listing = await asyncio.to_thread(links.read, url)
            cache.put("link:" + links.clean(url), listing, 600)
    except links.BlockedLink as problem:
        return {"error": f"SafeShelf can't open that link: {problem}"}
    page = listing.pop("read", "none")  # full / partial (the shop showed the server only part of it) / none
    named_by = None
    if page == "none":  # shops often block servers: the name shared with the link, else the name in the link itself
        pasted = tool_context.state.get("pasted") or ""
        for named_by, name in (("message", links.shared_name(pasted)),
                               ("link", links.name_from_url(links.first_url(pasted) or url))):
            if name:
                listing = {**listing, "title": name}
                break
        else:
            named_by = None
    runtime.step(tool_context.agent_name, "read_link",
                 (f"Read the page ({page}): {listing.get('title', '')[:80]} · price {listing.get('price')} · "
                  f"{len(listing.get('reviews', []))} reviews") if page != "none" else
                 f"The page could not be read; checking by the name in the {named_by}: {listing['title'][:80]}"
                 if named_by else "The page could not be read; checking by URL", time.monotonic() - started)
    return await investigate_listing(listing, page, tool_context.state.get("language", "en"), note=named_by)


async def check_image(image: str, language: str) -> dict:
    """Reads the shopper's screenshot or photo, then investigates the listing it shows. Raises BadImage."""
    import time
    data, mime_type = screenshot.decode(image)
    started = time.monotonic()

    def read():
        calls = gemini.track()
        return screenshot.read(data, mime_type), calls
    try:
        seen, calls = await asyncio.to_thread(read)
    except Exception as error:  # noqa: BLE001  every model failed: the chat says it could not read the image
        log.warning("screenshot not read: %s", type(error).__name__)
        runtime.step("shelf_chat", "read_image", "The image could not be read", time.monotonic() - started)
        return {"error": "SafeShelf could not read the image. Ask the shopper to send it again, or the product's "
                         "brand and model number."}
    listing = screenshot.to_listing(seen)
    runtime.step("shelf_chat", "read_image", screenshot.describe(seen, listing), time.monotonic() - started, calls)
    if not listing:
        return {"error": "The image shows no product SafeShelf can identify. Ask for a screenshot of the product "
                         "page, or a photo of the product's label."}
    observed = screenshot.label_observations(seen)
    return await investigate_listing(listing, "screenshot", language,
                                     {"source": "screenshot", "observations": observed} if observed else None)


def alternative_finder(model_name: str) -> LlmAgent:
    return LlmAgent(
        name="safer_alternative_finder",
        description="Finds safer products to buy instead of this one, with the reason each is safer.",
        model=runtime.model(model_name), instruction=ALTERNATIVE_INSTRUCTION,
        tools=[tools.get_alternatives, tools.get_relationships], generate_content_config=runtime.config(),
        **runtime.callbacks(model_name))


def find_safer_alternative_tool(model_name: str) -> AgentTool:
    tool = AgentTool(agent=alternative_finder(model_name))
    tool.name = "find_safer_alternative"
    return tool


def concierge(model_name: str) -> LlmAgent:
    return LlmAgent(
        name="shelf_chat",
        description="Answers a shopper's questions about one product, only from SafeShelf's stored evidence.",
        model=runtime.model(model_name), instruction=chat_core.INSTRUCTION + HOW_TO_WORK,
        tools=[*tools.EVIDENCE_TOOLS, find_safer_alternative_tool(model_name), check_link],
        generate_content_config=runtime.config(),
        **runtime.callbacks(model_name))


def _answer(product_id, language, session_id, text: str, seen: set[str], mode: str = "chat") -> dict:
    if guard.overclaims(text):  # a promise of safety or a legal finding is never passed on
        text = ("I can't promise that. Here is what SafeShelf found: open the card's evidence, and treat reports "
                "under review as AI findings, not a regulator's decision.")
    out = chat_core.result(product_id, language, session_id, text, seen)
    out["mode"] = mode
    out["steps"] = runtime.current().steps
    return out


async def chat_session(body: dict) -> dict:
    message = (body.get("message") or "").strip()
    image = body.get("image")
    if not message and not image:
        raise HTTPException(status_code=422, detail="Give a message")
    message = message or "Is this safe? Is it real?"
    product_id = body.get("product_id")
    language = chat_core.language(body.get("language"), message)  # a question typed in Tamil gets a Tamil answer
    session_id = body.get("session_id") or runtime.new_id("SS-A-")
    context = body.get("context")
    if image:  # a screenshot or photo (a phone has no extension): read it, then check that listing
        try:
            context = await check_image(image, language)
        except screenshot.BadImage as problem:
            raise HTTPException(status_code=422, detail=f"image: {problem}") from None
        product_id = context.get("product_id") or "unmatched"
    unmatched = chat_core.is_unmatched(product_id)
    url = None if image else links.first_url(message)
    stored = "{}"
    if not unmatched and not url:  # the safety record up front: most questions then need one model turn, not three
        record = await tools.call("shelf_chat", "getSafety", safety.safety, product_id)
        stored = json.dumps({"safety": record}, ensure_ascii=False, default=str) if "error" not in record else \
            "(not included: read it with your tools)"
    prompt, seen = chat_core.prepare(product_id, message[:1000], language, stored, context, body.get("history"))
    if image:
        prompt = "[The shopper sent an image; SafeShelf read it and checked that listing (the check result below).]\n" \
            + prompt
    if url:  # a pasted link is about that product, whatever product the screen had selected
        prompt = f"[The shopper pasted a product link: {url} - call check_link with it first.]\n" + prompt
    try:
        text, _ = await runtime.run(concierge, prompt, {"language": language, "pasted": message[:1000]},
                                    timeout_s=120 if url else 40)
    except Exception as error:  # noqa: BLE001  every agent model failed: the one-call chat still answers
        log.warning("Concierge failed (%s); one-call chat answers", type(error).__name__)
        fallback = await asyncio.to_thread(chat.answer, {**body, "mode": "chat", "language": language,
                                                         "message": message, "product_id": product_id,
                                                         "context": context})
        fallback["steps"] = runtime.current().steps + [{"n": len(runtime.current().steps) + 1, "agent": "shelf_chat",
                                                        "tool": "fallback", "summary": "Answered in one model call"}]
        return fallback
    link = runtime.current().results.get("checkLink")
    out = _answer(link["product_id"] if link else product_id, language, session_id, text, seen | runtime.current().seen)
    if link:
        out["link"] = link  # screens switch the chat to this product for follow-up questions
    return out


async def alternatives_session(body: dict) -> dict:
    product_id = body.get("product_id")
    if chat_core.is_unmatched(product_id):
        raise HTTPException(status_code=422, detail="Give the product_id of a product SafeShelf knows")
    language = chat_core.language(body.get("language"))
    prompt = (f"[Product: {product_id}] [Reply language: {chat_core.LANGUAGES[language]}]\n"
              f"Find safer products to buy instead of {product_id}.")
    try:
        text, _ = await runtime.run(alternative_finder, prompt, timeout_s=40)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="The AI is busy right now. Please try again in a minute.") from None
    out = _answer(product_id, language, body.get("session_id") or runtime.new_id("SS-A-"), text,
                  runtime.current().seen, mode="alternatives")
    out["alternatives"] = (runtime.current().results.get("getAlternatives") or {}).get("alternatives", [])
    return out
