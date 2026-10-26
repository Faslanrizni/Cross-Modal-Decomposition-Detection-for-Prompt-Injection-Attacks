"""verify_plain.py — six-check verifier for plain text channel."""
import csv
import json
import re
from pathlib import Path
from collections import Counter, defaultdict

MANIFEST = Path("plain_dataset/manifest/plain_manifest.csv")
OUT = Path("plain_dataset/verification")
OUT.mkdir(parents=True, exist_ok=True)

ATTACK_WORDS = re.compile(
    r"ignore|disregard|system prompt|reveal|password|secret|override|"
    r"jailbreak|credential|api[_ ]key|admin|exfiltrat|safety|filter|"
    r"rules|sudo|discard|disable|bypass|hack|hijack|leak|breach|exploit",
    re.I)

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))

# Check 1: no empty text
unchanged_failures = []
for r in rows:
    if not r["text"].strip():
        unchanged_failures.append({"id": r["id"], "reason": "empty text"})

# Check 2: attack-word scan on benign
benign_with_attack = []
for r in rows:
    if r["label"] == "benign":
        m = ATTACK_WORDS.search(r["text"])
        if m:
            benign_with_attack.append({"id": r["id"], "match": m.group()})

# Check 3: dedup within label
seen = defaultdict(list)
for r in rows:
    seen[(r["label"], r["text"])].append(r["id"])
dups_within = {k: v for k, v in seen.items() if len(v) > 1}

# Check 4: dedup across label
cross = defaultdict(set)
for r in rows:
    cross[r["text"]].add(r["label"])
dups_across = {k: list(v) for k, v in cross.items() if len(v) > 1}

# Check 5: distribution comparison
def stats(label):
    sel = [r for r in rows if r["label"] == label]
    lens = [int(r["token_len"]) for r in sel]
    return {"n": len(sel), "mean": round(sum(lens)/len(lens), 2),
            "min": min(lens), "max": max(lens)}

dist = {"attack": stats("attack"), "benign": stats("benign")}

# Check 6: hand-review sample
import random
rng = random.Random(42)
by_label = defaultdict(list)
for r in rows:
    by_label[r["label"]].append(r)
sample = []
for label in ("attack", "benign"):
    n = min(5, len(by_label[label]))
    sample.extend(rng.sample(by_label[label], n))

sample_file = OUT / "hand_review_sample.csv"
with sample_file.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "intent_id", "text",
                "intent_correct", "benign_actually_benign", "notes"])
    for r in sample:
        w.writerow([r["id"], r["label"], r["intent_id"], r["text"][:200], "", "", ""])

report = {
    "n_rows": len(rows),
    "unchanged_failures": unchanged_failures,
    "benign_with_attack_words": benign_with_attack,
    "duplicates_within_label": {str(k): v for k, v in dups_within.items()},
    "duplicates_across_labels": dups_across,
    "distribution": dist,
    "verdict": "PASS" if (
        not unchanged_failures
        and not benign_with_attack
        and not dups_within
        and not dups_across
    ) else "FAIL",
}
(OUT / "verification_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(report, indent=2))
print(f"\nWrote {OUT / 'verification_report.json'}")
print(f"Wrote {sample_file} with {len(sample)} rows for hand review")
print(f"Verdict: {report['verdict']}")