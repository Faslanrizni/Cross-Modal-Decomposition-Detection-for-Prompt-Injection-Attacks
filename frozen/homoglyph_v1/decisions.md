# Homoglyph dataset — locked decisions

**Date created:** 2026-10-27
**Last updated:** 2026-10-27 (post-audit corrections applied)
**Version:** 1.1

---

## 1. Overview

The homoglyph channel provides a text-encoding family where malicious
commands are rendered with characters substituted from other scripts
(cyrillic, greek). It is one of four channel families built for RQ1
(alongside ASCII art, QR code, and plain text).

**Row count:** 630 rows total.

- Main channel: 504 rows (252 attacks + 252 transformed benigns) —
  cyrillic and greek
- Control stratum: 126 rows (63 attacks + 63 benigns) — zero_width,
  combining, unicode_tags
- Natural benigns: 37 rows (untransformed; recorded with
  `benign_kind = "natural"`)
- Unique pairs: 315
- Unique intents: 21

**Frozen as:** `frozen/homoglyph_v1/`

---

## 2. Environment

- tokenizer: sentence-transformers/all-MiniLM-L6-v2
- torch: 2.14.1+cpu
- torchaudio: 2.11.0+cpu
- python: 3.12
- seed: 42

---

## 3. Tokenizer diagnostic (initial measurement)

The diagnostic ran on `all-MiniLM-L6-v2` to identify which homoglyph
techniques survive tokenization.

| Technique    | Tokens | UNK | UNK%   | Same as plain | Decision        |
| ------------ | ------ | --- | ------ | ------------- | --------------- |
| plain        | 4      | 0   | 0.0%   | (baseline)    | —               |
| cyrillic     | 9      | 2   | 22.2%  | False         | Main channel    |
| greek        | 24     | 0   | 0.0%   | False         | Main channel    |
| fullwidth    | 4      | 4   | 100.0% | False         | Excluded        |
| circled      | 4      | 4   | 100.0% | False         | Excluded        |
| zero_width   | 4      | 0   | 0.0%   | True          | Control stratum |
| combining    | 4      | 0   | 0.0%   | True          | Control stratum |
| unicode_tags | 0      | 0   | —      | False         | Control stratum |
| math_bold    | 4      | 4   | 100.0% | False         | Excluded        |
| math_double  | 4      | 4   | 100.0% | False         | Excluded        |
| squared      | 4      | 4   | 100.0% | False         | Excluded        |
| small_roman  | 6      | 3   | 75.0%  | False         | Excluded        |

**What this measures:** the initial diagnostic reports tokenization
behaviour — how many tokens result, how many are `[UNK]`, and whether
the token sequence is identical to plain text. It does not measure
whether the model can _read_ the substituted content semantically.
That distinction is important and is addressed in Section 5.

---

## 4. Map decisions

### 4.1 Cyrillic map (23 pairs, post-fix)

Initial map had 25 pairs. Vocab coverage check found two pairs whose
lookalikes are out-of-vocabulary in `all-MiniLM-L6-v2`:

- `S` → `Ѕ` (Cyrillic capital Dze)
- `s` → `ѕ` (Cyrillic lowercase Dze)

Both removed from forward and inverse maps. Cyrillic map is now 23
pairs, all in-vocab. Measured UNK rate on representative attack
sentences at both densities dropped from 22.2% to **0.0%**.

The current 23 cyrillic pairs:

- lowercase: `a, c, e, i, j, o, p, x, y` (9 pairs)
- uppercase: `A, B, C, E, H, I, J, K, M, O, P, T, X, Y` (14 pairs)

### 4.2 Greek map (25 pairs, unchanged)

25 pairs, all in-vocab. No changes needed.

### 4.3 Control stratum (3 techniques, excluded from LOFO)

- **zero_width** — inserted ZWSP; BERT-uncased normaliser strips
  format characters (Unicode category Cf), so the tokenizer sees plain
  text.
- **combining** — combining diaeresis; BERT-uncased normaliser strips
  combining marks (Unicode category Mn), so the tokenizer sees plain
  text.
- **unicode_tags** — tag codepoints (U+E0000 range); produce 0 tokens
  in MiniLM, so the model sees nothing.

These rows are marked `tokenizer_neutralised = True` in the manifest
and are **excluded from coverage, LOFO, and shortcut check**. They are
documented for completeness.

### 4.4 Excluded techniques (9 total)

- fullwidth, circled, math_bold, math_double, squared, small_roman —
  100% or mostly `[UNK]` tokens
