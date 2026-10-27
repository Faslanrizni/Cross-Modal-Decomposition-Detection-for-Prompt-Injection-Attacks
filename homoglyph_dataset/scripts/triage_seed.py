"""triage_seed.py — classify 20 raw homoglyph samples. RAW- prefix avoids ID collision."""
import csv
import json
from pathlib import Path
from collections import Counter

RAW = Path("homoglyph_dataset/raw/homoglyph_unicode_attacks")
OUT = Path("homoglyph_dataset/exclusions.csv")

TRIAGE = {
    "HGL-000001": ("keep", "Cyrillic lookalikes (і, о, е) — main channel"),
    "HGL-000002": ("control", "Zero-width space — control stratum"),
    "HGL-000003": ("flag", "RTL override — breaks text directionality, out of scope"),
    "HGL-000004": ("flag", "Small Roman numerals — 75% UNK, excluded"),
    "HGL-000005": ("flag", "Soft hyphen — stripped by tokenizer, out of scope"),
    "HGL-000006": ("control", "Word joiner — zero-width class, control stratum"),
    "HGL-000007": ("flag", "Math bold italic — 100% UNK, excluded"),
    "HGL-000008": ("flag", "Squared Latin letters — 100% UNK, excluded"),
    "HGL-000009": ("control", "Combining dot above — control stratum"),
    "HGL-000010": ("flag", "Braille blank — not in our technique set"),
    "HGL-000011": ("flag", "Cyrillic п + leetspeak — hybrid, not pure homoglyph"),
    "HGL-000012": ("control", "BOM insertion — zero-width class, control stratum"),
    "HGL-000013": ("flag", "Circled Latin — 100% UNK, excluded"),
    "HGL-000014": ("flag", "Fullwidth — 100% UNK, excluded"),
    "HGL-000015": ("control", "Unicode tag characters — control stratum"),
    "HGL-000016": ("keep", "Cyrillic lookalikes (є, а) — main channel"),
    "HGL-000017": ("flag", "Superscript — not in our set"),
    "HGL-000018": ("flag", "Math double-struck — 100% UNK, excluded"),
    "HGL-000019": ("control", "Combining diacritics — control stratum"),
    "HGL-000020": ("control", "Zero-width non-joiner — control stratum"),
}

seed_files = list(RAW.glob("*.json"))
if not seed_files:
    raise SystemExit(f"No JSON files in {RAW}")

rows = []
for f in sorted(seed_files):
    data = json.loads(f.read_text(encoding="utf-8"))
    for item in data:
        sid = item["id"]
        decision, reason = TRIAGE.get(sid, ("flag", "unknown"))
        rows.append({"sample_id": f"RAW-{sid}", "decision": decision, "reason": reason})

with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["sample_id", "decision", "reason"])
    w.writeheader()
    w.writerows(rows)

counts = Counter(r["decision"] for r in rows)
print(f"Wrote {OUT} with {len(rows)} rows")
print(f"  {dict(counts)}")