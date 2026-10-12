#!/usr/bin/env bash
# Feasibility test (12 Oct 2026): do hazard reviews appear before CPSC recalls?
# Run from this folder. Downloads ~13 GB in total; use Colab or a GCP VM, not a laptop.
set -euo pipefail
HF=https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw

# 1. CPSC recalls, 2019-2023
for y in 2019 2020 2021 2022 2023; do
  curl -s "https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallDateStart=$y-01-01&RecallDateEnd=$y-12-31" -o "recalls_$y.json"
done

# 2. Product metadata (4 GB): find the recalled brands' listings
curl -sL "$HF/meta_categories/meta_Cell_Phones_and_Accessories.jsonl" \
  | grep -iE 'vrurc|mycharge|a1366|535 power ?bank|"store": "anker"' > meta_hits.jsonl

# 3. Reviews (9.3 GB): keep only the target listings in targets.json
ASINS=$(python3 -c "import json; print('|'.join(a for t in json.load(open('targets.json')).values() for a in t['asins']))")
curl -sL "$HF/review_categories/Cell_Phones_and_Accessories.jsonl" \
  | grep -E "\"parent_asin\": \"($ASINS)\"" > reviews_hits.jsonl

# 4. Replay and apply the alarm rule (3 hazard-keyword reviews within 90 days)
python3 analyse.py reviews_hits.jsonl