- RTL override — breaks text directionality
- Soft hyphen — stripped by tokenizer
- BOM insertion — covered by zero_width class

Documented in `homoglyph_map.json` under `excluded` with reasons.

---

## 5. Perceivability — the correct test

The initial perceivability check (`in_family_ceiling.json`, kept as
`in_family_ceiling_DEPRECATED.json` in the frozen snapshot) used a
TF-IDF classifier on tokenized text. That test measures **bag-of-words
difference** between attack and benign sentences. It achieves high AUC
(0.8953) because attack sentences use different words from benign
sentences — not because the model can read the substituted text.

**This test does not measure readability.** The correct test embeds
`source_text` and `text` with MiniLM's actual encoder and compares
cosine similarity to a random-pair baseline.

### 5.1 Readability test result (`readability_test.json`)

Corrected test: embed source_text and text with `all-MiniLM-L6-v2`,
compute cosine similarity per row, compare to random-pair baseline.

| Subset           | mean_sim | delta vs random | Interpretation          |
| ---------------- | -------- | --------------- | ----------------------- |
| Random baseline  | 0.0865   | (0.0)           | —                       |
| **cyrillic 0.3** | 0.3898   | **+0.303**      | **Readable**            |
| **greek 0.3**    | 0.2872   | **+0.201**      | **Marginally readable** |
| cyrillic 0.6     | 0.1634   | +0.077          | Borderline unreadable   |
| greek 0.6        | 0.0958   | +0.009          | Unreadable (at chance)  |
| **Overall**      | 0.2340   | **+0.1476**     | **PARTIALLY_READABLE**  |

### 5.2 What this means

The channel is **readable at density 0.3** for both cyrillic and greek,
and **partially readable at cyrillic 0.6**, but **unreadable at greek
0.6** (delta 0.009, essentially at the random baseline).

At density 0.6, the substitution overwhelms the encoder's ability to
associate the transformed text with its source.

### 5.3 Per-density RQ1 strategy

Because readability differs by density, **RQ1 homoglyph results must
be reported per density, not aggregated**:

- **Density 0.3 subset (primary RQ1 result):** tests whether the model
  generalises across channel shift when the substituted text is
  readable. This is the defensible RQ1 measurement.
- **Density 0.6 subset (documented limitation):** tests channel shift
  at the edge of readability. Any LOFO failure on this subset reflects
  the encoder's inability to parse the text, not a generalisation
  failure. Report separately with the readability caveat.

Aggregating the two densities would conflate readable-channel
generalisation with unreadable-channel noise.

### 5.4 Threshold justification

The readability test uses a delta-based threshold:

- delta ≥ 0.20 → READABLE
- 0.10 ≤ delta < 0.20 → PARTIALLY_READABLE
- delta < 0.10 → UNREADABLE

Absolute cosine similarity values depend on sentence length and
content. The delta (mean similarity minus random baseline) controls for
both. Thresholds are chosen to match the empirical range observed on
this channel: the 0.3 subset sits well above 0.20, the 0.6 subset near
0.10 or below.

### 5.5 Greek token inflation

Greek is 0% UNK but tokenizes to ~6× the source length (4 → 24 tokens
for "ignore all previous instructions"). The model sees the full
content, but at inflated length. This is a documented property of the
tokenizer's character-level treatment of Greek, not a limitation of
the technique. The greek 0.3 readability result (+0.201) is measured
despite this inflation.

---

## 6. Shortcut check — two populations

The shortcut check tests whether surface features (nonascii_ratio,
script_count, token_len, unk_rate, density, technique) can distinguish
attack from benign.

Because naturals are untransformed (density=0.0), they create a
benign-only sub-signal. Two populations are checked.

### 6.1 Full population (attacks + all benigns including naturals)

- n_rows: 504
- logreg AUC: 0.6151, sd 0.0284
- tree AUC: 0.6636
- verdict: MINOR LEAKAGE

### 6.2 Transformed-only (naturals excluded)

- n_rows: 467
- logreg AUC: 0.5633, sd 0.0388
- tree AUC: 0.6008
- verdict: PASS

### 6.3 Interpretation

The full-population MINOR LEAKAGE is attributable to natural benigns.
Naturals have `density = 0.0` (untransformed), which is exclusively
benign and therefore a distinct surface signature. The `density`
coefficient is +0.295 in the feature diagnosis — the second-largest
feature after the joint technique constant.

The transformed-only PASS at 0.5633 confirms the pure homoglyph
channel is clean. Any LOFO result on attacks vs transformed benigns
reflects intent learning, not surface exploitation.

