# QR dataset — locked decisions

# Date: 2026-10-18

# Basis: existing generator config; round-trip verification; shortcut check pending

## Environment

- qrcode: <version from generator_config.json>
- opencv: <version from generator_config.json>
- zxing-cpp: <version from generator_config.json>
- python: 3.12

## Design decisions

### QR version — FIXED across all images

- Method: required_version() scans versions 1..40; picks smallest that fits ALL payloads
- Enforced via: qrcode.QRCode(version=fixed_version, ...) + make(fit=False)
- Why: prevents size leak. If attacks were longer than benigns, QR version would
  correlate with label, and image dimensions alone would classify with 100% accuracy.

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

## Scale

- 15 attacks + 15 matched benigns = 30 rows
- 11 unique attack intents (from retrofit)
- 6 new intents discovered from full-payload inspection

## Intent mapping (locked 2026-10-16)

Mapped in retrofit_qr.py; see QR_INTENT_MAP.

## Pending (to be completed in this rebuild)

- Six-check verifier (Step 5)
- Shortcut check (Step 8)
- Unified split with ASCII (Step 7)
