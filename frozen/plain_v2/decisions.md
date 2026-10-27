# Plain text dataset — locked decisions

# Date: 2026-10-26

## Environment

- tokenizer: sentence-transformers/all-MiniLM-L6-v2
- python: 3.12
- seed: 42

## Channel structure

- 21 intents × 2 phrasings = 42 attacks
- 42 matched benigns from a 56-sentence pool
- Total: 84 rows

## Matching rules

- Same `intent_id` on attack and benign (for split co-location)
- Same `phrasing_id` on attack and benign
- Token length matched (attack mean 7.6, benign mean 7.6)
- Character length approximately matched (attack mean 38.7, benign mean 36.6, delta 2.1 chars)
- Every benign used at most once (global uniqueness)

## Verification (2026-10-26)

- Verifier verdict: PASS
- 0 duplicates within or across labels
- 0 benign samples containing attack vocabulary
- 10 hand-reviewed rows: 0 failures, 0 unfilled
- Distribution: attack tokens mean 7.6, benign tokens mean 7.6

## Shortcut check (2026-10-26)

- Design: GroupKFold(5) grouped by intent_id
- Features: token_len, text_len, trailing_ws, leading_ws
- logreg AUC mean = 0.6155, sd = 0.1661
- Majority baseline = 0.50
- Verdict: MINOR LEAKAGE (0.60–0.65 band)

### Interpretation

The mean AUC of 0.6155 is 1.5 points above the PASS threshold.
However:

1. Per-fold AUCs range from 0.359 to 0.859. Folds 1 and 3 are
   below chance; fold 4 is an outlier at 0.859.
2. With n=84 (42 attacks + 42 benigns) and 21 intents across 5 folds,
   each fold has ~17 samples. AUC on 17 samples has a standard error
   of roughly 0.07, meaning the 95% confidence interval around the
   mean is [0.467, 0.764] — which includes 0.50 (chance).
3. The attack vs benign text_len distributions differ by only 2.1
   chars in the mean (38.7 vs 36.6, sd ~13 each). token_len is
   perfectly matched (7.6 vs 7.6). No single surface feature shows
   a systematic gap large enough to explain a true AUC of 0.62.
4. The most likely explanation is fold-level variance in a small
   sample, not a systematic surface leak.

### Consequence for the research

Plain text's role is the anchor family — it provides cross-family
twins for LOFO evaluation of other channels, not a standalone
classification benchmark. The MINOR LEAKAGE reading on its own
shortcut check does not affect that anchor role.

If a tighter estimate is required, the appropriate fix is to expand
to 3–4 phrasings per intent (126–168 rows), not to re-tune the
benign pool. Expanding the pool to chase the AUC threshold would
constitute over-fitting to the test metric.

## Known limitations

1. Small sample size (84 rows) means the shortcut check AUC has a
   wide confidence interval. The mean of 0.6155 cannot be
   distinguished from 0.50 at 95% confidence.
2. Two phrasings per intent (rather than 3–4) limits the
   sentence-held-out testing that homoglyph will use.
