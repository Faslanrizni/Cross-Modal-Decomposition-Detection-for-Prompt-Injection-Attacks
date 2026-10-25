# Dataset file guide

This catalog explains the current ASCII-art and QR dataset files, their role
in the research, and which versions to use. It is documentation only:
machine-readable files and frozen snapshots are not changed by this guide.

## Recommended files to use

- ASCII examples: `ascii_dataset/manifest/ascii_manifest.csv`
- ASCII fragments for decomposition experiments:
  `ascii_dataset/manifest/ascii_fragments.csv`
- QR examples and image paths: `qr_dataset/manifest_v3.csv`
- QR images: `qr_dataset/images/`
- Current QR cross-family coverage: `qr_dataset/intent_coverage.json`
- Current frozen baselines: `frozen/ascii_v1/` and `frozen/qr_v2/`

`qr_dataset/manifest.csv` and `qr_dataset/manifest_v2.csv` are earlier pipeline
stages. Use `manifest_v3.csv` for the common-schema QR dataset. `frozen/qr_v1/`
is retained as historical evidence; use `frozen/qr_v2/` for the corrected
coverage snapshot.

## How to read a manifest

- One manifest row describes one sample.
- `label` is `attack` or `benign`; `pair_id` links one attack to its benign
  comparison.
- `intent_id` identifies the attack goal. A benign pair inherits the same ID
  to preserve the pair relationship; it does not mean the benign content
  expresses that attack.
- `encoding_family` and `modality` indicate the channel and input type.
- `text`, `text_len`, and `token_len` record text and its lengths. For QR,
  `text` is the decoded payload; use the `png` path when the experiment input
  is an image.
- Channel-specific columns hold rendering parameters, image details, or
  provenance.

Do not add explanatory comment rows to CSV files or comments to JSON. Those
formats are consumed by parsers, and changes can invalidate frozen
byte-comparisons or image hashes. Keep explanations in this catalog.

## Live ASCII dataset

### Main files

| File | What it contains / how it is used |
|---|---|
| `ascii_dataset/intent_taxonomy.json` | Versioned source of truth for the 21 intents, category IDs, canonical commands, candidate art words, seed references, and ASCII-target flags. |
| `ascii_dataset/decisions.md` | Locked design rationale, generation choices, split definitions, caveats, and current scope/limitations. |
| `ascii_dataset/dataset_revision.txt` | Fingerprint and provenance for the source data used by this dataset revision. |
| `ascii_dataset/manifest/ascii_manifest.csv` | Main ASCII sample table: attack/benign rows, pair and intent IDs, composite text, token length, font, framing, leak tier, revision, and split. |
| `ascii_dataset/manifest/ascii_fragments.csv` | Two separately stored text components per attack: wrapper and rendered-art payload; records the label of each fragment alone. |
| `ascii_dataset/summary_ascii.json` | Aggregate counts and distributions for rows, pairs, intents, fonts, leak tiers, framing, and token lengths. |
| `ascii_dataset/generator_config.json` | Parameters and counts used by the ASCII generator, including seed, fonts, framing templates, and collision-filter description. |
| `ascii_dataset/intent_coverage.json` | Per-intent channel-family presence, ASCII attack counts, and whether the intent has a cross-family twin for ASCII LOFO. |
| `ascii_dataset/shortcut_check.json` | Surface-feature classifier results used to assess whether simple features predict labels; includes AUC and coefficients. |
| `ascii_dataset/exclusions.csv` | Triage decisions and reasons for the original seed examples; distinguishes kept, exploratory-only, and flagged examples. |
| `ascii_dataset/raw/ascii_art_injection/ascii_art_injection_001.json` | Original seed examples used for provenance and triage, not the generated main training manifest. |

### Splits and verification

