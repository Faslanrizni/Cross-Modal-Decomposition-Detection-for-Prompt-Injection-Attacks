# plain_v1 — first frozen version

**Date frozen:** 2026-10-26

## Contents

- manifest: plain_manifest.csv (84 rows = 42 attacks + 42 benigns)
- taxonomy: intent_taxonomy.json (shared with ASCII and QR, 21 intents)
- phrasings: phrasings.json (2 phrasings per intent + 56 benign sentences)
- splits: iid_all_families.json, lofo_ascii_art_held_out.json, lofo_qr_held_out.json, lofo_plain_held_out.json
- coverage: intent_coverage.json (21/21 testable in plain LOFO)
- shortcut_check.json: PASS
- verification: verification_report.json (PASS), verification_log.csv (10 rows hand-reviewed)

## What plain text provides

- Anchor family: cross-family twin for every intent
- Baseline for measuring channel-shift cost
- Unlocks 21/21 coverage for ASCII (up from 11/21)

## Known limitations

1. Only 2 phrasings per intent (smaller than the 4-6 in the ASCII channel)
2. 84 rows total — small, but by design (the anchor is not for scale)
3. No decomposition (plain text is single-fragment by construction)
