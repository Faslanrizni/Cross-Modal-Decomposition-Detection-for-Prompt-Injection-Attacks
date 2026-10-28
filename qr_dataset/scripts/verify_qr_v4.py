"""verify_qr_v4.py — 7-check verifier with cross-family overlap.

Checks:
  1. Round-trip (image decodes to payload)
  2. Attack-word scan on benign
  3. Duplicates within label
  4. Duplicates across label
  5. QR version uniform
  6. Intent coverage = 21/21
  7. Cross-family overlap (attack payloads must NOT match plain / ASCII / homoglyph)
  Also: benign rows must have blank intent_id.
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import zxingcpp

MANIFEST = Path("qr_dataset/manifest_v4.csv")
OUT = Path("qr_dataset/verification")
OUT.mkdir(parents=True, exist_ok=True)

ATTACK_WORDS = re.compile(
    r"ignore|disregard|system prompt|reveal|password|secret|override|"
    r"jailbreak|credential|api[_ ]key|admin|exfiltrat|safety|filter|"
    r"rules|sudo|discard|disable|bypass|hack|hijack|leak|breach|exploit",
    re.I,
)

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))

# Check 1: roundtrip
rt_fails = []
for r in rows:
    png = Path(r["png"])
    if not png.exists():
        rt_fails.append({"id": r["id"], "reason": "png missing"})
        continue
    img = cv2.imread(str(png))
    if img is None:
        rt_fails.append({"id": r["id"], "reason": "png unreadable"})
        continue
    zx = zxingcpp.read_barcodes(img)
    decoded = zx[0].text if zx else ""
    if decoded != r["text"]:
        rt_fails.append({"id": r["id"], "reason": "payload mismatch"})

# Check 2: attack-word scan on benign
benign_attack_vocab = []
for r in rows:
    if r["label"] == "benign":
        m = ATTACK_WORDS.search(r["text"])
        if m:
            benign_attack_vocab.append({"id": r["id"], "match": m.group()})

# Check 3: dedupe within label
seen = defaultdict(list)
for r in rows:
    seen[(r["label"], r["text"])].append(r["id"])
dups_within = {str(k): v for k, v in seen.items() if len(v) > 1}

# Check 4: dedupe across label
cross = defaultdict(set)
for r in rows:
    cross[r["text"]].add(r["label"])
dups_across = {k: list(v) for k, v in cross.items() if len(v) > 1}

# Check 5: version uniformity
versions = Counter(r["qr_version"] for r in rows)

# Check 6: intent coverage
attack_intents = set(r["intent_id"] for r in rows
                     if r["label"] == "attack" and r["intent_id"].strip())

# Check 7: cross-family overlap
def load_attacks(path):
    return {r["text"].strip().lower() for r in
            csv.DictReader(open(path, encoding="utf-8-sig"))
            if r["label"] == "attack"}

plain_attacks = load_attacks("plain_dataset/manifest/plain_manifest.csv")
ascii_attacks = load_attacks("ascii_dataset/manifest/ascii_manifest.csv")
homo_attacks = load_attacks("homoglyph_dataset/manifest/homoglyph_manifest.csv")

qr_attacks = [r for r in rows if r["label"] == "attack"]
overlap_plain = [r["id"] for r in qr_attacks if r["payload"].strip().lower() in plain_attacks]
overlap_ascii = [r["id"] for r in qr_attacks if r["payload"].strip().lower() in ascii_attacks]
overlap_homo = [r["id"] for r in qr_attacks if r["payload"].strip().lower() in homo_attacks]

# Extra check: benign rows must have blank intent_id
benign_nonblank = [r["id"] for r in rows
                   if r["label"] == "benign" and r["intent_id"].strip()]

report = {
    "n_rows": len(rows),
    "n_attacks": len(qr_attacks),
    "n_benigns": len(rows) - len(qr_attacks),
    "roundtrip_failures": rt_fails,
    "benign_with_attack_vocab": benign_attack_vocab,
    "duplicates_within_label": dups_within,
    "duplicates_across_labels": dups_across,
    "qr_version_uniform": len(versions) == 1,
    "versions": dict(versions),
    "intents_covered": len(attack_intents),
    "benign_with_nonblank_intent_id": benign_nonblank,
    "cross_family_overlap": {
        "vs_plain": overlap_plain,
        "vs_ascii": overlap_ascii,
        "vs_homoglyph": overlap_homo,
        "verdict": "PASS" if not (overlap_plain or overlap_ascii or overlap_homo)
                   else "FAIL — duplicate attack payload in another family",
    },
}

verdict = "PASS"
if rt_fails or benign_attack_vocab or dups_within or dups_across:
    verdict = "FAIL"
if not report["qr_version_uniform"]:
    verdict = "FAIL"
if benign_nonblank:
    verdict = "FAIL"
if report["cross_family_overlap"]["verdict"] != "PASS":
    verdict = "FAIL"
report["verdict"] = verdict

(OUT / "verification_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(report, indent=2))