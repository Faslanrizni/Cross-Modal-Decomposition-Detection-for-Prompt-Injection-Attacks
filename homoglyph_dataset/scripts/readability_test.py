"""readability_test.py — does MiniLM encode substituted text near its source?

The correct perceivability check. TF-IDF (used in in_family_ceiling.py)
measures bag-of-words difference, not semantic readability. This script
embeds source_text and text with MiniLM's actual encoder and computes
cosine similarity, compared to a random-pair baseline.
"""
import csv
import random
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MANIFEST = Path("homoglyph_dataset/manifest/homoglyph_manifest.csv")
OUT = Path("homoglyph_dataset/readability_test.json")

model = SentenceTransformer(MODEL)

rows = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))
        if r["label"] == "attack"
        and r["technique"] in ("cyrillic", "greek")
        and r["tokenizer_neutralised"].lower() == "false"]

src_texts = [r["source_text"] for r in rows]
trans_texts = [r["text"] for r in rows]

print(f"Encoding {len(rows)} attack rows...")
src_emb = model.encode(src_texts, normalize_embeddings=True, show_progress_bar=True)
trans_emb = model.encode(trans_texts, normalize_embeddings=True, show_progress_bar=True)

# Per-row similarity: source vs its own transformed version
per_row_sim = (src_emb * trans_emb).sum(1)

# Random baseline: source vs randomly paired transformed (unrelated)
rng = random.Random(42)
perm = rng.sample(range(len(rows)), len(rows))
random_sim = (src_emb * trans_emb[perm]).sum(1)

print()
print(f"{'scope':<20} {'mean_sim':<10} {'n'}")
print("-" * 45)
print(f"{'random baseline':<20} {float(random_sim.mean()):<10.4f} {len(rows)}")

results = {"random_baseline": round(float(random_sim.mean()), 4), "per_technique_density": {}}

for tech in ("cyrillic", "greek"):
    for density in ("0.3", "0.6"):
        idx = [i for i, r in enumerate(rows)
               if r["technique"] == tech and r["density"] == density]
        if not idx:
            continue
        sims = per_row_sim[idx]
        mean = float(sims.mean())
        results["per_technique_density"][f"{tech}_{density}"] = {
            "n": len(idx),
            "mean_sim": round(mean, 4),
            "min_sim": round(float(sims.min()), 4),
            "max_sim": round(float(sims.max()), 4),
        }
        print(f"{tech+'/'+density:<20} {mean:<10.4f} {len(idx)}")

# Interpretation
# Rule of thumb: source-vs-transformed similarity should be visibly
# higher than random. If the delta is < 0.1, MiniLM cannot associate
# the substituted text with its source (unreadable channel).
overall_mean = float(per_row_sim.mean())
random_baseline = float(random_sim.mean())
delta = overall_mean - random_baseline

if delta >= 0.20:
    verdict = "READABLE"
    action = "Proceed with LOFO"
elif delta >= 0.10:
    verdict = "PARTIALLY_READABLE"
    action = "Proceed with caveat"
else:
    verdict = "UNREADABLE"
    action = "Do NOT report LOFO on homoglyph; document as limitation"

results.update({
    "overall_mean_sim": round(overall_mean, 4),
    "delta_vs_random": round(delta, 4),
    "interpretation": verdict,
    "action": action,
})

OUT.write_text(__import__("json").dumps(results, indent=2), encoding="utf-8")
print()
print(__import__("json").dumps(results, indent=2))