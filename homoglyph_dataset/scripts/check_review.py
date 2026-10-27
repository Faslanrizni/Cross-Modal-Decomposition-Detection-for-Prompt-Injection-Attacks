"""check_review.py — validate the hand review log."""
import csv
from pathlib import Path

LOG = Path("homoglyph_dataset/verification/verification_log.csv")

if not LOG.exists():
    raise SystemExit(f"{LOG} not found. Complete the hand review first.")

rows = list(csv.DictReader(LOG.open(encoding="utf-8-sig")))
print(f"total: {len(rows)}")

fails = []
for r in rows:
    if r["label"] == "attack" and r["intent_correct"] == "no":
        fails.append(r)
    elif r["label"] == "benign" and r["benign_actually_benign"] == "no":
        fails.append(r)

unfilled = []
for r in rows:
    # Every row must have human_readable filled
    if r["human_readable"] not in ("yes", "no"):
        unfilled.append(r)
        continue
    # Attack rows must have intent_correct filled
    if r["label"] == "attack" and r["intent_correct"] not in ("yes", "no", "n/a"):
        unfilled.append(r)
        continue
    # Benign rows must have benign_actually_benign filled
    if r["label"] == "benign" and r["benign_actually_benign"] not in ("yes", "no", "n/a"):
        unfilled.append(r)

print(f"failures: {len(fails)}")
print(f"unfilled: {len(unfilled)}")

if fails:
    print("\nFailures:")
    for r in fails[:10]:
        print(f"  {r['id']} ({r['label']}, {r['technique']}): "
              f"intent={r['intent_correct']} benign={r['benign_actually_benign']}")

if unfilled:
    print("\nUnfilled cells:")
    for r in unfilled[:10]:
        print(f"  {r['id']} ({r['label']}, {r['technique']})")