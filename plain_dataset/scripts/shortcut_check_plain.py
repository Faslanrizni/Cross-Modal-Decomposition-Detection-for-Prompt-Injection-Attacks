import csv
import json
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, accuracy_score

SEED = 42
MANIFEST = Path("plain_dataset/manifest/plain_manifest.csv")
OUT = Path("plain_dataset/shortcut_check.json")

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
y = np.array([1 if r["label"] == "attack" else 0 for r in rows])
groups = np.array([r["split_group"] for r in rows])

def trailing_ws(t): return len(t) - len(t.rstrip())
def leading_ws(t): return len(t) - len(t.lstrip())

X = np.array([
    [int(r["token_len"]), int(r["text_len"]), trailing_ws(r["text"]), leading_ws(r["text"])]
    for r in rows
], dtype=float)

print(f"X shape: {X.shape}, y: {y.shape}")
print(f"unique split_groups (groups): {len(set(groups))}")

n_folds = min(5, len(set(groups)))
gkf = GroupKFold(n_splits=n_folds)
models = {
    "logreg": LogisticRegression(max_iter=1000),
    "tree": DecisionTreeClassifier(max_depth=3, random_state=SEED),
}
results = {name: {"auc": [], "acc": []} for name in models}

for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
    for name, clf in models.items():
        clf.fit(X[train_idx], y[train_idx])
        proba = clf.predict_proba(X[test_idx])[:, 1]
        auc = roc_auc_score(y[test_idx], proba)
        acc = accuracy_score(y[test_idx], (proba > 0.5).astype(int))
        results[name]["auc"].append(auc)
        results[name]["acc"].append(acc)
        print(f"  fold {fold} {name}: AUC={auc:.3f} ACC={acc:.3f}")

def mean(xs): return float(np.mean(xs)) if xs else 0.0

summary = {
    "seed": SEED,
    "cv": f"GroupKFold(n_splits={n_folds}) grouped by split_group",
    "logreg_auc_mean": round(mean(results["logreg"]["auc"]), 4),
    "logreg_auc_std": round(float(np.std(results["logreg"]["auc"])), 4),
    "tree_auc_mean": round(mean(results["tree"]["auc"]), 4),
    "majority_baseline": round(float(max(y.mean(), 1 - y.mean())), 4),
}
auc = summary["logreg_auc_mean"]
summary["verdict"] = (
    "PASS" if auc <= 0.60 else
    "MINOR LEAKAGE" if auc <= 0.65 else
    "FAIL"
)

OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print()
print(json.dumps(summary, indent=2))