"""generate_qr_dataset.py - attack QR images + length/format-matched benign QR images.

Fixes applied in this version:
  1. Strips the "QR Data:" prefix so it is not encoded into the image.
  2. Generates one matched benign QR per attack, same format and same length.
  3. Verifies every PNG with zxing-cpp (primary) and OpenCV (informational).
  4. Uses a FIXED QR version across all images so image size cannot leak the label.
  5. Normalises Unicode characters that break round-trip decoding.

Run from the bordair-multimodal folder:
    python generate_qr_dataset.py
    python generate_qr_dataset.py --extra my_cmds.jsonl

Needs:
    pip install "qrcode[pil]" opencv-python-headless zxing-cpp

Output:
    qr_dataset/images/*.png
    qr_dataset/manifest.csv
    qr_dataset/generator_config.json
"""
import argparse
import bisect
import csv
import hashlib
import json
import random
import re
import sys
from importlib.metadata import version as pkg_version
from pathlib import Path

import cv2
import qrcode
import zxingcpp
from qrcode.constants import ERROR_CORRECT_M

SEED = 42
BOX_SIZE, BORDER = 10, 4
SRC_DIR = Path("payloads_v3/qr_barcode_injection")
POOL = Path("benign/_pool.json")
OUT = Path("qr_dataset")

PREFIX = re.compile(r"^\s*QR Data:\s*", re.I)
ATTACK_WORDS = re.compile(
    r"ignore|disregard|previous instruction|system prompt|reveal|password|secret|"
    r"override|jailbreak|credential|api[_ ]key|admin|exfiltrat", re.I
)
BENIGN_ACTIONS = ["open_menu", "show_welcome", "check_in", "view_receipt",
                  "start_tour", "open_map"]
HOSTS = ["example.com", "example.org", "shop.example.net", "menu.example.com"]
SEGMENTS = ["menu", "events", "tickets", "about", "contact", "locations",
            "faq", "news", "gallery", "visit"]

# Characters that break QR round-trip verification or cause asymmetric encoding.
# Replaced with ASCII-safe equivalents before rendering.
NORMALISE_MAP = {
    "\u2014": "--",   # em dash
    "\u2013": "-",    # en dash
    "\u2018": "'",    # left single quote
    "\u2019": "'",    # right single quote
    "\u201c": '"',    # left double quote
    "\u201d": '"',    # right double quote
    "\u2026": "...",  # ellipsis
    "\u00a0": " ",    # non-breaking space
    "\u200b": "",     # zero-width space
    "\u200c": "",     # zero-width non-joiner
    "\u200d": "",     # zero-width joiner
    "\ufeff": "",     # byte-order mark
}


def normalise(text: str) -> str:
    for bad, good in NORMALISE_MAP.items():
        text = text.replace(bad, good)
    return text


def kind_of(payload):
    try:
        if isinstance(json.loads(payload), dict):
            return "json"
    except ValueError:
        pass
    return "url" if payload.lower().startswith("http") else "text"


