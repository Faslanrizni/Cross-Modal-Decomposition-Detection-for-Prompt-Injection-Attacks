"""freeze_audio.py — snapshot audio_dataset/ to frozen/audio_v1/.

Preserves decisions.md and CHANGELOG.md across runs. Two ways to author them:
  1. Save them in audio_dataset/ — the script copies them to frozen/audio_v1/
  2. Save them directly in frozen/audio_v1/ — the script preserves them

Run as many times as you like; markdown files are never lost.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

SRC = Path("audio_dataset")
DST = Path("frozen/audio_v1")

if not SRC.exists():
    print(f"ERROR: {SRC} does not exist. Run from the project root.")
    sys.exit(1)

if not (SRC / "manifest" / "audio_manifest.csv").exists():
    print("ERROR: audio_dataset/manifest/audio_manifest.csv missing.")
    sys.exit(1)

# ---------- 1. Preserve any existing markdown in DST ----------
markdown_files = ["decisions.md", "CHANGELOG.md"]
preserved = {}
for f in markdown_files:
    p = DST / f
    if p.exists():
        preserved[f] = p.read_bytes()
        print(f"backup:    {f} ({len(preserved[f])} bytes)")

# ---------- 2. Rebuild frozen folder ----------
if DST.exists():
    shutil.rmtree(DST)
for sub in ("manifest", "verification", "splits", "triage"):
    (DST / sub).mkdir(parents=True)

# ---------- 3. Copy required artefacts ----------
required = {
    "duration_report.json":                    "duration_report.json",
    "shortcut_check.json":                     "shortcut_check.json",
    "preflight_report.json":                   "preflight_report.json",
    "provenance.json":                         "provenance.json",
    "intent_taxonomy.json":                    "intent_taxonomy.json",
    "phrasings.json":                          "phrasings.json",
    "audio_config.json":                       "audio_config.json",
    "manifest/audio_manifest.csv":             "manifest/audio_manifest.csv",
    "triage/triage.csv":                       "triage/triage.csv",
    "triage/exclusions.csv":                   "triage/exclusions.csv",
    "triage/audio_exclusions.csv":             "triage/audio_exclusions.csv",
    "verification/roundtrip.json":             "verification/roundtrip.json",
    "verification/roundtrip_partial.json":     "verification/roundtrip_partial.json",
    "verification/verification_report.json":   "verification/verification_report.json",
    "verification/hand_review_sample.csv":     "verification/hand_review_sample.csv",
    "verification/verification_log.csv":       "verification/verification_log.csv",
}

copied, missing = [], []
for src_rel, dst_rel in required.items():
    s = SRC / src_rel
    if s.exists():
        shutil.copy2(s, DST / dst_rel)
        copied.append(src_rel)
    else:
        missing.append(src_rel)

for p in (SRC / "splits").glob("*.json"):
    shutil.copy2(p, DST / "splits" / p.name)
    copied.append(f"splits/{p.name}")

print(f"\ncopied {len(copied)} data files")

# ---------- 4. Restore / copy markdown files ----------
for f in markdown_files:
    # Priority 1: source in audio_dataset/ (authoring location)
    src_md = SRC / f
    if src_md.exists():
        shutil.copy2(src_md, DST / f)
        print(f"copied:    {f} (from audio_dataset/{f})")
        continue
    # Priority 2: restore the backup we made at the top
    if f in preserved:
        (DST / f).write_bytes(preserved[f])
        print(f"preserved: {f} (from previous frozen/audio_v1/{f})")
        continue
    # Priority 3: nothing to restore
    print(f"MISSING:   {f} — author it before the final freeze "
          f"(save in audio_dataset/{f} or frozen/audio_v1/{f})")

# ---------- 5. Required-files gate ----------
if missing:
    print("\nrequired files missing from source — freeze is INCOMPLETE:")
    for m in missing:
        print(f"  {m}")
    sys.exit(1)

# ---------- 6. Byte-identity check ----------
key_files = [
    "manifest/audio_manifest.csv",
    "shortcut_check.json",
    "audio_config.json",
    "verification/verification_report.json",
    "verification/roundtrip.json",
]
print("\nbyte-identity check (frozen vs live):")
all_same = True
for f in key_files:
    a, b = SRC / f, DST / f
    if not (a.exists() and b.exists()):
        print(f"  SKIP  {f}"); all_same = False; continue
    ha = hashlib.sha256(a.read_bytes()).hexdigest()
    hb = hashlib.sha256(b.read_bytes()).hexdigest()
    status = "SAME" if ha == hb else "DIFF"
    print(f"  {status}  {f}")
    if ha != hb:
        all_same = False

# ---------- 7. Final status ----------
total = sum(1 for _ in DST.rglob("*") if _.is_file())
print(f"\ntotal files in {DST}/: {total}")

md_present = all((DST / f).exists() for f in markdown_files)
if all_same and not missing and md_present:
    print("FREEZE COMPLETE")
    sys.exit(0)
elif all_same and not missing:
    print("FREEZE PENDING: author the missing markdown file(s) and re-run.")
    sys.exit(0)
else:
    print("FREEZE INCOMPLETE: see above.")
    sys.exit(1)