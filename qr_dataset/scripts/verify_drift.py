"""verify_drift.py — strict per-row drift check for QR expansion."""
import csv
from pathlib import Path

V3 = Path("qr_dataset/manifest_v3.csv")
V4 = Path("qr_dataset/manifest_v4.csv")

FROZEN_ASCII = Path("frozen/ascii_v1/manifest/ascii_manifest.csv")
LIVE_ASCII = Path("ascii_dataset/manifest/ascii_manifest.csv")
FROZEN_PLAIN = Path("frozen/plain_v2/manifest/plain_manifest.csv")
LIVE_PLAIN = Path("plain_dataset/manifest/plain_manifest.csv")
FROZEN_HOMO = Path("frozen/homoglyph_v1/manifest/homoglyph_manifest.csv")
LIVE_HOMO = Path("homoglyph_dataset/manifest/homoglyph_manifest.csv")

v3 = {r["id"]: r for r in csv.DictReader(V3.open(encoding="utf-8-sig"))}
v4 = {r["id"]: r for r in csv.DictReader(V4.open(encoding="utf-8-sig"))}

missing = [sid for sid in v3 if sid not in v4]
print(f"Old rows missing from v4: {len(missing)}")
if missing:
    print(f"  {missing[:5]}")

split_changes = []
for sid, old in v3.items():
    if sid in v4 and v4[sid]["split"] != old["split"]:
        split_changes.append((sid, old["split"], v4[sid]["split"]))
print(f"Old-row split changes: {len(split_changes)}")
if split_changes:
    for s in split_changes[:5]:
        print(f"  {s}")

png_changes = []
for sid, old in v3.items():
    if sid in v4 and v4[sid]["png_sha256"] != old["png_sha256"]:
        png_changes.append((sid, old["png_sha256"][:12], v4[sid]["png_sha256"][:12]))
print(f"Old-row png_sha256 changes: {len(png_changes)}")
if png_changes:
    for p in png_changes[:5]:
        print(f"  {p}")

def check_family(live_path, frozen_path, family):
    live = {r["id"]: r["split"] for r in
            csv.DictReader(live_path.open(encoding="utf-8-sig"))}
    frozen = list(csv.DictReader(frozen_path.open(encoding="utf-8-sig")))
    diffs = [(r["id"], r["split"], live.get(r["id"]))
             for r in frozen if r["split"] != live.get(r["id"])]
    print(f"{family} drift: {len(diffs)}/{len(frozen)}")

check_family(LIVE_ASCII, FROZEN_ASCII, "ascii_art")
check_family(LIVE_PLAIN, FROZEN_PLAIN, "plain")
check_family(LIVE_HOMO, FROZEN_HOMO, "homoglyph")