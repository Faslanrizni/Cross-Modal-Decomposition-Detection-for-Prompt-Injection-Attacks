# Audio Channel v1 — Design Decisions

## 1. Scope

Component A: channel-shift audio, supporting RQ1 as a held-out modality.
Component B (decomposition fragments) deferred to the decomposition
generator and not part of this snapshot.

## 2. Category triage

The v4 payload corpus is 1,704 delivery rows across 14 categories. A row
is audio-eligible if and only if its `audio_content` is a spoken utterance
that carries the attack through its meaning, the perturbation survives TTS,
and no visual / JSON / XML / codepoint structure is required.

### Included (5 categories, 684 speakable rows after triage)

| Category                     | Rows |
| ---------------------------- | ---- |
| beast_suffixes               | 210  |
| cipher_jailbreaks            | 114  |
| instruction_hierarchy_bypass | 90   |
| memory_poisoning             | 150  |
| multi_agent_contagion        | 120  |

### Excluded (9 categories, 1,020 rows)

`audio_adversarial_asr`, `chart_diagram_injection`, `computer_use_injection`,
`detector_evasion`, `mcp_tool_injection`, `pdf_active_content`,
`rag_chunk_boundary`, `reasoning_token_injection`, `unicode_tag_smuggling`.
Per-row reasons in `triage/exclusions.csv`.

### Payload-level further exclusions (17 rows)

Of the 684 speakable rows, 17 were excluded during duration matching:

- 6 cipher at 37.7–39.55 s (Morse/Base64 spoken character-by-character
  is not decodable as a cipher; no content check can verify it)
- 11 multi-agent at 9.54–10.05 s (JSON payloads just above the ±20 %
  relaxed-tier ceiling)

Full list in `triage/audio_exclusions.csv`.

Final manifest: **1,334 rows = 667 attack/benign pairs**.

## 3. Preflight

Whisper-base's 512-d encoder tested on 5 samples × 2 voices:

- `mean_sim_same_sent_diff_voice`: 0.9949
- `mean_sim_diff_sent_same_voice`: 0.9220
- delta: **0.0729** → MARGINAL

Attack-vs-benign pilot:

- attack_vs_attack: 0.922
- benign_vs_benign: 0.887
- attack_vs_benign: 0.643
- gap: **0.2614** → PASS (5× threshold)

The pilot is the metric that matters for RQ1. Whisper-base is
voice-invariant but content-sensitive at the attack/benign boundary.

## 4. Duration matching (P3)

Silence-trimmed, two-tier tolerance:

- **strict (±10 %)**: 603 pairs, mean delta 0.197 s — **primary RQ1 result**
- **relaxed (±20 %)**: 64 pairs, mean delta 1.56 s — documented limitation

Every row carries `duration_match_tier`. Primary RQ1 evaluation is
computed on `duration_match_tier == "strict"` only.

## 5. Reproducibility (P4)

pyttsx3 + SAPI5 on the same Windows install renders byte-identically.
Across machines it may not, so P4 is enforced by round-trip verification,
not by byte-identical regeneration.

The `find_voice_id` helper in every generation script matches "David" /
"Zira" as substrings because SAPI appends " - English (United States)"
to the voice names. The exact-match form fails silently and renders both
voices with the default voice — this was caught during preflight and fixed
in all four generation scripts.

## 6. Benign reuse (P2)

Benign audio may repeat up to `MAX_USES_PER_BENIGN = 4` times. Attack
audio integrity is verified by check 4. Reuse is on the benign side only
and does not affect P2.

## 7. Round-trip verification (P4)

Content verification uses **WER ≤ category_threshold OR keyword recall
≥ 0.55**. The OR semantics reflect that content verification asks "did
the ASR hear the attack?", not "did wav2vec2 spell every word correctly?".
wav2vec2-large-960h is a character-level CTC model with a floor of 10–15 %
WER on clean TTS English, higher on markup and adversarial suffixes.

### Per-category thresholds

| Category                     | Mode       | WER ≤ | KR ≥ |
| ---------------------------- | ---------- | ----- | ---- |
| beast_suffixes               | content    | 0.40  | 0.55 |
| cipher_jailbreaks            | structural | —     | —    |
| instruction_hierarchy_bypass | content    | 0.50  | 0.55 |
| memory_poisoning             | content    | 0.45  | 0.55 |
| multi_agent_contagion        | content    | 0.60  | 0.55 |
| benign                       | content    | 0.40  | 0.55 |

