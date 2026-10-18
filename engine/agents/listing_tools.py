"""The extension's listing checks, as chat tools: the chat can do what the in-page widget does.

Each one reads the shop page the chat is about (the link pasted this turn or earlier in the conversation, read
once and cached for 10 minutes by check_link) and runs the same engine code as /v1/listings/*:
  check_reviews          "Is it any good?"          POST /v1/listings/review-verdict
  check_claims           "Is it possible?"           POST /v1/listings/claims-check
  compare_price          "Is the price right?"       POST /v1/listings/price-benchmark
  check_listing_age      "How old is this listing?"  POST /v1/listings/listing-age
  check_official_seller  "Is it the brand's store?"  POST /v1/listings/official-seller
  identify_listing       "How was it identified?"    POST /v1/products/identify
  find_copies            "Find copies with AI"       POST /v1/products/duplicates
"""
import asyncio

from google.adk.tools import ToolContext

from engine import claims_check, gemini, identity, listing_age, official_seller, price_benchmark, review_verdict
from engine.agents import cache, links, runtime, tools

NO_PAGE = ("This check reads a shop's product page, and the chat has no link yet. Ask the shopper to paste the "
           "product link or send a screenshot of the product page.")


async def _listing(url: str, tool_context: ToolContext) -> dict:
    """The listing behind url, else the link this chat is about: from check_link's cache, read again if it expired."""
    current = runtime.current().results.get("checkLink") or {}
    url = url or current.get("url") or tool_context.state.get("link_url") or ""
    if not url.startswith("http"):
        return {"error": NO_PAGE}
    key = "link:" + links.clean(url)
    listing = cache.get(key)
    if listing is None:
        try:
            listing = await asyncio.to_thread(links.read, url)
        except links.BlockedLink as problem:
            return {"error": f"SafeShelf can't open that link: {problem}"}
        cache.put(key, listing, 600)
    listing = {k: v for k, v in listing.items() if k not in ("read", "via")}
    if not listing.get("title"):  # the shop hid the page from the server: the name the chat already has
        title = current.get("title") or tool_context.state.get("link_title")
        if title:
            listing["title"] = title
    return {**listing, "url": listing.get("url") or url}


async def _run(tool_context: ToolContext, operation_id: str, url: str, fn, *extra) -> dict:
    listing = await _listing(url, tool_context)
    if "error" in listing:
        return listing
    return await tools.call(tool_context.agent_name, operation_id, fn, listing, *extra)


async def check_reviews(tool_context: ToolContext, url: str = "") -> dict:
    """Is it any good? Reads the page's reviews: what buyers praise and complain about, how many were read, and
    whether the reviews look genuine. url: a product link; empty = the link this chat is about."""
    return await _run(tool_context, "listingReviewVerdict", url, review_verdict.review_verdict)


async def check_claims(tool_context: ToolContext, url: str = "") -> dict:
    """Is it possible? Checks the listing's technical claims (capacity, wattage, speed, battery life...) against
    what the technology can do and the real product's specs. url: empty = the link this chat is about."""
    return await _run(tool_context, "listingClaimsCheck", url, claims_check.check, gemini.grounded)


def _price(listing: dict) -> dict:
    references, kind = price_benchmark.references_for(listing, gemini.grounded)
    return price_benchmark.benchmark(listing, references, kind)


async def compare_price(tool_context: ToolContext, url: str = "") -> dict:
    """Is the price right? Compares the listing's price with the genuine product's usual price (a price far below
    it is a sign of a fake). url: empty = the link this chat is about."""
    return await _run(tool_context, "listingPriceBenchmark", url, _price)


async def check_listing_age(tool_context: ToolContext, url: str = "") -> dict:
    """How long the listing has been up (first available date, oldest review): a brand-new listing for a well-known
    product is a warning sign. url: empty = the link this chat is about."""
    return await _run(tool_context, "listingAge", url, listing_age.assess)


async def check_official_seller(tool_context: ToolContext, url: str = "") -> dict:
    """Is it sold by the brand's official store or an authorised seller, by SafeShelf's registry?
    url: empty = the link this chat is about."""
    return await _run(tool_context, "listingOfficialSeller", url, official_seller.assess)


async def identify_listing(tool_context: ToolContext, url: str = "") -> dict:
    """How SafeShelf identified the product on the page: brand, model, the stored product it matched and how sure
    the match is. url: empty = the link this chat is about."""
    return await _run(tool_context, "identifyProduct", url, identity.identify)


async def find_copies(product_id: str, tool_context: ToolContext) -> dict:
    """Searches for copies, rebrands and look-alikes of a stored product (the same hardware sold under other
    names), with AI. Slower than get_relationships, which only reads the ones already on file: use this when
    the shopper asks to find copies and get_relationships found none."""
    return await tools.call(tool_context.agent_name, "findDuplicates", identity.duplicates, product_id, False)


LISTING_TOOLS = [check_reviews, check_claims, compare_price, check_listing_age, check_official_seller,
                 identify_listing, find_copies]
