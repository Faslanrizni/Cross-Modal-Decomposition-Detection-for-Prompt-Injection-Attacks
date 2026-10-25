import csv
from pathlib import Path
from collections import Counter

MANIFEST = Path("ascii_dataset/manifest/ascii_manifest.csv")
FRAGMENTS_OLD = Path("ascii_dataset/manifest/ascii_fragments.csv")
FRAGMENTS_NEW = Path("ascii_dataset/manifest/ascii_fragments_v2.csv")

manifest = {r["id"]: r for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))}
old_frags = list(csv.DictReader(FRAGMENTS_OLD.open(encoding="utf-8-sig")))

new_frags = []
excluded_samples = set()
kept_samples = set()
for f in old_frags:
    sample = manifest.get(f["sample_id"])
    if not sample:
        continue
    if sample["plaintext_leak"] == "art+full_command":
        excluded_samples.add(f["sample_id"])
        continue
    new_frags.append(f)
    kept_samples.add(f["sample_id"])

with FRAGMENTS_NEW.open("w", newline="", encoding="utf-8-sig") as out:
    w = csv.DictWriter(out, fieldnames=list(old_frags[0]))
    w.writeheader()
    w.writerows(new_frags)

print(f"Old fragment rows: {len(old_frags)}")
print(f"New fragment rows: {len(new_frags)}")
print(f"Excluded samples (art+full_command): {len(excluded_samples)}")
print(f"Kept samples: {len(kept_samples)}")
print(f"  (228 art_only + 228 art+hint = 456 kept)")

by_tier = Counter(manifest[f["sample_id"]]["plaintext_leak"] for f in new_frags)
print(f"Tier distribution in new fragments: {dict(by_tier)}")

by_role = Counter(f["fragment_role"] for f in new_frags)
print(f"Role distribution: {dict(by_role)}")

labels = Counter(f["fragment_label_alone"] for f in new_frags)
print(f"Fragment label_alone values: {dict(labels)}")

# Sanity check
assert len(new_frags) == 912, f"Expected 912, got {len(new_frags)}"
assert dict(by_tier) == {"art_only": 456, "art+hint": 456}, f"Unexpected tier distribution: {dict(by_tier)}"
assert set(labels) == {"benign"}, f"Expected all benign, got {dict(labels)}"
print("\n✓ All sanity checks passed")