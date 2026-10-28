"""build_splits_audio.py — populate split column + build all split files.

Audio has 5 categories (not the 21-intent taxonomy other channels use), so:
  IID split   = category grouping (3 train / 1 val / 1 test)
  LOFO splits = hold out whole families or whole audio categories

Populates the `split` column of audio_manifest.csv AND writes split JSON files.
"""

import csv, json, random
from collections import Counter
from pathlib import Path

SEED     = 42
MANIFEST = Path("audio_dataset/manifest/audio_manifest.csv")
OUT      = Path("audio_dataset/splits"); OUT.mkdir(parents=True, exist_ok=True)
REF_DIR  = Path("plain_dataset/splits")

# --- load audio manifest ---
rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8-sig")))
cats = sorted({r["split_group"] for r in rows})
print(f"audio categories ({len(cats)}): {cats}")

# --- assign IID split by attack_category ---
rng = random.Random(SEED)
shuffled = list(cats)
rng.shuffle(shuffled)
n = len(shuffled)
n_train = max(1, int(n * 0.60))
n_val   = max(2, int(n * 0.80))
train_cats = shuffled[:n_train]
val_cats   = shuffled[n_train:n_val]
test_cats  = shuffled[n_val:]
print(f"  train_cats = {train_cats}")
print(f"  val_cats   = {val_cats}")
print(f"  test_cats  = {test_cats}")

def split_of(cat):
    if cat in train_cats: return "train"
    if cat in val_cats:   return "val"
    return "test"

for r in rows:
    r["split"] = split_of(r["split_group"])

# --- write manifest with populated split column ---
with MANIFEST.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print(f"\nmanifest updated: split column populated")

# --- IID split (audio-only) ---
(OUT / "iid_audio.json").write_text(json.dumps({
    "split_name": "iid_audio", "seed": SEED,
    "grouped_by": "attack_category",
    "train_categories": train_cats,
    "val_categories":   val_cats,
    "test_categories":  test_cats,
}, indent=2))

# --- LOFO: audio held out (primary RQ1) ---
(OUT / "lofo_audio_held_out.json").write_text(json.dumps({
    "split_name": "lofo_audio_held_out", "seed": SEED,
    "test_families":  ["audio"],
    "train_families": ["ascii_art", "qr", "plain", "homoglyph"],
}, indent=2))

# --- LOFO: joint QR + audio (RO5a primary) ---
(OUT / "lofo_qr_plus_audio_held_out.json").write_text(json.dumps({
    "split_name": "lofo_qr_plus_audio_held_out", "seed": SEED,
    "test_families":  ["qr", "audio"],
    "train_families": ["ascii_art", "plain", "homoglyph"],
}, indent=2))

# --- Per-category LOFO for each audio category ---
for held in cats:
    (OUT / f"lofo_audio_category_{held}_held_out.json").write_text(json.dumps({
        "split_name":             f"lofo_audio_category_{held}_held_out",
        "seed":                   SEED,
        "test_families":          ["audio"],
        "test_audio_categories":  [held],
        "train_families":         ["ascii_art", "qr", "plain", "homoglyph"],
        "train_audio_categories": [c for c in cats if c != held],
    }, indent=2))

# --- Copy reference split files from plain_dataset if present ---
if REF_DIR.exists():
    for ref in REF_DIR.glob("*.json"):
        dst = OUT / ref.name
        if not dst.exists():
            dst.write_bytes(ref.read_bytes())
            print(f"  copied ref: {ref.name}")

# --- report ---
split_counts = Counter(r["split"] for r in rows)
print(f"\nsplit counts:")
for s in ("train", "val", "test"):
    print(f"  {s:6s}: {split_counts.get(s, 0)}")
print(f"  total : {len(rows)}")

files = sorted(OUT.glob("*.json"))
print(f"\nwrote {len(files)} split files to {OUT}:")
for p in files:
    print(f"  {p.name}")