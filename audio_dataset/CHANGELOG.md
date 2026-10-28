# audio_v1 — first frozen snapshot

**Date frozen:** 10/28/2026

## Summary

The audio channel completes the six-family dataset (ASCII, QR, plain,
homoglyph, audio, + pending decomposition set). It provides RQ1's
primary held-out modality on 5 of 14 v4 categories, with 603
strict-tier pairs (P3-compliant) and 64 relaxed-tier pairs
(documented limitation).

## Manifest

- 1,334 rows (667 attacks + 667 benigns)
- 5 attack categories: beast_suffixes (210), cipher_jailbreaks (108),
  instruction_hierarchy_bypass (90), memory_poisoning (150),
  multi_agent_contagion (109)
- 2 voices: David, Zira (alternating by manifest row index)
- 603 strict pairs (±10 % duration), 64 relaxed pairs (±20 %)
- 667 attacks from ~111 v4 sources; 222 attack-SHA groups of 3 rows
  are "expected shared" (same content + same voice); 0 real collisions

## Verification summary

| Check                                  | Result                              | File                       |
| -------------------------------------- | ----------------------------------- | -------------------------- |
| Preflight speaker-vs-content           | delta 0.0729 (MARGINAL)             | `preflight_report.json`    |
| Preflight attack-vs-benign pilot       | gap 0.2614 (PASS)                   | `preflight_report.json`    |
| Duration matching                      | strict mean 0.197 s, relaxed 1.56 s | `duration_report.json`     |
| File / format / pair-parity (8 checks) | PASS                                | `verification_report.json` |
| Round-trip (wav2vec2)                  | 1316 / 1334 = 98.7 % pass           | `roundtrip.json`           |
| Shortcut AUC                           | strict 0.5185, full 0.5223          | `shortcut_check.json`      |
| Hand review (60 rows)                  | 0 failures, 0 unfilled              | `verification_log.csv`     |

## Splits (11 files)

- `iid_all_families.json`
- `lofo_audio_held_out.json`
- `lofo_ascii_art_held_out.json`
- `lofo_qr_held_out.json`
- `lofo_plain_held_out.json`
- `lofo_homoglyph_held_out.json`
- `lofo_qr_plus_audio_held_out.json` ← RO5a joint split, primary
- `lofo_audio_category_beast_suffixes_held_out.json`
- `lofo_audio_category_cipher_jailbreaks_held_out.json`
- `lofo_audio_category_instruction_hierarchy_bypass_held_out.json`
- `lofo_audio_category_memory_poisoning_held_out.json`
- `lofo_audio_category_multi_agent_contagion_held_out.json`

## Relationship to previous channels

Inherits from earlier freezes:

- `split_group` semantics — plain_v2
- Four provenance hashes — homoglyph_v1
- Round-trip verification as P4 — qr_v3
- `input_modality_for_training` column — qr_v3

## Component B (decomposition)

Not in this build. The decomposition generator reads
`frozen/audio_v1/manifest/audio_manifest.csv` and produces
clause-level audio fragments as **one carrier among three**
(text wrapper + image tile + audio clause) inside a single split plan.

## Known limitations

See `decisions.md §11` for the full list. In brief:

- TTS-only domain; real human speech untested
- Two SAPI voices only
- Duration is the primary leak vector (monitored by shortcut check;
  current AUC 0.5185 is clean)
- 5 of 14 v4 categories; 9 excluded with per-row reasons
- 222 attack audio SHA groups are expected (corpus design)
- 17 speakable attacks excluded during duration matching
- 18 round-trip residuals (wav2vec2 spelling; audio is faithful)
