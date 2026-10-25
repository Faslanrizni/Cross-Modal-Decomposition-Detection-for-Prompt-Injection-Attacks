import csv, json
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.preprocessing import OneHotEncoder

SEED = 42
MANIFEST = Path("ascii_dataset/manifest/ascii_manifest.csv")
OUT = Path("ascii_dataset/shortcut_check.json")

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))

y = np.array([1 if r["label"] == "attack" else 0 for r in rows])
groups = np.array([r["intent_id"] for r in rows])

# --- Numeric features ---
def leading_ws(text):
    return len(text) - len(text.lstrip())

def trailing_ws(text):
    return len(text) - len(text.rstrip())

num = np.array([
    [
        int(r["token_len"]),
        int(r["text_len"]),
        r["text"].count("\n"),
        trailing_ws(r["text"]),
        leading_ws(r["text"]),
    ]
    for r in rows
], dtype=float)

# --- Categorical features (one-hot) ---
cat = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit_transform(
    [[r["ascii_font"], r["framing_template"], r["plaintext_leak"]] for r in rows]
)

X = np.hstack([num, cat])
print(f"X shape: {X.shape}, y shape: {y.shape}")
print(f"label balance: attack={y.sum()}, benign={len(y)-y.sum()}")
print(f"unique intents (groups): {len(set(groups))}")

# --- GroupKFold: 5 folds grouped by intent_id ---
gkf = GroupKFold(n_splits=5)
models = {
    "logreg": LogisticRegression(max_iter=1000),
    "tree":   DecisionTreeClassifier(max_depth=3, random_state=SEED),
}

results = {name: {"auc": [], "acc": []} for name in models}

for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
    for name, clf in models.items():
        clf.fit(X[train_idx], y[train_idx])
        proba = clf.predict_proba(X[test_idx])[:, 1]
        pred = (proba > 0.5).astype(int)
        auc = roc_auc_score(y[test_idx], proba)
        acc = accuracy_score(y[test_idx], pred)
        results[name]["auc"].append(auc)
        results[name]["acc"].append(acc)
        print(f"  fold {fold} {name}: AUC={auc:.3f} ACC={acc:.3f}")

# --- Final feature importances from a full-fit logistic regression ---
clf = LogisticRegression(max_iter=1000)
clf.fit(X, y)
feature_names = ["token_len", "text_len", "line_count", "trailing_ws", "leading_ws"]
# Add one-hot feature names
ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit(
    [[r["ascii_font"], r["framing_template"], r["plaintext_leak"]] for r in rows]
)
feature_names += list(ohe.get_feature_names_out(["font", "framing", "leak"]))

coefs = sorted(
    zip(feature_names, clf.coef_[0].tolist()),
    key=lambda x: abs(x[1]),
    reverse=True
)[:12]

# --- Report ---
def mean(xs):
    return float(np.mean(xs)) if xs else 0.0

summary = {
    "seed": SEED,
    "cv": "GroupKFold(n_splits=5) grouped by intent_id",
    "logreg_auc_mean": round(mean(results["logreg"]["auc"]), 4),
    "logreg_auc_std":  round(float(np.std(results["logreg"]["auc"])), 4),
    "logreg_acc_mean": round(mean(results["logreg"]["acc"]), 4),
    "tree_auc_mean":   round(mean(results["tree"]["auc"]), 4),
    "tree_auc_std":    round(float(np.std(results["tree"]["auc"])), 4),
    "tree_acc_mean":   round(mean(results["tree"]["acc"]), 4),
    "majority_baseline": round(float(max(y.mean(), 1 - y.mean())), 4),
    "top_feature_coefficients": [
        {"feature": f, "coef": round(c, 4)} for f, c in coefs
    ],
}
auc = summary["logreg_auc_mean"]
if auc <= 0.60:
    summary["verdict"] = "PASS"
elif auc <= 0.65:
    summary["verdict"] = "MINOR LEAKAGE"
else:
    summary["verdict"] = "FAIL — return to Step 5"

with OUT.open("w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print()
print(json.dumps(summary, indent=2))
print(f"\nWrote {OUT}")