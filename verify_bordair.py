"""verify_bordair.py

Run from the bordair-multimodal folder:   python verify_bordair.py
Read-only: it never modifies a dataset file. It writes three CSVs to ./verification/

  1_schema_report.csv      every file: record count, fields present, label counts
  2_decomposition_review.csv   the cross_modal_decomposition seeds, ready for manual review
  3_split_review.csv       random samples of text_image_split (+ benign twin) and triple

The word-coverage column is only a crude pre-screen. It does NOT replace reading
each row yourself and filling in the blank review columns.
"""
import csv
import glob
import json
import os
import random
import re
from collections import Counter

OUT = "verification"
os.makedirs(OUT, exist_ok=True)
random.seed(42)  # fixed so the same rows are sampled every run

CONTENT_KEYS = ["text", "image_content", "doc_content", "document_content",
                "audio_content", "audio_transcript", "content"]
REVIEW_COLS = ["text_alone_benign", "image_alone_benign", "doc_or_audio_alone_benign",
               "full_command_in_one_field", "combination_reconstructs_attack", "notes"]


def load_records(path):
    """Return a list of dict records from .json/.jsonl, whatever the wrapper shape."""
    try:
        if path.endswith(".jsonl"):
            with open(path, encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # report, do not crash
        print(f"  !! could not read {path}: {exc}")
        return None
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
    return []


def words(s):
    return set(re.findall(r"\w+", s.lower()))


def review_row(path, idx, rec, tag=""):
    fields = {k: str(rec[k]) for k in CONTENT_KEYS if isinstance(rec.get(k), str) and rec[k].strip()}
    all_words = words(" ".join(fields.values()))
    coverage = 0.0
    if all_words:
        coverage = max(len(words(v) & all_words) / len(all_words) for v in fields.values())
    other = {k: v for k, v in rec.items() if k not in CONTENT_KEYS}
    row = {"set": tag, "file": path.replace("\\", "/"), "index": idx, "id": rec.get("id", ""),
           "non_empty_fields": ";".join(fields),
           "max_single_field_word_coverage": round(coverage, 2)}
    for k in CONTENT_KEYS:
        row[k] = fields.get(k, "")
    row["other_fields"] = json.dumps(other, ensure_ascii=False)[:600]
    for c in REVIEW_COLS:
        row[c] = ""
    return row


def write_csv(name, rows):
    if not rows:
        print(f"  (no rows for {name})")
        return
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path}  ({len(rows)} rows)")


def schema_report():
    files = glob.glob("payloads*/**/*.json*", recursive=True) + glob.glob("benign/*.json")
    rows, totals = [], Counter()
    for path in sorted(set(files)):
        if os.path.basename(path).startswith("summary"):
            continue
        recs = load_records(path)
        if recs is None:
            rows.append({"file": path, "records": "READ_ERROR", "fields": "", "expected_detection": ""})
            continue
        keys = Counter(k for r in recs for k in r)
        labels = Counter(str(r.get("expected_detection")) for r in recs)
        totals.update(labels)
        rows.append({"file": path.replace("\\", "/"), "records": len(recs),
                     "fields": ";".join(f"{k}:{c}" for k, c in sorted(keys.items())),
                     "expected_detection": ";".join(f"{k}:{c}" for k, c in labels.items())})
    write_csv("1_schema_report.csv", rows)
    print("  label totals across all files you have:", dict(totals))
    print("  Use YOUR counted totals in the proposal, not the dataset card's.")


def decomposition_review():
    rows = []
    for path in sorted(glob.glob("payloads_v5/cross_modal_decomposition/*.json*")):
        for i, rec in enumerate(load_records(path) or []):
            rows.append(review_row(path, i, rec, "decomposition_seed"))
    write_csv("2_decomposition_review.csv", rows)


def split_review(n_attack=40, n_benign=20, n_triple=20):
    rows = []
    sources = [("payloads_v4_crossmodal/text_image_split/*.json", n_attack, "split_attack"),
               ("benign/v4cm_text_image_split.json", n_benign, "split_benign_twin"),
               ("payloads_v4_crossmodal/triple/*.json", n_triple, "triple_attack")]
    for pattern, n, tag in sources:
        pool = []
        for path in sorted(glob.glob(pattern)):
            pool += [(path, i, r) for i, r in enumerate(load_records(path) or [])]
        for path, i, rec in random.sample(pool, min(n, len(pool))):
            rows.append(review_row(path, i, rec, tag))
    write_csv("3_split_review.csv", rows)


if __name__ == "__main__":
    print("1/3 schema report");            schema_report()
    print("2/3 decomposition seeds");      decomposition_review()
    print("3/3 split / triple samples");   split_review()
    print("Done. Open the CSVs in Excel and fill the blank review columns by hand.")
