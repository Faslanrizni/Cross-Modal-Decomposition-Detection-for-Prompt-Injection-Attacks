@'

# qr_v1 — SUPERSEDED by qr_v2

**Date frozen:** 2026-10-19
**Date superseded:** 2026-10-19
**Reason:** intent_coverage.json misreported testable_in_qr_lofo as 21/21
when the correct count is 11/21.

## The bug

The coverage-generation code in qr_dataset/scripts/freeze_splits_all.py used:

    "testable_in_qr_lofo": "ascii_art" in families,

This returned true for every intent because every intent appears in ASCII.
It did not check whether the intent also appears in QR (the test family),
so it claimed all 21 intents were LOFO-testable when only 11 actually are.

## The fix

    "testable_in_qr_lofo": ("qr" in families) and (len(families) >= 2),
    "testable_in_ascii_lofo": ("ascii_art" in families) and (len(families) >= 2),

Both flags now require the intent to appear in the test family AND in at
least one training family.

## What changed between v1 and v2

**Data files (byte-identical between v1 and v2):**

- manifest/manifest_v3.csv
- generator_config.json
- summary_qr.json
- shortcut_check.json
- dataset_revision.txt
- full_payloads.txt
- splits/iid_all_families.json
- splits/lofo_qr_held_out.json
- splits/lofo_ascii_held_out.json
- verification/verification_report.json
- verification/hand_review_sample.csv

**Files that changed between v1 and v2:**

- intent_coverage.json — the coverage correction described above
- decisions.md — extended with audit findings (E6 length-matching caveat,
  K3 shortcut variance caveat, G2 regeneration semantics) after v1 was frozen
- verification/verification_log.csv — completed hand review (was empty in v1)

## What to use

Use frozen/qr_v2/ for all downstream work and the dissertation. This
folder (qr_v1) is retained as evidence of the iteration history.
'@ | Out-File -Encoding utf8 frozen\qr_v1\CHANGELOG.md