### 6.4 The `unk_rate` coefficient is 0.000

Direct evidence that the vocab coverage fix worked. The removal of
`Ѕ` and `ѕ` eliminated the tokenizer UNK artefact from the shortcut
features.

---

## 7. Natural benigns

37 sentences across five languages, all non-ASCII, all harmless.

Language distribution:

- French: 8
- German: 8
- Spanish: 7
- Russian: 7
- Greek: 7

### 7.1 Natural share denominators

37 natural benigns = **11.8% of all 315 benigns** = **14.7% of the 252
main-channel benigns**.

Report both. Use 14.7% when discussing the substituted channel;
11.8% when discussing the whole dataset. The natural share must stay
in the 10-20% range to prevent "non-ASCII = attack" learning.

### 7.2 Natural benign hand review

All 37 naturals were hand-reviewed (separate from the 28-row main
sample). Result: `naturals_review.csv` — 37 rows, all `harmless=yes`,
all `attack_vocabulary=no`. Language labels verified per row.

---

## 8. Contrastive-training rule

**Positive pairs** for the contrastive loss (Pillar A) MUST require
both:

1. `label == "attack"`
2. matching `intent_id`

Across channels:

- ASCII, QR: `intent_id` populated on both rows of a pair
- Plain, homoglyph: `intent_id` populated only on attack rows; blank
  on benign rows (`Fix 5`)

Any script that constructs positives without checking `label ==
"attack"` will silently include benigns as positives in ASCII and QR
(because those channels carry `intent_id` on benign rows). That would
produce a corrupted contrastive objective.

**Grouping** (for split assignment, pair co-location, coverage
counting) MUST use `split_group`. This field is populated on both rows
of every pair in every channel, regardless of `intent_id` state.

Scripts compliant with this rule:

- `freeze_splits_all.py` v2 (row_intent() prefers split_group)
- `shortcut_check_plain.py` v2 (uses split_group)
- `shortcut_check_homoglyph.py` v2 (uses split_group)
- `in_family_ceiling.py` (uses split_group)

Any future training script must follow the same rule.

---

## 9. Statistical independence

The 504 main-channel rows are derived from **63 source sentences**
(21 intents × 3 phrasings). Each source is rendered 4 ways
(2 techniques × 2 densities). Effective sample size is **21 intents**,
not 504 rows.

RQ1 results will report:

- intent-level bootstrap confidence intervals
- leave-intents-out cross-validation
- row-level metrics for comparison

The IID split is 14/3/4 intents. Test-set rows are
4 intents × 3 phrasings × 4 renderings × 2 labels = 96 rows — but
these are not 96 independent samples. Bootstrap on intents (21
resamples) is the correct uncertainty estimate. Any test treating
rows as independent will overstate significance.

---

## 10. RQ1 status

The homoglyph channel enables **two supplementary LOFO directions**
(hold out ASCII, hold out plain). It does not close RQ1 on its own.

The proposal's primary RQ1 evaluation (RO5a) holds out **QR and
audio**. QR is currently 11/21 coverage; audio is not yet built.
Homoglyph strengthens the training side so that when QR and audio
are added, the model will have seen each intent in three
text-modalities (ASCII, plain, homoglyph).

**What is measurable today:**

- Hold out ASCII (train on plain + homoglyph): 21 intents
- Hold out plain (train on ASCII + homoglyph): 21 intents
- Technique-held-out (cyrillic vs greek): 21 intents, within-family
  robustness sub-test of RQ1

**What is not closed by homoglyph:** RQ1 primary evaluation (requires
QR and audio), RQ2 (requires decomposition sets), RQ3 (requires
decomposition sets).

---

## 11. RQ2 and RQ3 status

- **RQ2 (decomposition):** not supported by homoglyph. Requires
  decomposition sets.
- **RQ3 (arity and splitting):** not supported by homoglyph. Requires
  4-way and clause-boundary splits in decomposition sets.

The technique-held-out split (cyrillic vs greek) is a **within-family
robustness sub-test of RQ1**, not RQ3. This distinction is important
at viva: an examiner reading "RQ3 supported" would ask for arity and
splitting evidence, which homoglyph does not provide.

---

## 12. Documented observations

The homoglyph build produced three documented observations. These are
observations from measured behaviour, not research findings.

