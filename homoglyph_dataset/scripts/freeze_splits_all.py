"""freeze_splits_all.py — 4-family split freezer v2.

Fixes:
  Process A: reads existing iid_all_families.json instead of re-shuffling
  Process D: technique-held-out splits also constrain intents (not just technique)
"""
import csv
import json
from pathlib import Path

SEED = 42
MANIFESTS = {
    "ascii_art": Path("ascii_dataset/manifest/ascii_manifest.csv"),
    "qr": Path("qr_dataset/manifest_v4.csv"),
    "plain": Path("plain_dataset/manifest/plain_manifest.csv"),
    "homoglyph": Path("homoglyph_dataset/manifest/homoglyph_manifest.csv"),
}

def row_intent(r):
    sg = r.get("split_group", "").strip()
    return sg if sg else r.get("intent_id", "").strip()

def row_for_coverage(family, r):
    if family == "homoglyph":
        return r.get("tokenizer_neutralised", "").lower() != "true"
    return True

family_rows = {}
for family, path in MANIFESTS.items():
    if not path.exists():
        print(f"SKIP: {family}")
        continue
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    coverage_rows = [r for r in rows if row_for_coverage(family, r)]
    family_rows[family] = {"all": rows, "for_coverage": coverage_rows}
    print(f"Loaded {family}: {len(rows)} rows ({len(coverage_rows)} for coverage)")

family_attack_intents = {
    family: set(row_intent(r) for r in data["for_coverage"]
                if r["label"] == "attack" and row_intent(r))
    for family, data in family_rows.items()
}
all_intents = sorted(set().union(*family_attack_intents.values()))
print(f"Total intents: {len(all_intents)}")

# Process A: read existing IID split
SPLITS_FILE = Path("plain_dataset/splits/iid_all_families.json")
if SPLITS_FILE.exists():
    iid = json.loads(SPLITS_FILE.read_text(encoding="utf-8"))
    print(f"Loaded existing IID split ({len(iid['train_intents'])} train, "
          f"{len(iid['val_intents'])} val, {len(iid['test_intents'])} test)")
else:
    import random
    rng = random.Random(SEED)
    shuffled = all_intents[:]
    rng.shuffle(shuffled)
    n = len(shuffled)
    train_n, val_n = int(n * 0.70), int(n * 0.85)
    iid = {
        "split_name": "iid_all_families", "seed": SEED, "grouped_by": "split_group",
        "families": sorted(family_rows.keys()),
        "train_intents": shuffled[:train_n],
        "val_intents": shuffled[train_n:val_n],
        "test_intents": shuffled[val_n:],
    }
    print("Created new IID split (first run)")

Path("homoglyph_dataset/splits").mkdir(parents=True, exist_ok=True)
(Path("homoglyph_dataset/splits") / "iid_all_families.json").write_text(
    json.dumps(iid, indent=2), encoding="utf-8")

# Channel LOFO
for held_out in family_rows:
    lofo = {
        "split_name": f"lofo_{held_out}_held_out", "seed": SEED,
        "test_families": [held_out],
        "train_families": [f for f in family_rows if f != held_out],
    }
    (Path("homoglyph_dataset/splits") / f"lofo_{held_out}_held_out.json").write_text(
        json.dumps(lofo, indent=2), encoding="utf-8")

# Process D: technique-held-out ALSO groups by intent
if "homoglyph" in family_rows:
    hg = family_rows["homoglyph"]["for_coverage"]
    techs = sorted(set(r["technique"] for r in hg if r["label"] == "attack"))
    for held_out_tech in techs:
        split = {
            "split_name": f"lofo_homoglyph_technique_{held_out_tech}",
            "seed": SEED,
            "test_techniques": [held_out_tech],
            "train_techniques": [t for t in techs if t != held_out_tech],
            "test_intents": iid["test_intents"],
            "train_intents": iid["train_intents"] + iid["val_intents"],
        }
        (Path("homoglyph_dataset/splits") / f"lofo_homoglyph_technique_{held_out_tech}.json").write_text(
            json.dumps(split, indent=2), encoding="utf-8")

# Coverage
coverage = {}
for intent in all_intents:
    families_with_intent = [f for f, ints in family_attack_intents.items() if intent in ints]
    coverage[intent] = {
        "families": families_with_intent,
        "counts": {f: sum(1 for r in family_rows[f]["for_coverage"]
                          if row_intent(r) == intent and r["label"] == "attack")
                   for f in families_with_intent},
    }
    for f in family_rows:
        coverage[intent][f"testable_in_{f}_lofo"] = (
            f in families_with_intent and len(families_with_intent) > 1
        )

coverage_dirs = {"ascii_art": "ascii_dataset", "qr": "qr_dataset",
                 "plain": "plain_dataset", "homoglyph": "homoglyph_dataset"}
for family, cdir in coverage_dirs.items():
    if family in family_rows:
        (Path(cdir) / "intent_coverage.json").write_text(
            json.dumps(coverage, indent=2), encoding="utf-8")

def split_of(key):
    if key in iid["train_intents"]: return "train"
    if key in iid["val_intents"]: return "val"
    return "test"

for family, data in family_rows.items():
    for r in data["all"]:
        if not r.get("split", "").strip():  # only fill empty splits
            r["split"] = split_of(row_intent(r))
    path = MANIFESTS[family]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(data["all"][0]))
        w.writeheader()
        w.writerows(data["all"])

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