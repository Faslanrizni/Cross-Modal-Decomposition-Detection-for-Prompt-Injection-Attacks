"""generate_homoglyph.py — homoglyph channel generator v2.

Fixes applied vs v1:
  - Fix 3: 4 provenance hashes (raw folder, phrasings, map, natural benigns)
  - Fix 5a: benign_kind column (transformed / natural)
  - Fix 5b: natural rows skip fold-back verification
  - Process C: hashlib-based stable hashing (Python hash() is per-process random)
  - Natural benigns are in the pool; if picked, no transformation is applied

Produces 630 rows: 504 main (252 atk + 252 ben) + 126 control (63 + 63).
"""
import csv
import hashlib
import json
import random
import unicodedata
from pathlib import Path
from transformers import AutoTokenizer

SEED = 42
TAXONOMY = Path("homoglyph_dataset/intent_taxonomy.json")
PHRASINGS = Path("homoglyph_dataset/phrasings.json")
MAP = Path("homoglyph_dataset/homoglyph_map.json")
NATURAL = Path("homoglyph_dataset/natural_benigns.json")
RAW_FOLDER = Path("homoglyph_dataset/raw/homoglyph_unicode_attacks")
OUT = Path("homoglyph_dataset")

TOK = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")


def stable_hash_int(s):
    """Process-stable hash. Python's built-in hash() is randomized per run."""
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)