| File | What it contains / how it is used |
|---|---|
| `ascii_dataset/splits/iid.json` | Intent-grouped IID train/validation/test assignment for the ASCII channel. |
| `ascii_dataset/splits/lofo_channel.json` | LOFO channel plan/placeholder describing target and available channel families. |
| `ascii_dataset/splits/exploratory_ascii_leak_tier.json` | Exploratory within-ASCII split holding out the `art_only` leak tier. |
| `ascii_dataset/splits/exploratory_ascii_block_font.json` | Exploratory plan for an `ansi_shadow` probe; the note says that probe is not in the current manifest. |
| `ascii_dataset/verification/verification_report.json` | Machine-generated aggregate checks, including regeneration, duplicate, benign-word, and token-length results. |
| `ascii_dataset/verification/verification_log.csv` | Human-review outcomes for the sampled ASCII examples. |
| `ascii_dataset/verification/hand_review_sample.csv` | The 40-row sample selected for ASCII human review. |
| `ascii_dataset/logs/generation.log` | Generation log location; currently empty (0 bytes). |
| `ascii_dataset/logs/verification.log` | Verification log location; currently empty (0 bytes). |

### ASCII scripts

| File | Purpose |
|---|---|
| `ascii_dataset/scripts/write_taxonomy.py` | Writes the taxonomy JSON, including the intent and category definitions. |
| `ascii_dataset/scripts/verify_taxonomy.py` | Checks intent uniqueness, candidate words, category references, and renderability in training fonts. |
| `ascii_dataset/scripts/triage_seed.py` | Applies documented triage decisions to the raw ASCII-art seed file and writes `exclusions.csv`. |
| `ascii_dataset/scripts/generate_ascii.py` | Renders attack art, creates matched benign rows, writes the ASCII manifest/fragments/config/summary. |
| `ascii_dataset/scripts/freeze_splits.py` | Builds ASCII IID and exploratory split metadata and calculates the initial ASCII/QR coverage view. |
| `ascii_dataset/scripts/verify_ascii.py` | Checks regeneration, benign attack-word presence, duplicates, token distributions, block-character behavior, and creates a review sample/report. |
| `ascii_dataset/scripts/prefill_ascii_review.py` | Prefills review-log fields that can be checked from the taxonomy and generated samples; human-review fields still need appropriate review. |
| `ascii_dataset/scripts/check_review.py` | Summarizes failed or unfilled ASCII review-log entries. |
| `ascii_dataset/scripts/shortcut_check.py` | Evaluates a logistic-regression/tree baseline on surface features using intent-grouped folds and writes shortcut results. |
| `ascii_dataset/scripts/retrofit_qr.py` | Earlier QR retrofit step that maps QR attacks to taxonomy intents and writes `qr_dataset/manifest_v2.csv`. |
| `ascii_dataset/scripts/dump_qr_payloads.py` | Exports full QR attack payloads to `qr_dataset/full_payloads.txt` for manual intent inspection. |

## Live QR dataset

### Manifests, images, and configuration

| File or files | What it contains / how it is used |
|---|---|
| `qr_dataset/manifest.csv` | Earlier generated QR manifest. It predates taxonomy retrofit and the final unified schema. |
| `qr_dataset/manifest_v2.csv` | Retrofitted QR manifest with intent mapping and QR-specific information; an intermediate stage. |
| `qr_dataset/manifest_v3.csv` | Recommended QR manifest: common fields first, then QR fields such as payload, QR version, PNG path, hash, and decoder results. |
| `qr_dataset/images/QR-000001.png` through `qr_dataset/images/QR-000015.png` | Fifteen attack QR images. Each ID corresponds to an attack row in the manifest. |
| `qr_dataset/images/B-QR-000001.png` through `qr_dataset/images/B-QR-000015.png` | Fifteen benign QR images. Each `B-` image is the benign counterpart of the matching attack ID and pair. |
| `qr_dataset/full_payloads.txt` | Full text payloads for QR attack examples, exported for intent review. |
| `qr_dataset/generator_config.json` | QR rendering settings, package versions, fixed version, image dimensions, and generation-time round-trip statistics. |
| `qr_dataset/dataset_revision.txt` | Fingerprint and provenance for the QR source payload folder. |
| `qr_dataset/summary_qr.json` | Aggregate row, pair, intent, format, QR-version, and token-length statistics. |
| `qr_dataset/intent_coverage.json` | Per-intent family membership and corrected `testable_in_qr_lofo` / `testable_in_ascii_lofo` flags. |
| `qr_dataset/shortcut_check.json` | Surface-feature classifier AUC and coefficients for the QR samples. Interpret it with the documented small-sample variance caveat. |

### QR splits and verification

