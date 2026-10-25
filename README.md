
**Contribution to the source:** cross-family queries become a single column filter. `pd.concat([ascii_df, qr_df])` now produces a valid dataframe.

**Files:** both manifests

### 2.10 Intent coverage report (11/21 cross-family)

**Original:** no coverage reporting.

**Extension:** for each intent, records which families contain it and whether it is testable in each LOFO direction.

**Contribution to the source:** makes the RQ1 scope explicit. 11/21 intents are cross-family testable today; the other 10 will become testable when more channels are added.

**File:** `qr_dataset/intent_coverage.json` (byte-identical to `ascii_dataset/intent_coverage.json`)

### 2.11 Shortcut check (surface-invariance proof)

**Original:** no verification that the label does not leak through surface features.

**Extension:** a trivial classifier trained on surface-only features (length, line count, font, framing, tier, whitespace) achieves:
- **ASCII**: AUC 0.556 (PASS)
- **QR**: AUC 0.5111 (PASS, with n=30 variance caveat)

**Contribution to the source:** this is the evidence that any successful LOFO result from the actual model is attributable to intent learning, not to surface exploitation.

**Files:** `ascii_dataset/shortcut_check.json`, `qr_dataset/shortcut_check.json`

### 2.12 Verification pipeline (six checks + hand review)

**Original:** no verification beyond the source author's construction.

**Extension:** six automated checks per channel:

1. Regeneration (ASCII) / round-trip (QR)
2. Attack-word scan on benign
3. Deduplication
4. Distribution comparison
5. Tokenizer / version audit
6. Hand-review sampling

Plus a 40-row (ASCII) + 30-row (QR) hand review with semantic verification of every intent mapping.

**Contribution to the source:** every claim about the dataset is now recomputable from raw files, not just asserted.

**Files:** `verification/verification_report.json`, `verification/verification_log.csv`

### 2.13 Split structure (IID + LOFO + exploratory)

**Original:** no splits.

**Extension:**
- **IID split** — grouped by `intent_id`, 14 train / 3 val / 4 test intents, identical across families
- **LOFO channel splits** — QR-held-out and ASCII-held-out, one file per direction
- **Exploratory folds** — `art_only` leak tier held out, `ansi_shadow` block font held out

**Contribution to the source:** RQ1 becomes measurable. Without grouped splits, any LOFO result is confounded by intent leakage.

**Files:** `ascii_dataset/splits/`, `qr_dataset/splits/`

### 2.14 Frozen snapshots with CHANGELOGs

**Original:** no frozen version; the dataset was a working directory.

**Extension:** immutable `ascii_v1/` and `qr_v2/` snapshots with CHANGELOGs explaining:
- What was frozen (date, file list)
- Known limitations (K1–K5)
- Why `qr_v2` supersedes `qr_v1` (the coverage correction)

**Contribution to the source:** provides a stable reference for the dissertation and protects against silent drift.

**Files:** `frozen/ascii_v1/`, `frozen/qr_v2/`, `frozen/qr_v1/CHANGELOG.md`

---

## 3. What was preserved (the source)

It is equally important to be clear about what came from the source and was not modified.

### 3.1 Raw payloads (unmodified)

The raw attack payloads from `bordair-multimodal` are preserved byte-for-byte in `ascii_dataset/raw/ascii_art_injection/` and used as input to the QR generator. The SHA256 fingerprint of the raw source folder is recorded in both `dataset_revision.txt` files.

**Verify the fingerprint:**

```bash
cat ascii_dataset/dataset_revision.txt
cat qr_dataset/dataset_revision.txt
