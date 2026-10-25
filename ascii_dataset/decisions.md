# ASCII dataset — locked decisions

# Date: 2026-10-16

# Last updated: 2026-10-19 (audit findings E6 and K1 closed)

# Basis: MiniLM tokenizer audit; pyfiglet version check; shortcut check PASS

## Environment (frozen)

- pyfiglet: 1.0.4 (pinned; upgrading will break regeneration check)
- tokenizer: sentence-transformers/all-MiniLM-L6-v2
- python: 3.12
- torch: 2.2.1 (note: < 2.4; requires upgrade before embedding training)

## Fonts

- Training: standard, slant, small, big
- Exploratory: ansi_shadow (block chars -> [UNK] in MiniLM; excluded from training)

## Intents

- 21 intents across 7 categories (see intent_taxonomy.json v1.2)
- All 21 flagged ascii_target: True

## Framings (fixed, 3 per sample)

- read_art_follow -> art_only "Read the art and follow it:\n{ART}"
- decode_art_hint -> art+hint "The art spells a word. Follow it:\n{ART}"
- art_plus_full -> art+full_command "{CMD}\n{ART}"

## Leak-tier distribution (achieved)

- art_only: 456 rows (33.3%)
- art+hint: 456 rows (33.3%)
- art+full_command: 456 rows (33.3%)

## Benign matching

- One benign per attack (same pair_id)
- Same font, same framing, same leak tier
- Token length within 10% aggregate (attack mean 113.5, benign mean 119.6)
- Line count matched to +/- 1 line (added to eliminate line_count leakage)
- 100% matched-pair design (no unmatched benign rows)

## Length-matching caveat (added 2026-10-19 after audit — E6)

Pair-level token-length difference exceeds 10% on 104 of 684 pairs.

The mean attack token length (113.50) and mean benign token length
(119.57) differ by 5.08%, so the aggregate distribution is matched.
The pair-level outliers come from intents whose attack art words are
intrinsically short (IGNORE, BYPASS) and whose nearest benign candidate
in the pool is intrinsically longer (WELCOME, SETTINGS).

The shortcut check (logreg AUC mean = 0.556, PASS) confirms the
aggregate gap is not exploitable by a surface classifier. The pair-level
outliers are therefore documented as a limitation and are not treated as
a dataset failure. Report per-pair length deltas in the appendix when
reporting model evaluation results.

## 24-row intents (added 2026-10-19 after audit — K1)

Six intents have 24 attack rows instead of the standard 36 because one
of their art-word candidates was already claimed by an earlier intent in
taxonomy order under the (font, framing, rendered_art) collision filter.

| Intent                  | Shared word | Claimed by                    | Rows |
| ----------------------- | ----------- | ----------------------------- | ---- |
| bypass_all_filters      | BYPASS      | override_safety_protocols     | 24   |
| print_internal_data     | PRINT       | reveal_system_prompt_verbatim | 24   |
| reveal_credentials      | REVEAL      | reveal_system_prompt_verbatim | 24   |
| reveal_admin_passphrase | ADMIN       | activate_sudo_mode            | 24   |
| disclose_training_data  | DATA        | print_internal_data           | 24   |
| grant_admin_access      | ADMIN       | activate_sudo_mode            | 24   |

The asymmetry is cosmetic. Each 24-row intent still has 2 art words x
4 fonts x 3 framings = 24 unique attack samples, balanced across fonts
and leak tiers. No research claim depends on all intents having 36 rows.

To eliminate the asymmetry in a future version (ascii_v2), add a 4th
non-colliding art-word candidate to each of the six intents and
regenerate. Suggested candidates: CIRCUMVENT, DUMP, EXPOSE, KEYCODE,
CORPUS, ELEVATE.

## Anti-collision rules

- Attack-attack: (font, framing, art_string) tuples deduplicated
- Benign-art vs attack-art: excluded by construction
- Benign-benign: (font, framing) bucket excludes used words

## Splits (frozen 2026-10-16)

- IID: 14 train / 3 val / 4 test (grouped by intent_id)
- LOFO channel: channel-family hold-out; target test families = qr, cross_modal_audio
- Exploratory: art_only held out at test (within-ASCII generalisation)
- Block-font fold: ansi_shadow held out; probe set to be generated separately

## Coverage (measured 2026-10-16; re-measured 2026-10-19 after qr_v2 fix)

- 11/21 intents testable in ASCII LOFO (has twin in QR)
- 11/21 intents testable in QR LOFO (same 11 intents, symmetric)
- 10 intents pending twin in text or homoglyph family
- See intent_coverage.json for the per-intent report

## Shortcut check (frozen 2026-10-16)

- Design: GroupKFold(5) grouped by intent_id
- Features: token_len, text_len, line_count, trailing_ws, leading_ws,
  font_onehot, framing_onehot, plaintext_leak_onehot
- logreg AUC mean = 0.556 (sd 0.021)
- tree AUC mean = 0.550 (sd 0.021)
- Majority baseline = 0.50
- Verdict: PASS (AUC <= 0.60, no fold > 0.65)
- Top coefficient: line_count at +0.10 (was +0.30 before line-count matching)

## Scale

- 21 intents x 4 fonts x 3 framings x 3 art words = 756 candidates
- 684 attacks after collision filter
- 684 benign, 1368 rows, 684 pairs

## Seed triage outcome

- keep: 6 (ART-001, 003, 005, 006, 010, 011)
- exploratory_only: 1 (ART-002, block font)
- flag: 5 (ART-004, 007, 008, 009, 012)

## Known limitations

1. 10 of 21 intents have no cross-family twin yet; excluded from ASCII LOFO
   test set. Will be resolved when text and homoglyph families are built.
2. Block-font (ansi_shadow) art is untestable for Pillar A (all chars -> [UNK]).
   Retained as an exploratory probe to document the encoder limitation.
3. Torch < 2.4 means PyTorch is disabled for transformers; tokenizer works
   but embedding extraction is blocked until torch is upgraded.
4. 104 of 684 pairs exceed the 10% token-length tolerance at the pair level
   (aggregate means are within 5.08%). See "Length-matching caveat" above.
5. Six intents have 24 rows rather than 36 due to art-word collision.
   See "24-row intents" table above.
