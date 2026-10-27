"""check_vocab_coverage.py — is the UNK rate inherent or map-choice?

For each mapped character in cyrillic and greek maps, check whether
all-MiniLM-L6-v2 tokenizes it to [UNK] or to a real token.

If several characters are out-of-vocab, the 22.2% cyrillic UNK rate is
an artefact of map choice. Removing or replacing those characters can
drop UNK to ~0% and make homoglyph readable.

If most characters are out-of-vocab, the UNK rate is inherent to the
technique — accept it and document the limitation.
"""
from transformers import AutoTokenizer
import json
from pathlib import Path

TOK = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
hmap = json.loads(Path("homoglyph_dataset/homoglyph_map.json").read_text(encoding="utf-8"))

report = {}

for tech in ["cyrillic", "greek"]:
    spec = hmap["techniques"][tech]
    print(f"\n=== {tech} map coverage ===")
    print(f"{'latin':<6} {'lookalike':<10} {'status':<15} {'tokens'}")
    print("-" * 60)

    in_vocab = []
    out_vocab = []

    for latin, look in sorted(spec["forward"].items()):
        tokens = TOK.tokenize(look)
        is_unk = any(t == "[UNK]" for t in tokens)
        status = "OUT-OF-VOCAB" if is_unk else "in-vocab"
        print(f"{latin:<6} {look:<10} {status:<15} {tokens}")
        if is_unk:
            out_vocab.append({"latin": latin, "lookalike": look, "tokens": tokens})
        else:
            in_vocab.append({"latin": latin, "lookalike": look, "tokens": tokens})

    print(f"\n  → {len(in_vocab)}/{len(spec['forward'])} in-vocab")

    if out_vocab:
        print(f"  → Out-of-vocab: {[f'{o['latin']}->{o['lookalike']}' for o in out_vocab]}")
        print(f"  → Recommendation: remove these {len(out_vocab)} pairs from the map,")
        print(f"    or replace with in-vocab lookalikes.")
    else:
        print(f"  → All lookalikes in-vocab. No change needed.")

    report[tech] = {
        "total": len(spec["forward"]),
        "in_vocab": len(in_vocab),
        "out_vocab": len(out_vocab),
        "out_vocab_pairs": [{"latin": o["latin"], "lookalike": o["lookalike"]} for o in out_vocab],
    }

Path("homoglyph_dataset/vocab_coverage_report.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
for tech, r in report.items():
    status = (
        "CLEAN" if r["out_vocab"] == 0
        else f"{r['out_vocab']} pairs to fix"
    )
    print(f"  {tech}: {r['in_vocab']}/{r['total']} in-vocab ({status})")

print(f"\nWrote homoglyph_dataset/vocab_coverage_report.json")