**Observation 1 — Normaliser behaviour.** All-MiniLM-L6-v2 uses
BERT-uncased's normaliser, which strips format characters (Unicode
category Cf, e.g. ZWSP) and combining marks (category Mn, e.g.
diaeresis). Zero-width, combining, and tag techniques are neutralised
by this. Defending against the surviving cyrillic/greek attacks
requires **confusable folding (UTS #39)**, not NFKC. NFKC would fold
fullwidth and circled but not cyrillic or greek.

**Observation 2 — Vocabulary coverage.** Fullwidth, circled, math bold,
and squared characters are not in MiniLM's vocabulary. Because BERT
does not apply NFKC, these produce 100% `[UNK]` tokens. Two of the 25
initial cyrillic lookalikes (`Ѕ`, `ѕ`) were similarly out-of-vocab
and were removed to bring cyrillic UNK to 0%.

**Observation 3 — Natural share trade-off.** Natural benigns
(untransformed non-ASCII) prevent "non-ASCII = attack" learning at the
cost of introducing a `density=0` signal. Quantified at AUC 0.6151
full-population vs 0.5633 transformed-only. Both are reported; the
trade-off is a design decision, not a defect.

---

## 13. Known limitations

1. **Mechanism-held-out LOFO not testable.** Only one surviving
   mechanism (substitution). Technique-held-out (cyrillic vs greek)
   is the within-family robustness test.

2. **Vocab-tailored cyrillic map.** The cyrillic map uses only
   characters that are in-vocab for all-MiniLM-L6-v2. Two lookalikes
   (`Ѕ`, `ѕ`) were removed because they produce `[UNK]` tokens on this
   tokenizer. A real attacker would not remove these — the model would
   encounter them at deployment. The channel is therefore
   MiniLM-friendly by construction. A different text encoder would
   require its own vocab coverage check before use.

3. **Readability is density-dependent.** Density 0.3 is readable
   (delta +0.30 cyrillic, +0.20 greek). Density 0.6 is borderline
   unreadable (cyrillic +0.08) or unreadable (greek +0.01). RQ1
   results must be reported per density; aggregation is not valid.

4. **Greek token inflation.** Greek is 0% UNK but tokenizes to ~6×
   source length. The model sees full content at inflated length.

5. **Control stratum is documentation.** zero_width, combining,
   unicode_tags are neutralised by BERT normaliser or invisible. They
   are not test data and must never leak into training splits.

6. **Full-population shortcut AUC 0.6151 (MINOR LEAKAGE).** Driven by
   natural benigns' `density=0.0` signal. Transformed-only PASSes at
   0.5633. Both populations reported.

7. **Small-sample variance.** 504 rows derived from 63 unique source
   sentences across 21 intents. Effective n = 21 intents. Report
   bootstrap CIs on intents, not rows.

---

## 14. Frozen artefacts

The frozen snapshot `frozen/homoglyph_v1/` contains:

| File                                | Purpose                                               |
| ----------------------------------- | ----------------------------------------------------- |
| `homoglyph_map.json`                | 5 techniques (2 main, 3 control), 9 excluded          |
| `vocab_coverage_report.json`        | Per-character in-vocab check                          |
| `readability_test.json`             | **Correct perceivability test** (MiniLM cosine)       |
| `in_family_ceiling_DEPRECATED.json` | Old TF-IDF test (superseded, retained as audit trail) |
| `shortcut_check.json`               | Two-population result                                 |
| `homoglyph_manifest.csv`            | 630 rows                                              |
| `verification_report.json`          | Six-check verification (PASS)                         |
| `verification_log.csv`              | 28-row main-channel hand review                       |
| `naturals_review.csv`               | 37-row natural benigns review                         |
| `naturals_review_sample.csv`        | 37-row pre-filled sample                              |
| `exclusions.csv`                    | 20 raw samples triaged                                |
| `natural_benigns.json`              | 37 non-ASCII benign sentences                         |
| `intent_taxonomy.json`              | Shared 21-intent taxonomy                             |
| `phrasings.json`                    | Shared 3-phrasings + 210-benigns input                |
| `intent_coverage.json`              | 21/21 in homoglyph LOFO                               |
| `summary_homoglyph.json`            | Composition record                                    |
| `generator_config.json`             | Reproducibility + 4 provenance hashes                 |
| `decisions.md`                      | This file                                             |
| `CHANGELOG.md`                      | Freeze record + corrections                           |
| `manifest/homoglyph_manifest.csv`   | (duplicated in manifest/)                             |
| `verification/*`                    | All verification artefacts                            |
| `splits/*`                          | IID + 4 channel LOFO + 2 technique LOFO               |

---

**End of decisions.md.**
