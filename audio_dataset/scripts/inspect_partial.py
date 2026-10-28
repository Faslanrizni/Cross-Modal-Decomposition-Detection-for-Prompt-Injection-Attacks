"""inspect_partial.py — diagnose the round-trip failures.
Distinguishes no_expected_text (bug) from wer_or_kr (real ASR mismatch)."""
import json, csv
from collections import Counter, defaultdict
from pathlib import Path

partial = json.loads(
    Path("audio_dataset/verification/roundtrip_partial.json").read_text())
manifest = {r["id"]: r for r in csv.DictReader(
    open("audio_dataset/manifest/audio_manifest.csv", encoding="utf-8-sig"))}

print(f"total rows:  {len(partial)}")
failed = [v for v in partial.values() if not v["ok"]]
print(f"failed:      {len(failed)}")
print(f"by label:    {dict(Counter(v['label'] for v in failed))}")
print(f"by reason:   {dict(Counter(v.get('reason', 'wer_or_kr') for v in failed))}")
print()

# Per-category breakdown
print("Per-category pass rate (attacks):")
cat_total, cat_fail = defaultdict(int), defaultdict(int)
for v in partial.values():
    if v["label"] != "attack": continue
    cat = manifest[v["id"]]["attack_category"]
    cat_total[cat] += 1
    if not v["ok"]: cat_fail[cat] += 1
for c in sorted(cat_total):
    n = cat_total[c]; f = cat_fail[c]
    print(f"  {c:35s} {n-f:>4}/{n:<4} pass ({100*(n-f)/n:.1f}%)")
print()

# Sample: 3 benign failures with their hypotheses
print("=== 3 benign failures (reference vs hypothesis) ===")
benign_fails = [v for v in failed if v["label"] == "benign"]
for v in benign_fails[:3]:
    print(f"  {v['id']}  wer={v.get('wer')}  kr={v.get('keyword_recall')}")
    print(f"    reason: {v.get('reason','wer_or_kr')}")
    print(f"    hyp:    {v.get('hyp','')[:150]!r}")
print()

# Sample: 3 benign successes (to compare)
print("=== 3 benign successes ===")
benign_ok = [v for v in partial.values() if v["ok"] and v["label"] == "benign"]
for v in benign_ok[:3]:
    print(f"  {v['id']}  wer={v.get('wer')}  kr={v.get('keyword_recall')}")
print()

# Sample: 2 attack failures per category
print("=== attack failures (2 per category, with hypotheses) ===")
by_cat = defaultdict(list)
for v in failed:
    if v["label"] != "attack": continue
    by_cat[manifest[v["id"]]["attack_category"]].append(v)
for c in sorted(by_cat):
    print(f"\n[{c}]")
    for v in by_cat[c][:2]:
        print(f"  {v['id']}  wer={v.get('wer')}  kr={v.get('keyword_recall')}")
        print(f"    hyp: {v.get('hyp','')[:150]!r}")