### Why cipher is structural

wav2vec2 has never seen ciphertext. No ASR transcribes
"Ljqruh suhylrxv lqvwuxfwlrqv" faithfully. The correct P4 check for
cipher is structural: WAV exists, well-formed 16 kHz mono PCM_16,
non-silent, correct duration. Faithfulness to the intended ciphertext
is confirmed by generation-time TTS determinism.

### Final pass rate

1316 / 1334 = **98.7 %**. The 18 residuals are wav2vec2 spelling errors
on bracketed markup and underscores. Full list in
`verification/roundtrip.json → failures`. Manual listening on 5 samples
confirmed audio faithfulness.

### Threshold calibration note

Thresholds were chosen after observing the pilot distribution on the
same 1,334 rows. This is legitimate for verification-method calibration,
not for evaluation-metric tuning. The primary evaluation metric — AUC
on the strict tier — remains pre-registered at ≤ 0.60.

## 8. Input modality

Every row carries `input_modality_for_training: waveform_and_text`.
The training loop must pass both `text` (encoder input) and `audio_path`
(waveform input). Neither alone is sufficient — the attack is the pair.

## 9. Shortcut check

- strict AUC: **0.5185**, std 0.0199 — essentially chance
- full AUC: 0.5223, std 0.0288

Surface features (duration, file size, text length, RMS, ZCR, voice,
method, category) cannot separate the classes. All legitimate signal is
in the audio content.

## 10. Attack audio shared across wrappers

The v4 corpus emits **6 delivery rows per v4 source**, all sharing one
`audio_content` but with different wrapper `text` (strategy:
`benign_text_full_injection`). Voice alternates per manifest row, so
each source produces **two SHA groups of 3 rows each** (one per voice).

- **222 attack-SHA groups of 3 rows** — expected shared, not a defect
- **0 real collisions** (different content or different voice, same SHA)

This is a genuine corpus property, not a bug:

1. Faithful to the corpus design.
2. Tests wrapper-invariance: same audio under 6 different prompts should
   be flagged regardless of wrapper.
3. Split hygiene: all 6 variants of a source land in the same
   `split_group` (category), so no attack appears in both train and test.
4. Shortcut AUC of 0.5185 empirically confirms the shared audio introduces
   no leak.

Verifier distinguishes `attack_audio_expected_shared_groups` (same content

- voice → same SHA, informational) from `attack_audio_real_collisions`
  (different content or voice → same SHA, must be 0).

## 11. Known limitations

1. **TTS-only domain.** Attack and benign audio are both synthetic.
   Real human speech is untested. Model cannot be claimed to generalise
   to human speakers.
2. **Two SAPI voices.** David and Zira.
3. **Duration is the primary leak vector.** Shortcut AUC 0.5185 confirms
   the current dataset is clean on this vector.
4. **Category coverage is 5 of 14.** The 9 excluded categories are
   documented per-row in `triage/exclusions.csv`.
5. **Component B (decomposition fragments) not in this build.**
6. **17 speakable attacks excluded** — `triage/audio_exclusions.csv`.
7. **18 round-trip residuals** — `verification/roundtrip.json`.
8. **222 attack audio SHA groups** — expected, documented in §10.

## 12. Files in this snapshot

frozen/audio_v1/
manifest/audio_manifest.csv 1,334 rows
triage/triage.csv 1,704-row triage record
triage/exclusions.csv 1,020 category-level exclusions
triage/audio_exclusions.csv 17 payload-level exclusions
splits/\*.json 11 split files
verification/roundtrip.json final content check
verification/roundtrip_partial.json per-row ASR hypotheses
verification/verification_report.json 8-check PASS
verification/hand_review_sample.csv
verification/verification_log.csv
preflight_report.json speaker gate
duration_report.json strict/relaxed statistics
shortcut_check.json tier-aware AUC 0.5185
intent_taxonomy.json
phrasings.json
audio_config.json
provenance.json
decisions.md this file
CHANGELOG.md
