"""check_review.py — verify hand review is complete and shows no failures.

Reads audio_dataset/verification/verification_log.csv and reports:
  total     — number of reviewed rows
  failures  — rows where the reviewer marked 'no'
  unfilled  — rows with missing or invalid verdict values

Exit codes: 0 if clean, 1 if there are failures or unfilled rows.
"""

import csv
import sys
from pathlib import Path

LOG = Path("audio_dataset/verification/verification_log.csv")

if not LOG.exists():
    print(f"MISSING: {LOG}")
    print("Save the filled hand_review_sample.csv as verification_log.csv first.")
    sys.exit(1)

rows = list(csv.DictReader(LOG.open(encoding="utf-8-sig")))
print(f"total: {len(rows)}")

# --- failures: any row where a verdict is 'no' ---
fails = [
    r for r in rows
    if (r["label"] == "attack" and r.get("intent_correct") == "no")
    or (r["label"] == "benign" and r.get("benign_actually_benign") == "no")
]
print(f"failures: {len(fails)}")

# --- unfilled: missing human_audible, or missing verdict, or invalid value ---
def missing_verdict(r):
    label = r["label"]
    audible = (r.get("human_audible") or "").strip().lower()
    if audible not in ("yes", "no"):
        return True
    if label == "attack":
        v = (r.get("intent_correct") or "").strip().lower()
        return v not in ("yes", "no", "n/a")
    if label == "benign":
        v = (r.get("benign_actually_benign") or "").strip().lower()
        return v not in ("yes", "no", "n/a")
    return True  # unknown label

unfilled = [r for r in rows if missing_verdict(r)]
print(f"unfilled: {len(unfilled)}")

for r in fails[:10]:
    print(f"  FAIL     {r['id']} ({r['label']}, {r['attack_category']}, "
          f"tier={r['duration_match_tier']})")
for r in unfilled[:10]:
    print(f"  UNFILLED {r['id']}")

# --- fail-fast for CI / script chains ---
if fails or unfilled:
    sys.exit(1)
sys.exit(0)