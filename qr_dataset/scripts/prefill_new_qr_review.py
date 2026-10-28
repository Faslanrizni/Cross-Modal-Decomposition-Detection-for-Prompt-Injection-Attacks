"""prefill_new_qr_review.py — hand-review CSV for the 40 new rows."""
import csv
from pathlib import Path

MANIFEST = Path("qr_dataset/manifest_v4.csv")
OUT = Path("qr_dataset/verification/expansion_review_sample.csv")

OLD_IDS = {f"QR-{i:06d}" for i in range(1, 16)}
OLD_IDS |= {f"B-QR-{i:06d}" for i in range(1, 16)}

rows = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))
        if r["id"] not in OLD_IDS]

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "intent_id", "format", "payload",
                "intent_correct", "benign_actually_benign", "notes"])
    for r in rows:
        w.writerow([r["id"], r["label"], r["intent_id"], r["format"],
                    r["payload"][:200], "", "", ""])

print(f"Wrote {OUT} with {len(rows)} new rows (excludes 30 v2 rows)")