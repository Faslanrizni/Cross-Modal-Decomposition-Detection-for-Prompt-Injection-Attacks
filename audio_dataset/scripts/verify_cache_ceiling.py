import json
from collections import defaultdict
from pathlib import Path

c = json.loads(Path("audio_dataset/audio/_benign_cache/index.json").read_text())
ds = [r["duration_s"] for r in c]

print(f"cache entries:  {len(ds)}")
print(f"min:            {min(ds):.2f}")
print(f"max:            {max(ds):.2f}")
print(f">6s:            {sum(1 for d in ds if d > 6)}")
print(f">9s:            {sum(1 for d in ds if d > 9)}")
print(f">10s:           {sum(1 for d in ds if d > 10)}")
print(f">12s:           {sum(1 for d in ds if d > 12)}")
print(f">15s:           {sum(1 for d in ds if d > 15)}")

per_voice = defaultdict(list)
for r in c:
    per_voice[r["voice"]].append(r["duration_s"])
print()
for v, d in per_voice.items():
    print(f"{v}: n={len(d)} max={max(d):.2f} >12s={sum(1 for x in d if x > 12)}")