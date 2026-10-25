import csv
from pathlib import Path

LOG = Path("qr_dataset/verification/verification_log.csv")

rows = list(csv.DictReader(LOG.open(encoding="utf-8-sig")))
print(f"total: {len(rows)}")

fails = [
    r for r in rows
    if r["payload_visible"] != "yes"
    or r["intent_correct"] == "no"
    or r["benign_actually_benign"] == "no"
]

unfilled = [
    r for r in rows
    if (r["label"] == "attack" and r["intent_correct"] not in ("yes", "no"))
    or (r["label"] == "benign" and r["benign_actually_benign"] not in ("yes", "no"))
]

print(f"failures: {len(fails)}")
print(f"unfilled: {len(unfilled)}")

if fails:
    for r in fails[:10]:
        print(f"  FAIL {r['id']}")

if unfilled:
    for r in unfilled[:10]:
        print(f"  UNFILLED {r['id']}")