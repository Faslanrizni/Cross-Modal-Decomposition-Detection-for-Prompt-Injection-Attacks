import csv
import json
import re
from pathlib import Path
import pyfiglet

MANIFEST = Path("ascii_dataset/manifest/ascii_manifest.csv")
TAXONOMY = Path("ascii_dataset/intent_taxonomy.json")
SAMPLE = Path("ascii_dataset/verification/hand_review_sample.csv")
OUT = Path("ascii_dataset/verification/verification_log.csv")

COMMAND_VOCAB = re.compile(
    r"ignore|disregard|system prompt|reveal|password|secret|override|"
    r"jailbreak|credential|exfiltrat|safety|filter|rules|sudo|discard|"
    r"disable|bypass|hack|hijack|leak|breach|exploit|print|output|"
    r"disclose|grant|activate|append|fabricate|approve|maintenance|"
    r"internal|train|session|steal|creds|auth|protocol|admin|api|key|"
    r"config|clean|verified|valid|fake|false|lie|endpoint|route|link|url|"
    r"dump|expose|corpus|elevate|circumvent|maint|debug|mode",
    re.I,
)

# Load canonical_command from the taxonomy (this was the missing piece)
tax = json.loads(TAXONOMY.read_text(encoding="utf-8"))
intent_cmd = {i["intent_id"]: i["canonical_command"] for i in tax["intents"]}

manifest = {r["id"]: r for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))}
sample = list(csv.DictReader(SAMPLE.open(encoding="utf-8-sig")))

out = []
diagnostics = []

for s in sample:
    mid = s["id"]
    m = manifest.get(mid)
    if not m:
        out.append({"id": mid, "label": "", "plaintext_leak": "", "text": "",
                    "art_decodes": "not_found", "intent_correct": "",
                    "benign_actually_benign": "", "leak_tier_correct": "", "notes": ""})
        continue

    label = m["label"]
    tier = m["plaintext_leak"]
    text = m["text"]
    intent_id = m["intent_id"]
    art_word = m["art_word"]
    font = m["ascii_font"]

    # --- art_decodes ---
    try:
        art = pyfiglet.figlet_format(art_word, font=font).rstrip()
        art_decodes = "yes" if art and art in text else "no"
    except Exception as e:
        art_decodes = f"error: {e}"
        art = ""

    # --- framing: remove art and any residual whitespace-only lines ---
    if art:
        framing_lines = [ln for ln in text.replace(art, "").split("\n") if ln.strip()]
        framing = " ".join(framing_lines).strip()
    else:
        framing = text.strip()

    # --- leak_tier_correct ---
    if tier == "art_only":
        m_vocab = COMMAND_VOCAB.search(framing)
        if m_vocab:
            leak_tier_correct = "no"
            diagnostics.append(f"{mid} [{tier}] framefrag='{framing[:60]}' matched '{m_vocab.group()}'")
        else:
            leak_tier_correct = "yes"

    elif tier == "art+full_command":
        if label == "attack":
            cmd = intent_cmd.get(intent_id, "").lower()
            cmd_words = [w for w in cmd.split() if len(w) > 3]
            hits = sum(1 for w in cmd_words if w in framing.lower())
            threshold = max(2, len(cmd_words) // 2) if cmd_words else 1
            if hits >= threshold:
                leak_tier_correct = "yes"
            else:
                leak_tier_correct = "no"
                diagnostics.append(f"{mid} [{tier}, attack] framing='{framing[:60]}' missing command '{cmd[:40]}' (hits={hits}/{len(cmd_words)})")
        else:
            # Benign art+full_command rows have a benign command, not attack command.
            # Correct condition: framing contains a nontrivial sentence.
            if len(framing) >= 15:
                leak_tier_correct = "yes"
            else:
                leak_tier_correct = "no"
                diagnostics.append(f"{mid} [{tier}, benign] framing too short: '{framing}'")

    else:  # art+hint
        leak_tier_correct = "human"

    out.append({
        "id": mid,
        "label": label,
        "intent_id": intent_id,           
        "canonical_command": intent_cmd.get(intent_id, ""),  
        "art_word": art_word,                 
        "plaintext_leak": tier,
        "text": text,
        "art_decodes": art_decodes,
        "intent_correct": "",
        "benign_actually_benign": "",
        "leak_tier_correct": leak_tier_correct,
        "notes": "",
    })

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

n_yes = sum(1 for r in out if r["art_decodes"] == "yes")
n_no = sum(1 for r in out if r["art_decodes"] == "no")
n_err = sum(1 for r in out if r["art_decodes"].startswith("error"))
lt_yes = sum(1 for r in out if r["leak_tier_correct"] == "yes")
lt_no = sum(1 for r in out if r["leak_tier_correct"] == "no")
lt_human = sum(1 for r in out if r["leak_tier_correct"] == "human")

print(f"Wrote {OUT} with {len(out)} rows")
print(f"  art_decodes:      {n_yes} yes, {n_no} no, {n_err} error")
print(f"  leak_tier_correct: {lt_yes} yes, {lt_no} no, {lt_human} need human")

if diagnostics:
    print(f"\n{len(diagnostics)} diagnostic rows (these are the ones to spot-check):")
    for d in diagnostics[:20]:
        print(f"  {d}")