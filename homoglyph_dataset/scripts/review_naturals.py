"""review_naturals.py — produce a hand-review CSV for natural benigns."""
import csv
from pathlib import Path

MANIFEST = Path("homoglyph_dataset/manifest/homoglyph_manifest.csv")
OUT = Path("homoglyph_dataset/verification/naturals_review_sample.csv")

rows = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))
        if r["benign_kind"] == "natural"]

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "text", "language", "harmless", "attack_vocabulary", "notes"])
    for r in rows:
        w.writerow([r["id"], r["text"], "", "", "", ""])

print(f"Wrote {OUT} with {len(rows)} rows")