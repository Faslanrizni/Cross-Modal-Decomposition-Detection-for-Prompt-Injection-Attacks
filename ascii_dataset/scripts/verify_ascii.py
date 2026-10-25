import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

import pyfiglet
from transformers import AutoTokenizer

MANIFEST = Path("ascii_dataset/manifest/ascii_manifest.csv")
OUT = Path("ascii_dataset/verification")
OUT.mkdir(parents=True, exist_ok=True)

TOK = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
ATTACK_WORDS = re.compile(
    r"ignore|disregard|system prompt|reveal|password|secret|override|jailbreak|"
    r"credential|api[_ ]key|admin|exfiltrat|safety|filter|rules|sudo|discard|"
    r"disable|bypass|hack|hijack|leak|breach|exploit",
    re.I)

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))

# 1. Regeneration check
regen_failures = []
for r in rows:
    art = pyfiglet.figlet_format(r["art_word"], font=r["ascii_font"]).rstrip()
    if not art.strip():
        regen_failures.append(r["id"])
    elif r["label"] == "attack" and art not in r["text"]:
        regen_failures.append(r["id"])

# 2. Attack-word scan on benign
benign_with_attack = []
for r in rows:
    if r["label"] == "benign":
        m = ATTACK_WORDS.search(r["text"])
        if m:
            benign_with_attack.append({"id": r["id"], "match": m.group()})

# 3. Dedup
seen = defaultdict(list)
for r in rows:
    seen[(r["label"], r["text"])].append(r["id"])
dups_within = {k: v for k, v in seen.items() if len(v) > 1}
cross = defaultdict(set)
for r in rows:
    cross[r["text"]].add(r["label"])
dups_across = {k: list(v) for k, v in cross.items() if len(v) > 1}

# 4. Distribution comparison
def stats(label):
    sel = [r for r in rows if r["label"] == label]
    lens = [int(r["token_len"]) for r in sel]
    return {"n": len(sel), "mean": round(sum(lens)/len(lens), 2),
            "min": min(lens), "max": max(lens)}

dist = {"attack": stats("attack"), "benign": stats("benign")}

# 5. Block-char audit
block_audit = {}
for art in ["██████╗", "██╔══██╗", "╔══╗"]:
    block_audit[art] = TOK.tokenize(art)

report = {
    "n_rows": len(rows),
    "regen_failures": regen_failures,
    "benign_with_attack_words": benign_with_attack,
    "duplicates_within_label": {str(k): v for k, v in dups_within.items()},
    "duplicates_across_labels": dups_across,
    "distribution": dist,
    "block_char_tokenization": block_audit,
    "verdict": "PASS" if not regen_failures and not benign_with_attack
                          and not dups_within and not dups_across else "FAIL",
}
(OUT / "verification_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(json.dumps({k: v for k, v in report.items() if k != "block_char_tokenization"},
                 indent=2, ensure_ascii=False))
print("Block-char tokenization:")
for k, v in block_audit.items():
    print(f"  {k!r} -> {v}")

# 6. Hand-review sample (40 rows, stratified)
import random
rng = random.Random(42)
stratified = []
for label in ("attack", "benign"):
    for leak in ("art_only", "art+hint", "art+full_command"):
        pool = [r for r in rows if r["label"] == label and r["plaintext_leak"] == leak]
        if pool:
            stratified.append(rng.choice(pool))
            stratified.append(rng.choice(pool))
# top up to 40
remaining = [r for r in rows if r not in stratified]
rng.shuffle(remaining)
sample = stratified + remaining[:max(0, 40 - len(stratified))]

sample_file = OUT / "hand_review_sample.csv"
with sample_file.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "label", "plaintext_leak", "text",
                "art_decodes", "intent_correct",
                "benign_actually_benign", "leak_tier_correct", "notes"])
    for r in sample:
        w.writerow([r["id"], r["label"], r["plaintext_leak"], r["text"][:250],
                    "", "", "", "", ""])

print(f"\nWrote {sample_file} with {len(sample)} rows for hand review")
print(f"Verdict: {report['verdict']}")