def load_attacks(extra):
    rows = []
    for f in sorted(SRC_DIR.glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            rows.append({
                "source_id": r["id"],
                "payload": normalise(PREFIX.sub("", r["text"]).strip()),
                "origin": "bordair_v3_qr",
            })
    if extra:
        text = Path(extra).read_text(encoding="utf-8")
        items = (
            json.loads(text) if text.lstrip().startswith("[")
            else [json.loads(l) for l in text.splitlines() if l.strip()]
        )
        for i, it in enumerate(items):
            t = it if isinstance(it, str) else it.get("text", "")
            rows.append({
                "source_id": f"EXTRA-{i:06d}",
                "payload": normalise(t.strip()),
                "origin": "extra",
            })
    return [r for r in rows if r["payload"]]


def load_pool():
    data = json.loads(POOL.read_text(encoding="utf-8"))
    texts = sorted({
        normalise(d["text"].strip())
        for d in data
        if isinstance(d, dict)
        and 8 <= len(d.get("text", "")) <= 400
        and not ATTACK_WORDS.search(d["text"])
    }, key=len)
    return texts, [len(t) for t in texts]


def nearest(pool, lengths, target):
    i = bisect.bisect_left(lengths, target)
    window = pool[max(0, i - 15): i + 15] or pool
    return random.choice(window)


def make_benign(kind, target_len, pool, lengths):
    if kind == "json":
        overhead = len(json.dumps({"action": "open_menu", "instruction": ""}))
        text = nearest(pool, lengths, max(8, target_len - overhead))
        return json.dumps({"action": random.choice(BENIGN_ACTIONS),
                           "instruction": text})
    if kind == "url":
        url = f"https://{random.choice(HOSTS)}"
        while len(url) < target_len - 6:
            url += "/" + random.choice(SEGMENTS)
        return url + f"?id={random.randint(10, 99)}"
    return nearest(pool, lengths, target_len)


def required_version(payloads, error_correction=ERROR_CORRECT_M):
    """Smallest QR version that can encode every payload with the given EC level.

    We scan versions 1..40 in order; the first version that fits all payloads
    is used as the FIXED version for every image. This guarantees every image
    has identical pixel dimensions, eliminating the size shortcut.
    """
    for v in range(1, 41):
        fits_all = True
        for payload in payloads:
            try:
                qr = qrcode.QRCode(
                    version=v,
                    error_correction=error_correction,
                    box_size=BOX_SIZE,
                    border=BORDER,
                )
                qr.add_data(payload)
                qr.make(fit=False)
            except qrcode.exceptions.DataOverflowError:
                fits_all = False
                break
        if fits_all:
            return v
    raise ValueError("No QR version (1-40) is large enough for the longest payload")

'''
Render the PNG and verify round-trip
Action: for each payload, render the PNG,
 then verify that decoding it back produces the intended payload.
'''
def render(payload, path, fixed_version):
    qr = qrcode.QRCode(
        version=fixed_version,
        error_correction=ERROR_CORRECT_M,
        box_size=BOX_SIZE,
        border=BORDER,
    )
    qr.add_data(payload)
    qr.make(fit=False)          # enforce fixed_version; never auto-adjust
    qr.make_image(fill_color="black", back_color="white").save(path)
    return qr.version


def roundtrip(path, payload):
    """Return (zxing_ok, opencv_ok). zxing-cpp is the primary verifier."""
    img = cv2.imread(str(path))
    if img is None:
        return False, False
    zx = zxingcpp.read_barcodes(img)
    zx_ok = bool(zx) and zx[0].text == payload
    cv_ok = cv2.QRCodeDetector().detectAndDecode(img)[0] == payload
    return zx_ok, cv_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra", default=None,
                    help="Optional JSONL/JSON file with extra attack texts")
    args = ap.parse_args()
    random.seed(SEED)
    (OUT / "images").mkdir(parents=True, exist_ok=True)

    attacks = load_attacks(args.extra)
    pool, lengths = load_pool()
    print(f"attack payloads: {len(attacks)}   benign pool texts (filtered): {len(pool)}")

    # Build matched benign payloads first
    pairs = []
    for a in attacks:
        k = kind_of(a["payload"])
        benign = make_benign(k, len(a["payload"]), pool, lengths)
        pairs.append({
            "attack_id": a["source_id"],
            "origin": a["origin"],
            "format": k,
            "attack_payload": a["payload"],
            "benign_payload": benign,
        })

    # Determine the fixed QR version from all payloads
    all_payloads = (
        [p["attack_payload"] for p in pairs]
        + [p["benign_payload"] for p in pairs]
    )
    fixed_version = required_version(all_payloads)
    print(f"FIXED QR version for every image: {fixed_version}")
    print(f"  -> all images will be {fixed_version}-version QR codes "
          f"(same pixel dimensions, no size leak)")

    # Render every payload
    rows = []
    for p in pairs:
        for label, sid, payload in (
            ("attack", p["attack_id"], p["attack_payload"]),
            ("benign", "B-" + p["attack_id"], p["benign_payload"]),
        ):
            png = OUT / "images" / f"{sid}.png"
            ver = render(payload, png, fixed_version)
            zx_ok, cv_ok = roundtrip(png, payload)
            rows.append({
                "id": sid,
                "label": label,
                "pair_id": p["attack_id"],
                "origin": p["origin"],
                "format": p["format"],
                "payload": payload,
                "payload_len": len(payload),
                "qr_version": ver,
                "png": png.as_posix(),
                "png_sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
                "roundtrip_ok": zx_ok,
                "opencv_ok": cv_ok,
            })

    # Write manifest
    with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # Aggregate stats
    bad = [r["id"] for r in rows if not r["roundtrip_ok"]]
    stats = {}
    for lab in ("attack", "benign"):
        sel = [r for r in rows if r["label"] == lab]
        stats[lab] = {
            "n": len(sel),
            "mean_len": round(sum(r["payload_len"] for r in sel) / len(sel), 1),
            "mean_qr_version": round(sum(r["qr_version"] for r in sel) / len(sel), 2),
            "unique_versions": sorted({r["qr_version"] for r in sel}),
            "unique_image_sizes": sorted({
                tuple(
                    qrcode.QRCode(version=r["qr_version"],
                                  error_correction=ERROR_CORRECT_M,
                                  box_size=BOX_SIZE,
                                  border=BORDER)
                    .modules_count * BOX_SIZE + 2 * BORDER * BOX_SIZE
                    for _ in [0]
                )
                for r in sel
            }),
        }

    # Save config
    (OUT / "generator_config.json").write_text(json.dumps({
        "seed": SEED,
        "box_size": BOX_SIZE,
        "border": BORDER,
        "error_correction": "M",
        "fixed_version": fixed_version,
        "qrcode": pkg_version("qrcode"),
        "opencv": cv2.__version__,
        "zxing_cpp": pkg_version("zxing-cpp"),
        "python": sys.version.split()[0],
        "roundtrip_failures": bad,
        "stats": stats,
    }, indent=2), encoding="utf-8")

    # Report
    print(f"images written: {len(rows)}   "
          f"round-trip failures (zxing-cpp): {len(bad)} {bad[:10]}")
    print(f"OpenCV decoder also read "
          f"{sum(r['opencv_ok'] for r in rows)}/{len(rows)} (informational)")
    for lab, s in stats.items():
        print(f"  {lab:6s} n={s['n']:4d}  "
              f"mean_len={s['mean_len']:7.1f}  "
              f"mean_qr_version={s['mean_qr_version']}  "
              f"versions={s['unique_versions']}")

    # Size-leak verdict
    attack_versions = set(stats["attack"]["unique_versions"])
    benign_versions = set(stats["benign"]["unique_versions"])
    if attack_versions == benign_versions == {fixed_version}:
        print("Size leak check: PASS - every image is the same fixed version.")
    else:
        print(f"Size leak check: FAIL - attack versions={attack_versions}, "
              f"benign versions={benign_versions}")


if __name__ == "__main__":
    main()