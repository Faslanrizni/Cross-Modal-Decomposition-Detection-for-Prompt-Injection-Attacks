"""verify_audio.py — 8 checks; collision check is content-aware.

Expected: same audio_content + same voice -> same SHA (v4 corpus design).
Bug:      different audio_content -> same SHA (impossible with TTS; fail).
"""

import csv, json, wave
from pathlib import Path
from collections import defaultdict, Counter

rows = list(csv.DictReader(open(
    "audio_dataset/manifest/audio_manifest.csv", encoding="utf-8-sig")))
TRIAGE = {r["id"]: r for r in csv.DictReader(
              open("audio_dataset/triage/triage.csv", encoding="utf-8-sig"))
          if r["decision"] == "speakable"}

checks = {}

# 1. every audio file exists
checks["missing_files"] = [r["id"] for r in rows
                           if not Path(r["audio_path"]).exists()]

# 2. every file is 16 kHz mono PCM_16
bad_fmt = []
for r in rows:
    try:
        with wave.open(r["audio_path"], "rb") as w:
            if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (16000, 1, 2):
                bad_fmt.append(r["id"])
    except Exception as e:
        bad_fmt.append(f"{r['id']}:{type(e).__name__}")
checks["bad_format"] = bad_fmt

# 3. wrapper text present
checks["empty_wrapper"] = [r["id"] for r in rows if not r["text"].strip()]

# 4. ATTACK audio integrity — content-aware
by_sha_attacks = defaultdict(list)
for r in rows:
    if r["label"] == "attack":
        by_sha_attacks[r["audio_sha256"]].append(r)

expected_groups = {}    # sha -> {n, voice, content_preview}
real_collisions = []    # sha -> different contents or different voices

for sha, members in by_sha_attacks.items():
    if len(members) < 2: continue
    contents = set()
    unknown_sources = []
    for m in members:
        tri = TRIAGE.get(m["source_v4_id"])
        if tri is None:
            unknown_sources.append(m["source_v4_id"]); continue
        contents.add(tri["audio_content"])
    voices = {m["voice_id"] for m in members}
    if len(contents) == 1 and len(voices) == 1 and not unknown_sources:
        expected_groups[sha] = {
            "n_rows": len(members),
            "voice":   list(voices)[0],
            "content_preview": list(contents)[0][:60],
        }
    else:
        real_collisions.append({
            "sha": sha,
            "n_members": len(members),
            "n_unique_contents": len(contents),
            "n_unique_voices": len(voices),
            "unknown_sources": unknown_sources,
            "source_v4_ids": sorted({m["source_v4_id"] for m in members}),
        })

checks["attack_audio_real_collisions"] = real_collisions
checks["attack_audio_expected_shared_groups"] = {
    "n_groups": len(expected_groups),
    "n_rows_involved": sum(g["n_rows"] for g in expected_groups.values()),
    "group_size_distribution":
        dict(Counter(g["n_rows"] for g in expected_groups.values())),
    "voice_breakdown":
        dict(Counter(g["voice"] for g in expected_groups.values())),
    "note":
        "Same audio_content + same voice -> identical WAV. "
        "This is the v4 corpus's benign_text_full_injection design: "
        "6 wrapper variants per source, voice alternating per row, so each "
        "voice receives 3 byte-identical renders of the same attack.",
}

# 5. BENIGN audio rules
benign_hashes = [r["audio_sha256"] for r in rows if r["label"] == "benign"]
benign_counts = Counter(benign_hashes)
checks["benign_audio_overuse"] = {h: n for h, n in benign_counts.items() if n > 4}
checks["benign_equals_attack"] = list(set(benign_hashes) & set(by_sha_attacks))

# 6. duration distribution per tier and label
def dist(label, tier=None):
    sel = [float(r["duration_s"]) for r in rows
           if r["label"] == label
           and (tier is None or r["duration_match_tier"] == tier)]
    return {"n": len(sel),
            "mean": round(sum(sel)/len(sel), 3) if sel else 0,
            "min":  round(min(sel), 3) if sel else 0,
            "max":  round(max(sel), 3) if sel else 0}
checks["distribution"] = {
    "attack_strict":  dist("attack", "strict"),
    "benign_strict":  dist("benign", "strict"),
    "attack_relaxed": dist("attack", "relaxed"),
    "benign_relaxed": dist("benign", "relaxed"),
}

# 7. category counts
checks["categories"] = dict(Counter(r["attack_category"] for r in rows
                                    if r["label"] == "attack"))

# 8. pair parity
by_pair = defaultdict(list)
for r in rows: by_pair[r["pair_id"]].append(r)
pair_parity = {"missing": [], "voice": [], "text": [], "category": [], "method": []}
for pid, members in by_pair.items():
    if len(members) != 2: pair_parity["missing"].append(pid); continue
    a = next((m for m in members if m["label"] == "attack"), None)
    b = next((m for m in members if m["label"] == "benign"), None)
    if not (a and b): pair_parity["missing"].append(pid); continue
    if a["voice_id"] != b["voice_id"]:                 pair_parity["voice"].append(pid)
    if a["text"] != b["text"]:                         pair_parity["text"].append(pid)
    if a["attack_category"] != b["attack_category"]:   pair_parity["category"].append(pid)
    if a["audio_method"] != b["audio_method"]:         pair_parity["method"].append(pid)
checks["pair_parity"] = pair_parity

# verdict — only REAL collisions fail
checks["verdict"] = "PASS" if (
    not checks["missing_files"]
    and not checks["bad_format"]
    and not checks["empty_wrapper"]
    and not checks["attack_audio_real_collisions"]
    and not checks["benign_audio_overuse"]
    and not checks["benign_equals_attack"]
    and not pair_parity["missing"]
    and not pair_parity["voice"]
    and not pair_parity["text"]
    and not pair_parity["category"]
    and not pair_parity["method"]
) else "FAIL"

Path("audio_dataset/verification/verification_report.json").write_text(
    json.dumps(checks, indent=2, ensure_ascii=False))

print(json.dumps({
    "verdict":                              checks["verdict"],
    "missing_files":                        len(checks["missing_files"]),
    "bad_format":                           len(checks["bad_format"]),
    "empty_wrapper":                        len(checks["empty_wrapper"]),
    "attack_audio_real_collisions":         len(checks["attack_audio_real_collisions"]),
    "attack_audio_expected_shared_groups":  checks["attack_audio_expected_shared_groups"],
    "benign_audio_overuse":                 len(checks["benign_audio_overuse"]),
    "benign_equals_attack":                 len(checks["benign_equals_attack"]),
    "categories":                           checks["categories"],
    "distribution":                         checks["distribution"],
    "pair_parity":                          {k: len(v) for k, v in pair_parity.items()},
}, indent=2))