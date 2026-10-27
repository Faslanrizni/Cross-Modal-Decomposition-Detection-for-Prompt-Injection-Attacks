"""verify_map.py — validate homoglyph_map.json structure and consistency."""
import json
import sys
from pathlib import Path

MAP = Path("homoglyph_dataset/homoglyph_map.json")

if not MAP.exists():
    sys.exit(f"ERROR: {MAP} not found. Run from project root.")

try:
    hmap = json.loads(MAP.read_text(encoding="utf-8"))
except UnicodeDecodeError as e:
    sys.exit(f"ERROR: {MAP} is not valid UTF-8: {e}")

main = [k for k, v in hmap["techniques"].items() if v["channel"] == "main"]
control = [k for k, v in hmap["techniques"].items() if v["channel"] == "control"]
excluded = hmap["excluded"]

print(f"File: {MAP}")
print(f"  Main techniques:    {main}")
print(f"  Control techniques: {control}")
print(f"  Excluded techniques: {len(excluded)}")

errors = []

if set(main) != {"cyrillic", "greek"}:
    errors.append(f"Main techniques should be cyrillic+greek, got {main}")
if set(control) != {"zero_width", "combining", "unicode_tags"}:
    errors.append(f"Control techniques should be zero_width+combining+unicode_tags, got {control}")

for tech_name in main:
    spec = hmap["techniques"][tech_name]
    fwd = spec["forward"]
    inv = spec["inverse"]

    print(f"\n  {tech_name}:")
    print(f"    forward map size: {len(fwd)}")
    print(f"    inverse map size: {len(inv)}")

    for latin, look in fwd.items():
        if inv.get(look) != latin:
            errors.append(f"{tech_name}: forward[{latin!r}]={look!r}, inverse[{look!r}]={inv.get(look)!r} (expected {latin!r})")

    for look, latin in inv.items():
        if look not in fwd.values():
            errors.append(f"{tech_name}: inverse key {look!r} not in forward values")

    targets = list(fwd.values())
    if len(targets) != len(set(targets)):
        from collections import Counter
        dupes = {t: c for t, c in Counter(targets).items() if c > 1}
        errors.append(f"{tech_name}: duplicate lookalike targets {dupes}")

    print(f"    Sample mappings:")
    for latin, look in list(fwd.items())[:5]:
        print(f"      {latin} -> {look}")

print()
if errors:
    print("VALIDATION FAILED:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
else:
    print("VALIDATION PASSED — all maps are consistent.")
    sys.exit(0)