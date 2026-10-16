"""Japan's Consumer Affairs Agency recall information site (recall.caa.go.jp), live.

Access verified 16 Oct 2026: plain HTTP; content under the Public Data License 1.0 (reuse with the source credited and
edits marked). The site search is the same form a browser sends (session cookie, then a POST with the keyword); each
matching notice's detail page is read for its fields, kept in the original Japanese: 型番 (model number), 対応開始日
(action start date), 対象の特定情報 (how to identify affected units, including lots and serials), and the reason.
"""
import html as html_lib
import json
import re

import httpx

from engine import locales
from engine.sources import normalizer, policy
from engine.sources.adapters import _http
from engine.sources.adapters._http import Base
from engine.sources.base import ERROR, SourceFailure, SourceQuery, SourceRecord, now, payload_hash

SITE = "https://www.recall.caa.go.jp"
MAX_DETAILS = 6
ROW = re.compile(r'<a href="/result/detail\.php\?rcl=(\d+)[^"]*"[^>]*>([^<]+)</a>.*?result_list_post_date">([^<]*)<'
                 r'.*?result_list_start_date">([^<]*)<', re.DOTALL)
QUILL = re.compile(r"contentsText = '(.*?)';\s*quill = new Quill\('#(\w+)'", re.DOTALL)
FIELD_ORDER = {"details1": "contact", "details2": "action", "details3": "identification", "details4": "remarks"}
LABELLED = re.compile(r"(商品名|対応開始日)\s*</[^>]+>\s*<[^>]+>\s*([^<]+)<")
HEADLINE = re.compile(r'<p class="[^"]*detail_title_sub[^"]*">([^<]+)<|<h3[^>]*>([^<]+)</h3>')
ACTION_WORDS = {"回収": "recall", "返金": "refund", "交換": "replacement", "無償修理": "free repair", "点検": "inspection",
                "注意喚起": "warning", "回収命令": "recall order"}


def quill_text(raw: str) -> str:
    """The text of one read-only Quill block on the page (a JS string holding JSON)."""
    try:
        ops = json.loads(re.sub(r"\\(.)", lambda m: m.group(1), raw))["ops"]
    except (ValueError, KeyError, TypeError):
        return ""
    return "".join(op.get("insert") for op in ops if isinstance(op.get("insert"), str)).strip()


def parse_search(page: str) -> list[dict]:
    return [{"rcl": m[1], "title": html_lib.unescape(m[2]).strip(), "posted": m[3].strip(), "start": m[4].strip()}
            for m in ROW.finditer(page)]


def parse_detail(page: str, title_hint: str = "") -> dict:
    fields = {FIELD_ORDER.get(box, box): quill_text(raw) for raw, box in QUILL.findall(page)}
    text = re.sub(r"<[^>]+>", "\n", page)
    text = html_lib.unescape(re.sub(r"[ \t]+", " ", text))
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and "contentsText" not in ln and "quill" not in ln]

    def after(label: str) -> str:
        for i, ln in enumerate(lines[:-1]):
            if ln == label:
                return lines[i + 1]
        return ""

    title = title_hint
    if not title:  # the notice title is the line after the breadcrumb's "home" link
        crumb = next((i for i, ln in enumerate(lines) if ln.startswith("リコール情報サイトホーム")), None)
        title = lines[crumb + 1] if crumb is not None and crumb + 1 < len(lines) else ""
    hazard = ""
    if title in lines:  # the line under the repeated title is the incident summary
        idx = len(lines) - 1 - lines[::-1].index(title)
        hazard = lines[idx + 1] if idx + 1 < len(lines) and lines[idx + 1] != "商品名" else ""
    return {"title": title, "hazard": hazard, "product_name": after("商品名"), "start_date": after("対応開始日"),
            "management_no": (re.search(r"管理番号：\s*(\d+)", text) or [None, ""])[1], **fields}


