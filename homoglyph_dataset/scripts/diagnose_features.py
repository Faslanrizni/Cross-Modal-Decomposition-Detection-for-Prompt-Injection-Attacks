"""diagnose_features.py — which feature is leaking in the homoglyph shortcut check?"""
import csv
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from collections import defaultdict

MANIFEST = Path("homoglyph_dataset/manifest/homoglyph_manifest.csv")
rows = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))
        if r["tokenizer_neutralised"].lower() == "false"]

y = np.array([1 if r["label"] == "attack" else 0 for r in rows])

def script_count(sm):
    return len(sm.split("+"))

num_features = ["nonascii_ratio", "script_count", "token_len", "unk_rate", "density"]
num = np.array([
    [float(r["nonascii_ratio"]), script_count(r["script_mix"]),
     int(r["token_len"]), float(r["unk_rate"]), float(r["density"])]
    for r in rows
], dtype=float)

cat = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit_transform(
    [[r["technique"]] for r in rows]
)
X = np.hstack([num, cat])

clf = LogisticRegression(max_iter=1000)
clf.fit(X, y)

feature_names = num_features + ["technique_cyrillic", "technique_greek"]
print("Coefficients (sorted by |coef|):")
coefs = list(zip(feature_names, clf.coef_[0]))
coefs.sort(key=lambda x: abs(x[1]), reverse=True)
for name, coef in coefs:
    bar = "#" * int(abs(coef) * 20)
    print(f"  {name:<20} {coef:+.3f} {bar}")

print()
print("Mean feature values by label:")
by_label = defaultdict(lambda: defaultdict(list))
for r in rows:
    label = r["label"]
    by_label[label]["nonascii_ratio"].append(float(r["nonascii_ratio"]))
    by_label[label]["token_len"].append(int(r["token_len"]))
    by_label[label]["unk_rate"].append(float(r["unk_rate"]))

for feature in ["nonascii_ratio", "token_len", "unk_rate"]:
    attack_mean = np.mean(by_label["attack"][feature])
    benign_mean = np.mean(by_label["benign"][feature])
    delta = attack_mean - benign_mean
    print(f"  {feature:<20} attack={attack_mean:.3f} benign={benign_mean:.3f} delta={delta:+.3f}")