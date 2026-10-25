# Bordair Multimodal Prompt Injection Dataset — Extended

**A two-family prompt-injection dataset that EXTENDS the original `bordair-multimodal` dataset with a 21-intent taxonomy, matched benign pairs, four font variations, three leak tiers, fragment-level decomposition records, and full verification — built for measuring cross-channel generalisation in multimodal AI security research.**

| | |
|---|---|
| **Project** | Final Year Project — multimodal prompt-injection detection |
| **Author** | Faslan Rizni |
| **Original dataset** | `bordair-multimodal` (HuggingFace) — **source only, extended significantly** |
| **This repository** | **Extension** of bordair-multimodal for research use |
| **Channels prepared** | ASCII art (extended), QR code (extended) |
| **Channels in progress** | Homoglyph (planned), text (planned), cross-modal (planned) |
| **Status** | ASCII v1 and QR v2 **frozen and verified** — ready for RQ1 evaluation |
| **Verification** | `DATASET STATUS: READY` (0 failures, 0 warnings) |
| **Last updated** | 2026-10-25 |

---

## ⚠️ Important: This is an EXTENDED dataset, not a copy

**The original `bordair-multimodal` dataset** (HuggingFace, `Bordair/bordair-multimodal`) provides raw prompt-injection payloads across multiple attack categories, 12 hand-authored ASCII samples, and QR payloads. It does **not** provide a unified intent taxonomy, matched benign pairs, font variations, leak tiers, fragment-level decomposition, verification, splits, or frozen snapshots.

**This repository EXTENDS that source** for research use. Every extension is documented, verified, and traceable to a specific file. The provenance from the original source is preserved in `dataset_revision.txt` (SHA256 fingerprint of the raw source folder) and `seed_sample_ids` (per-intent anchors to source samples).

| Extension | What was added | Not in original |
|---|---|---|
| **Intent taxonomy** | 21 intents across 7 categories, with canonical commands, art-word candidates, cross-family promises | ❌ Not present |
| **Matched benign pairs** | 684 ASCII + 15 QR benign samples, length-matched, format-matched, line-count-matched | ❌ Not present |
| **Four font variations** | `standard`, `slant`, `small`, `big` for every ASCII intent | ❌ Original used one font per sample |
| **Three framing templates** | `art_only`, `art+hint`, `art+full_command` — three leak tiers per attack | ❌ Not present |
| **Six new intents** | `label_content_safe`, `label_document_approved`, `fabricate_false_information`, `append_hidden_instructions`, `reveal_api_endpoints`, `activate_maintenance_mode` — discovered from QR full-payload inspection | ❌ Not in any taxonomy |
| **New category** | `misinformation` — makes model lie about safety or document status | ❌ Not in original |
| **Fixed QR version** | All 30 QR images use version 9 to eliminate the size leak | ❌ Original used natural sizes |
| **Fragment decomposition** | 1,368 fragment rows (wrapper + payload) for Pillar C training | ❌ Not present |
| **Shared manifest schema** | 15-column shared schema across both channels | ❌ Original manifests differ per channel |
| **Intent coverage report** | 11/21 cross-family testable, both LOFO directions | ❌ Not present |
| **Shortcut check** | Proof that no surface feature leaks the label (AUC ≤ 0.60) | ❌ Not present |
| **Verification pipeline** | Six-check verifier + hand review (70 rows total) | ❌ Not present |
| **Split structure** | IID + LOFO + exploratory folds, byte-identical across families | ❌ Not present |
| **Frozen snapshots** | Immutable `ascii_v1/` and `qr_v2/` with CHANGELOGs | ❌ Not present |

**Attribution to the original:** the raw payloads from `bordair-multimodal` are used as the seed material. Every intent is anchored to at least one original sample where possible. No original payload is modified; all extensions are additions, not replacements.

---

## Table of Contents

