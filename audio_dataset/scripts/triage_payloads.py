"""triage_payloads.py — decide which v4 rows are audio-eligible."""
import json, csv
from pathlib import Path
from collections import Counter

SRC = [
    Path("payloads_v4_crossmodal/text_audio/text_audio_001.json"),
    Path("payloads_v4_crossmodal/text_audio/text_audio_002.json"),
    Path("payloads_v4_crossmodal/text_audio/text_audio_003.json"),
    Path("payloads_v4_crossmodal/text_audio/text_audio_004.json"),
]
OUT = Path("audio_dataset/triage"); OUT.mkdir(parents=True, exist_ok=True)

CFG = json.loads(Path("audio_dataset/audio_config.json").read_text())
SPEAKABLE = set(CFG["speakable_categories"])

EXCL_REASON = {
    "audio_adversarial_asr":    "ASR-pipeline behaviour, not spoken content",
    "chart_diagram_injection":  "needs visual parser (chart label / SVG / HTML)",
    "computer_use_injection":   "needs screen render (UAC, ARIA, overlay)",
    "detector_evasion":         "perturbation does not survive TTS uniformly",
    "mcp_tool_injection":       "JSON tool descriptor, not spoken utterance",
    "pdf_active_content":       "needs PDF parser (JS / XFA / AcroForm)",
    "rag_chunk_boundary":       "needs structural markers (XML / <|im_start|> / null)",
    "reasoning_token_injection":"needs <thinking>/<scratchpad> marker to trigger",
    "unicode_tag_smuggling":    "invisible U+E0000 tag chars, dropped by TTS",
}

rows = []
for p in SRC:
    if not p.exists():
        print(f"MISSING: {p}"); continue
    items = json.loads(p.read_text(encoding="utf-8"))
    print(f"{p.name}: {len(items)} rows")
    for it in items:
        cat = it.get("category", "")
        if "audio_content" not in it:
            rows.append({"id": it["id"], "category": cat,
                         "source_file": p.name, "decision": "excluded",
                         "reason": "no audio_content field",
                         "audio_content": "", "text": it.get("text",""),
                         "audio_method": "", "attack_source": "",
                         "attack_reference": ""})
            continue
        if cat in SPEAKABLE:
            dec, reason = "speakable", ""
        else:
            dec = "excluded"
            reason = EXCL_REASON.get(cat, f"unrecognised category: {cat}")
        rows.append({
            "id": it["id"], "category": cat, "source_file": p.name,
            "decision": dec, "reason": reason,
            "audio_content": it["audio_content"],
            "text": it.get("text",""),
            "audio_method": it.get("audio_method",""),
            "attack_source": it.get("attack_source",""),
            "attack_reference": it.get("attack_reference",""),
        })

with (OUT/"triage.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

excl = [r for r in rows if r["decision"]=="excluded"]
with (OUT/"exclusions.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(excl[0]))
    w.writeheader(); w.writerows(excl)

speak = [r for r in rows if r["decision"]=="speakable"]
print(f"\nTotal:      {len(rows)}")
print(f"Speakable:  {len(speak)}")
print(f"Excluded:   {len(excl)}")
print(f"\nSpeakable by category:")
for cat, n in sorted(Counter(r["category"] for r in speak).items()):
    print(f"  {cat:35s} {n:>4}")
print(f"\nExcluded by category:")
for cat, n in sorted(Counter(r["category"] for r in excl).items()):
    print(f"  {cat:35s} {n:>4}")