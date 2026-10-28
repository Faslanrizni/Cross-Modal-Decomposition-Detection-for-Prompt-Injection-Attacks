"""roundtrip_verify.py — wav2vec2 ASR round-trip with progress + resume.

- Prints progress every 25 files.
- Saves partial results to verification/roundtrip_partial.json every 50 files.
- On restart, skips files already present in the partial file.
- Compares ASR output to the actual spoken content (attack: audio_content
  from triage; benign: original text from benign cache index).
"""
import csv, json, re, hashlib
from pathlib import Path
import torch, librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

CFG     = json.loads(Path("audio_dataset/audio_config.json").read_text())
BENIGN  = json.loads(Path("audio_dataset/audio/_benign_cache/index.json").read_text())
TRIAGE  = [r for r in csv.DictReader(
              open("audio_dataset/triage/triage.csv", encoding="utf-8-sig"))
           if r["decision"] == "speakable"]
PARTIAL = Path("audio_dataset/verification/roundtrip_partial.json")
OUT     = Path("audio_dataset/verification/roundtrip.json")

attack_text = {r["id"]: r["audio_content"] for r in TRIAGE}
benign_text = {hashlib.sha256(Path(b["path"]).read_bytes()).hexdigest(): b["text"]
               for b in BENIGN}

MODEL = Wav2Vec2ForCTC.from_pretrained(CFG["asr_for_verification"]).eval()
PROC  = Wav2Vec2Processor.from_pretrained(CFG["asr_for_verification"])
STOP  = set("the a an and or of to in on for is are was were be been being "
            "it its this that these those i you he she they we me my your "
            "our their with at by from as so if then".split())

def transcribe(path):
    y, _ = librosa.load(path, sr=16000, mono=True)
    y, _ = librosa.effects.trim(y, top_db=CFG["silence_trim_top_db"])
    inp = PROC(y, sampling_rate=16000, return_tensors="pt").input_values
    with torch.no_grad():
        ids = torch.argmax(MODEL(inp).logits, dim=-1)[0]
    return PROC.decode(ids, skip_special_tokens=True).lower()

def norm(s): return re.sub(r"[^a-z0-9 ]", " ", s.lower()).strip()

def wer(ref, hyp):
    import jiwer
    return jiwer.wer(norm(ref), norm(hyp)) if ref.strip() else 0.0

def keyword_recall(ref, hyp):
    ref_kw = {w for w in norm(ref).split() if w not in STOP and len(w) > 2}
    return len(ref_kw & set(norm(hyp).split())) / len(ref_kw) if ref_kw else 1.0

rows = list(csv.DictReader(open("audio_dataset/manifest/audio_manifest.csv",
                                   encoding="utf-8-sig")))
results = json.loads(PARTIAL.read_text()) if PARTIAL.exists() else {}
print(f"resuming with {len(results)} of {len(rows)} already done")

for i, r in enumerate(rows, 1):
    if r["id"] in results:
        continue
    expected = attack_text.get(r["source_v4_id"]) if r["label"] == "attack" \
               else benign_text.get(r["audio_sha256"])
    if not expected:
        results[r["id"]] = {"id": r["id"], "label": r["label"],
                            "ok": False, "reason": "no_expected_text"}
        continue
    hyp = transcribe(r["audio_path"])
    w, kr = wer(expected, hyp), keyword_recall(expected, hyp)
    ok = (w <= CFG["wer_threshold"]) and (kr >= CFG["keyword_recall_threshold"])
    results[r["id"]] = {"id": r["id"], "label": r["label"],
                        "wer": round(w, 4), "keyword_recall": round(kr, 4),
                        "ok": ok, "hyp": hyp[:120] if not ok else ""}
    if i % 25 == 0:
        print(f"  [{i}/{len(rows)}] processed, failures so far: "
              f"{sum(1 for v in results.values() if not v['ok'])}")
    if i % 50 == 0:
        PARTIAL.write_text(json.dumps(results, indent=2))

PARTIAL.write_text(json.dumps(results, indent=2))

def stats(label):
    sel = [v for v in results.values() if v["label"] == label]
    return {
        "n": len(sel),
        "mean_wer": round(float(sum(v.get("wer", 0) for v in sel) / len(sel)), 4) if sel else 0,
        "mean_keyword_recall": round(float(sum(v.get("keyword_recall", 0) for v in sel) / len(sel)), 4) if sel else 0,
        "n_fail": sum(1 for v in sel if not v["ok"]),
    }

failures = [v for v in results.values() if not v["ok"]]
report = {
    "n": len(results),
    "attack": stats("attack"),
    "benign": stats("benign"),
    "failures": failures[:20],
    "verdict": "PASS" if not failures else "FAIL",
}
OUT.write_text(json.dumps(report, indent=2))
print()
print(json.dumps({k: v for k, v in report.items() if k != "failures"}, indent=2))