"""Feasibility: do hazard reviews appear before the recall date?
Usage: python3 analyse.py reviews_hits.jsonl
"""
import json, sys, re, datetime as dt
from collections import defaultdict

# target product -> (recall date, parent_asins)
TARGETS = json.load(open("targets.json"))
HAZ = re.compile(r"\b(fire|flame|smok\w*|melt\w*|burn\w*|scorch\w*|overheat\w*|too hot|very hot|extremely hot|spark\w*|explod\w*|swell\w*|swollen|bulg\w*|caught fire)\b", re.I)

asin2t = {a: name for name, t in TARGETS.items() for a in t["asins"]}
rows = defaultdict(list)
for line in open(sys.argv[1]):
    try:
        r = json.loads(line)
    except Exception:
        continue
    t = asin2t.get(r.get("parent_asin"))
    if not t:
        continue
    d = dt.datetime.utcfromtimestamp(r["timestamp"] / 1000).date()
    text = (r.get("title") or "") + " " + (r.get("text") or "")
    rows[t].append((d, bool(HAZ.search(text)), bool(r.get("images")), r.get("rating"), text[:160]))

for name, t in TARGETS.items():
    recall = dt.date.fromisoformat(t["recall"])
    rs = sorted(rows[name])
    before = [x for x in rs if x[0] < recall]
    haz = [x for x in before if x[1]]
    print(f"\n=== {name}  recall {recall}")
    print(f"reviews: {len(rs)} total, {len(before)} before recall, {len(haz)} hazard-keyword before recall, {sum(1 for x in haz if x[2])} with photos")
    # simple alarm rule: 3 hazard reviews within 90 days
    flag = None
    for i in range(len(haz)):
        win = [x for x in haz if 0 <= (x[0] - haz[i][0]).days <= 90]
        if len(win) >= 3:
            flag = win[2][0]
            break
    if flag:
        print(f"FLAG (3 hazard reviews in 90 days) on {flag}: lead time {(recall - flag).days} days ({(recall - flag).days / 7:.1f} weeks)")
    else:
        print("no flag before recall")
    for x in haz[:6]:
        print("  ", x[0], f"{x[3]}★", "📷" if x[2] else "  ", x[4].replace("\n", " ")[:120])