def hash_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def hash_folder(folder_path):
    folder = Path(folder_path)
    hashes = []
    for f in sorted(folder.rglob("*")):
        if f.is_file():
            rel = f.relative_to(folder).as_posix()
            hashes.append(f"{rel}|{hashlib.sha256(f.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(hashes).encode()).hexdigest()


def tok_len(text):
    return len(TOK.tokenize(text))


def unk_rate(text):
    ids = TOK.tokenize(text)
    return ids.count("[UNK]") / len(ids) if ids else 0.0


def nonascii_ratio(text):
    return sum(1 for c in text if ord(c) > 127) / len(text) if text else 0.0


def apply_substitution(text, forward_map, density, rng):
    eligible = [i for i, c in enumerate(text) if c in forward_map]
    if not eligible:
        return text
    n = max(1, int(len(eligible) * density))
    chosen = rng.sample(eligible, min(n, len(eligible)))
    out = list(text)
    for i in chosen:
        out[i] = forward_map[out[i]]
    return "".join(out)


def apply_zero_width(text, insert_char, density, rng):
    out = []
    for i, c in enumerate(text):
        out.append(c)
        if i < len(text) - 1 and rng.random() < density:
            out.append(insert_char)
    return "".join(out)


def apply_combining(text, combining_char, targets, density, rng):
    out = []
    for c in text:
        out.append(c)
        if c in targets and rng.random() < density:
            out.append(combining_char)
    return "".join(out)


def apply_tags(text, tag_offset):
    return "".join(chr(ord(c) + tag_offset) for c in text)


def transform(text, technique, spec, density, source_id):
    rng = random.Random(stable_hash_int(f"{source_id}|{technique}|{density}"))
    if "forward" in spec:
        return apply_substitution(text, spec["forward"], density, rng)
    if technique == "zero_width":
        return apply_zero_width(text, spec["insert_char"], density, rng)
    if technique == "combining":
        return apply_combining(text, spec["combining_char"], spec["target_chars"], density, rng)
    if technique == "unicode_tags":
        return apply_tags(text, spec["tag_offset"])
    raise ValueError(f"Unknown technique: {technique}")


def fold_back(text, technique, spec):
    if "inverse" in spec:
        inv = spec["inverse"]
        return "".join(inv.get(c, c) for c in text)
    if technique == "zero_width":
        return text.replace(spec["insert_char"], "")
    if technique == "combining":
        cleaned = "".join(c for c in text if unicodedata.category(c) != "Mn")
        return unicodedata.normalize("NFKC", cleaned)
    if technique == "unicode_tags":
        off = spec["tag_offset"]
        return "".join(chr(ord(c) - off) if 0xE0000 <= ord(c) <= 0xE007F else c for c in text)
    return None


def main():
    rng = random.Random(SEED)
    OUT.mkdir(exist_ok=True)
    (OUT / "manifest").mkdir(exist_ok=True)

    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    phrasings = json.loads(PHRASINGS.read_text(encoding="utf-8"))
    hmap = json.loads(MAP.read_text(encoding="utf-8"))
    natural = json.loads(NATURAL.read_text(encoding="utf-8"))

    intent_to_cat = {i["intent_id"]: i["category_id"] for i in taxonomy["intents"]}

    # Fix 3: four derivation hashes
    raw_folder_hash = hash_folder(RAW_FOLDER)
    phrasings_hash = hash_file(PHRASINGS)
    map_hash = hash_file(MAP)
    natural_hash = hash_file(NATURAL)

    provenance = {
        "dataset_revision": f"folder_sha256={raw_folder_hash}",
        "derivation_hash_phrasings": f"sha256={phrasings_hash}",
        "derivation_hash_map": f"sha256={map_hash}",
        "derivation_hash_natural": f"sha256={natural_hash}",
    }

    # Benign pool: (text, is_natural)
    benign_pool = []
    for b in phrasings["benign_commands"]:
        benign_pool.append((b, False))
    for b in natural["sentences"]:
        benign_pool.append((b, True))
    benign_pool = list(dict.fromkeys(benign_pool))  # dedup, preserve order

    main_techs = {k: v for k, v in hmap["techniques"].items() if v["channel"] == "main"}
    control_techs = {k: v for k, v in hmap["techniques"].items() if v["channel"] == "control"}

    rows = []
    next_id = 1
    pair_id = 1
    used_benigns = set()

    def pick_benign(attack_text):
        """Pick closest char-length benign. Never reuse natural benigns (they
        are not transformed, so reuse would produce duplicate text)."""
        attack_chars = len(attack_text)
        scored = []
        for b, is_nat in benign_pool:
            key = (b, is_nat)
            if key in used_benigns:
                continue
            scored.append((abs(len(b) - attack_chars), b, is_nat))
        if not scored:
            # Fallback: reuse only TRANSFORMED benigns (never natural)
            for b, is_nat in benign_pool:
                if is_nat:
                    continue
                scored.append((abs(len(b) - attack_chars), b, is_nat))
            if not scored:
                # Last resort (should not happen): allow any reuse
                for b, is_nat in benign_pool:
                    scored.append((abs(len(b) - attack_chars), b, is_nat))
        scored.sort()
        top = scored[:5]
        chosen = rng.choice(top)
        used_benigns.add((chosen[1], chosen[2]))
        return chosen[1], chosen[2]

    def add_pair(base_text, technique, spec, density, intent_id, category, phrasing_id,
                forced_benign=None):
        nonlocal next_id, pair_id

        attack_text = transform(base_text, technique, spec, density, f"A{next_id}")
        attack_fold = fold_back(attack_text, technique, spec) == base_text

        if forced_benign is not None:
            benign_base, is_natural = forced_benign
        else:
            benign_base, is_natural = pick_benign(attack_text)

        if is_natural:
            benign_text = benign_base
            benign_kind = "natural"
            benign_technique = "none"
            benign_density = "0.0"
            benign_fold = True
        else:
            benign_text = transform(benign_base, technique, spec, density, f"B{next_id}")
            benign_kind = "transformed"
            benign_technique = technique
            benign_density = str(density)
            benign_fold = fold_back(benign_text, technique, spec) == benign_base

        pid = f"PAIR-{pair_id:05d}"
        common = {
            "pair_id": pid,
            "intent_category": category,
            "encoding_family": "homoglyph",
            "modality": "text",
            "mechanism": spec["mechanism"],
            "script_mix": spec["script_mix"],
            "tokenizer_neutralised": spec["channel"] == "control",
            "label_method": "generated_from_taxonomy",
            "licence": "HuggingFace standard",
            "split": "",
            "split_group": intent_id,
            "phrasing_id": phrasing_id,
            **provenance,
        }

        rows.append({
            "id": f"HGL-{next_id:06d}",
            "label": "attack",
            "intent_id": intent_id,
            "text": attack_text,
            "text_len": len(attack_text),
            "token_len": tok_len(attack_text),
            "source_text": base_text,
            "technique": technique,
            "density": str(density),
            "benign_kind": "",
            "nonascii_ratio": round(nonascii_ratio(attack_text), 4),
            "unk_rate": round(unk_rate(attack_text), 4),
            "fold_back_ok": attack_fold,
            "source_file": "generated_from_phrasings",
            **common,
        })
        next_id += 1

        rows.append({
            "id": f"HGL-{next_id:06d}",
            "label": "benign",
            "intent_id": "",
            "text": benign_text,
            "text_len": len(benign_text),
            "token_len": tok_len(benign_text),
            "source_text": benign_base,
            "technique": benign_technique,
            "density": benign_density,
            "benign_kind": benign_kind,
            "nonascii_ratio": round(nonascii_ratio(benign_text), 4),
            "unk_rate": round(unk_rate(benign_text), 4),
            "fold_back_ok": benign_fold,
            "source_file": "generated_from_benign_pool",
            "label_method": "generated_from_benign_pool",
            **common,
        })
        next_id += 1
        pair_id += 1

    # Main channel
    for intent in taxonomy["intents"]:
        intent_id = intent["intent_id"]
        if intent_id not in phrasings["phrasings"]:
            continue
        category = intent_to_cat[intent_id]
        for p_idx, base in enumerate(phrasings["phrasings"][intent_id], start=1):
            for tech_name, spec in main_techs.items():
                for density in spec["density_levels"]:
                    add_pair(base, tech_name, spec, density, intent_id, category, f"P{p_idx}")

    # Control stratum (P1 only, 1 density)
    for intent_idx, intent in enumerate(taxonomy["intents"]):
        intent_id = intent["intent_id"]
        if intent_id not in phrasings["phrasings"]:
            continue
        category = intent_to_cat[intent_id]
        base = phrasings["phrasings"][intent_id][0]
        for tech_name, spec in control_techs.items():
            for density in spec["density_levels"]:
                if tech_name == "unicode_tags":
                    forced = benign_pool[intent_idx % len(benign_pool)]
                    used_benigns.add(forced)  # ← FIX: prevent pick_benign from re-picking it
                    add_pair(base, tech_name, spec, density, intent_id, category,
                             "P1", forced_benign=forced)
                else:
                    add_pair(base, tech_name, spec, density, intent_id, category, "P1")

    # Write manifest
    manifest_path = OUT / "manifest" / "homoglyph_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # Summary
    main_rows = [r for r in rows if not r["tokenizer_neutralised"]]
    control_rows = [r for r in rows if r["tokenizer_neutralised"]]
    attacks = [r for r in rows if r["label"] == "attack"]
    benigns = [r for r in rows if r["label"] == "benign"]
    natural_benigns = [r for r in benigns if r["benign_kind"] == "natural"]
    fold_failures = sum(1 for r in rows if not r["fold_back_ok"])

    summary = {
        "total_rows": len(rows),
        "main_rows": len(main_rows),
        "control_rows": len(control_rows),
        "attack_rows": len(attacks),
        "benign_rows": len(benigns),
        "natural_benigns": len(natural_benigns),
        "natural_fraction": round(len(natural_benigns) / len(benigns), 4) if benigns else 0,
        "unique_pairs": len(set(r["pair_id"] for r in rows)),
        "unique_intents": len(set(r["split_group"] for r in rows)),
        "fold_back_failures": fold_failures,
        "techniques": {
            "main": list(main_techs.keys()),
            "control": list(control_techs.keys()),
        },
    }
    (OUT / "summary_homoglyph.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    (OUT / "generator_config.json").write_text(json.dumps({
        "seed": SEED,
        "tokenizer": "sentence-transformers/all-MiniLM-L6-v2",
        "version": "2.0",
        "main_techniques": list(main_techs.keys()),
        "control_techniques": list(control_techs.keys()),
        "provenance": provenance,
        "note": "v2 applies: Fix 3 (4 hashes), Fix 5a (benign_kind), Fix 5b (natural skip fold-back), Process C (stable hashing)",
    }, indent=2), encoding="utf-8")

    print(f"Wrote {manifest_path}")
    print(f"  total rows:         {len(rows)}")
    print(f"  main channel:       {len(main_rows)}")
    print(f"  control stratum:    {len(control_rows)}")
    print(f"  attacks:            {len(attacks)}")
    print(f"  benigns:            {len(benigns)}")
    print(f"  natural benigns:    {len(natural_benigns)} ({summary['natural_fraction']*100:.1f}%)")
    print(f"  unique pairs:       {summary['unique_pairs']}")
    print(f"  unique intents:     {summary['unique_intents']}")
    print(f"  fold-back failures: {fold_failures}")

        # Post-generation duplicate check (fails fast)
    from collections import Counter
    seen = Counter()
    for r in rows:
        seen[(r["label"], r["text"])] += 1
    dupes = {k: v for k, v in seen.items() if v > 1}
    if dupes:
        print(f"\nFAIL: {len(dupes)} duplicate (label, text) groups detected")
        for (label, text), count in list(dupes.items())[:5]:
            print(f"  {label} x{count}: {text[:80]}")
        raise SystemExit(
            "Duplicates exist in the manifest. Fix the generator before running verify."
        )
    print(f"\nDuplicate check: PASS (all {len(rows)} rows are unique)")


if __name__ == "__main__":
    main()