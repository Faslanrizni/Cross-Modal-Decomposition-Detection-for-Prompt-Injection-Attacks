import csv, json
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.preprocessing import OneHotEncoder

SEED = 42
MANIFEST = Path("qr_dataset/manifest_v3.csv")
OUT = Path("qr_dataset/shortcut_check.json")

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
y = np.array([1 if r["label"] == "attack" else 0 for r in rows])
groups = np.array([r["intent_id"] for r in rows])

def trailing_ws(text): return len(text) - len(text.rstrip())
def leading_ws(text): return len(text) - len(text.lstrip())

num = np.array([
    [int(r["token_len"]), int(r["text_len"]), int(r["qr_version"]),
     trailing_ws(r["text"]), leading_ws(r["text"])]
    for r in rows
], dtype=float)

cat = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit_transform(
    [[r["format"]] for r in rows]
)
X = np.hstack([num, cat])

print(f"X shape: {X.shape}, y shape: {y.shape}")
print(f"label balance: attack={y.sum()}, benign={len(y)-y.sum()}")
print(f"unique intents (groups): {len(set(groups))}")

gkf = GroupKFold(n_splits=5)
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

clf = LogisticRegression(max_iter=1000)
clf.fit(X, y)
feature_names = ["token_len", "text_len", "qr_version", "trailing_ws", "leading_ws"]
ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit([[r["format"]] for r in rows])
feature_names += list(ohe.get_feature_names_out(["format"]))
coefs = sorted(zip(feature_names, clf.coef_[0].tolist()),
               key=lambda x: abs(x[1]), reverse=True)[:8]

def mean(xs): return float(np.mean(xs)) if xs else 0.0

summary = {
    "seed": SEED,
    "cv": "GroupKFold(n_splits=5) grouped by intent_id",
    "logreg_auc_mean": round(mean(results["logreg"]["auc"]), 4),
    "logreg_auc_std":  round(float(np.std(results["logreg"]["auc"])), 4),
    "tree_auc_mean":   round(mean(results["tree"]["auc"]), 4),
    "majority_baseline": round(float(max(y.mean(), 1 - y.mean())), 4),
    "top_feature_coefficients": [
        {"feature": f, "coef": round(c, 4)} for f, c in coefs
    ],
}
auc = summary["logreg_auc_mean"]
summary["verdict"] = (
    "PASS" if auc <= 0.60 else
    "MINOR LEAKAGE" if auc <= 0.65 else
    "FAIL — return to Step 4"
)

OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print()
print(json.dumps(summary, indent=2))