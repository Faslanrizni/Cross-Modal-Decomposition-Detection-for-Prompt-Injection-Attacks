@'

# qr_v2 — supersedes qr_v1

**Date frozen:** 2026-10-19
**Supersedes:** qr_v1 (frozen 2026-10-19)

## What changed

Only intent_coverage.json. The v1 coverage file reported
testable_in_qr_lofo as 21/21 because the generation code checked only
whether an intent appeared in ASCII (a training family), not whether
it also appeared in QR (the test family). All 21 intents appear in
ASCII, so the check returned true for all of them.

With only 11 intents appearing in both QR and ASCII, the correct count
is 11/21 in both LOFO directions. This is now reflected in v2.

## Files identical between v1 and v2

All other files are byte-identical between v1 and v2. See the audit
report and decisions.md for details.

## Impact on the research

RQ1 (channel-shift generalisation) can be evaluated on 11 of 21 intents
in either LOFO direction. The other 10 intents are ASCII-only and will
become testable when the text or homoglyph training family is added.

No data artefacts were changed. Only the coverage reporting field was
corrected.
'@ | Out-File -Encoding utf8 frozen\qr_v2\CHANGELOG.md
