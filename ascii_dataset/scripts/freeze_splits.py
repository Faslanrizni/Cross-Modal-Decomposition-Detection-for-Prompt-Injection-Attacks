import csv, json, random
from collections import defaultdict, Counter
from pathlib import Path

SEED = 42
MANIFEST = Path("ascii_dataset/manifest/ascii_manifest.csv")
QR_MANIFEST = Path("qr_dataset/manifest_v2.csv")
SPLITS = Path("ascii_dataset/splits")
SPLITS.mkdir(parents=True, exist_ok=True)

# --- Load ASCII manifest ---
rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
intents = sorted(set(r["intent_id"] for r in rows if r["label"] == "attack"))
print(f"ASCII intents: {len(intents)}")

# --- IID split: 70/15/15 grouped by intent_id ---
rng = random.Random(SEED)
shuffled = intents[:]
rng.shuffle(shuffled)
n = len(shuffled)
train_n = int(n * 0.70)
val_n = int(n * 0.85)

iid_split = {                          # <-- renamed from 'iid' to 'iid_split'
    "split_name": "iid_group_by_intent",
    "seed": SEED,
    "grouped_by": "intent_id",
    "train_intents": shuffled[:train_n],
    "val_intents": shuffled[train_n:val_n],
    "test_intents": shuffled[val_n:],
}
with (SPLITS / "iid.json").open("w", encoding="utf-8") as f:
    json.dump(iid_split, f, indent=2)

# --- LOFO channel split (placeholder until other families exist) ---
lofo_channel = {
    "split_name": "lofo_channel",
    "seed": SEED,
    "note": "Channel-family hold-out. Completed when text, homoglyph, QR, and audio families are frozen.",
    "available_families_so_far": ["ascii_art", "qr"],
    "test_families_target": ["qr", "cross_modal_audio"],
    "train_families_target": ["text", "homoglyph", "ascii_art"],
}
with (SPLITS / "lofo_channel.json").open("w", encoding="utf-8") as f:
    json.dump(lofo_channel, f, indent=2)

# --- Exploratory fold: hold out art_only at test ---
exploratory = {
    "split_name": "exploratory_ascii_leak_tier_holdout",
    "seed": SEED,
    "train_leak_tiers": ["art+hint", "art+full_command"],
    "test_leak_tiers": ["art_only"],
    "note": "Within-ASCII generalisation: model sees framed and full-command art at training; tested on art-only samples.",
}
with (SPLITS / "exploratory_ascii_leak_tier.json").open("w", encoding="utf-8") as f:
    json.dump(exploratory, f, indent=2)

# --- Ansi-shadow exploratory fold (block font, held out from training) ---
block_fold = {
    "split_name": "exploratory_ascii_block_font",
    "seed": SEED,
    "train_fonts": ["standard", "slant", "small", "big"],
    "test_fonts": ["ansi_shadow"],
    "note": "Block characters map to [UNK] in MiniLM. Probe set to be generated separately; not present in current manifest.",
}
with (SPLITS / "exploratory_ascii_block_font.json").open("w", encoding="utf-8") as f:
    json.dump(block_fold, f, indent=2)

# --- Cross-family intent coverage check ---
qr_rows = []
if QR_MANIFEST.exists():
    qr_rows = list(csv.DictReader(QR_MANIFEST.open(encoding="utf-8-sig")))
qr_attack_intents = set(
    r["intent_id"] for r in qr_rows
    if r.get("label") == "attack" and r.get("intent_id")
)

coverage = {}
for intent in intents:                 # <-- renamed loop variable from 'iid' to 'intent'
    families_present = {"ascii_art"}
    if intent in qr_attack_intents:
        families_present.add("qr")
    coverage[intent] = {
        "families": sorted(families_present),
        "ascii_art_rows": sum(
            1 for r in rows if r["intent_id"] == intent and r["label"] == "attack"
        ),
        "testable_in_ascii_lofo": len(families_present) > 1,
    }
with (Path("ascii_dataset") / "intent_coverage.json").open("w", encoding="utf-8") as f:
    json.dump(coverage, f, indent=2)

# --- Assign split column to manifest ---
def split_of(intent_id):
    if intent_id in iid_split["train_intents"]:
        return "train"
    if intent_id in iid_split["val_intents"]:
        return "val"
    return "test"

for r in rows:
    r["split"] = split_of(r["intent_id"])

with MANIFEST.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

# --- Report ---
print(f"\nIID split:")
print(f"  train: {len(iid_split['train_intents'])} intents")
print(f"  val:   {len(iid_split['val_intents'])} intents")
print(f"  test:  {len(iid_split['test_intents'])} intents")

testable = sum(1 for v in coverage.values() if v["testable_in_ascii_lofo"])
print(f"\nCross-family coverage:")
print(f"  {testable}/{len(coverage)} intents testable in ASCII LOFO")
missing = [i for i, v in coverage.items() if not v["testable_in_ascii_lofo"]]
if missing:
    print(f"  intents missing a twin in QR/text/homoglyph:")
    for i in missing:
        print(f"    - {i}")

# --- Split composition per set ---
split_counts = defaultdict(Counter)
for r in rows:
    split_counts[r["split"]][r["label"]] += 1

print(f"\nRows per split:")
for s in ("train", "val", "test"):
    c = split_counts[s]
    total = c["attack"] + c["benign"]
    print(f"  {s}: {c['attack']} attack, {c['benign']} benign, total {total}")

print(f"\nWrote:")
print(f"  {SPLITS}/iid.json")
print(f"  {SPLITS}/lofo_channel.json")
print(f"  {SPLITS}/exploratory_ascii_leak_tier.json")
print(f"  {SPLITS}/exploratory_ascii_block_font.json")
print(f"  ascii_dataset/intent_coverage.json")
print(f"  manifest updated with split column")