| File | What it contains / how it is used |
|---|---|
| `qr_dataset/splits/iid_all_families.json` | Shared intent-grouped IID train/validation/test intent assignment for ASCII and QR. |
| `qr_dataset/splits/lofo_qr_held_out.json` | LOFO plan: train on ASCII and hold out QR for testing. |
| `qr_dataset/splits/lofo_ascii_held_out.json` | Symmetric LOFO plan: train on QR and hold out ASCII for testing. |
| `qr_dataset/verification/verification_report.json` | Aggregate QR verification results, including round-trip failures, duplicates, and version uniformity. |
| `qr_dataset/verification/verification_log.csv` | Human-review results for QR samples. |
| `qr_dataset/verification/hand_review_sample.csv` | QR samples selected for human review. |

### QR scripts

| File | Purpose |
|---|---|
| `qr_dataset/scripts/generate_qr_images.py` | Builds attack and matched benign payloads, chooses one QR version for all images, renders PNGs, decodes them, and writes the initial manifest/config. |
| `qr_dataset/scripts/build_manifest_v3.py` | Converts the intermediate QR manifest into the unified v3 schema and computes token lengths and summary statistics. |
| `qr_dataset/scripts/freeze_splits_all.py` | Creates the shared IID split, both QR/ASCII LOFO specifications, recomputed cross-family coverage, and populates the split field in both manifests. |
| `qr_dataset/scripts/verify_qr.py` | Checks QR decoding, benign attack-word hits, duplicates, distributions, version uniformity, and creates the review sample/report. |
| `qr_dataset/scripts/verify_existing_images.py` | Rechecks already-rendered QR image files against their expected payloads. |
| `qr_dataset/scripts/prefill_qr_review.py` | Prefills mechanically checkable QR review fields for the hand-review log. |
| `qr_dataset/scripts/check_review.py` | Summarizes failed or incomplete QR review entries. |
| `qr_dataset/scripts/shortcut_check_qr.py` | Evaluates surface-feature baselines on QR data and records coefficients/AUC results. |
| `qr_dataset/scripts/fingerprint_source.py` | Computes a SHA-256 fingerprint for the source QR payload folder and writes the revision record. |

## Frozen snapshots

Frozen directories preserve named dataset releases. Their files are copies
for reproducibility, not additional independent samples. The descriptions
above for each live file apply to its same-purpose frozen counterpart.

### `frozen/ascii_v1/`

| Frozen path(s) | Relationship to live ASCII data |
|---|---|
| `frozen/ascii_v1/manifest/ascii_manifest.csv` | Frozen copy of `ascii_dataset/manifest/ascii_manifest.csv`. |
| `frozen/ascii_v1/manifest/ascii_fragments.csv` | Frozen copy of `ascii_dataset/manifest/ascii_fragments.csv`. |
| `frozen/ascii_v1/intent_taxonomy.json` | Frozen copy of `ascii_dataset/intent_taxonomy.json`. |
| `frozen/ascii_v1/decisions.md` | Frozen copy of `ascii_dataset/decisions.md`. |
| `frozen/ascii_v1/dataset_revision.txt` | Frozen copy of the ASCII revision record. |
| `frozen/ascii_v1/generator_config.json` | Frozen copy of the ASCII generator configuration. |
| `frozen/ascii_v1/intent_coverage.json` | Frozen copy of the ASCII coverage file. |
| `frozen/ascii_v1/shortcut_check.json` | Frozen copy of the ASCII shortcut results. |
| `frozen/ascii_v1/summary_ascii.json` | Frozen copy of the ASCII summary. |
| `frozen/ascii_v1/exclusions.csv` | Frozen copy of the seed triage exclusions. |
| `frozen/ascii_v1/splits/exploratory_ascii_block_font.json` | Frozen ASCII block-font exploratory split. |
| `frozen/ascii_v1/splits/exploratory_ascii_leak_tier.json` | Frozen ASCII leak-tier exploratory split. |
| `frozen/ascii_v1/splits/iid.json` | Frozen ASCII IID split. |
| `frozen/ascii_v1/splits/lofo_channel.json` | Frozen ASCII channel LOFO plan. |
| `frozen/ascii_v1/verification/hand_review_sample.csv` | Frozen ASCII review sample. |
| `frozen/ascii_v1/verification/verification_log.csv` | Frozen ASCII human-review log. |
| `frozen/ascii_v1/verification/verification_report.json` | Frozen ASCII verification report. |
| `frozen/ascii_v1/CHANGELOG.md` | Release notes for ASCII v1; documentation only, not a live dataset input. |

