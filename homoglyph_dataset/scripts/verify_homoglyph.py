"""verify_homoglyph.py — six-check verifier with 30-row stratified hand review."""
import csv
import json
import random
from pathlib import Path
from collections import Counter

MANIFEST = Path("homoglyph_dataset/manifest/homoglyph_manifest.csv")
OUT = Path("homoglyph_dataset/verification")
OUT.mkdir(parents=True, exist_ok=True)

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
main_rows = [r for r in rows if r["tokenizer_neutralised"].lower() == "false"]
control_rows = [r for r in rows if r["tokenizer_neutralised"].lower() == "true"]

fold_failures = [r["id"] for r in rows if r["fold_back_ok"].lower() != "true"]
empty = [r["id"] for r in rows if not r["text"].strip()]

seen, dup_ids = {}, []
for r in rows:
    key = (r["label"], r["text"])
    if key in seen:
        dup_ids.append(r["id"])
    seen[key] = True

cross, cross_dups = {}, []
for r in rows:
    if r["text"] in cross and cross[r["text"]] != r["label"]:
        cross_dups.append(r["id"])
    cross[r["text"]] = r["label"]

# 30-row stratified sample: 2 per (technique, density, label) cell
rng = random.Random(42)
sample = []
for tech in sorted(set(r["technique"] for r in rows if r["label"] == "attack")):
    densities = sorted(set(r["density"] for r in rows
                           if r["technique"] == tech and r["label"] == "attack"))
    for density in densities:
        for label in ("attack", "benign"):
            pool = [r for r in rows
                    if r["technique"] == tech
                    and r["density"] == density
                    and r["label"] == label]
            if pool:
                sample.extend(rng.sample(pool, min(2, len(pool))))
sample = sample[:30]

sample_file = OUT / "hand_review_sample.csv"
with sample_file.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "intent_id", "technique", "density", "source_text", "text",
                "human_readable", "intent_correct", "benign_actually_benign", "notes"])
    for r in sample:
        w.writerow([r["id"], r["label"], r["intent_id"], r["technique"], r["density"],
                    r["source_text"][:100], r["text"][:200], "", "", "", ""])

tech_counts = Counter(r["technique"] for r in rows)
natural_count = sum(1 for r in rows if r["benign_kind"] == "natural")
benign_count = sum(1 for r in rows if r["label"] == "benign")

report = {
    "n_rows": len(rows),
    "n_main": len(main_rows),
    "n_control": len(control_rows),
    "fold_back_failures": fold_failures,
    "empty_text": empty,
    "duplicates_within_label": dup_ids,
    "duplicates_across_labels": cross_dups,
    "natural_benigns": natural_count,
    "natural_fraction": round(natural_count / benign_count, 4) if benign_count else 0,
    "technique_counts": dict(tech_counts),
    "hand_review_rows": len(sample),
    "verdict": "PASS" if (
        not fold_failures and not empty and not dup_ids and not cross_dups
    ) else "FAIL",
}
(OUT / "verification_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(report, indent=2))
print(f"\nWrote {sample_file} with {len(sample)} rows for hand review")
print(f"Verdict: {report['verdict']}")