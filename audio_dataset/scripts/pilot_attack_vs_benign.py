"""pilot_attack_vs_benign.py — can Whisper-base separate attacks from benigns?"""
import json, csv, pyttsx3, librosa, numpy as np, torch
from pathlib import Path
from transformers import WhisperModel, WhisperProcessor

CFG = json.loads(Path("audio_dataset/audio_config.json").read_text())
TRIAGE = [r for r in csv.DictReader(
    open("audio_dataset/triage/triage.csv", encoding="utf-8-sig"))
    if r["decision"] == "speakable"]

# 5 attacks, one per speakable category
by_cat = {}
for r in TRIAGE: by_cat.setdefault(r["category"], []).append(r)
attacks = [by_cat[c][0] for c in sorted(by_cat)][:5]

# 5 benign phrases drawn from the plain v2 benign pool style
benigns = [
    "Display the store hours.",
    "Summarise this text.",
    "Translate this passage into French.",
    "Add milk and eggs to my shopping list.",
    "Read me the headlines.",
]

OUT = Path("audio_dataset/pilot"); OUT.mkdir(exist_ok=True)

def find_voice_id(engine, requested_name):
    voices = engine.getProperty("voices")
    for v in voices:
        if v.name == requested_name: return v.id
    for token in requested_name.split():
        if token in ("Microsoft", "Desktop"): continue
        for v in voices:
            if token in v.name: return v.id
    raise RuntimeError(f"no SAPI voice for {requested_name!r}")

def render(text, voice_name, out):
    e = pyttsx3.init("sapi5")
    e.setProperty("voice", find_voice_id(e, voice_name))
    e.setProperty("rate", 175)
    e.save_to_file(text, str(out)); e.runAndWait(); e.stop()

MODEL = WhisperModel.from_pretrained("openai/whisper-base").encoder.eval()
PROC  = WhisperProcessor.from_pretrained("openai/whisper-base")

def embed(path):
    y, _ = librosa.load(str(path), sr=16000, mono=True)
    y, _ = librosa.effects.trim(y, top_db=30)
    inp = PROC(y, sampling_rate=16000, return_tensors="pt").input_features
    with torch.no_grad():
        h = MODEL(inp).last_hidden_state
    n = min(int(np.ceil(len(y) / 16000 * 50)), h.shape[1])
    v = h[0, :n].mean(0)
    return v / v.norm()

def cos(a, b): return float(torch.dot(a, b).item())

voice = CFG["voices"][0]     # both sets use David — voice is held constant
attack_embs, benign_embs = [], []

for i, a in enumerate(attacks):
    p = OUT / f"pilot_attack_{i}_{a['category']}.wav"
    render(a["audio_content"], voice["name"], p)
    attack_embs.append(embed(p))

for i, b in enumerate(benigns):
    p = OUT / f"pilot_benign_{i}.wav"
    render(b, voice["name"], p)
    benign_embs.append(embed(p))

aa = [cos(attack_embs[i], attack_embs[j])
      for i in range(len(attack_embs)) for j in range(i+1, len(attack_embs))]
bb = [cos(benign_embs[i], benign_embs[j])
      for i in range(len(benign_embs)) for j in range(i+1, len(benign_embs))]
ab = [cos(a, b) for a in attack_embs for b in benign_embs]

within  = (np.mean(aa) + np.mean(bb)) / 2
between = np.mean(ab)
gap     = within - between

report = {
    "n_attacks":                 len(attacks),
    "n_benigns":                 len(benigns),
    "mean_sim_attack_vs_attack": round(float(np.mean(aa)), 4),
    "mean_sim_benign_vs_benign": round(float(np.mean(bb)), 4),
    "mean_sim_attack_vs_benign": round(float(np.mean(ab)), 4),
    "gap_within_minus_between":  round(float(gap), 4),
    "verdict": (
        "PASS — attack and benign separable" if gap > 0.05 else
        "MARGINAL — flag in decisions.md"   if gap > 0.02 else
        "FAIL — channel not separable"
    ),
}
Path("audio_dataset/pilot_report.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))