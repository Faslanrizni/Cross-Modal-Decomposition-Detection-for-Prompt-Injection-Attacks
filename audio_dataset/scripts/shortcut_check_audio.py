"""shortcut_check_audio.py — tier-aware. Strict AUC is the primary result."""
import csv, json, numpy as np, soundfile as sf
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score

rows = list(csv.DictReader(open("audio_dataset/manifest/audio_manifest.csv",
                                   encoding="utf-8-sig")))
METHODS = ["speech", "ultrasonic", "whispered", "background", "reversed", "speed_shifted"]
CATS    = sorted({r["attack_category"] for r in rows})

def rms(p):
    y, sr = sf.read(p); return float(np.sqrt(np.mean(y**2)))
def zcr(p):
    y, sr = sf.read(p); return float(np.mean(np.abs(np.diff(np.sign(y))) > 0))

def build_X(subset):
    return np.array([[
        float(r["duration_s"]),
        Path(r["audio_path"]).stat().st_size,
        float(r["text_len"]),
        len(r["text"].split()),
        rms(r["audio_path"]),
        zcr(r["audio_path"]),
        1.0 if r["voice_id"] == "voice_male" else 0.0,
        *[1.0 if r["audio_method"] == m else 0.0 for m in METHODS],
        *[1.0 if r["attack_category"] == c else 0.0 for c in CATS],
    ] for r in subset], dtype=float)

def auc_for(subset):
    X = build_X(subset)
    y = np.array([1 if r["label"] == "attack" else 0 for r in subset])
    g = np.array([r["split_group"] for r in subset])
    aucs = []
    for tr, te in GroupKFold(n_splits=5).split(X, y, g):
        if len(set(y[tr])) < 2 or len(set(y[te])) < 2: continue
        clf = LogisticRegression(max_iter=1000).fit(X[tr], y[tr])
        aucs.append(roc_auc_score(y[te], clf.predict_proba(X[te])[:, 1]))
    return round(float(np.mean(aucs)), 4), round(float(np.std(aucs)), 4)

strict_subset = [r for r in rows if r["duration_match_tier"] == "strict"]
full_subset   = rows
strict_auc, strict_std = auc_for(strict_subset)
full_auc,   full_std   = auc_for(full_subset)

def verdict(a):
    return "PASS" if a <= 0.60 else "MINOR_LEAKAGE" if a <= 0.65 else "FAIL"

report = {
    "n_strict":       len(strict_subset),
    "n_full":         len(full_subset),
    "strict_auc_mean": strict_auc, "strict_auc_std": strict_std,
    "strict_verdict":  verdict(strict_auc),
    "full_auc_mean":   full_auc,   "full_auc_std":   full_std,
    "full_verdict":    verdict(full_auc),
    "primary_reading": "strict",
}
Path("audio_dataset/shortcut_check.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))