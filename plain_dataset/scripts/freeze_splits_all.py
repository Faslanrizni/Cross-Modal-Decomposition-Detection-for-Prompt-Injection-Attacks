"""freeze_splits_all.py — v2 (3-family aware, split_group support).

For each row, split assignment is based on:
  - split_group if present and non-empty (plain channel)
  - intent_id otherwise (ASCII, QR, and plain attacks)
"""
import csv
import json
import random
from pathlib import Path

SEED = 42
MANIFESTS = {
    "ascii_art": Path("ascii_dataset/manifest/ascii_manifest.csv"),
    "qr": Path("qr_dataset/manifest_v3.csv"),
    "plain": Path("plain_dataset/manifest/plain_manifest.csv"),
}

def row_intent(r):
    """Return the intent key for split assignment."""
    sg = r.get("split_group", "").strip()
    if sg:
        return sg
    return r.get("intent_id", "").strip()

family_rows = {}
for family, path in MANIFESTS.items():
    if not path.exists():
        print(f"SKIP: {family} ({path} not found)")
        continue
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    family_rows[family] = rows
    print(f"Loaded {family}: {len(rows)} rows")

family_attack_intents = {
    family: set(row_intent(r) for r in rows if r["label"] == "attack" and row_intent(r))
    for family, rows in family_rows.items()
}
all_intents = sorted(set().union(*family_attack_intents.values()))
print(f"Total intents: {len(all_intents)}")

rng = random.Random(SEED)
shuffled = all_intents[:]
rng.shuffle(shuffled)
n = len(shuffled)
train_n = int(n * 0.70)
val_n = int(n * 0.85)
iid = {
    "split_name": "iid_all_families", "seed": SEED, "grouped_by": "intent_id",
    "families": sorted(family_rows.keys()),
    "train_intents": shuffled[:train_n],
    "val_intents": shuffled[train_n:val_n],
    "test_intents": shuffled[val_n:],
}
Path("plain_dataset/splits").mkdir(parents=True, exist_ok=True)
(Path("plain_dataset/splits") / "iid_all_families.json").write_text(
    json.dumps(iid, indent=2), encoding="utf-8")

for held_out in family_rows:
    lofo = {
        "split_name": f"lofo_{held_out}_held_out", "seed": SEED,
        "test_families": [held_out],
        "train_families": [f for f in family_rows if f != held_out],
    }
    (Path("plain_dataset/splits") / f"lofo_{held_out}_held_out.json").write_text(
        json.dumps(lofo, indent=2), encoding="utf-8")

coverage = {}
for intent in all_intents:
    families_with_intent = [
        f for f, intents in family_attack_intents.items() if intent in intents
    ]
    coverage[intent] = {
        "families": families_with_intent,
        "counts": {f: sum(1 for r in family_rows[f]
                          if row_intent(r) == intent and r["label"] == "attack")
                   for f in families_with_intent},
    }
    for f in family_rows:
        coverage[intent][f"testable_in_{f}_lofo"] = (
            f in families_with_intent and len(families_with_intent) > 1
        )

coverage_dirs = {"ascii_art": "ascii_dataset", "qr": "qr_dataset", "plain": "plain_dataset"}
for family, cdir in coverage_dirs.items():
    if family in family_rows:
        (Path(cdir) / "intent_coverage.json").write_text(
            json.dumps(coverage, indent=2), encoding="utf-8")

def split_of(intent_key):
    if intent_key in iid["train_intents"]: return "train"
    if intent_key in iid["val_intents"]: return "val"
    return "test"

for family, rows in family_rows.items():
    for r in rows:
        r["split"] = split_of(row_intent(r))
    path = MANIFESTS[family]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

print()
print("=" * 60)
print("SPLIT INTEGRITY REPORT")
print("=" * 60)
print(f"Total intents: {len(all_intents)}")
print(f"  train: {len(iid['train_intents'])}, val: {len(iid['val_intents'])}, test: {len(iid['test_intents'])}")
print()
print("Coverage per family:")
for family in family_rows:
    testable = sum(1 for v in coverage.values() if v.get(f"testable_in_{family}_lofo"))
    print(f"  {family}: {testable}/{len(all_intents)}")