import csv
import re
from pathlib import Path
from collections import Counter

from transformers import AutoTokenizer

IN = Path("qr_dataset/manifest_v2.csv")
OUT = Path("qr_dataset/manifest_v3.csv")
SUMMARY = Path("qr_dataset/summary_qr.json")
REV_FILE = Path("qr_dataset/dataset_revision.txt")

TOK = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

# Read folder fingerprint
rev_text = REV_FILE.read_text(encoding="utf-8")
rev = re.search(r"folder_sha256=([a-f0-9]{64})", rev_text).group(1)
dataset_revision = f"folder_sha256={rev}"

# Read existing v2
rows = list(csv.DictReader(IN.open(encoding="utf-8-sig")))

# Build v3
for r in rows:
    payload = r["payload"]
    r["modality"] = "image"
    r["text"] = payload
    r["text_len"] = len(payload)
    r["token_len"] = len(TOK.tokenize(payload))
    r["source_file"] = r.get("origin", "")
    r["label_method"] = "seed_inherited" if r["label"] == "attack" else "seed_inherited"
    r["dataset_revision"] = dataset_revision
    r["licence"] = "HuggingFace standard"
    r["split"] = ""  # populated in Step 7

# Column order: shared first, then family-specific
shared = [
    "id", "label", "pair_id", "intent_id", "intent_category",
    "encoding_family", "modality", "text", "text_len", "token_len",
    "source_file", "label_method", "dataset_revision", "licence", "split",
]
family_specific = [
    "origin", "format", "payload", "payload_len", "qr_version",
    "png", "png_sha256", "roundtrip_ok", "opencv_ok",
]
fieldnames = shared + family_specific

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fieldnames})

# Summary
attacks = [r for r in rows if r["label"] == "attack"]
benign = [r for r in rows if r["label"] == "benign"]
summary = {
    "total_rows": len(rows),
    "attack_rows": len(attacks),
    "benign_rows": len(benign),
    "unique_pairs": len(set(r["pair_id"] for r in rows)),
    "unique_intents": len(set(r["intent_id"] for r in attacks)),
    "format_distribution": dict(Counter(r["format"] for r in rows)),
    "qr_version_distribution": dict(Counter(r["qr_version"] for r in rows)),
    "token_len_attack": {
        "mean": round(sum(r["token_len"] for r in attacks) / len(attacks), 2),
        "min": min(r["token_len"] for r in attacks),
        "max": max(r["token_len"] for r in attacks),
    },
    "token_len_benign": {
        "mean": round(sum(r["token_len"] for r in benign) / len(benign), 2),
        "min": min(r["token_len"] for r in benign),
        "max": max(r["token_len"] for r in benign),
    },
    "intents_per_category": dict(Counter(r["intent_category"] for r in attacks)),
}

import json
SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

print(f"Wrote {OUT}: {len(rows)} rows")
print(f"Wrote {SUMMARY}")
print(json.dumps(summary, indent=2))