'''
Action (dump_qr_payloads.py): write the full text of every QR attack to full_payloads.txt.

Why this was necessary: the initial attempt to inspect payloads used a 70-character truncation. For some attacks, that was enough to see the intent.
'''
import csv
from pathlib import Path

MANIFEST = Path("qr_dataset/manifest.csv")
OUT = Path("qr_dataset/full_payloads.txt")

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
attacks = [r for r in rows if r["label"] == "attack"]

with OUT.open("w", encoding="utf-8") as f:
    for r in attacks:
        f.write(f"=== {r['id']} ===\n")
        f.write(f"pair_id: {r['pair_id']}\n")
        f.write(f"payload_len: {r['payload_len']}\n")
        f.write(f"payload:\n{r['payload']}\n")
        f.write("\n")

print(f"Wrote {OUT} with {len(attacks)} attack payloads")