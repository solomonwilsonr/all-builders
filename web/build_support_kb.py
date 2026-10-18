"""Builds web/site/support-kb.json, what the site's Help chat knows: the text of every site page, one entry per
section, plus the home-page FAQ and a few support answers the pages don't spell out (EXTRA).

Run after changing a site page: python3 web/build_support_kb.py (make support-kb; deploy-web runs it too).
The widget (site/support.js) searches this file in the browser when the API can't answer; the API's
/v1/support/ask (engine/support.py) sends all of it to Gemini, so every answer comes from the site itself.
"""
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent / "site"
OUT = SITE / "support-kb.json"
PAGES = {  # file -> the name a shopper knows the page by
    "index.html": "Home",
    "how.html": "How it works",
    "agents.html": "For agents",
    "results.html": "Results",
    "team.html": "Team",
    "get.html": "Android app",
    "shelf.html": "My Shelf",
}
SKIP = {"script", "style", "svg", "noscript", "nav", "template", "button"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BREAK = {"h1", "h2", "h3", "h4", "p", "li", "summary", "article", "tr", "div", "dt", "dd", "pre", "details"}

# Answers a visitor asks for that no single page section holds. Keep each one true to the site and the product.
EXTRA = [
    {"url": "index.html", "page": "Home", "title": "Signing in, guest checks and limits",
     "text": "You can use SafeShelf free on the web, with no card and nothing to install. As a guest you get 1 live "
             "check on this browser, plus six sample listings with known answers. Sign in with Google or with email "
             "and password for 5 live checks a day, Ask Eddy and Listen in 26 languages, and My Shelf. Sign in from "
             "the account button at the top right of any page. While we test, signed-in checks are not counted. The "
             "API rate-limits every caller; if you see a 'too many requests' message, wait a minute and try again. "
             "The demo also has a daily limit of AI checks; if it is reached, try again the next day."},
    {"url": "chat.html", "page": "Chat", "title": "Chat with Eddy: checking a product",
     "text": "The Chat page is where you check a product with Eddy, SafeShelf's assistant. Paste a product link or a "
             "screenshot of a listing, or pick one of the demo products, and ask: is it safe, is it real, is the "
             "seller authorised, is there a safer one? Eddy checks recalls, reviews and safety registries and shows "
             "its sources. You can scan a label with the camera button, ask out loud with the mic and hear the "
             "answer read aloud, in English, Hindi and 24 more languages. Signing in is needed to ask about your own "
             "listings. Talk mode is a live voice conversation: point the camera at a label and ask 'Is this safe?'. "
             "The Tools drawer is for judges and developers: it switches the API, runs other agents (Investigate, "
             "Safer alternative, Report draft, Official sites) and shows the investigation trace."},
    {"url": "index.html#faq", "page": "Home", "title": "Reading a verdict: the colours",
     "text": "Every check ends in a colour set by code, not by the AI model. Red means a real concern, such as an "
             "official recall of this exact model. Amber means take care: for example hazard reports under review, "
             "a copied listing, an unauthorised seller, or the same model recalled abroad. Green means nothing was "
             "found in the records checked. Grey means 'Not enough evidence yet': SafeShelf could not match the "
             "exact model or the evidence is thin, so it makes no safety claim. Green is never a guarantee: no "
             "matching recall is not proof of safety or authenticity. Every line names its source; open it to check."},
    {"url": "how.html#where", "page": "How it works", "title": "Where SafeShelf works: shops, countries, languages",
     "text": "SafeShelf is built for shoppers in India, Japan, Australia, Singapore and the rest of Asia-Pacific. It "
             "reads listings on Amazon India (.in), Amazon Japan (.co.jp), Amazon Australia (.com.au), Amazon "
             "Singapore (.sg), Amazon US (.com) and Flipkart. It checks official recalls and notices from 10 "
             "regulators: CPSC (US), ACCC (Australia), KATS (South Korea), CAA (Japan), CCPA and BIS (India), BSMI "
             "(Taiwan), CPSO (Singapore), ASEAN product alerts and the OECD. Eddy answers in 26 languages, including "
             "Hindi, Bengali, Marathi, Telugu, Tamil, Gujarati, Urdu, Kannada, Japanese, Korean, Chinese, "
             "Indonesian, Malay, Thai, Vietnamese and Filipino."},
    {"url": "team.html", "page": "Team", "title": "Getting help, reporting a problem, contact",
     "text": "SafeShelf is built by Team Hashes (Solomon and Seshu) for the AI Builder Cup 2026. To report a bug or a "
             "wrong answer, or to ask something this chat cannot answer, open an issue on the project's GitHub "
             "repository: https://github.com/solomonwilsonr/all-builders. Judges can use the judges' page "
             "(../index.html) for the six sample listings, the live lab and the bench results."},
    {"url": "agents.html", "page": "For agents", "title": "API keys and API docs",
     "text": "Agents connect to the MCP server at https://safeshelf-api-368488022657.asia-south1.run.app/mcp and send "
             "their key in the x-api-key header. The full API reference, with every request field and response "
             "shape, is the API docs page (api.html). The live investigation streams its steps "
             "as server-sent events from POST /v1/agent/sessions/stream. Every tool is read-only."},
]


class Sections(HTMLParser):
    """Splits <main> into its top-level <section>s: heading, anchor id and visible text. Skips aria-hidden copies
    (the logo marquee repeats itself) and the in-page jump menus."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.hidden_at: int | None = None  # stack depth where a skipped or aria-hidden element began
        self.in_main = False
        self.section_at: int | None = None
        self.sections: list[dict] = []
        self.faq: list[tuple[str, str]] = []
        self.heading_at: int | None = None  # stack depth of the section's first h1/h2, while inside it

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.in_main = True
        if tag == "button" and a.get("data-a") and "|" in a["data-a"]:
            question, answer = a["data-a"].split("|", 1)
            self.faq.append((question, answer))
        if tag in VOID:
            return
        self.stack.append(tag)
        depth = len(self.stack)
        if self.hidden_at is None and (tag in SKIP or a.get("aria-hidden") == "true"):
            self.hidden_at = depth
        if self.in_main and tag == "section" and self.section_at is None:
            self.section_at = depth
            self.sections.append({"id": a.get("id") or "", "title": "", "parts": []})
        elif self.section_at is not None and tag in BREAK:
            self.sections[-1]["parts"].append("\n")
        if tag in {"h1", "h2"} and self.section_at is not None and not self.sections[-1]["title"]:
            self.heading_at = depth

    def handle_endtag(self, tag):
        if tag in VOID or tag not in self.stack:
            return
        while self.stack:  # close anything left open inside it (an unclosed <p> or <li>)
            depth = len(self.stack)
            if self.hidden_at is not None and depth <= self.hidden_at:
                self.hidden_at = None
            if self.section_at is not None and depth <= self.section_at:
                self.section_at = None
            if self.heading_at is not None and depth <= self.heading_at:
                self.heading_at = None
            if self.stack.pop() == tag:
                break
        if tag == "main":
            self.in_main = False

    def handle_data(self, data):
        text = data.strip()
        if not text or self.section_at is None or self.hidden_at is not None:
            return
        section = self.sections[-1]
        if self.heading_at is not None:
            section["title"] += (" " if section["title"] else "") + text
        section["parts"].append(text + " ")


def tidy(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n[ \n]*", "\n", text)
    return text.strip()


def strip_tags(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def build() -> dict:
    chunks: list[dict] = []
    for name, page in PAGES.items():
        parser = Sections()
        parser.feed((SITE / name).read_text())
        for n, section in enumerate(parser.sections):
            text = tidy("".join(section["parts"]))
            if len(text) < 60:
                continue
            anchor = f"#{section['id']}" if section["id"] else ""
            title = tidy(section["title"]) or page
            chunks.append({"url": f"{name}{anchor}", "page": page, "title": title, "text": text,
                           "_order": n})
        for question, answer in parser.faq:
            chunks.append({"url": f"{name}#faq", "page": page, "title": question, "text": strip_tags(answer)})
    chunks += EXTRA
    for n, chunk in enumerate(chunks, 1):
        chunk.pop("_order", None)
        chunk["id"] = f"S{n}"
    return {"about": "What the SafeShelf site's Help chat knows. Made by web/build_support_kb.py; do not edit.",
            "chunks": [{k: c[k] for k in ("id", "page", "title", "url", "text")} for c in chunks]}


if __name__ == "__main__":
    kb = build()
    OUT.write_text(json.dumps(kb, ensure_ascii=False, indent=1) + "\n")
    size = sum(len(c["text"]) for c in kb["chunks"])
    print(f"{OUT.relative_to(SITE.parent.parent)}: {len(kb['chunks'])} entries, {size:,} characters")
