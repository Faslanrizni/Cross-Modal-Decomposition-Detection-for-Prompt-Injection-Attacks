import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import zxingcpp
from transformers import AutoTokenizer

MANIFEST = Path("qr_dataset/manifest_v3.csv")
OUT = Path("qr_dataset/verification")
OUT.mkdir(parents=True, exist_ok=True)

TOK = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
ATTACK_WORDS = re.compile(
    r"ignore|disregard|system prompt|reveal|password|secret|override|jailbreak|"
    r"credential|api[_ ]key|admin|exfiltrat|safety|filter|rules|sudo|discard|"
    r"disable|bypass|hack|hijack|leak|breach|exploit",
    re.I)

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))

# Check 1 — Round-trip regeneration
roundtrip_failures = []
for r in rows:
    png = Path(r["png"])
    if not png.exists():
        roundtrip_failures.append({"id": r["id"], "reason": "PNG missing"})
        continue
    img = cv2.imread(str(png))
    if img is None:
        roundtrip_failures.append({"id": r["id"], "reason": "PNG unreadable"})
        continue
    zx = zxingcpp.read_barcodes(img)
    decoded = zx[0].text if zx else ""
    if decoded != r["text"]:
        roundtrip_failures.append({
            "id": r["id"], "reason": "payload mismatch",
            "expected": r["text"][:60], "decoded": decoded[:60],
        })

# Check 2 — Attack-word scan on benign
benign_with_attack = []
for r in rows:
    if r["label"] == "benign":
        m = ATTACK_WORDS.search(r["text"])
        if m:
            benign_with_attack.append({"id": r["id"], "match": m.group()})

# Check 3 — Deduplication
seen = defaultdict(list)
for r in rows:
    seen[(r["label"], r["text"])].append(r["id"])
dups_within = {k: v for k, v in seen.items() if len(v) > 1}
cross = defaultdict(set)
for r in rows:
    cross[r["text"]].add(r["label"])
dups_across = {k: list(v) for k, v in cross.items() if len(v) > 1}

# Check 4 — Distribution comparison
def stats(label):
    sel = [r for r in rows if r["label"] == label]
    lens = [int(r["token_len"]) for r in sel]
    return {"n": len(sel), "mean": round(sum(lens)/len(lens), 2),
            "min": min(lens), "max": max(lens)}

dist = {"attack": stats("attack"), "benign": stats("benign")}

# Check 5 — QR version uniformity
versions = sorted(set(int(r["qr_version"]) for r in rows))

# Check 6 — Hand-review sampling
import random
rng = random.Random(42)
by_label = defaultdict(list)
for r in rows:
    by_label[r["label"]].append(r)
sample = []
for label in ("attack", "benign"):
    pool = by_label[label]
    n = min(20, len(pool))
    sample.extend(rng.sample(pool, n))

sample_file = OUT / "hand_review_sample.csv"
with sample_file.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "intent_id", "text",
                "payload_visible", "intent_correct",
                "benign_actually_benign", "notes"])
    for r in sample:
        w.writerow([r["id"], r["label"], r["intent_id"], r["text"][:200],
                    "", "", "", ""])

report = {
    "n_rows": len(rows),
    "roundtrip_failures": roundtrip_failures,
    "benign_with_attack_words": benign_with_attack,
    "duplicates_within_label": {str(k): v for k, v in dups_within.items()},
    "duplicates_across_labels": dups_across,
    "distribution": dist,
    "qr_versions": versions,
    "qr_version_uniform": len(versions) == 1,
    "verdict": "PASS" if (
        not roundtrip_failures
        and not benign_with_attack
        and not dups_within
        and not dups_across
        and len(versions) == 1
    ) else "FAIL",
}

report_file = OUT / "verification_report.json"
report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(report, indent=2))
print(f"\nWrote {report_file}")
print(f"Wrote {sample_file} ({len(sample)} rows for hand review)")