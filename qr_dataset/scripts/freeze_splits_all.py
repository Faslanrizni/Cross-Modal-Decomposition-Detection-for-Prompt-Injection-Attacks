import csv, json, random
from collections import defaultdict, Counter
from pathlib import Path

SEED = 42
QR_MANIFEST = Path("qr_dataset/manifest_v3.csv")
ASCII_MANIFEST = Path("ascii_dataset/manifest/ascii_manifest.csv")
QR_SPLITS = Path("qr_dataset/splits")
ASCII_SPLITS = Path("ascii_dataset/splits")
QR_SPLITS.mkdir(exist_ok=True)

qr_rows = list(csv.DictReader(QR_MANIFEST.open(encoding="utf-8-sig")))
ascii_rows = list(csv.DictReader(ASCII_MANIFEST.open(encoding="utf-8-sig")))

# Gather all intents across both families
all_intents = sorted(set(
    r["intent_id"] for r in qr_rows + ascii_rows
    if r["label"] == "attack" and r["intent_id"]
))

rng = random.Random(SEED)
shuffled = all_intents[:]
rng.shuffle(shuffled)
n = len(shuffled)
train_n = int(n * 0.70)
val_n = int(n * 0.85)

iid = {
    "split_name": "iid_all_families",
    "seed": SEED,
    "grouped_by": "intent_id",
    "train_intents": shuffled[:train_n],
    "val_intents": shuffled[train_n:val_n],
    "test_intents": shuffled[val_n:],
    "families": ["qr", "ascii_art"],
}

(QR_SPLITS / "iid_all_families.json").write_text(json.dumps(iid, indent=2), encoding="utf-8")

# LOFO QR held out
lofo_qr = {
    "split_name": "lofo_qr_held_out",
    "seed": SEED,
    "test_families": ["qr"],
    "train_families": ["ascii_art"],
    "note": "QR is the held-out channel family for RQ1. Train on ASCII, test on QR.",
}
(QR_SPLITS / "lofo_qr_held_out.json").write_text(json.dumps(lofo_qr, indent=2), encoding="utf-8")

# LOFO ASCII held out (symmetry check)
lofo_ascii = {
    "split_name": "lofo_ascii_held_out",
    "seed": SEED,
    "test_families": ["ascii_art"],
    "train_families": ["qr"],
    "note": "Symmetric counter-test: hold out ASCII, train on QR.",
}
(QR_SPLITS / "lofo_ascii_held_out.json").write_text(json.dumps(lofo_ascii, indent=2), encoding="utf-8")

# Cross-family coverage
qr_attack_intents = set(
    r["intent_id"] for r in qr_rows
    if r["label"] == "attack" and r["intent_id"]
)
ascii_attack_intents = set(
    r["intent_id"] for r in ascii_rows
    if r["label"] == "attack" and r["intent_id"]
)

coverage = {}
for intent in all_intents:
    families = []
    if intent in qr_attack_intents:
        families.append("qr")
    if intent in ascii_attack_intents:
        families.append("ascii_art")
    coverage[intent] = {
        "families": families,
        "qr_rows": sum(1 for r in qr_rows if r["intent_id"] == intent and r["label"] == "attack"),
        "ascii_art_rows": sum(1 for r in ascii_rows if r["intent_id"] == intent and r["label"] == "attack"),
        "testable_in_qr_lofo": ("qr" in families) and (len(families) >= 2),
        "testable_in_ascii_lofo": ("ascii_art" in families) and (len(families) >= 2),
    }
(Path("qr_dataset") / "intent_coverage.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")

# Populate split column in both manifests
def split_of(intent_id):
    if intent_id in iid["train_intents"]:
        return "train"
    if intent_id in iid["val_intents"]:
        return "val"
    return "test"

for r in qr_rows:
    r["split"] = split_of(r["intent_id"])
with QR_MANIFEST.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(qr_rows[0]))
    w.writeheader()
    w.writerows(qr_rows)

for r in ascii_rows:
    r["split"] = split_of(r["intent_id"])
with ASCII_MANIFEST.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(ascii_rows[0]))
    w.writeheader()
    w.writerows(ascii_rows)

# Report
print(f"Total intents (both families): {len(all_intents)}")
print(f"  train: {len(iid['train_intents'])}")
print(f"  val:   {len(iid['val_intents'])}")
print(f"  test:  {len(iid['test_intents'])}")

print(f"\nCoverage:")
testable_qr = sum(1 for v in coverage.values() if v["testable_in_qr_lofo"])
testable_ascii = sum(1 for v in coverage.values() if v["testable_in_ascii_lofo"])
print(f"  testable in QR LOFO:    {testable_qr}/{len(coverage)}")
print(f"  testable in ASCII LOFO: {testable_ascii}/{len(coverage)}")

print(f"\nQR rows by split:")
split_counts = Counter(r["split"] for r in qr_rows)
for s in ("train", "val", "test"):
    print(f"  {s}: {split_counts[s]}")

print(f"\nASCII rows by split:")
split_counts = Counter(r["split"] for r in ascii_rows)
for s in ("train", "val", "test"):
    print(f"  {s}: {split_counts[s]}")

print(f"\nWrote:")
print(f"  {QR_SPLITS}/iid_all_families.json")
print(f"  {QR_SPLITS}/lofo_qr_held_out.json")
print(f"  {QR_SPLITS}/lofo_ascii_held_out.json")
print(f"  qr_dataset/intent_coverage.json")
testable_qr = sum(1 for v in coverage.values() if v["testable_in_qr_lofo"])
testable_ascii = sum(1 for v in coverage.values() if v["testable_in_ascii_lofo"])
print(f"Coverage:")
print(f"  testable in QR LOFO:    {testable_qr}/{len(coverage)}")
print(f"  testable in ASCII LOFO: {testable_ascii}/{len(coverage)}")