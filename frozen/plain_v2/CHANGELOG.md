# plain_v2 — second frozen version (supersedes plain_v1)

**Date frozen:** 2026-10-26
**Supersedes:** plain_v1 (2026-10-26)

## Summary of changes from v1

| Dimension | v1 | v2 |
|---|---|---|
| Rows | 84 (42 atk + 42 ben) | 126 (63 atk + 63 ben) |
| Phrasings per intent | 2 (P1, P2) | 3 (P1, P2, P3 long-form) |
| Benign pool size | 56 | 210 |
| Matching rule | token length only | 10*token_delta + char_delta |
| Shortcut AUC | 0.6155 (MINOR LEAKAGE) | 0.5232 (PASS) |
| Shortcut AUC std | 0.1661 | 0.0256 |

## The five fixes applied

1. **Two-dimensional length matching** — score now combines token
   length (10x weight) and character length (1x weight). Closed the
   tail-length leak that caused v1's AUC 0.6155.

2. **P3 long-form phrasings added** — 21 new 12-20 word phrasings,
   one per intent. Enables visible homoglyph substitution and 4-way
   decomposition for RQ3.

3. **Benign pool expanded to 210 sentences** — from 56. Now spans
   4-34 tokens so P3 attacks have close-length matches.

4. **`derivation_hash` field added** — SHA256 of phrasings.json.
   Fixes P4 provenance (row now points to its actual direct source,
   not just the upstream ASCII corpus).

5. **`split_group` field added; benign `intent_id` now empty** —
   prevents the contrastive loss from misreading benign samples as
   positives for their paired attack's intent.

## Shortcut check v2

- logreg AUC mean = 0.5232, sd = 0.0256
- Per-fold AUCs: 0.498, 0.569, 0.510, 0.507, 0.531
- All folds within ±0.05 of chance
- Verdict: PASS

## Row count derivation

21 intents x 3 phrasings x 2 (attack+benign) = 126 rows
63 unique attack sentences, 63 unique benign sentences
21 unique pairs per phrasing index (63 pairs total)

## Coverage

- plain: 21/21 testable in plain LOFO
- Lifts ASCII coverage from 11/21 (v1 state) to 21/21 (v2 state)
- Same coverage as v1; only the row count and quality improved

## Known limitations

1. Small sample (126 rows) — shortcut AUC has wide CI, though
   dramatically tighter than v1.
2. Three phrasings per intent (P1, P2, P3).
3. All plain text is generated from phrasings.json.

## Downstream impact of split_group rename

Any script that groups rows by intent MUST use `split_group`, not
`intent_id`. After Fix 5, benign rows have empty `intent_id`; their
paired intent lives in `split_group`.

Scripts already updated for this:
- freeze_splits_all.py v2 (uses row_intent() helper)
- shortcut_check_plain.py v2 (uses split_group for GroupKFold)

Training code that constructs contrastive positive pairs must filter
to `label == "attack"` before grouping by `intent_id`.
