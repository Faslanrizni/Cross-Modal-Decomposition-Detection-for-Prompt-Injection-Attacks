"""in_family_ceiling.py — can the model read homoglyph text at all?

TF-IDF classifier on tokenized text, 5-fold GroupKFold by split_group.
If AUC > 0.65, homoglyph is readable; LOFO on it is informative.
If AUC < 0.60, homoglyph is unreadable; LOFO failure would reflect
perceivability, not generalisation.

Runs on main channel only (control stratum excluded).
"""
import csv
import json
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, accuracy_score
from transformers import AutoTokenizer

TOK = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

def tokenize(text):
    return TOK.tokenize(text)

MANIFEST = Path("homoglyph_dataset/manifest/homoglyph_manifest.csv")
rows = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))
        if r["tokenizer_neutralised"].lower() == "false"]

texts = [r["text"] for r in rows]
y = np.array([1 if r["label"] == "attack" else 0 for r in rows])
groups = np.array([r["split_group"] for r in rows])

vectorizer = TfidfVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None)
X = vectorizer.fit_transform(texts)

gkf = GroupKFold(n_splits=5)
aucs, accs = [], []
for train_idx, test_idx in gkf.split(X, y, groups):
    if len(set(y[train_idx])) < 2 or len(set(y[test_idx])) < 2:
        continue
    clf = LogisticRegression(max_iter=1000, solver="liblinear")
    clf.fit(X[train_idx], y[train_idx])
    proba = clf.predict_proba(X[test_idx])[:, 1]
    aucs.append(roc_auc_score(y[test_idx], proba))
    accs.append(accuracy_score(y[test_idx], (proba > 0.5).astype(int)))

mean_auc = float(np.mean(aucs)) if aucs else 0.0
mean_acc = float(np.mean(accs)) if accs else 0.0

if mean_auc > 0.65:
    interpretation = "READABLE"
    action = "Proceed with LOFO evaluation"
elif mean_auc > 0.60:
    interpretation = "WEAK READ"
    action = "Proceed with caveat; report per-technique AUC"
else:
    interpretation = "UNREADABLE"
    action = "Do NOT report LOFO on homoglyph as a generalisation result"

result = {
    "in_family_auc_mean": round(mean_auc, 4),
    "in_family_acc_mean": round(mean_acc, 4),
    "n_rows": len(rows),
    "n_folds_used": len(aucs),
    "interpretation": interpretation,
    "action": action,
}
Path("homoglyph_dataset/in_family_ceiling.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))