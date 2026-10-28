"""preflight_speaker_check.py — does Whisper cluster by content or voice?"""
import json, csv, pyttsx3, librosa, numpy as np, torch, soundfile as sf
from pathlib import Path
from transformers import WhisperModel, WhisperProcessor

CFG = json.loads(Path("audio_dataset/audio_config.json").read_text())
SPEAK = set(CFG["speakable_categories"])
TRIAGE = list(csv.DictReader(open("audio_dataset/triage/triage.csv",
                                encoding="utf-8-sig")))
OUT = Path("audio_dataset/preflight"); OUT.mkdir(exist_ok=True)

MODEL = WhisperModel.from_pretrained("openai/whisper-base").encoder.eval()
PROC  = WhisperProcessor.from_pretrained("openai/whisper-base")

# Pick 5 sample attacks, one per speakable category
by_cat = {}
for r in TRIAGE:
    if r["decision"] != "speakable": continue
    by_cat.setdefault(r["category"], []).append(r)
samples = [by_cat[c][0] for c in sorted(by_cat)]

def find_voice_id(engine, requested_name):
    """SAPI appends ' - English (United States)' to voice names.
    Try exact, then token-based match on the meaningful word."""
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
        f"no SAPI voice matches {requested_name!r}; "
        f"available: {[v.name for v in voices]}"
    )


def render(text, voice_name, out):
    e = pyttsx3.init("sapi5")
    e.setProperty("voice", find_voice_id(e, voice_name))
    e.setProperty("rate", 175)
    e.save_to_file(text, str(out)); e.runAndWait(); e.stop()

def embed(path):
    y, _ = librosa.load(str(path), sr=16000, mono=True)
    y, _ = librosa.effects.trim(y, top_db=30)
    inp = PROC(y, sampling_rate=16000, return_tensors="pt").input_features
    with torch.no_grad():
        h = MODEL(inp).last_hidden_state          # (1, 1500, 512)
    # Mean-pool over VALID frames only
    n_frames = min(int(np.ceil(len(y)/16000*50)), h.shape[1])
    pooled = h[0, :n_frames].mean(0)
    return pooled / pooled.norm()

embs = {}
for r in samples:
    for v in CFG["voices"]:
        p = OUT / f"{r['id']}_{v['id']}.wav"
        if not p.exists():
            render(r["audio_content"], v["name"], p)
        embs[(r["id"], v["id"])] = embed(p)

same_sent_diff_voice, diff_sent_same_voice = [], []
for r in samples:
    same_sent_diff_voice.append(
        float(torch.dot(embs[(r["id"], "voice_male")],
                        embs[(r["id"], "voice_female")])))
for r1 in samples:
    for r2 in samples:
        if r1["id"] == r2["id"]: continue
        diff_sent_same_voice.append(
            float(torch.dot(embs[(r1["id"], "voice_male")],
                            embs[(r2["id"], "voice_male")])))

ms = float(np.mean(same_sent_diff_voice))
md = float(np.mean(diff_sent_same_voice))
delta = ms - md
report = {
    "n_samples": len(samples),
    "mean_sim_same_sent_diff_voice": round(ms, 4),
    "mean_sim_diff_sent_same_voice": round(md, 4),
    "delta": round(delta, 4),
    "verdict": "PASS" if delta > 0.10 else "FAIL — voice dominates content",
}
Path("audio_dataset/preflight_report.json").write_text(
    json.dumps(report, indent=2))
print(json.dumps(report, indent=2))