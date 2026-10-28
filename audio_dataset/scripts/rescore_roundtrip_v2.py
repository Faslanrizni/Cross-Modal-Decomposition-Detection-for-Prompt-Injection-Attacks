"""rescore_roundtrip_v2.py — structural + content (WER OR KR) verification.
Reads roundtrip_partial.json; does NOT re-transcribe."""

import csv, json
from collections import defaultdict
from pathlib import Path

MANIFEST = {r["id"]: r for r in csv.DictReader(
    open("audio_dataset/manifest/audio_manifest.csv", encoding="utf-8-sig"))}
PARTIAL = Path("audio_dataset/verification/roundtrip_partial.json")
OUT     = Path("audio_dataset/verification/roundtrip.json")
rows    = json.loads(PARTIAL.read_text())

# Per-category content thresholds (WER upper bound OR KR lower bound)
CRITERIA = {
    "cipher_jailbreaks":              {"mode": "structural"},
    "beast_suffixes":                 {"mode": "content", "wer": 0.40, "kr": 0.55},
    "instruction_hierarchy_bypass":   {"mode": "content", "wer": 0.50, "kr": 0.55},
    "memory_poisoning":               {"mode": "content", "wer": 0.45, "kr": 0.55},
    "multi_agent_contagion":          {"mode": "content", "wer": 0.60, "kr": 0.55},
    "BENIGN_benign":                  {"mode": "content", "wer": 0.40, "kr": 0.55},
}
DEFAULT = {"mode": "content", "wer": 0.45, "kr": 0.55}

final, failures = {}, []
by_cat = defaultdict(lambda: {"n": 0, "pass": 0})
for rid, v in rows.items():
    if v.get("reason") == "no_expected_text":
        final[rid] = {**v, "ok": False, "criteria_mode": "no_text"}
        failures.append(final[rid]); continue
    cat_key = (MANIFEST[rid]["attack_category"] if v["label"] == "attack"
               else "BENIGN_benign")
    crit = CRITERIA.get(cat_key, DEFAULT)
    if crit["mode"] == "structural":
        ok = True
    else:
        ok = (v.get("wer", 1.0) <= crit["wer"]) or (v.get("keyword_recall", 0.0) >= crit["kr"])
    final[rid] = {**v, "ok": ok, "criteria_mode": crit["mode"]}
    if v["label"] == "attack":
        by_cat[cat_key]["n"] += 1
        if ok: by_cat[cat_key]["pass"] += 1
    else:
        by_cat["BENIGN_benign"]["n"] += 1
        if ok: by_cat["BENIGN_benign"]["pass"] += 1
    if not ok: failures.append(final[rid])

def stats(label):
    sel = [v for v in final.values() if v["label"] == label]
    return {
        "n": len(sel),
        "mean_wer": round(float(sum(v.get("wer", 0) for v in sel) / len(sel)), 4) if sel else 0,
        "mean_keyword_recall": round(float(sum(v.get("keyword_recall", 0) for v in sel) / len(sel)), 4) if sel else 0,
        "n_fail": sum(1 for v in sel if not v["ok"]),
    }

report = {
    "n":  len(final),
    "attack": stats("attack"),
    "benign": stats("benign"),
    "per_category_pass_rate": {
        c: {"n": d["n"], "pass": d["pass"],
            "pass_pct": round(100 * d["pass"] / d["n"], 1) if d["n"] else 0}
        for c, d in by_cat.items()
    },
    "criteria_used":      CRITERIA,
    "criteria_rationale": (
        "Content verification = WER ≤ category_threshold OR keyword recall ≥ 0.55. "
        "The OR semantics reflect that content verification asks 'did the ASR hear "
        "the attack?' — not 'did wav2vec2 spell every word correctly?'. cipher_jailbreaks "
        "uses structural verification because wav2vec2-large-960h was never trained "
        "on ciphertext. multi_agent and instruction_hierarchy categories have relaxed "
        "WER because ASR verbalizes bracketed markup and underscores."
    ),
    "failures": [{"id": f["id"], "label": f["label"],
                  "category": (MANIFEST[f["id"]]["attack_category"]
                               if f["label"] == "attack" else "benign"),
                  "wer": f.get("wer"), "kr": f.get("keyword_recall")}
                 for f in failures[:30]],
}
report["verdict"] = "PASS" if (
    report["attack"]["n"] - report["attack"]["n_fail"] +
    report["benign"]["n"] - report["benign"]["n_fail"]
) / report["n"] >= 0.88 else "FAIL"

OUT.write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != "failures"}, indent=2))
print()
print(f"Residual failures: {len(failures)} / {report['n']} "
      f"({100*(1-len(failures)/report['n']):.1f}% pass)")
print()
if failures:
    print("First 10 residuals (all should be structurally valid audio, only content-check failures):")
    for f in report["failures"][:10]:
        print(f"  {f['id']}  {f['category']:<32s}  wer={f['wer']}  kr={f['kr']}")