def to_record(rcl: str, row: dict, detail: dict, retrieved_at) -> SourceRecord:
    ident = detail.get("identification") or ""
    title = detail.get("title") or row.get("title") or ""
    original = "\n".join(x for x in (title, detail.get("hazard"), ident, detail.get("remarks")) if x)
    models = normalizer.models_in(ident) or normalizer.models_in(title)
    brands = re.findall(r"^([^「]+)「", title)  # 平南商事「HAIARA モバイルバッテリー」: company before the quotes
    product = detail.get("product_name") or ""
    ascii_brand = re.findall(r"[A-Za-z][A-Za-z0-9&.\-]{2,}", product.split(" ")[0]) if product else []
    action = next((en for ja, en in ACTION_WORDS.items() if ja in title), "recall")
    published = normalizer.to_datetime(row.get("posted")) or normalizer.to_datetime(detail.get("start_date"))
    ids = normalizer.identifiers(brands + ascii_brand, original, models=models)
    return SourceRecord(
        source="jp_caa", record_id=f"jp_caa:{rcl}", source_url=f"{SITE}/result/detail.php?rcl={rcl}&screenkbn=06",
        record_type="safety_notice" if action == "warning" else "recall_notice", raw_payload_hash=payload_hash(detail),
        event_at=None, source_published_at=published,
        source_updated_at=None, retrieved_at=retrieved_at, product_identifiers=ids,
        claims=normalizer.recall_claims(title, detail.get("hazard") or "", detail.get("action") or "", ids["models"],
                                        "recall" if action != "warning" else "safety_notice", original),
        title=title, hazard=detail.get("hazard") or "", remedy=detail.get("action") or "", jurisdiction="JP",
        affected_markets=["JP"], language=locales.detect_language(original) if original else "ja",
        original_text=original[:2000], legal_scope=action, publication_timezone="Asia/Tokyo", authority="CAA",
        attribution="出典：消費者庁リコール情報サイト (Consumer Affairs Agency); fields extracted by SafeShelf")


class Adapter(Base):
    async def search(self, query: SourceQuery) -> list[SourceRecord]:
        terms = [t for t in (policy.clean_term(query.model), policy.clean_term(query.brand)) if t]
        if not terms:
            return []
        ok, why = policy.allowed_url(SITE, self.domains)
        if not ok:
            raise SourceFailure(ERROR, why)
        rows: dict[str, dict] = {}
        async with httpx.AsyncClient(transport=_http.transport, timeout=self.timeout, follow_redirects=True,
                                     headers={"User-Agent": _http.USER_AGENT, "Referer": SITE + "/"}) as client:
            try:
                await client.get(SITE + "/")  # the search needs the session cookie the home page sets
                for term in terms[:2]:
                    found = await self._post(client, term[:30])  # the site's box takes 30 characters
                    for row in found:
                        rows.setdefault(row["rcl"], row)
                    if found and term == terms[0] and query.model:
                        break  # the model number found notices: the brand search would only add noise
                details = {}
                for rcl in list(rows)[:MAX_DETAILS]:
                    response = await client.get(f"{SITE}/result/detail.php", params={"rcl": rcl, "screenkbn": "06"})
                    if response.status_code == 200:
                        details[rcl] = parse_detail(response.text, rows[rcl]["title"])
            except httpx.TimeoutException:
                raise SourceFailure("timeout", f"no answer within {self.timeout:g} s") from None
            except httpx.HTTPError as error:
                raise SourceFailure(ERROR, f"could not reach the site ({type(error).__name__})") from None
        retrieved = now()
        records = [to_record(rcl, rows[rcl], d, retrieved) for rcl, d in details.items()]
        if query.as_of:
            records = [r for r in records if r.source_published_at and r.source_published_at <= query.as_of]
        return records

    async def _post(self, client: httpx.AsyncClient, term: str) -> list[dict]:
        response = await client.post(f"{SITE}/result/index.php",
                                     data={"search": term, "screenkbn": "01", "category": "0"})
        if response.status_code in (401, 403):
            raise SourceFailure("blocked", f"the site refused the request ({response.status_code})")
        if response.status_code >= 400:
            raise SourceFailure(ERROR, f"the site answered {response.status_code}")
        return parse_search(response.text)
