import csv
from pathlib import Path
import cv2
import zxingcpp

MANIFEST = Path("qr_dataset/manifest.csv")

rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
failures = []

for r in rows:
    png = Path(r["png"])
    if not png.exists():
        failures.append({"id": r["id"], "reason": "PNG missing"})
        continue
    img = cv2.imread(str(png))
    if img is None:
        failures.append({"id": r["id"], "reason": "PNG unreadable"})
        continue
    zx = zxingcpp.read_barcodes(img)
    decoded = zx[0].text if zx else ""
    if decoded != r["payload"]:
        failures.append({
            "id": r["id"],
            "reason": "payload mismatch",
            "expected": r["payload"][:60],
            "decoded": decoded[:60],
        })

print(f"Verified {len(rows)} rows")
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print(f"  {f}")
    raise SystemExit(1)
print("All images round-trip cleanly to their manifest payload.")