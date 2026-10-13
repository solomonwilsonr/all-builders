#!/bin/bash
# M1/M2: startup script for a throwaway Compute Engine VM. Streams Amazon Reviews 2023 review files and keeps
# the reviews of the backtest ASINs (data/plan_backtest_reviews.py -> gs://.../jobs/review_asins/<Category>.txt),
# uploads them to the bucket, then shuts the VM down (delete it afterwards).
set -u
BUCKET=gs://safeshelf-data-03d8d835
OUT=$BUCKET/amazon_reviews_backtest

apt-get update -qq && apt-get install -y -qq python3-requests
mkdir -p /scan/raw /scan/asins && cd /scan
gcloud storage cp $BUCKET/jobs/stream_reviews.py /scan/stream_reviews.py
gcloud storage cp "$BUCKET/jobs/review_asins/*.txt" /scan/asins/
for f in /scan/asins/*.txt; do
  c=$(basename "$f" .txt)
  python3 stream_reviews.py reviews --category "$c" --asins "$f" --out "raw/reviews_$c.jsonl" > "raw/log_$c.txt" 2>&1 &
done
wait
gcloud storage cp raw/* "$OUT/"
echo done | gcloud storage cp - "$OUT/_DONE"
shutdown -h now
