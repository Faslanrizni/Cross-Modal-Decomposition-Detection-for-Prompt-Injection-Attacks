import hashlib, json
from pathlib import Path
files = {
    "taxonomy":     Path("audio_dataset/intent_taxonomy.json"),
    "phrasings":    Path("audio_dataset/phrasings.json"),
    "audio_config": Path("audio_dataset/audio_config.json"),
}
prov = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in files.items()}
prov["payloads_dir"] = "payloads_v4_crossmodal/text_audio/"
Path("audio_dataset/provenance.json").write_text(json.dumps(prov, indent=2))
print(json.dumps(prov, indent=2))