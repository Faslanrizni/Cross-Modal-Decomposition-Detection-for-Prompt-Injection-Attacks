# homoglyph_v1 — frozen 2026-10-27

## Version history

- **v1.0** — initial freeze (superseded by v1.1 corrections below)
- **v1.1** — post-audit corrections applied. This is the current state.

## Contents

630 rows total:

- 504 main channel (252 attacks + 252 transformed benigns, cyrillic + greek)
- 126 control stratum (63 + 63, zero_width + combining + unicode_tags)
- 37 natural benigns embedded in the 252 transformed population
  (recorded with `benign_kind = "natural"`)

## Verification summary

| Check                                               | Result                                |
| --------------------------------------------------- | ------------------------------------- |
| Fold-back failures                                  | 0                                     |
| Duplicate rows                                      | 0                                     |
| Verification verdict                                | PASS                                  |
| Hand review (main 28 rows)                          | 0 failures, 0 unfilled                |
| Hand review (37 naturals)                           | 37/37 harmless, 0 attack vocabulary   |
| In-family ceiling (TF-IDF, deprecated)              | 0.8953 (see below)                    |
| **Readability test (MiniLM cosine, authoritative)** | **delta 0.1476 → PARTIALLY_READABLE** |
| Shortcut AUC (full population)                      | 0.6151 (MINOR LEAKAGE)                |
| Shortcut AUC (transformed only)                     | 0.5633 (PASS)                         |

## Corrections applied in v1.1 (2026-10-27)

### Correction 1 — Readability test supersedes TF-IDF in-family ceiling

`in_family_ceiling.json` (TF-IDF classifier, AUC 0.8953) measured
bag-of-words difference, not semantic readability. It was incorrectly
interpreted as proof that MiniLM can read the substituted text.

**Correct test:** `readability_test.json` — embed source_text and text
with MiniLM's actual encoder, compute cosine similarity vs random
baseline.

**Correct result:** overall delta 0.1476 → PARTIALLY_READABLE.

- cyrillic 0.3: delta +0.303 (readable)
- greek 0.3: delta +0.201 (marginally readable)
- cyrillic 0.6: delta +0.077 (borderline unreadable)
- greek 0.6: delta +0.009 (unreadable)

Both files retained. `in_family_ceiling_DEPRECATED.json` keeps the
audit trail; `readability_test.json` is authoritative.

### Correction 2 — RQ1 homoglyph results must be per density

Density 0.3 is the primary RQ1 subset (readable). Density 0.6 is
documented as borderline/unreadable. Aggregation would conflate
channel generalisation with readability failure.

### Correction 3 — RQ1 headline corrected

Homoglyph enables supplementary LOFO directions (hold out ASCII,
hold out plain). The proposal's primary RQ1 (RO5a) holds out QR and
audio. Homoglyph strengthens the training side, not closes RQ1.

### Correction 4 — Vocab tailoring documented as limitation

Cyrillic map uses only in-vocab characters. `Ѕ` and `ѕ` removed. The
channel is MiniLM-friendly by construction; a different encoder needs
its own vocab check.

### Correction 5 — Greek token inflation documented

Greek is 0% UNK but ~6× token inflation. Full content visible at
inflated length.

### Correction 6 — Natural share denominator

37 naturals = 11.8% of all 315 benigns = 14.7% of 252 main-channel
benigns. Report the 14.7% when discussing the substituted channel.

### Correction 7 — Contrastive-training rule documented

Positive pairs require `label == "attack"` and matching `intent_id`.
Grouping uses `split_group`. Documented in decisions.md Section 8.

### Correction 8 — Statistical independence documented

Effective n = 21 intents, not 504 rows. RQ1 results will use
intent-level bootstrap CIs.

### Correction 9 — Naturals review completed

37/37 natural benigns hand-reviewed: all harmless, all no attack
vocabulary, language labels verified.

## Known limitations (summary)

1. Only substitution mechanism survives → mechanism-held-out LOFO not testable
2. Cyrillic map is vocab-tailored
3. Readability is density-dependent (0.3 readable, 0.6 borderline)
4. Greek token inflation ~6×
5. Control stratum is documentation, excluded from LOFO
6. Full-population shortcut AUC 0.6151 (naturals drive it)
7. Effective n = 21 intents, not 504 rows

See `decisions.md` for full details.
