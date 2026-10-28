"""prefill_review.py — stratified by (category, tier, label)."""
import csv, random
from pathlib import Path
from collections import defaultdict

rows = list(csv.DictReader(open("audio_dataset/manifest/audio_manifest.csv",
                                   encoding="utf-8-sig")))
rng = random.Random(42)
by_cell = defaultdict(list)
for r in rows:
    by_cell[(r["attack_category"], r["duration_match_tier"], r["label"])].append(r)

sample = []
for cell, members in by_cell.items():
    sample.extend(rng.sample(members, min(3, len(members))))

out = Path("audio_dataset/verification/hand_review_sample.csv")
with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "attack_category", "duration_match_tier",
                "duration_s", "text", "audio_path",
                "human_audible", "intent_correct", "benign_actually_benign", "notes"])
    for r in sample:
        w.writerow([r["id"], r["label"], r["attack_category"],
                    r["duration_match_tier"], r["duration_s"],
                    r["text"][:200], r["audio_path"], "", "", "", ""])
print(f"wrote {len(sample)} rows for review "
      f"(across {len(by_cell)} cells)")