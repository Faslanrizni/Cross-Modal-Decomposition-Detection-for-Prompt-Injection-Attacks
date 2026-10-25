import csv
from pathlib import Path

MANIFEST = Path("qr_dataset/manifest_v3.csv")
SAMPLE = Path("qr_dataset/verification/hand_review_sample.csv")
OUT = Path("qr_dataset/verification/verification_log.csv")

manifest = {r["id"]: r for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))}
sample = list(csv.DictReader(SAMPLE.open(encoding="utf-8-sig")))

out = []
for s in sample:
    mid = s["id"]
    m = manifest.get(mid)
    if not m:
        out.append({
            "id": mid, "label": s.get("label", ""), "intent_id": "",
            "text": s.get("text", ""), "payload_visible": "not_found",
            "intent_correct": "", "benign_actually_benign": "", "notes": "",
        })
        continue
    payload = m["payload"]
    text = m["text"]
    payload_visible = "yes" if payload and payload in text else "no"
    out.append({
        "id": mid, "label": m["label"], "intent_id": m["intent_id"],
        "text": text, "payload_visible": payload_visible,
        "intent_correct": "", "benign_actually_benign": "", "notes": "",
    })

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

n_yes = sum(1 for r in out if r["payload_visible"] == "yes")
n_no = sum(1 for r in out if r["payload_visible"] == "no")
print(f"Wrote {OUT} with {len(out)} rows")
print(f"  payload_visible: {n_yes} yes, {n_no} no")