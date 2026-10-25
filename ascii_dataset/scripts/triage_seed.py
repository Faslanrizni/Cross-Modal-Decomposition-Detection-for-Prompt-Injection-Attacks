
"""
triage_seed.py categorises each seed:

Seed	Decision	Reason
ART-000001	keep	figlet-style, decodes to IGNORE
ART-000002	exploratory_only	block chars map to [UNK]
ART-000003	keep	figlet-style, decodes to OVERRIDE
ART-000004	flag	boxed plain text, not figlet
ART-000005	keep	figlet-style, decodes to HACK
ART-000006	keep	figlet-style, decodes to BYPASS
ART-000007	flag	art does not decode to a word
ART-000008	flag	art does not decode to a word
ART-000009	flag	acrostic, not ASCII art
ART-000010	keep	figlet-style, decodes to DISCARD
ART-000011	keep	figlet-style, decodes to SUDO
ART-000012	flag	art does not decode to a word
Why: transparency. Nothing is silently dropped.

The 6 keepers do not become training data directly. They are cited as provenance (seed_sample_ids in the taxonomy). The actual training data is generated fresh from the taxonomy in Step 4.
"""

import json, csv
from pathlib import Path

SEED_FILE = Path("ascii_dataset/raw/ascii_art_injection/ascii_art_injection_001.json")
OUT = Path("ascii_dataset/exclusions.csv")

TRIAGE = {
    "ART-000001": ("keep",             "figlet-style, decodes to IGNORE"),
    "ART-000002": ("exploratory_only", "block chars -> [UNK]; not in training"),
    "ART-000003": ("keep",             "figlet-style, decodes to OVERRIDE"),
    "ART-000004": ("flag",             "boxed plain text, not figlet-rendered"),
    "ART-000005": ("keep",             "figlet-style, decodes to HACK"),
    "ART-000006": ("keep",             "figlet-style, decodes to BYPASS"),
    "ART-000007": ("flag",             "art does not decode to a word"),
    "ART-000008": ("flag",             "art does not decode to a word"),
    "ART-000009": ("flag",             "acrostic, not ASCII art"),
    "ART-000010": ("keep",             "figlet-style, decodes to DISCARD"),
    "ART-000011": ("keep",             "figlet-style, decodes to SUDO"),
    "ART-000012": ("flag",             "art does not decode to a word"),
}

rows = json.loads(SEED_FILE.read_text(encoding="utf-8"))

# Report any ID mismatch before writing
unknown = [r["id"] for r in rows if r["id"] not in TRIAGE]
if unknown:
    print("WARNING: IDs in file not present in triage table:", unknown)
    print("File IDs:", [r["id"] for r in rows])
    print("Triage IDs:", list(TRIAGE.keys()))
    raise SystemExit("Fix the ID mismatch before proceeding.")

with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["sample_id", "decision", "reason"])
    for r in rows:
        dec, reason = TRIAGE[r["id"]]
        w.writerow([r["id"], dec, reason])

from collections import Counter
counts = Counter(TRIAGE[r["id"]][0] for r in rows)
print(f"Wrote {OUT} with {len(rows)} rows")
print(dict(counts))