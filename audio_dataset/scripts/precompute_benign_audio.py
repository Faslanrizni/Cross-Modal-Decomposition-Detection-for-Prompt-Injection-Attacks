"""precompute_benign_audio.py — cache 210 benigns × 2 voices with voice fix."""
import json, pyttsx3, librosa, numpy as np, soundfile as sf
from pathlib import Path

CFG   = json.loads(Path("audio_dataset/audio_config.json").read_text())
PHR   = json.loads(Path("audio_dataset/phrasings.json").read_text())
CACHE = Path("audio_dataset/audio/_benign_cache"); CACHE.mkdir(parents=True, exist_ok=True)
RAW   = Path("audio_dataset/audio/_raw");          RAW.mkdir(parents=True, exist_ok=True)

def find_voice_id(engine, requested_name):
    """SAPI appends ' - English (United States)'; match on the meaningful token."""
    voices = engine.getProperty("voices")
    for v in voices:
        if v.name == requested_name:
            return v.id
    for token in requested_name.split():
        if token in ("Microsoft", "Desktop"):
            continue
        for v in voices:
            if token in v.name:
                return v.id
    raise RuntimeError(
        f"no SAPI voice for {requested_name!r}; "
        f"available: {[v.name for v in voices]}")

def render_raw(text, voice_name, rate, out):
    e = pyttsx3.init("sapi5")
    e.setProperty("voice", find_voice_id(e, voice_name))
    e.setProperty("rate", rate)
    e.save_to_file(text, str(out)); e.runAndWait(); e.stop()

def trim_and_norm(in_path, out_path):
    y, _ = librosa.load(str(in_path), sr=16000, mono=True)
    y, _ = librosa.effects.trim(y, top_db=CFG["silence_trim_top_db"])
    peak = np.max(np.abs(y)) or 1.0
    y = y / peak * CFG["peak_normalise_target"]
    sf.write(str(out_path), y, 16000, subtype="PCM_16")
    return len(y) / 16000

cache = []
benign_texts = (list(PHR.get("benign_commands", []))
                + list(PHR.get("benign_commands_long", [])))
cache = []
n_sentences = len(benign_texts)
print(f"benign texts: {len(PHR.get('benign_commands',[]))} short + "
      f"{len(PHR.get('benign_commands_long',[]))} long = {n_sentences}")
for voice in CFG["voices"]:
    print(f"Voice: {voice['id']} -> {voice['name']!r}")
    for i, text in enumerate(benign_texts):
        raw   = RAW   / f"{voice['id']}_{i:04d}_raw.wav"
        final = CACHE / f"{voice['id']}_{i:04d}.wav"
        if not raw.exists():
            render_raw(text, voice["name"], voice["rate"], raw)
        d = trim_and_norm(raw, final) if not final.exists() \
            else librosa.get_duration(path=str(final))
        cache.append({"voice": voice["id"], "text": text,
                      "path": str(final), "duration_s": round(d, 3)})

Path("audio_dataset/audio/_benign_cache/index.json").write_text(
    json.dumps(cache, indent=2))
print(f"cached {len(cache)} ({n_sentences} sentences × {len(CFG['voices'])} voices)")