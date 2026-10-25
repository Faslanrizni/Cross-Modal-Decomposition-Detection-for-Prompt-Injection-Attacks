import csv
from pathlib import Path

LOG = Path("ascii_dataset/verification/verification_log.csv")

rows = list(csv.DictReader(LOG.open(encoding="utf-8-sig")))
print(f"total: {len(rows)}")

fails = [
    r for r in rows
    if r["art_decodes"] != "yes"
    or r["leak_tier_correct"] not in ("yes", "n/a", "")
    or r["intent_correct"] == "no"
    or r["benign_actually_benign"] == "no"
]

unfilled = [
    r for r in rows
    if (r["label"] == "attack" and r["intent_correct"] not in ("yes", "no"))
    or (r["label"] == "benign" and r["benign_actually_benign"] not in ("yes", "no"))
    or r["leak_tier_correct"] == "human"
]

print(f"failures: {len(fails)}")
print(f"unfilled: {len(unfilled)}")

if fails:
    print("\nFAILURES:")
    for r in fails[:10]:
        print(
            f"  {r['id']}: intent={r['intent_correct']} "
            f"benign={r['benign_actually_benign']} "
            f"tier={r['leak_tier_correct']} "
            f"art={r['art_decodes']}"
        )

if unfilled:
    print("\nUNFILLED:")
    for r in unfilled[:10]:
        print(f"  {r['id']}")