### `frozen/qr_v2/` — current frozen QR release

| Frozen path(s) | Relationship to live QR data |
|---|---|
| `frozen/qr_v2/manifest/manifest_v3.csv` | Frozen copy of live `qr_dataset/manifest_v3.csv`. |
| `frozen/qr_v2/decisions.md` | Frozen copy of QR locked decisions and documented limitations. |
| `frozen/qr_v2/dataset_revision.txt` | Frozen QR source fingerprint. |
| `frozen/qr_v2/full_payloads.txt` | Frozen full QR attack payload export. |
| `frozen/qr_v2/generator_config.json` | Frozen QR generator configuration. |
| `frozen/qr_v2/intent_coverage.json` | Frozen corrected QR coverage data; use this version rather than QR v1. |
| `frozen/qr_v2/shortcut_check.json` | Frozen QR shortcut-check results. |
| `frozen/qr_v2/summary_qr.json` | Frozen QR aggregate summary. |
| `frozen/qr_v2/splits/iid_all_families.json` | Frozen shared IID split. |
| `frozen/qr_v2/splits/lofo_ascii_held_out.json` | Frozen ASCII-held-out LOFO specification. |
| `frozen/qr_v2/splits/lofo_qr_held_out.json` | Frozen QR-held-out LOFO specification. |
| `frozen/qr_v2/verification/hand_review_sample.csv` | Frozen QR review sample. |
| `frozen/qr_v2/verification/verification_log.csv` | Frozen QR human-review log. |
| `frozen/qr_v2/verification/verification_report.json` | Frozen QR verification report. |
| `frozen/qr_v2/CHANGELOG.md` | Release notes describing the corrected QR coverage snapshot. |

### `frozen/qr_v1/` — superseded historical QR release

| Frozen path(s) | What it is |
|---|---|
| `frozen/qr_v1/manifest/manifest_v3.csv` | Historical QR manifest from v1; superseded by the v2 frozen release. |
| `frozen/qr_v1/decisions.md` | Historical QR design notes as captured in v1. |
| `frozen/qr_v1/dataset_revision.txt` | QR source fingerprint from v1. |
| `frozen/qr_v1/full_payloads.txt` | Historical full attack payload export. |
| `frozen/qr_v1/generator_config.json` | Historical QR generator configuration. |
| `frozen/qr_v1/intent_coverage.json` | Superseded coverage file; it incorrectly marked all 21 intents as QR-LOFO testable. |
| `frozen/qr_v1/shortcut_check.json` | Historical QR shortcut-check results. |
| `frozen/qr_v1/summary_qr.json` | Historical QR summary. |
| `frozen/qr_v1/splits/iid_all_families.json` | Historical shared IID split. |
| `frozen/qr_v1/splits/lofo_ascii_held_out.json` | Historical ASCII-held-out LOFO specification. |
| `frozen/qr_v1/splits/lofo_qr_held_out.json` | Historical QR-held-out LOFO specification. |
| `frozen/qr_v1/verification/hand_review_sample.csv` | QR review sample captured for v1. |
| `frozen/qr_v1/verification/verification_report.json` | QR verification report captured for v1. |
| `frozen/qr_v1/CHANGELOG.md` | Explains why QR v1 was superseded by QR v2; retain for audit history. |

## Research-use summary

- **RQ1 (channel shift):** use the shared `intent_id` values, the two manifests,
  corrected coverage, and LOFO split specifications. Current ASCII/QR overlap
  is 11 of 21 intents.
- **RQ2 (fragment fusion):** use the ASCII main manifest together with the
  ASCII fragment manifest. Each attack currently has a wrapper and payload.
- **RQ3 (unseen arity/splitting):** the current fragment manifest records two
  fragments per attack; it does not itself provide unseen fragment arities or
  alternative split strategies.
- **Versioning:** use the live v3 manifests for current experiments, and use
  `frozen/ascii_v1/` plus `frozen/qr_v2/` when you need the frozen release
  snapshots. Keep `frozen/qr_v1/` only as historical provenance.
