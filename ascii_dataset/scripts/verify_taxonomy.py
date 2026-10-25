"""
verify_taxonomy.py confirms:

21 unique intent IDs

All art words render in all 4 training fonts

All category IDs exist

Why this comes before generation: the taxonomy is the contract. The generator reads from it. If you wrote it after generation, the data would shape the taxonomy rather than the taxonomy shaping the data — a form of leakage

"""

import json, pyfiglet
from pathlib import Path

TAXONOMY = Path("ascii_dataset/intent_taxonomy.json")
TRAIN_FONTS = ["standard", "slant", "small", "big"]

t = json.loads(TAXONOMY.read_text(encoding="utf-8"))

# Check 1: unique intent IDs
ids = [i["intent_id"] for i in t["intents"]]
assert len(ids) == len(set(ids)), f"duplicate intent_id: {ids}"

# Check 2: every intent has art_word_candidates
for i in t["intents"]:
    assert i.get("art_word_candidates"), f"{i['intent_id']} has no art words"

# Check 3: every category_id used exists in categories
cats = {c["category_id"] for c in t["categories"]}
for i in t["intents"]:
    assert i["category_id"] in cats, f"{i['intent_id']} has unknown category"

# Check 4: every art word renders in every training font
failures = []
for i in t["intents"]:
    for w in i["art_word_candidates"]:
        for f in TRAIN_FONTS:
            try:
                art = pyfiglet.figlet_format(w, font=f)
            except Exception as e:
                failures.append((i["intent_id"], w, f, str(e)))
                continue
            if not art.strip():
                failures.append((i["intent_id"], w, f, "empty render"))

if failures:
    print("FAIL: some art words do not render:")
    for row in failures:
        print("  ", row)
    raise SystemExit(1)

print(f"PASS: {len(ids)} unique intents")
print(f"PASS: all intents have art_word_candidates")
print(f"PASS: all category_ids valid")
print(f"PASS: all art words render in all {len(TRAIN_FONTS)} training fonts")
print(f"  fonts: {TRAIN_FONTS}")