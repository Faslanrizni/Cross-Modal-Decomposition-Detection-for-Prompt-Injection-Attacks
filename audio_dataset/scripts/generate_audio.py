"""generate_audio.py — 684 attacks + 684 matched benigns = 1368 rows.

Two-tier matching:
  strict  ±10% (primary, P3-compliant)
  relaxed ±20% (fallback for the long tail — documented in the report)

Attack-render cache in audio_dataset/audio/_attack_cache/ keyed by
(v4_id, voice_id), so retries skip re-rendering."""
import csv, json, random, hashlib, librosa, pyttsx3, numpy as np, soundfile as sf
from pathlib import Path

SEED   = 42
CFG    = json.loads(Path("audio_dataset/audio_config.json").read_text())
PROV   = json.loads(Path("audio_dataset/provenance.json").read_text())
BENIGN = json.loads(Path("audio_dataset/audio/_benign_cache/index.json").read_text())
TRIAGE = [r for r in csv.DictReader(
              open("audio_dataset/triage/triage.csv", encoding="utf-8-sig"))
          if r["decision"] == "speakable"]

AUDIO        = Path("audio_dataset/audio"); AUDIO.mkdir(exist_ok=True)
RAW          = Path("audio_dataset/audio/_raw"); RAW.mkdir(exist_ok=True)
ATTACK_CACHE = Path("audio_dataset/audio/_attack_cache"); ATTACK_CACHE.mkdir(exist_ok=True)

rng = random.Random(SEED)
used_benigns = {}
MAX_USES_PER_BENIGN = 4

TOL_STRICT  = CFG["duration_tolerance_pct"] / 100.0   # 0.10
TOL_RELAXED = 0.20

def find_voice_id(engine, requested_name):
    voices = engine.getProperty("voices")
    for v in voices:
        if v.name == requested_name: return v.id
    for token in requested_name.split():
        if token in ("Microsoft", "Desktop"): continue
        for v in voices:
            if token in v.name: return v.id
    raise RuntimeError(f"no SAPI voice for {requested_name!r}")

def render_trim(text, voice, out):
    raw = RAW / (out.stem + "_raw.wav")
    e = pyttsx3.init("sapi5")
    e.setProperty("voice", find_voice_id(e, voice["name"]))
    e.setProperty("rate",   voice["rate"])
    e.setProperty("volume", voice["volume"])
    e.save_to_file(text, str(raw)); e.runAndWait(); e.stop()
    y, _ = librosa.load(str(raw), sr=16000, mono=True)
    y, _ = librosa.effects.trim(y, top_db=CFG["silence_trim_top_db"])
    peak = np.max(np.abs(y)) or 1.0
    y = y / peak * CFG["peak_normalise_target"]
    sf.write(str(out), y, 16000, subtype="PCM_16")
    return len(y) / 16000

def render_attack_cached(v4_id, text, voice, out):
    cache_path = ATTACK_CACHE / f"{v4_id}_{voice['id']}.wav"
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        out.write_bytes(cache_path.read_bytes())
        return librosa.get_duration(path=str(out))
    d = render_trim(text, voice, out)
    cache_path.write_bytes(out.read_bytes())
    return d

def pick_benign_two_tier(voice_id, target_dur, attack_id):
    for tol, tier in ((TOL_STRICT, "strict"), (TOL_RELAXED, "relaxed")):
        pool = []
        for r in BENIGN:
            if r["voice"] != voice_id: continue
            key = (voice_id, r["text"])
            if used_benigns.get(key, 0) >= MAX_USES_PER_BENIGN: continue
            if abs(r["duration_s"] - target_dur) > tol * target_dur: continue
            pool.append((abs(r["duration_s"] - target_dur),
                         r["text"], r["path"], r["duration_s"]))
        if pool:
            pool.sort()
            c = rng.choice(pool[:5])
            return c[0], c[1], c[2], c[3], tier
    raise RuntimeError(
        f"no benign within ±{int(TOL_RELAXED*100)}% of {target_dur:.2f}s for "
        f"{attack_id} (voice={voice_id}). "
        f"Add longer benigns to phrasings.json or raise TOL_RELAXED.")

# --- cache recovery from the partial run ---
print("Populating attack cache from partial previous run (if any)...")
recovered = 0
for idx, r in enumerate(TRIAGE):
    voice = CFG["voices"][idx % len(CFG["voices"])]
    cp    = ATTACK_CACHE / f"{r['id']}_{voice['id']}.wav"
    if cp.exists(): continue
    old   = AUDIO / f"AUD-{2*idx+1:06d}.wav"
    if old.exists() and old.stat().st_size > 1000:
        cp.write_bytes(old.read_bytes())
        recovered += 1
print(f"Recovered {recovered} attack renders from the partial run.")

rows, pairs = [], []
excluded    = []
nid, pid = 1, 1
tier_counts = {"strict": 0, "relaxed": 0, "excluded": 0}
start_total = len(TRIAGE)

