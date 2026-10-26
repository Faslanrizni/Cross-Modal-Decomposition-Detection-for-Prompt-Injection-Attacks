"""generate_plain.py — plain text channel generator.

Produces 21 intents × 2 phrasings = 42 attacks + 42 matched benigns = 84 rows.
No font, no framing, no fragments — plain text has no encoding axis.

Version 1.1 (2026-10-25):
  - Fixed duplicate benign issue: now tracks used benigns globally
    across all intents, not per-intent.
  - Added post-run integrity check (no duplicate benigns).
  - Added post-run length-drift report.
"""
import csv
import json
import random
from pathlib import Path
from transformers import AutoTokenizer

SEED = 42
TAXONOMY = Path("plain_dataset/intent_taxonomy.json")
PHRASINGS = Path("plain_dataset/phrasings.json")
OUT = Path("plain_dataset")

TOK = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")


def tok_len(text):
    return len(TOK.tokenize(text))


def main():
    rng = random.Random(SEED)
    OUT.mkdir(exist_ok=True)
    (OUT / "manifest").mkdir(exist_ok=True)

    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    phrasings = json.loads(PHRASINGS.read_text(encoding="utf-8"))
    intent_to_cat = {i["intent_id"]: i["category_id"] for i in taxonomy["intents"]}
    benign_pool = phrasings["benign_commands"]

    benign_lengths = [(b, tok_len(b)) for b in benign_pool]
    used_benigns_globally = set()

    rows = []
    next_id = 1
    pair_id = 1

    for intent in taxonomy["intents"]:
        intent_id = intent["intent_id"]
        if intent_id not in phrasings["phrasings"]:
            print(f"WARNING: no phrasings for {intent_id}")
            continue
        category = intent_to_cat[intent_id]
        intent_phrasings = phrasings["phrasings"][intent_id]

        for phrasing_idx, attack_text in enumerate(intent_phrasings, start=1):
            attack_tokens = tok_len(attack_text)
            pid = f"PAIR-{pair_id:05d}"

            # Attack row
            attack_id = f"PLAIN-{next_id:06d}"
            rows.append({
                "id": attack_id,
                "label": "attack",
                "pair_id": pid,
                "intent_id": intent_id,
                "intent_category": category,
                "encoding_family": "plain",
                "modality": "text",
                "text": attack_text,
                "text_len": len(attack_text),
                "token_len": attack_tokens,
                "source_file": "generated_from_phrasings",
                "label_method": "generated_from_taxonomy",
                "dataset_revision": "folder_sha256=a7e32ca2d5ddcc5cc1c3dea3be42649009252e34e98b0f48d18ed60352335598",
                "licence": "HuggingFace standard",
                "split": "",
                "phrasing_id": f"P{phrasing_idx}",
            })
            next_id += 1

            # Matched benign: closest length, globally unused
            candidates = [
                (abs(l - attack_tokens), b)
                for b, l in benign_lengths
                if b not in used_benigns_globally
            ]
            if not candidates:
                print(f"WARNING: benign pool exhausted at {pid} — reusing")
                candidates = [(abs(l - attack_tokens), b) for b, l in benign_lengths]
            candidates.sort()
            top = candidates[:5]
            benign_text = rng.choice(top)[1]
            used_benigns_globally.add(benign_text)

            benign_id = f"PLAIN-{next_id:06d}"
            rows.append({
                "id": benign_id,
                "label": "benign",
                "pair_id": pid,
                "intent_id": intent_id,
                "intent_category": category,
                "encoding_family": "plain",
                "modality": "text",
                "text": benign_text,
                "text_len": len(benign_text),
                "token_len": tok_len(benign_text),
                "source_file": "generated_from_benign_pool",
                "label_method": "generated_from_benign_pool",
                "dataset_revision": "folder_sha256=a7e32ca2d5ddcc5cc1c3dea3be42649009252e34e98b0f48d18ed60352335598",
                "licence": "HuggingFace standard",
                "split": "",
                "phrasing_id": f"P{phrasing_idx}",
            })
            next_id += 1
            pair_id += 1

    # Write manifest
    manifest_path = OUT / "manifest" / "plain_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # Summary
    attacks = [r for r in rows if r["label"] == "attack"]
    benigns = [r for r in rows if r["label"] == "benign"]

    summary = {
        "total_rows": len(rows),
        "attack_rows": len(attacks),
        "benign_rows": len(benigns),
        "unique_pairs": len(set(r["pair_id"] for r in rows)),
        "unique_intents": len(set(r["intent_id"] for r in rows)),
        "token_len_attack": {
            "mean": round(sum(r["token_len"] for r in attacks) / len(attacks), 2),
            "min": min(r["token_len"] for r in attacks),
            "max": max(r["token_len"] for r in attacks),
        },
        "token_len_benign": {
            "mean": round(sum(r["token_len"] for r in benigns) / len(benigns), 2),
            "min": min(r["token_len"] for r in benigns),
            "max": max(r["token_len"] for r in benigns),
        },
    }
    (OUT / "summary_plain.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    # Config
    (OUT / "generator_config.json").write_text(json.dumps({
        "seed": SEED,
        "tokenizer": "sentence-transformers/all-MiniLM-L6-v2",
        "n_intents": len(taxonomy["intents"]),
        "n_phrasings_per_intent": 2,
        "n_benign_pool": len(benign_pool),
        "version": "1.1",
        "uniqueness_rule": "global (across all intents)",
    }, indent=2), encoding="utf-8")

    # Report
    print(f"Wrote {manifest_path}")
    print(f"  total rows: {len(rows)}")
    print(f"  attack:     {len(attacks)}")
    print(f"  benign:     {len(benigns)}")
    print(f"  pairs:      {summary['unique_pairs']}")
    print(f"  intents:    {summary['unique_intents']}")
    print(f"  attack tokens mean: {summary['token_len_attack']['mean']}")
    print(f"  benign tokens mean: {summary['token_len_benign']['mean']}")

    # Post-run integrity check
    print()
    print("=" * 60)
    print("INTEGRITY CHECK")
    print("=" * 60)

    benign_texts = [r["text"] for r in benigns]
    unique_benigns = set(benign_texts)
    if len(benign_texts) == len(unique_benigns):
        print(f"OK: all {len(benign_texts)} benigns are unique")
    else:
        from collections import Counter
        dupes = Counter(benign_texts)
        duplicate_texts = {t: c for t, c in dupes.items() if c > 1}
        print(f"FAIL: {len(duplicate_texts)} duplicate benign texts")
        for t, c in duplicate_texts.items():
            print(f"  {c}x: {t}")
        raise SystemExit("Duplicate benigns — fix benign pool size")

    # Pair-level length drift
    deltas = []
    for pid in sorted(set(r["pair_id"] for r in rows)):
        pair = [r for r in rows if r["pair_id"] == pid]
        a = next(r for r in pair if r["label"] == "attack")
        b = next(r for r in pair if r["label"] == "benign")
        deltas.append(abs(int(a["token_len"]) - int(b["token_len"])))

    print(f"pair length delta: mean={sum(deltas)/len(deltas):.2f}, "
          f"max={max(deltas)}, "
          f"pairs_with_delta_>5={sum(1 for d in deltas if d > 5)}/{len(deltas)}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()