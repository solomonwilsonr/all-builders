"""Chart for the deck (checklist item 7): days between the first regulator's notice and the JAPAC regulator's notice
for the same model, one bar per pair, from bench/crossborder_results.json. Writes bench/crossborder_chart.svg.

    python3 bench/crossborder_chart.py
"""
import html
import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent
NAMES = {"US": "US", "AU": "Australia", "JP": "Japan", "KR": "Korea", "SG": "Singapore"}
SERIES, TEXT, MUTED, GRID, SURFACE = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


# Short product names for the chart (the full notice titles are in crossborder_review.md).
SHORT = {"HT2410": "EGO Power+ hedge trimmer", "J04402": "Janod Cocoon activity table", "CAH16WRW1": "NZXT H1 PC case",
         "4M012": "4moms mamaRoo swing", "SHL96": "PowerXL juicer", "ESWM02": "PowerXL waffle maker",
         "ESWM03": "PowerXL waffle maker", "2G520": "ESR HaloLock power bank", "SK3000": "Thermos Stainless King jar",
         "SK3020": "Thermos Stainless King jar", "BPD005": "Belkin BoostCharge Pro charger",
         "BS30KP365": "Baseus 65W power bank", "ATHCK3TW": "Audio-Technica ATH-CK3TW case",
         "PPCXW06": "Baseus magnetic power bank", "GJD49": "Fisher-Price Baby Biceps toy",
         "PA10": "Yamaha PA-10 adaptor", "4M005": "4moms mamaRoo swing", "HBJ89": "Thomas & Friends toy truck",
         "MMA008": "Belkin power bank / charger"}


def short(pair: dict) -> str:
    return SHORT.get(pair["model"], pair["model"])


def main() -> None:
    data = json.loads((HERE / "crossborder_results.json").read_text())
    pairs = sorted([p for p in data["candidates"] if p["lead_days"] is not None], key=lambda p: -p["lead_days"])
    leads = [p["lead_days"] for p in pairs if p["lead_days"] > 0]
    median = statistics.median(leads)
    left, right, top, row, bar_h = 400, 90, 100, 26, 14
    width, height = 1100, top + row * len(pairs) + 70
    plot_w = width - left - right
    scale = plot_w / (max(p["lead_days"] for p in pairs) * 1.08)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="Inter, Segoe UI, Arial, sans-serif" role="img" aria-labelledby="t d">',
           f'<title id="t">Same model, recalled abroad first</title>',
           f'<desc id="d">Days between the first regulator notice and the JAPAC regulator notice for the same model, '
           f'{len(pairs)} pairs, median {median:g} days.</desc>',
           f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>',
           f'<text x="24" y="36" font-size="22" font-weight="700" fill="{TEXT}">Another regulator recalled the same '
           f'model first: a median of {median:g} days earlier</text>',
           f'<text x="24" y="62" font-size="14" fill="{MUTED}">Days from the first notice to the JAPAC regulator\'s '
           f'notice · {len(pairs)} pairs, stored notices 2019–2026 · same model code</text>']
    for tick in range(0, int(max(p["lead_days"] for p in pairs)) + 1, 50):
        x = left + tick * scale
        out.append(f'<line x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{top + row * len(pairs)}" stroke="{GRID}"/>')
        out.append(f'<text x="{x:.1f}" y="{top + row * len(pairs) + 18}" font-size="12" fill="{MUTED}" '
                   f'text-anchor="middle">{tick}</text>')
    out.append(f'<text x="{left + plot_w / 2:.1f}" y="{top + row * len(pairs) + 40}" font-size="12" fill="{MUTED}" '
               f'text-anchor="middle">days earlier</text>')
    for i, p in enumerate(pairs):
        y = top + i * row
        w = max(p["lead_days"] * scale, 2)
        label = f'{short(p)}'
        route = f'{NAMES.get(p["first"]["country"], p["first"]["country"])} → ' \
                f'{NAMES.get(p["later"]["country"], p["later"]["country"])}'
        tip = html.escape(f'{p["first"]["authority"]} {p["first"]["date"]} → {p["later"]["authority"]} '
                          f'{p["later"]["date"]}: {p["lead_days"]} days ({p["model"]})')
        out.append(f'<text x="{left - 10}" y="{y + bar_h - 2}" font-size="13" fill="{TEXT}" text-anchor="end">'
                   f'{html.escape(label)} <tspan fill="{MUTED}">· {route}</tspan></text>')
        out.append(f'<path d="M{left},{y} h{w - 4:.1f} a4,4 0 0 1 4,4 v{bar_h - 8} a4,4 0 0 1 -4,4 h-{w - 4:.1f} z" '
                   f'fill="{SERIES}"><title>{tip}</title></path>')
        if p["lead_days"] >= 50 or p["lead_days"] == 0 or i == len(pairs) - 1:
            text = "same day" if p["lead_days"] == 0 else f'{p["lead_days"]} days'
            out.append(f'<text x="{left + w + 6:.1f}" y="{y + bar_h - 2}" font-size="12" fill="{MUTED}">{text}</text>')
    mx = left + median * scale
    out.append(f'<line x1="{mx:.1f}" y1="{top - 14}" x2="{mx:.1f}" y2="{top + row * len(pairs)}" stroke="{TEXT}" '
               f'stroke-dasharray="4 4"/>')
    out.append(f'<text x="{mx + 6:.1f}" y="{top - 16}" font-size="12" fill="{TEXT}">median {median:g} days</text>')
    out.append(f'<text x="24" y="{height - 10}" font-size="11" fill="{MUTED}">Source: CPSC, ACCC, CAA, KATS, CPSO '
               f'notices (OECD GlobalRecalls). Every pair is listed with its notices in bench/crossborder_review.md for a person to confirm.</text>')
    out.append("</svg>")
    (HERE / "crossborder_chart.svg").write_text("\n".join(out) + "\n")
    print(f"wrote bench/crossborder_chart.svg ({len(pairs)} pairs, median {median:g} days)")


if __name__ == "__main__":
    main()