1. [Overview](#1-overview)
2. [What was extended (the contribution)](#2-what-was-extended-the-contribution)
3. [What was preserved (the source)](#3-what-was-preserved-the-source)
4. [What problem this dataset solves](#4-what-problem-this-dataset-solves)
5. [Quick start](#5-quick-start)
6. [Repository structure](#6-repository-structure)
7. [The dataset](#7-the-dataset)
8. [The five design principles](#8-the-five-design-principles)
9. [How the data maps to the research questions](#9-how-the-data-maps-to-the-research-questions)
10. [Verifying the dataset](#10-verifying-the-dataset)
11. [Using the dataset](#11-using-the-dataset)
12. [Reproducing the dataset](#12-reproducing-the-dataset)
13. [Known limitations](#13-known-limitations)
14. [Adding new channels](#14-adding-new-channels)
15. [Derivation chain (source → extension)](#15-derivation-chain-source--extension)
16. [Citation](#16-citation)

---

## 1. Overview

This repository contains a **research extension** of the `bordair-multimodal` prompt-injection dataset. Two channel families are prepared, frozen, and verified:

- **ASCII art** (`ascii_dataset/`) — 1,368 rows, 684 attack/benign pairs, 21 intents across 4 fonts and 3 leak tiers, plus 1,368 fragment rows for decomposition training.
- **QR code** (`qr_dataset/`) — 30 rows, 15 attack/benign pairs, 11 intents, all images at fixed QR version 9 to eliminate size leak.

Both channels are:
- **Extended** from the raw source: they add the taxonomy, matched benigns, verification, splits, and fragment decomposition that the original does not provide.
- **Frozen** as immutable snapshots under `frozen/`: `frozen/ascii_v1/` (18 files) and `frozen/qr_v2/` (15 files, superseding `qr_v1`).
- **Verified** by `verify_dataset_ready.py` (65+ checks, all pass).

The extension enables **RQ1** (channel-shift generalisation) to be measured on 11 intents per LOFO direction, and provides **partial support for RQ2** (decomposition detection) via the fragment file.

---

## 2. What was extended (the contribution)

This section lists every extension this repository makes to `bordair-multimodal`. It is the contribution claim of the research.

### 2.1 The intent taxonomy (21 intents, 7 categories)

**Original:** no taxonomy; payloads were categorised by attack source (ArtPrompt, FigStep, etc.) but not by intent.

**Extension:** a unified taxonomy where every attack is tagged with `intent_id` and `category_id`. The taxonomy is the artefact that makes cross-channel generalisation measurable.

**File:** `ascii_dataset/intent_taxonomy.json`

### 2.2 Six new intents discovered from QR full-payload inspection

**Original:** 15 intents were derived from the 6 valid ASCII seed samples plus the standard text-prompt-injection literature.

**Extension:** six more intents were discovered by inspecting the full text of every QR attack (not just the first 70 characters):

| New intent | Discovered from | Attack behaviour |
|---|---|---|
| `label_content_safe` | QR-000004, 005, 006 | Tell the model to report content as safe |
| `label_document_approved` | QR-000013, 015 | Report document as approved/processed |
| `fabricate_false_information` | QR-000008 | Fabricate a false claim |
| `append_hidden_instructions` | QR-000009 | Append attacker text to response |
| `reveal_api_endpoints` | QR-000012 | Reveal API paths |
| `activate_maintenance_mode` | QR-000014 | Enter maintenance mode |

**Evidence:** `qr_dataset/full_payloads.txt` (the full payloads that revealed them) + `retrofit_qr.py` (the mapping)

### 2.3 The "misinformation" category (7th category)

**Original:** 6 categories — system prompt extraction, instruction hijack, safety bypass, credential exfiltration, privilege escalation, information extraction.

**Extension:** a 7th category — **misinformation** — added because the 6 new intents are not about *doing* something dangerous, they are about *saying* something false. This is a genuinely distinct attack class.

**File:** `ascii_dataset/intent_taxonomy.json`, category list

### 2.4 Matched benign pairs (684 ASCII + 15 QR)

**Original:** attacks only; no benign counterparts.

**Extension:** every attack is paired with a matched benign that shares the same font/format, framing template, leak tier, comparable token length (±10%), comparable line count (±1 for ASCII), and the same intent_id for split co-location.

**Files:** `ascii_dataset/manifest/ascii_manifest.csv`, `qr_dataset/manifest_v3.csv`

### 2.5 Four font variations (ASCII)

**Original:** each ASCII sample was rendered in one font.

**Extension:** every attack is rendered in all four training fonts (`standard`, `slant`, `small`, `big`), producing 4× the sample count and multiple surface forms per intent.

**File:** `ascii_dataset/manifest/ascii_manifest.csv`, `ascii_font` column

### 2.6 Three leak tiers (ASCII)

**Original:** no concept of leak tier.

**Extension:** three framing templates that control how much of the command is visible:

| Template | Leak tier | What the framing reveals |
|---|---|---|
| `read_art_follow` | `art_only` | Nothing — pure channel-shift test |
| `decode_art_hint` | `art+hint` | A hint about the type of command |
| `art_plus_full` | `art+full_command` | The full command verbatim |

**File:** `ascii_dataset/manifest/ascii_manifest.csv`, `plaintext_leak` column

### 2.7 Fixed QR version (eliminates size leak)

**Original:** each payload was encoded at its natural QR version (7 for attacks, 3 for benigns — image sizes differ).

**Extension:** all 30 images use version 9 (fixed via `required_version()` scanning versions 1–40 for the smallest that fits all payloads). Eliminates the shortcut where a classifier reads only image dimensions.

**Evidence:** `qr_dataset/decisions.md` + `shortcut_check.json` (AUC 0.5111, PASS)

### 2.8 Fragment decomposition records (1,368 rows)

**Original:** no fragment-level data; each attack is a single composite string.

**Extension:** every attack has exactly two fragment rows in `ascii_fragments.csv`:
- Fragment 1 (wrapper): the framing text alone
- Fragment 2 (payload): the rendered art alone

Both marked `fragment_label_alone = benign`. The composite is the attack.

**File:** `ascii_dataset/manifest/ascii_fragments.csv` (1,368 rows)

### 2.9 Shared manifest schema (15 columns)

**Original:** each channel had its own schema.

**Extension:** both manifests share the same 15-column schema: d, label, pair_id, intent_id, intent_category, encoding_family,
modality, text, text_len, token_len, source_file, label_method,
dataset_revision, licence, split


**Files:** both manifests

### 2.10 Intent coverage report (11/21 cross-family)

**Original:** no coverage reporting.

**Extension:** for each intent, records which families contain it and whether it is testable in each LOFO direction.

**File:** `qr_dataset/intent_coverage.json` (byte-identical to `ascii_dataset/intent_coverage.json`)

### 2.11 Shortcut check (surface-invariance proof)

**Original:** no verification that the label does not leak through surface features.

**Extension:** a trivial classifier trained on surface-only features (length, line count, font, framing, tier, whitespace) achieves:
- **ASCII**: AUC 0.556 (PASS)
- **QR**: AUC 0.5111 (PASS, with n=30 variance caveat)

**Files:** `ascii_dataset/shortcut_check.json`, `qr_dataset/shortcut_check.json`

### 2.12 Verification pipeline (six checks + hand review)

**Original:** no verification beyond the source author's construction.

**Extension:** six automated checks per channel (regeneration/round-trip, attack-word scan, deduplication, distribution comparison, tokenizer/version audit, hand-review sampling) plus a 40-row (ASCII) + 30-row (QR) hand review with semantic verification of every intent mapping.

**Files:** `verification/verification_report.json`, `verification/verification_log.csv`

### 2.13 Split structure (IID + LOFO + exploratory)

**Original:** no splits.

**Extension:**
- **IID split** — grouped by `intent_id`, 14 train / 3 val / 4 test intents, identical across families
- **LOFO channel splits** — QR-held-out and ASCII-held-out, one file per direction
- **Exploratory folds** — `art_only` leak tier held out, `ansi_shadow` block font held out

**Files:** `ascii_dataset/splits/`, `qr_dataset/splits/`

### 2.14 Frozen snapshots with CHANGELOGs

**Original:** no frozen version.

**Extension:** immutable `ascii_v1/` and `qr_v2/` snapshots with CHANGELOGs explaining what was frozen, known limitations (K1–K5), and why `qr_v2` supersedes `qr_v1`.

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

