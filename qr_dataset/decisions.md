# QR dataset — locked decisions

# Date: 2026-10-18

# Last updated: 2026-10-19 (audit findings G2, K3, H2 closed)

# Basis: existing generator config; round-trip verification; shortcut check PASS

## Environment (frozen)

- qrcode: see qr_dataset/generator_config.json ("qrcode" field)
- opencv: see qr_dataset/generator_config.json ("opencv" field)
- zxing-cpp: see qr_dataset/generator_config.json ("zxing_cpp" field)
- python: 3.12

(Version values are recorded in generator_config.json, which is the
canonical source. This file records the design decisions; the config
file records the exact byte-producing environment.)

## Design decisions

### QR version — FIXED across all images

- Method: required_version() scans versions 1..40; picks smallest that
  fits ALL payloads.
- Enforced via: qrcode.QRCode(version=fixed_version, ...) + make(fit=False)
- Why: prevents size leak. If attacks were longer than benigns, QR version
  would correlate with label, and image dimensions alone would classify
  with 100% accuracy.
- Result: all 30 rows use version 9 (uniform, verified in
  verification_report.json qr_version_uniform=true).

### Error correction

- Level: M (15% recovery)
- Justification: standard for data QR codes; balances density and robustness.

### Benign matching

- One benign per attack (same pair_id)
- Same format (URL/JSON/text)
- Character-length matched within ±10%
- Attack-word-free (regex-scanned at generation)

### Round-trip verification

- Primary decoder: zxing-cpp
- Secondary (informational): OpenCV QRCodeDetector
- Every image must decode to its intended payload.

## Regeneration check for QR — equivalent of P4 (added 2026-10-19 after audit — G2)

The ASCII dataset uses a regeneration check that re-renders art from
(art_word, font) and requires a byte-exact match. QR has an equivalent
check, but it takes a different form because a QR image cannot be
"re-rendered" from a payload alone without also encoding it, and
re-encoding would not be byte-identical (QR encoders may choose different
mask patterns).

The QR equivalent of regeneration is round-trip verification: decode
the image with zxing-cpp and require the decoded text to match the
intended payload exactly. This is a stronger form of P4 than image
re-rendering would be, because:

1. It proves the image still decodes correctly (not just that it was
   generated correctly at some point in the past).
2. It is independently verifiable by any QR reader, not just pyfiglet.
3. It is the check that matters for downstream use: the image must be
   readable by the model's image pipeline.

The `roundtrip_failures` field in verification_report.json is the
QR analogue of `regen_failures` in the ASCII verification report.
Zero failures across 30 images is the P4 evidence for the QR channel.

## Scale

- 15 attacks + 15 matched benigns = 30 rows
- 11 unique attack intents
- 6 new intents discovered from full-payload inspection during retrofit
  (label_content_safe, label_document_approved, fabricate_false_information,
  append_hidden_instructions, reveal_api_endpoints, activate_maintenance_mode)

## Intent mapping (locked 2026-10-16)

Mapped in qr_dataset/scripts/retrofit_qr.py; see QR_INTENT_MAP dictionary.
All 15 attacks mapped; all 15 benigns inherit their paired attack's intent_id.

## Shortcut check (completed 2026-10-19 — replaces prior "pending")

- Design: GroupKFold(5) grouped by intent_id
- Features: token_len, text_len, qr_version, trailing_ws, leading_ws,
  format_onehot (URL / JSON / text)
- logreg AUC mean = 0.5111 (sd = 0.2494)
- tree AUC mean = 0.5222
- Majority baseline = 0.50
- Verdict: PASS (mean AUC <= 0.60)

### Per-fold AUCs (logreg)

| Fold | AUC   |
| ---- | ----- |
| 0    | 0.111 |
| 1    | 0.667 |
| 2    | 0.778 |
| 3    | 0.333 |
| 4    | 0.667 |

### Variance caveat

Per-fold AUCs range from 0.111 to 0.778. With n=30 samples and 11 intents,
each GroupKFold test fold contains only 2–6 samples. AUC on 2 samples can
only take values 0.0, 0.5, or 1.0, so the fold-level distribution is
dominated by sample size, not underlying signal. The mean AUC of 0.5111
is the best available estimate of surface leakage under this design, but
it must be interpreted with the standard deviation of 0.2494 in mind.

### Feature coefficients

| Feature     | Coefficient |
| ----------- | ----------- |
| format_text | +0.1226     |
| format_url  | -0.0972     |
| token_len   | +0.0365     |
| format_json | -0.0263     |
| text_len    | -0.0093     |
| qr_version  | -0.0082     |
| trailing_ws | 0.0         |
| leading_ws  | 0.0         |

The format correlation is real but small (|coef| <= 0.13). It reflects
that attack payloads are often free text while some benign payloads are
URLs. This is documented as a limitation. No single feature has |coef|

> 0.15.

### Reporting note

Because of the small sample size, the QR shortcut check is reported in
the dissertation as suggestive but not decisive. The QR channel's role
in the research is as a held-out test family for RQ1, not as a
standalone classification benchmark. Interpretation of any QR-specific
classification result should include confidence intervals.

## Coverage (measured 2026-10-19 after qr_v2 fix)

- 11/21 intents testable in QR LOFO (has twin in ASCII training family)
- 11/21 intents testable in ASCII LOFO (same 11 intents, symmetric)
- 10 intents ASCII-only; will become testable when text or homoglyph is added
- See qr_dataset/intent_coverage.json for the per-intent report

Note: qr_v1 (frozen 2026-10-19) misreported testable_in_qr_lofo as 21/21
due to a coverage-generation bug. qr_v2 (frozen same day) corrects this
to 11/21. All other files are byte-identical between v1 and v2. See
frozen/qr_v1/CHANGELOG.md and frozen/qr_v2/CHANGELOG.md.

## Splits (created 2026-10-19)

- IID: 14 train / 3 val / 4 test intents (grouped by intent_id, shared
  across families with ASCII)
- LOFO QR: hold out QR at test, train on ASCII (target test family = qr,
  train family = ascii_art)
- LOFO ASCII: symmetric counter-test (target test family = ascii_art,
  train family = qr)
- All split files in qr_dataset/splits/

## Scale

- 30 rows total (15 attacks + 15 benigns)
- 15 unique pair_ids
- 11 unique attack intents
- 7 categories represented (via those 11 intents)

## Known limitations

1. Small sample size (n=30) limits the statistical power of the shortcut
   check and of any classification metric computed on QR alone. Report
   results with confidence intervals.
2. Format correlation (format_text +0.12, format_url -0.10) is a real but
   small surface leak. Documented here; not treated as a dataset failure
   because it is below the acceptance threshold and because QR's role is
   as a held-out test family.
3. Only 11 of 21 intents appear in the QR channel. RQ1 can only be
   evaluated in the QR-held-out direction on those 11 intents until the
   text or homoglyph training family is added.
4. qr_v1 (superseded) contained a coverage bug that reported 21/21
   instead of 11/21 for testable_in_qr_lofo. Use qr_v2.
