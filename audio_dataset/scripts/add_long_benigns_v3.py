"""Add concatenated long benigns covering the 9-15s band.
Concatenates existing short benigns (2 or 3 at a time) so the output
lengths are deterministic given the phrase pool."""
import json, random
from pathlib import Path

P = Path("audio_dataset/phrasings.json")
data = json.loads(P.read_text(encoding="utf-8"))
short        = data["benign_commands"]
existing     = data.get("benign_commands_long", [])
existing_set = set(existing)

rng = random.Random(42)
new_long = []

# 2-sentence combos, targeting 35-60 words (~9-15s at ~235 wpm)
attempts = 0
while len(new_long) < 50 and attempts < 5000:
    attempts += 1
    i, j = rng.sample(range(len(short)), 2)
    combo = f"{short[i].rstrip('.')}. {short[j]}"
    wc = len(combo.split())
    if 35 <= wc <= 60 and combo not in existing_set and combo not in new_long:
        new_long.append(combo)

# 3-sentence combos, targeting 45-70 words (~11-18s)
attempts = 0
while len(new_long) < 80 and attempts < 5000:
    attempts += 1
    i, j, k = rng.sample(range(len(short)), 3)
    combo = f"{short[i].rstrip('.')}. {short[j].rstrip('.')}. {short[k]}"
    wc = len(combo.split())
    if 45 <= wc <= 70 and combo not in existing_set and combo not in new_long:
        new_long.append(combo)

combined = list(dict.fromkeys(existing + new_long))
data["benign_commands_long"] = combined
P.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"short:  {len(short)}")
print(f"long:   {len(existing)} -> {len(combined)} (+{len(combined)-len(existing)})")
print(f"total:  {len(short) + len(combined)} sentences to render")
print()
print("word-count distribution of the 80 new long benigns:")
import collections
wc_buckets = collections.Counter()
for c in new_long:
    wc = len(c.split())
    bucket = "35-44w" if wc <= 44 else "45-54w" if wc <= 54 else "55-70w"
    wc_buckets[bucket] += 1
for b, n in sorted(wc_buckets.items()):
    print(f"  {b}: {n}")