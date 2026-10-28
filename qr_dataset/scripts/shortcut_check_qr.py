"""shortcut_check_qr.py — surface-invariance check for the QR channel.

Groups by split_group (not intent_id), because new benign rows have blank
intent_id per Fix 5. split_group is populated on both rows of every pair.
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
MANIFEST = Path("qr_dataset/manifest_v4.csv")
OUT = Path("qr_dataset/shortcut_check.json")

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
y = np.array([1 if r["label"] == "attack" else 0 for r in rows])
groups = np.array([r["split_group"] for r in rows])  # ← was intent_id

def trailing_ws(t): return len(t) - len(t.rstrip())
def leading_ws(t): return len(t) - len(t.lstrip())

num = np.array([
    [int(r["token_len"]), int(r["text_len"]), int(r["qr_version"]),
     trailing_ws(r["text"]), leading_ws(r["text"])]
    for r in rows
], dtype=float)

cat = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit_transform(
    [[r["format"]] for r in rows]
)
X = np.hstack([num, cat])

print(f"X shape: {X.shape}, y: {y.shape}")
print(f"unique split_groups: {len(set(groups))}")
print(f"label balance: attack={int(y.sum())}, benign={int(len(y) - y.sum())}")

n_folds = min(5, len(set(groups)))
gkf = GroupKFold(n_splits=n_folds)
models = {
    "logreg": LogisticRegression(max_iter=1000),
    "tree": DecisionTreeClassifier(max_depth=3, random_state=SEED),
}
results = {name: {"auc": [], "acc": []} for name in models}

for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
    if len(set(y[train_idx])) < 2 or len(set(y[test_idx])) < 2:
        print(f"  fold {fold} SKIPPED: single class in train or test")
        continue
    for name, clf in models.items():
        clf.fit(X[train_idx], y[train_idx])
        proba = clf.predict_proba(X[test_idx])[:, 1]
        results[name]["auc"].append(roc_auc_score(y[test_idx], proba))
        results[name]["acc"].append(accuracy_score(y[test_idx], (proba > 0.5).astype(int)))
        print(f"  fold {fold} {name}: AUC={results[name]['auc'][-1]:.3f}")

def mean(xs): return float(np.mean(xs)) if xs else 0.0

summary = {
    "seed": SEED,
    "cv": f"GroupKFold(n_splits={n_folds}) grouped by split_group",
    "logreg_auc_mean": round(mean(results["logreg"]["auc"]), 4),
    "logreg_auc_std": round(float(np.std(results["logreg"]["auc"])), 4),
    "tree_auc_mean": round(mean(results["tree"]["auc"]), 4),
    "majority_baseline": round(float(max(y.mean(), 1 - y.mean())), 4),
    "n_folds_used": len(results["logreg"]["auc"]),
}
auc = summary["logreg_auc_mean"]
summary["verdict"] = (
    "PASS" if auc <= 0.60 else
    "MINOR LEAKAGE" if auc <= 0.65 else "FAIL"
)

OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print()
print(json.dumps(summary, indent=2))