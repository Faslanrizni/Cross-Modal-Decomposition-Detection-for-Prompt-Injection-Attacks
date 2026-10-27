"""generate_plain.py — plain text channel generator (v2).

Changes from v1:
  - Fix 1: match on BOTH token length (10x weight) and char length
  - Fix 2: P3 long-form phrasing per intent (3 phrasings instead of 2)
  - Fix 3: expanded benign pool (150 sentences, 4-25 tokens)
  - Fix 4: derivation_hash field (SHA256 of phrasings.json)
  - Fix 5: benign rows carry empty intent_id, split_group holds the paired intent

Produces 21 intents × 3 phrasings × 2 (atk+ben) = 126 rows.
"""
import csv
import hashlib
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

    # Fix 4: hash the actual derivation source
    derivation_hash = hashlib.sha256(PHRASINGS.read_bytes()).hexdigest()

    # Fix 1: store token AND char length per benign
    benign_lengths = [(b, tok_len(b), len(b)) for b in benign_pool]
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
            attack_chars = len(attack_text)
            pid = f"PAIR-{pair_id:05d}"

            # --- Attack row ---
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
                "text_len": attack_chars,
                "token_len": attack_tokens,
                "source_file": "generated_from_phrasings",
                "label_method": "generated_from_taxonomy",
                "dataset_revision": "folder_sha256=a7e32ca2d5ddcc5cc1c3dea3be42649009252e34e98b0f48d18ed60352335598",
                "derivation_hash": f"phrasings_sha256={derivation_hash}",
                "licence": "HuggingFace standard",
                "split": "",
                "split_group": intent_id,
                "phrasing_id": f"P{phrasing_idx}",
            })
            next_id += 1

            # --- Matched benign: fix 1 (token AND char length) ---
            candidates = []
            for b, tl, cl in benign_lengths:
                if b in used_benigns_globally:
                    continue
                score = 10 * abs(tl - attack_tokens) + abs(cl - attack_chars)
                candidates.append((score, b))
            if not candidates:
                print(f"WARNING: benign pool exhausted at {pid} — reusing")
                for b, tl, cl in benign_lengths:
                    score = 10 * abs(tl - attack_tokens) + abs(cl - attack_chars)
                    candidates.append((score, b))
            candidates.sort()
            top = candidates[:5]
            benign_text = rng.choice(top)[1]
            used_benigns_globally.add(benign_text)

            # --- Benign row: fix 5 (empty intent_id, split_group carries paired intent) ---
            benign_id = f"PLAIN-{next_id:06d}"
            rows.append({
                "id": benign_id,
                "label": "benign",
                "pair_id": pid,
                "intent_id": "",
                "intent_category": category,
                "encoding_family": "plain",
                "modality": "text",
                "text": benign_text,
                "text_len": len(benign_text),
                "token_len": tok_len(benign_text),
                "source_file": "generated_from_benign_pool",
                "label_method": "generated_from_benign_pool",
                "dataset_revision": "folder_sha256=a7e32ca2d5ddcc5cc1c3dea3be42649009252e34e98b0f48d18ed60352335598",
                "derivation_hash": f"phrasings_sha256={derivation_hash}",
                "licence": "HuggingFace standard",
                "split": "",
                "split_group": intent_id,
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
        "unique_intents": len(set(r["split_group"] for r in rows)),
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
        "char_len_attack": {
            "mean": round(sum(r["text_len"] for r in attacks) / len(attacks), 2),
            "min": min(r["text_len"] for r in attacks),
            "max": max(r["text_len"] for r in attacks),
        },
        "char_len_benign": {
            "mean": round(sum(r["text_len"] for r in benigns) / len(benigns), 2),
            "min": min(r["text_len"] for r in benigns),
            "max": max(r["text_len"] for r in benigns),
        },
    }
    (OUT / "summary_plain.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    (OUT / "generator_config.json").write_text(json.dumps({
        "seed": SEED,
        "tokenizer": "sentence-transformers/all-MiniLM-L6-v2",
        "n_intents": len(taxonomy["intents"]),
        "n_phrasings_per_intent": 3,
        "n_benign_pool": len(benign_pool),
        "version": "2.0",
        "uniqueness_rule": "global (across all intents)",
        "matching_rule": "10*token_delta + char_delta",
        "derivation_source": "phrasings.json",
    }, indent=2), encoding="utf-8")

    print(f"Wrote {manifest_path}")
    print(f"  total rows:      {len(rows)}")
    print(f"  attack:          {len(attacks)}")
    print(f"  benign:          {len(benigns)}")
    print(f"  pairs:           {summary['unique_pairs']}")
    print(f"  unique intents:  {summary['unique_intents']}")
    print(f"  attack tokens:   {summary['token_len_attack']}")
    print(f"  benign tokens:   {summary['token_len_benign']}")
    print(f"  attack chars:    {summary['char_len_attack']}")
    print(f"  benign chars:    {summary['char_len_benign']}")

    # Integrity check
    print()
    print("=" * 60)
    print("INTEGRITY CHECK")
    print("=" * 60)

    benign_texts = [r["text"] for r in benigns]
    if len(benign_texts) == len(set(benign_texts)):
        print(f"OK: all {len(benign_texts)} benigns are unique")
    else:
        from collections import Counter
        dupes = {t: c for t, c in Counter(benign_texts).items() if c > 1}
        print(f"FAIL: {len(dupes)} duplicate benign texts")
        for t, c in list(dupes.items())[:5]:
            print(f"  {c}x: {t[:60]}")
        raise SystemExit("Duplicate benigns")

    # Pair-level deltas
    tok_deltas, chr_deltas = [], []
    for pid in sorted(set(r["pair_id"] for r in rows)):
        pair = [r for r in rows if r["pair_id"] == pid]
        a = next(r for r in pair if r["label"] == "attack")
        b = next(r for r in pair if r["label"] == "benign")
        tok_deltas.append(abs(int(a["token_len"]) - int(b["token_len"])))
        chr_deltas.append(abs(int(a["text_len"]) - int(b["text_len"])))

    print(f"pair token delta: mean={sum(tok_deltas)/len(tok_deltas):.2f}, max={max(tok_deltas)}")
    print(f"pair char  delta: mean={sum(chr_deltas)/len(chr_deltas):.2f}, max={max(chr_deltas)}")
    print(f"pairs with char delta > 5: {sum(1 for d in chr_deltas if d > 5)}/{len(chr_deltas)}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()