for idx, r in enumerate(TRIAGE):
    voice = CFG["voices"][idx % len(CFG["voices"])]
    aid   = f"AUD-{nid:06d}"
    apath = AUDIO / f"{aid}.wav"
    adur  = render_attack_cached(r["id"], r["audio_content"], voice, apath)

    # Pair — do this BEFORE emitting the attack row, so exclusion is clean
    try:
        delta, btext, bpath_cached, bdur, tier = pick_benign_two_tier(
            voice["id"], adur, aid)
    except RuntimeError as e:
        tier_counts["excluded"] += 1
        excluded.append({
            "v4_id": r["id"], "attack_category": r["category"],
            "voice_id": voice["id"], "duration_s": round(adur, 3),
            "reason": str(e),
        })
        print(f"  EXCLUDED {r['id']} ({r['category']}, {adur:.2f}s): no match")
        continue

    # attack row
    rows.append({
        "id": aid, "label": "attack", "pair_id": f"PAIR-{pid:05d}",
        "source_v4_id": r["id"], "attack_category": r["category"],
        "encoding_family": "audio", "modality": "audio",
        "input_modality_for_training": "waveform_and_text",
        "text": r["text"], "text_len": len(r["text"]),
        "audio_method": r["audio_method"], "voice_id": voice["id"],
        "audio_path": str(apath),
        "audio_sha256": hashlib.sha256(apath.read_bytes()).hexdigest(),
        "duration_s": round(adur, 3),
        "duration_match_tier": tier,
        "source_file": r["source_file"],
        "label_method": "authored_from_v4_payload",
        "attack_source": r["attack_source"],
        "attack_reference": r["attack_reference"],
        "dataset_revision": PROV["taxonomy"],
        "derivation_hash_phrasings": PROV["phrasings"],
        "licence": "HuggingFace standard",
        "split": "", "split_group": r["category"],
    })
    nid += 1

    # benign row (copy from cache)
    key = (voice["id"], btext)
    used_benigns[key] = used_benigns.get(key, 0) + 1
    tier_counts[tier] += 1
    bpath = AUDIO / f"AUD-{nid:06d}.wav"
    bpath.write_bytes(Path(bpath_cached).read_bytes())

    rows.append({
        "id": f"AUD-{nid:06d}", "label": "benign", "pair_id": f"PAIR-{pid:05d}",
        "source_v4_id": r["id"], "attack_category": r["category"],
        "encoding_family": "audio", "modality": "audio",
        "input_modality_for_training": "waveform_and_text",
        "text": r["text"], "text_len": len(r["text"]),
        "audio_method": r["audio_method"], "voice_id": voice["id"],
        "audio_path": str(bpath),
        "audio_sha256": hashlib.sha256(bpath.read_bytes()).hexdigest(),
        "duration_s": round(bdur, 3),
        "duration_match_tier": tier,
        "source_file": "generated_from_benign_pool",
        "label_method": "generated_from_benign_pool",
        "attack_source": "", "attack_reference": "",
        "dataset_revision": PROV["taxonomy"],
        "derivation_hash_phrasings": PROV["phrasings"],
        "licence": "HuggingFace standard",
        "split": "", "split_group": r["category"],
    })
    nid += 1; pid += 1
    pairs.append({"aid": aid, "adur": adur, "bdur": bdur,
                  "delta": delta, "tier": tier})

    if (idx + 1) % 50 == 0:
        print(f"  [{idx+1}/{start_total}] strict={tier_counts['strict']} "
              f"relaxed={tier_counts['relaxed']} excluded={tier_counts['excluded']}")

# --- writes ---
Path("audio_dataset/manifest").mkdir(exist_ok=True)
with open("audio_dataset/manifest/audio_manifest.csv", "w",
          newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

if excluded:
    with open("audio_dataset/triage/audio_exclusions.csv", "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(excluded[0]))
        w.writeheader(); w.writerows(excluded)

strict_pairs  = [p for p in pairs if p["tier"] == "strict"]
relaxed_pairs = [p for p in pairs if p["tier"] == "relaxed"]

report = {
    "n_attack_pairs_total":         len(pairs),
    "n_strict_pairs":               len(strict_pairs),
    "n_relaxed_pairs":              len(relaxed_pairs),
    "n_excluded_attacks":           len(excluded),
    "strict_pct_of_manifest":       round(len(strict_pairs) / len(pairs), 4) if pairs else 0,
    "relaxed_pct_of_manifest":      round(len(relaxed_pairs) / len(pairs), 4) if pairs else 0,
    "delta_mean_s_strict":          round(float(np.mean([p["delta"] for p in strict_pairs])), 3) if strict_pairs else 0,
    "delta_max_s_strict":           round(float(np.max([p["delta"] for p in strict_pairs])), 3) if strict_pairs else 0,
    "delta_mean_s_relaxed":         round(float(np.mean([p["delta"] for p in relaxed_pairs])), 3) if relaxed_pairs else 0,
    "delta_max_s_relaxed":          round(float(np.max([p["delta"] for p in relaxed_pairs])), 3) if relaxed_pairs else 0,
    "tolerance_strict_pct":         int(TOL_STRICT * 100),
    "tolerance_relaxed_pct":        int(TOL_RELAXED * 100),
    "unique_benign_texts_used":     len(used_benigns),
    "max_reuses_per_benign":        max(used_benigns.values()) if used_benigns else 0,
}
Path("audio_dataset/duration_report.json").write_text(json.dumps(report, indent=2))
print()
print(json.dumps(report, indent=2))
print(f"\nManifest rows: {len(rows)}")
print(f"Excluded:      {len(excluded)} attacks (see triage/audio_exclusions.csv)")