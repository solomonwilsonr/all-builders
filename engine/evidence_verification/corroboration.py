"""Independent corroboration (plan v2.2 J1, J3 step 4): which reports are separate observations.

Ten articles repeating one incident are one observation. Reports join a group when they share a source record ID,
an image, a citation of each other, or nearly the same words (copied complaints, syndicated articles, a regulator's
notice and SafeShelf's stored copy of it). Distinct publishers are kept, but the independent count is the number of
groups, never the number of reports.
"""
import hashlib
import re

from engine import locales

SIMILAR = 0.6          # word 5-gram overlap that makes two texts one observation
SAME_DAY_SIMILAR = 0.3  # lower bar for reports of the same product on the same date


def shingles(text: str, n: int = 5) -> set[str]:
    words = re.findall(r"\w+", locales.fold(text or "").lower())
    if len(words) < n:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


class _Groups:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def join(self, a: int, b: int) -> None:
        self.parent[self.find(a)] = self.find(b)


def group(observations: list[dict]) -> list[dict]:
    """observations: {id, record_id?, text, date?, image_hashes?, url?, cites?, publisher?}.
    Returns groups: {group_id, members, publishers, reason}."""
    n = len(observations)
    groups, reasons = _Groups(n), {}
    grams = [shingles(o.get("text") or "") for o in observations]
    for i in range(n):
        for j in range(i + 1, n):
            a, b = observations[i], observations[j]
            why = None
            if a.get("record_id") and a.get("record_id") == b.get("record_id"):
                why = "same official record"
            elif set(a.get("image_hashes") or []) & set(b.get("image_hashes") or []):
                why = "same photo"
            elif (a.get("url") and a["url"] in (b.get("cites") or [])) or \
                    (b.get("url") and b["url"] in (a.get("cites") or [])):
                why = "one cites the other"
            else:
                overlap = jaccard(grams[i], grams[j])
                if overlap >= SIMILAR:
                    why = "nearly the same words"
                elif a.get("date") and a.get("date") == b.get("date") and overlap >= SAME_DAY_SIMILAR:
                    why = "same day, similar words"
            if why:
                groups.join(i, j)
                reasons[groups.find(j)] = why
    by_root: dict[int, list[int]] = {}
    for i in range(n):
        by_root.setdefault(groups.find(i), []).append(i)
    out = []
    for root, members in by_root.items():
        ids = sorted(observations[i]["id"] for i in members)
        out.append({"group_id": "OG-" + hashlib.sha1("|".join(ids).encode()).hexdigest()[:10].upper(),
                    "members": ids,
                    "publishers": sorted({observations[i].get("publisher") or "" for i in members} - {""}),
                    "reason": reasons.get(root, "independent") if len(members) > 1 else "independent"})
    return out


def independent_count(observations: list[dict]) -> int:
    return len(group(observations))


def membership(groups: list[dict]) -> dict[str, str]:
    return {m: g["group_id"] for g in groups for m in g["members"]}
