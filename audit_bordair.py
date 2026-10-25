"""audit_bordair.py - the automatable checks from the dataset verification checklist.

Run from the bordair-multimodal folder:   python audit_bordair.py
Optional: pip install scikit-learn   (only needed for check 4, the shortcut audit)
Read-only. Prints a report and saves it to verification/4_audit_report.txt

These are SCREENS, not proofs. The keyword screen in check 3 is crude; the
human review and the trained-baseline filter still have to be done.
"""
import glob
import hashlib
import json
import os
import random
import re
from collections import Counter

OUT = "verification"
os.makedirs(OUT, exist_ok=True)
random.seed(42)

SUBS = ["text_image_full", "text_image_split", "text_document",
        "text_audio", "image_document", "triple"]
CONTENT_KEYS = ["text", "image_content", "doc_content", "document_content", "audio_content"]
AUDIT_META = ["image_type", "doc_type", "doc_location", "audio_method", "strategy"]
FRAGMENTS = {"text_image_split": ["text", "image_content"],
             "image_document": ["image_content", "doc_content"],
             "triple": ["image_content", "doc_content", "audio_content"]}
KEYWORDS = re.compile(r"ignore|disregard|previous instruction|system prompt|reveal|password|"
                      r"secret|exfiltrat|override|jailbreak|api[_ ]key|credential", re.I)
REPORT = []


def say(msg=""):
    print(msg)
    REPORT.append(str(msg))


def load_records(path):
    try:
        if path.endswith(".jsonl"):
            with open(path, encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        say(f"  !! could not read {path}: {exc}")
        return None
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def load_sub(sub):
    recs = []
    for p in sorted(glob.glob(f"payloads_v4_crossmodal/{sub}/*.json")):
        recs += load_records(p) or []
    return recs


def content_key(r):
    parts = [str(r.get(k, "")) for k in CONTENT_KEYS]
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


WRAPPER_SUBS = {"text_image_full", "text_document", "text_audio", "triple"}


def payload_key(r, sub):
    """Key of the attack payload only: drops the stock wrapper sentence where 'text' is just a wrapper."""
    keys = [k for k in CONTENT_KEYS if not (k == "text" and sub in WRAPPER_SUBS)]
    return hashlib.md5("|".join(str(r.get(k, "")) for k in keys).encode("utf-8")).hexdigest()


def dedupe(recs):
    seen, out = set(), []
    for r in recs:
        k = content_key(r)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def check1_duplication():
    say("== 1. Effective sample size: records vs distinct seeds vs distinct payload (wrapper excluded) ==")
    for sub in SUBS:
        recs = load_sub(sub)
        if recs:
            seeds = {r.get("v4_source_id") for r in recs}
            say(f"{sub:18s} records={len(recs):6d}  distinct v4_source_id={len(seeds):4d}  "
                f"distinct payload={len({payload_key(r, sub) for r in recs}):6d}")


def check2_wrappers():
    say("\n== 2. Wrapper text (the 'text' field): attack vs benign twin ==")
    for sub in SUBS:
        a = load_sub(sub)
        b = load_records(f"benign/v4cm_{sub}.json") or []
        at, bt = {r.get("text", "") for r in a}, {r.get("text", "") for r in b}
        say(f"{sub:18s} attack distinct text={len(at):5d}  benign distinct text={len(bt):6d}  shared={len(at & bt)}")


def check3_split_halves():
    say("\n== 3. Split-fragment screen (crude keyword proxy for 'not benign alone') ==")
    for sub, fields in FRAGMENTS.items():
        recs = load_sub(sub)
        if not recs:
            continue
        empty = any_kw = both_clean = 0
        for r in recs:
            frags = [str(r.get(k, "")).strip() for k in fields if str(r.get(k, "")).strip()]
            if len(frags) < 2:
                empty += 1
                continue
            hits = [bool(KEYWORDS.search(f)) for f in frags]
            any_kw += any(hits)
            both_clean += not any(hits)
        n = len(recs)
        say(f"{sub:18s} n={n:5d}  <2 non-empty fragments={empty/n:6.1%}  "
            f"a fragment has override keywords={any_kw/n:6.1%}  no fragment has keywords={both_clean/n:6.1%}")


def check4_shortcuts(max_n=20000):
    say("\n== 4. Shortcut audit: can ONE field or the tags alone separate attack from benign? ==")
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import roc_auc_score
        from sklearn.model_selection import GroupShuffleSplit
    except ImportError:
        say("scikit-learn not installed - skipped (pip install scikit-learn)")
        return
    views = {
        "wrapper_text_only": lambda r: str(r.get("text", "")),
        "payload_fields_only": lambda r: " ".join(str(r.get(k, "")) for k in CONTENT_KEYS if k != "text"),
        "metadata_tags_only": lambda r: " ".join(f"{k}={r.get(k)}" for k in AUDIT_META),
    }
    for sub in SUBS:
        a = dedupe(load_sub(sub))
        b = dedupe(load_records(f"benign/v4cm_{sub}.json") or [])
        if len(a) < 50 or len(b) < 50:
            say(f"{sub}: not enough records (attack={len(a)}, benign={len(b)})")
            continue
        a = random.sample(a, min(max_n, len(a)))
        b = random.sample(b, min(max_n, len(b)))
        recs, y = a + b, [1] * len(a) + [0] * len(b)
        groups = [str(r.get("v4_source_id") or content_key(r)) for r in recs]
        tr, te = next(GroupShuffleSplit(1, test_size=0.3, random_state=42).split(recs, y, groups))
        for name, fn in views.items():
            X = [fn(r) for r in recs]
            vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2, max_features=50000)
            Xtr = vec.fit_transform([X[i] for i in tr])
            Xte = vec.transform([X[i] for i in te])
            ytr, yte = [y[i] for i in tr], [y[i] for i in te]
            if len(set(yte)) < 2:
                continue
            model = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
            auc = roc_auc_score(yte, model.predict_proba(Xte)[:, 1])
            flag = "   <-- SHORTCUT: fix before using" if auc > 0.95 else ""
            say(f"{sub:18s} {name:20s} held-out-group AUC={auc:.3f}{flag}")


def check5_sources_and_ids():
    say("\n== 5. Source concentration and ID uniqueness across ALL attack files ==")
    sources, ids = Counter(), Counter()
    for p in glob.glob("payloads*/**/*.json*", recursive=True):
        if os.path.basename(p).startswith("summary"):
            continue
        for r in load_records(p) or []:
            sources[str(r.get("attack_source") or r.get("source") or "UNKNOWN")[:70]] += 1
            if r.get("id") is not None:
                ids[r["id"]] += 1
    total = sum(sources.values())
    say(f"total attack records read: {total}")
    for s, c in sources.most_common(12):
        say(f"  {c/total:6.1%}  {c:7d}  {s}")
    say(f"duplicated IDs: {sum(1 for c in ids.values() if c > 1)}")


if __name__ == "__main__":
    check1_duplication()
    check2_wrappers()
    check3_split_halves()
    check4_shortcuts()
    check5_sources_and_ids()
    with open(os.path.join(OUT, "4_audit_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(REPORT))
    print("\nSaved verification/4_audit_report.txt")
