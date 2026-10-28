'''
can dlt
'''
import csv
from pathlib import Path

t = [r for r in csv.DictReader(
        open("audio_dataset/triage/triage.csv", encoding="utf-8-sig"))
     if r["decision"] == "speakable"]

long_cipher = sum(
    1 for r in t
    if r["category"] == "cipher_jailbreaks"
    and (len(r["audio_content"]) > 500 or "Morse" in r["audio_content"])
)

json_ma = sum(
    1 for r in t
    if r["category"] == "multi_agent_contagion"
    and (r["audio_content"].strip().startswith("{")
         or '"' in r["audio_content"][:5])
)

short_mem = sum(
    1 for r in t
    if r["category"] in ("memory_poisoning", "instruction_hierarchy_bypass")
    and 0 < len(r["audio_content"]) <= 500
)

print(f"cipher_jailbreaks rows with Morse or >500 chars: {long_cipher}")
print(f"multi_agent_contagion rows with JSON syntax:     {json_ma}")
print(f"memory+hierarchy rows (natural language, keep):  {short_mem}")