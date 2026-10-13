#!/bin/bash
# M1: startup script for a throwaway Compute Engine VM. Streams Amazon Reviews 2023 metadata and keeps everyday
# products in the demo categories (chargers, power banks, heaters, cords, TVs) with 30+ ratings, as a real catalog
# for identify / find copies / price and photo checks. Uploads to the bucket, then shuts the VM down.
set -u
BUCKET=gs://safeshelf-data-03d8d835
OUT=$BUCKET/amazon_catalog
TITLE='\b(wall charger|usb[- ]?c charger|fast charger|gan charger|charging block|charger block|power bank|portable charger|battery pack|space heater|heater|heated blanket|electric blanket|extension cord|power strip|surge protector|smart tv|led tv|4k tv|television)\b'

apt-get update -qq && apt-get install -y -qq python3-requests
mkdir -p /scan/raw && cd /scan
gcloud storage cp $BUCKET/jobs/stream_reviews.py /scan/stream_reviews.py
for c in Cell_Phones_and_Accessories Electronics Home_and_Kitchen Tools_and_Home_Improvement Appliances; do
  python3 stream_reviews.py meta --category "$c" --title-match "$TITLE" --min-ratings 30 \
    --out "raw/catalog_$c.jsonl" > "raw/log_$c.txt" 2>&1 &
done
wait
gcloud storage cp raw/* "$OUT/"
echo done | gcloud storage cp - "$OUT/_DONE"
shutdown -h now
