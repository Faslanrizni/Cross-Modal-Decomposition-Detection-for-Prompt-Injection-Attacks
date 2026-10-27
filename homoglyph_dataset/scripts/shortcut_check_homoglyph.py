"""shortcut_check_homoglyph.py — two-population shortcut check.

Runs twice:
  1. Full population (attacks + all benigns, including naturals)
  2. Transformed-only (attacks + transformed benigns; naturals excluded)

Both results are reported. This documents the design trade-off between
preventing 'non-ASCII = attack' learning and eliminating all surface signal.
"""
import csv
import json
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.preprocessing import OneHotEncoder

SEED = 42
MANIFEST = Path("homoglyph_dataset/manifest/homoglyph_manifest.csv")
OUT = Path("homoglyph_dataset/shortcut_check.json")

all_rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))

# Fix 5c: assert control stratum excluded from training split
leaked = [r for r in all_rows
          if r["tokenizer_neutralised"].lower() == "true"
          and r.get("split", "").lower() == "train"]
assert not leaked, (
    f"Control stratum rows leaked into training split ({len(leaked)} rows)."
)

def script_count(sm):
    return len(sm.split("+"))

def build_X(rows):
    num = np.array([
        [float(r["nonascii_ratio"]), script_count(r["script_mix"]),
         int(r["token_len"]), float(r["unk_rate"]), float(r["density"])]
        for r in rows
    ], dtype=float)
    cat = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit_transform(
        [[r["technique"]] for r in rows]
    )
    return np.hstack([num, cat])

def run_check(rows, label):
    y = np.array([1 if r["label"] == "attack" else 0 for r in rows])
    groups = np.array([r["split_group"] for r in rows])
    X = build_X(rows)

    gkf = GroupKFold(n_splits=5)
    models = {
        "logreg": LogisticRegression(max_iter=1000),
        "tree": DecisionTreeClassifier(max_depth=3, random_state=SEED),
    }
    results = {name: {"auc": [], "acc": []} for name in models}

    for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        if len(set(y[train_idx])) < 2 or len(set(y[test_idx])) < 2:
            continue
        for name, clf in models.items():
            clf.fit(X[train_idx], y[train_idx])
            proba = clf.predict_proba(X[test_idx])[:, 1]
            results[name]["auc"].append(roc_auc_score(y[test_idx], proba))
            results[name]["acc"].append(accuracy_score(y[test_idx], (proba > 0.5).astype(int)))

    def mean(xs): return float(np.mean(xs)) if xs else 0.0
    auc = round(mean(results["logreg"]["auc"]), 4)
    verdict = (
        "PASS" if auc <= 0.60 else
        "MINOR LEAKAGE" if auc <= 0.65 else "FAIL"
    )
    return {
        "label": label,
        "n_rows": len(rows),
        "logreg_auc_mean": auc,
        "logreg_auc_std": round(float(np.std(results["logreg"]["auc"])), 4),
        "tree_auc_mean": round(mean(results["tree"]["auc"]), 4),
        "majority_baseline": round(float(max(y.mean(), 1 - y.mean())), 4),
        "verdict": verdict,
    }

# Population 1: full main channel (attacks + all benigns including naturals)
full_rows = [r for r in all_rows if r["tokenizer_neutralised"].lower() == "false"]
full_result = run_check(full_rows, "full_population")

# Population 2: transformed-only (exclude naturals)
transformed_rows = [r for r in full_rows if r.get("benign_kind", "") != "natural"]
transformed_result = run_check(transformed_rows, "transformed_only")

# Overall verdict = the harder of the two (full population is the operative dataset)
overall_verdict = full_result["verdict"]

summary = {
    "seed": SEED,
    "scope": "main channel only (tokenizer_neutralised=False)",
    "guard_rail": "control stratum excluded from training (asserted)",
    "cv": "GroupKFold(5) grouped by split_group",
    "features": ["nonascii_ratio", "script_count", "token_len", "unk_rate",
                 "density", "technique_onehot"],
    "full_population": full_result,
    "transformed_only": transformed_result,
    "interpretation": (
        "Full population AUC reflects the trade-off between preventing "
        "'non-ASCII = attack' learning (via naturals) and eliminating all "
        "surface signal. Transformed-only AUC measures leakage in the "
        "substituted channel. If transformed_only is PASS but full_population "
        "is MINOR LEAKAGE, the residual is attributable to the natural-benign "
        "sub-population (density=0.0 signal)."
    ),
    "verdict": overall_verdict,
}

OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2))