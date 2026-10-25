import hashlib
from pathlib import Path

SRC = Path("payloads_v3/qr_barcode_injection")
OUT = Path("qr_dataset/dataset_revision.txt")

files = sorted(f for f in SRC.rglob("*") if f.is_file())
lines = []
for f in files:
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    rel = f.relative_to(SRC).as_posix()
    lines.append(f"{rel}|{h}")

combined = "\n".join(lines).encode("utf-8")
folder_sha = hashlib.sha256(combined).hexdigest()

content = (
    f"dataset_name=bordair-multimodal\n"
    f"dataset_type=folder (not a git repo)\n"
    f"source_path={SRC.as_posix()}\n"
    f"file_count={len(files)}\n"
    f"folder_sha256={folder_sha}\n"
)
OUT.write_text(content, encoding="utf-8")
print(content)