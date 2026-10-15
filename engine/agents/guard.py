"""Safety rules for every agent (SAFESHELF.md 12.4). Code checks these; no model output can override them."""
import re

from engine.chat_core import EVIDENCE_ID

# Never clicked, whatever the model proposes: buying, accounts, forms and anything that sends something.
BLOCKED_TEXT = re.compile(
    r"\b(buy|add to (cart|bag|basket|wish ?list)|cart|checkout|check out|pay|payment|place (your )?order|order now|"
    r"subscribe|sign ?in|log ?in|sign ?up|register|account|submit|send|delete|confirm|redeem|"
    r"one-?click|cash on delivery|emi)\b", re.IGNORECASE)
BLOCKED_HREF = re.compile(
    r"/(cart|checkout|buy|signin|sign-in|login|log-in|register|account|ap/signin|gp/cart|gp/buy|payment|"
    r"wishlist|orders?)(/|\?|$)|^(javascript|mailto|tel):", re.IGNORECASE)
BLOCKED_TAGS = {"input", "textarea", "select", "form", "option"}
BLOCKED_TYPES = {"submit", "password", "email", "tel", "file"}

# An answer must never promise safety or make a legal finding (12.3, 12.4).
OVERCLAIM = re.compile(
    r"\b(guaranteed|100 ?% safe|completely safe|totally safe|certified safe|verified safe|perfectly safe|"
    r"definitely safe|is a scam|is fraud(ulent)?|illegal)\b", re.IGNORECASE)


def blocked(element: dict) -> str | None:
    """Why this page element must not be clicked, or None when it is allowed (read-only browsing)."""
    tag = str(element.get("tag") or "").lower()
    if tag in BLOCKED_TAGS or str(element.get("type") or "").lower() in BLOCKED_TYPES:
        return "a form field: SafeShelf never fills in or submits forms"
    if BLOCKED_HREF.search(str(element.get("href") or "")):
        return "a link to buying or an account: SafeShelf never buys or signs in"
    words = " ".join(str(element.get(k) or "") for k in ("text", "aria", "title"))
    if BLOCKED_TEXT.search(words):
        return "a buy, account or submit control: SafeShelf never buys, signs in or sends anything"
    return None


def keep_cited(text: str, seen: set[str]) -> list[str]:
    """Evidence IDs in the answer that the agent really read; invented IDs are dropped."""
    return [e for e in dict.fromkeys(EVIDENCE_ID.findall(text or "")) if e in seen]


def overclaims(text: str) -> bool:
    return bool(OVERCLAIM.search(text or ""))
