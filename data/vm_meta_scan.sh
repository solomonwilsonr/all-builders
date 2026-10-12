#!/bin/bash
# M1/M2: startup script for a throwaway Compute Engine VM. Streams Amazon Reviews 2023 metadata for
# the categories below, keeps listings whose metadata names a recalled brand, uploads the matches to
# the bucket, then shuts the VM down (delete it afterwards). Launch it with the gcloud command in data/README.md.
set -u
BUCKET=gs://safeshelf-data-03d8d835
OUT=$BUCKET/amazon_meta_matches
# Brands and models from data/raw/cpsc_backtest_candidates.jsonl (electrical recalls only).
MATCH='vrurc|mycharge|amazon ?basics[^"]{0,40}ceramic|skylight[^"]{0,40}(frame|adapter)|marpac|yogasleep|little experimenter|mobile warming|dell[^"]{0,40}hybrid|dewalt[^"]{0,20}dwd11|ring video doorbell|homerygardens|trianium|monoprice[^"]{0,40}cat ?6|b-air|bluedri|relaygo|republic wireless|line ?6 relay|elektron|gas ?one[^"]{0,40}hose|flame king|hovertrax|caldwell[^"]{0,30}e-max|goal ?zero|illu-mist|jimco|victory innovations|protexus|gyroor|scotch[^"]{0,30}tl1302|aduro|airsure|gel blaster|ancheer|warmwave|soundboks|toolguards|fitbit ionic|geek heat|zooby|infanttech|bqqzhz|sahara[^"]{0,30}dehydrator|flo[^"]{0,20}battery back|sunbeam[^"]{0,40}heated|bedsure[^"]{0,40}(heated|heating|electric)|anker[^"]{0,40}(535|powercore 20k|a1366)|vornado[^"]{0,20}srth|bissell[^"]{0,40}(crosswave|2551)'
CATS="Cell_Phones_and_Accessories Electronics Home_and_Kitchen Tools_and_Home_Improvement Appliances Toys_and_Games Sports_and_Outdoors Musical_Instruments Office_Products Baby_Products Health_and_Household Patio_Lawn_and_Garden Industrial_and_Scientific"

apt-get update -qq && apt-get install -y -qq python3-requests
mkdir -p /scan/raw && cd /scan
gcloud storage cp $BUCKET/jobs/stream_reviews.py /scan/stream_reviews.py
for c in $CATS; do
  python3 stream_reviews.py meta --category "$c" --match "$MATCH" --out "raw/meta_$c.jsonl" > "raw/log_$c.txt" 2>&1 &
done
wait
gcloud storage cp raw/* "$OUT/"
echo done | gcloud storage cp - "$OUT/_DONE"
shutdown -h now
