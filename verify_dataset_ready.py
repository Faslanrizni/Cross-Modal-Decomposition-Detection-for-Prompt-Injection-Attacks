"""
verify_dataset_ready.py
Complete verification that the QR and ASCII channels are ready for research use.

Run from the project root:
    python verify_dataset_ready.py

Exit code 0 = ready. Exit code 1 = not ready (details printed).
"""
import csv
import hashlib
import json
import sys
from pathlib import Path
from collections import Counter

ROOT = Path.cwd()

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

failures = []
warnings = []

def check(condition, message, detail=""):
    if condition:
        print(f"{PASS} {message}")
        return True
    else:
        print(f"{FAIL} {message}" + (f" -- {detail}" if detail else ""))
        failures.append(message)
        return False

def warn(condition, message, detail=""):
    if condition:
        print(f"{PASS} {message}")
        return True
    else:
        print(f"{WARN} {message}" + (f" -- {detail}" if detail else ""))
        warnings.append(message)
        return False

def file_exists(relpath, label=""):
    p = ROOT / relpath
    exists = p.is_file()
    display = label or relpath
    check(exists, f"Exists: {display}", "file not found" if not exists else "")
    return p if exists else None

def load_csv(relpath):
    p = ROOT / relpath
    if not p.is_file():
        return None
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def load_json(relpath):
    p = ROOT / relpath
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def sha256(relpath):
    p = ROOT / relpath
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()

# =============================================================================
print("=" * 72)
print("PART A -- FILE EXISTENCE")
print("=" * 72)
# =============================================================================

print("\n--- A1. ASCII live files ---")
ascii_live_files = [
    "ascii_dataset/decisions.md",
    "ascii_dataset/dataset_revision.txt",
    "ascii_dataset/intent_taxonomy.json",
    "ascii_dataset/exclusions.csv",
    "ascii_dataset/generator_config.json",
    "ascii_dataset/summary_ascii.json",
    "ascii_dataset/intent_coverage.json",
    "ascii_dataset/shortcut_check.json",
    "ascii_dataset/manifest/ascii_manifest.csv",
    "ascii_dataset/manifest/ascii_fragments.csv",
    "ascii_dataset/verification/verification_report.json",
    "ascii_dataset/verification/verification_log.csv",
    "ascii_dataset/verification/hand_review_sample.csv",
    "ascii_dataset/splits/iid.json",
    "ascii_dataset/splits/lofo_channel.json",
    "ascii_dataset/splits/exploratory_ascii_leak_tier.json",
    "ascii_dataset/splits/exploratory_ascii_block_font.json",
    "ascii_dataset/raw/ascii_art_injection/ascii_art_injection_001.json",
]
ascii_live_present = sum(1 for f in ascii_live_files if (ROOT / f).is_file())
for f in ascii_live_files:
    file_exists(f)
print(f"\n  ASCII live: {ascii_live_present}/{len(ascii_live_files)} present")

print("\n--- A2. ASCII frozen snapshot ---")
ascii_frozen_files = [
    "frozen/ascii_v1/decisions.md",
    "frozen/ascii_v1/dataset_revision.txt",
    "frozen/ascii_v1/exclusions.csv",
    "frozen/ascii_v1/generator_config.json",
    "frozen/ascii_v1/intent_taxonomy.json",
    "frozen/ascii_v1/intent_coverage.json",
    "frozen/ascii_v1/shortcut_check.json",
    "frozen/ascii_v1/summary_ascii.json",
    "frozen/ascii_v1/CHANGELOG.md",
    "frozen/ascii_v1/manifest/ascii_manifest.csv",
    "frozen/ascii_v1/manifest/ascii_fragments.csv",
    "frozen/ascii_v1/verification/verification_report.json",
    "frozen/ascii_v1/verification/verification_log.csv",
    "frozen/ascii_v1/verification/hand_review_sample.csv",
    "frozen/ascii_v1/splits/iid.json",
    "frozen/ascii_v1/splits/lofo_channel.json",
    "frozen/ascii_v1/splits/exploratory_ascii_leak_tier.json",
    "frozen/ascii_v1/splits/exploratory_ascii_block_font.json",
]
ascii_frozen_present = sum(1 for f in ascii_frozen_files if (ROOT / f).is_file())
for f in ascii_frozen_files:
    file_exists(f)
print(f"\n  ASCII frozen: {ascii_frozen_present}/{len(ascii_frozen_files)} present")

print("\n--- A3. QR live files (manifests + metadata) ---")
qr_live_files = [
    "qr_dataset/dataset_revision.txt",
    "qr_dataset/decisions.md",
    "qr_dataset/full_payloads.txt",
    "qr_dataset/generator_config.json",
    "qr_dataset/intent_coverage.json",
    "qr_dataset/shortcut_check.json",
    "qr_dataset/summary_qr.json",
    "qr_dataset/manifest.csv",
    "qr_dataset/manifest_v2.csv",
    "qr_dataset/manifest_v3.csv",
    "qr_dataset/verification/verification_report.json",
    "qr_dataset/verification/verification_log.csv",
    "qr_dataset/verification/hand_review_sample.csv",
    "qr_dataset/splits/iid_all_families.json",
    "qr_dataset/splits/lofo_qr_held_out.json",
    "qr_dataset/splits/lofo_ascii_held_out.json",
]
qr_live_present = sum(1 for f in qr_live_files if (ROOT / f).is_file())
for f in qr_live_files:
    file_exists(f)
print(f"\n  QR live metadata: {qr_live_present}/{len(qr_live_files)} present")

print("\n--- A4. QR images (30 PNGs) ---")
qr_images_present = 0
for i in range(1, 16):
    attack_png = f"qr_dataset/images/QR-{i:06d}.png"
    benign_png = f"qr_dataset/images/B-QR-{i:06d}.png"
    if (ROOT / attack_png).is_file():
        qr_images_present += 1
    if (ROOT / benign_png).is_file():
        qr_images_present += 1
check(qr_images_present == 30, f"QR images: {qr_images_present}/30 present")
if qr_images_present < 30:
    for i in range(1, 16):
        for png in (f"qr_dataset/images/QR-{i:06d}.png", f"qr_dataset/images/B-QR-{i:06d}.png"):
            if not (ROOT / png).is_file():
                print(f"  Missing: {png}")

print("\n--- A5. QR frozen snapshots ---")
qr_v2_files = [
    "frozen/qr_v2/dataset_revision.txt",
    "frozen/qr_v2/decisions.md",
    "frozen/qr_v2/full_payloads.txt",
    "frozen/qr_v2/generator_config.json",
    "frozen/qr_v2/intent_coverage.json",
    "frozen/qr_v2/shortcut_check.json",
    "frozen/qr_v2/summary_qr.json",
    "frozen/qr_v2/CHANGELOG.md",
    "frozen/qr_v2/manifest/manifest_v3.csv",
    "frozen/qr_v2/verification/verification_report.json",
    "frozen/qr_v2/verification/verification_log.csv",
    "frozen/qr_v2/verification/hand_review_sample.csv",
    "frozen/qr_v2/splits/iid_all_families.json",
    "frozen/qr_v2/splits/lofo_qr_held_out.json",
    "frozen/qr_v2/splits/lofo_ascii_held_out.json",
]
qr_v2_present = sum(1 for f in qr_v2_files if (ROOT / f).is_file())
for f in qr_v2_files:
    file_exists(f)
print(f"\n  QR v2 frozen: {qr_v2_present}/{len(qr_v2_files)} present")

check((ROOT / "frozen/qr_v1").is_dir(), "frozen/qr_v1 exists (superseded audit trail)")
check((ROOT / "frozen/qr_v1/CHANGELOG.md").is_file(), "frozen/qr_v1/CHANGELOG.md exists")

print("\n--- A6. Scripts ---")
script_files = [
    "ascii_dataset/scripts/triage_seed.py",
    "ascii_dataset/scripts/write_taxonomy.py",
    "ascii_dataset/scripts/verify_taxonomy.py",
    "ascii_dataset/scripts/generate_ascii.py",
    "ascii_dataset/scripts/verify_ascii.py",
    "ascii_dataset/scripts/prefill_ascii_review.py",
    "ascii_dataset/scripts/check_review.py",
    "ascii_dataset/scripts/freeze_splits_all.py",
    "qr_dataset/scripts/verify_qr.py",
    "qr_dataset/scripts/prefill_qr_review.py",
    "qr_dataset/scripts/check_review.py",
    "qr_dataset/scripts/shortcut_check_qr.py",
    "qr_dataset/scripts/build_manifest_v3.py",
]
scripts_present = sum(1 for f in script_files if (ROOT / f).is_file())
for f in script_files:
    warn((ROOT / f).is_file(), f"Script: {f}", "not found (may be at different path)")
print(f"\n  Scripts: {scripts_present}/{len(script_files)} present")

# =============================================================================
print("\n" + "=" * 72)
print("PART B -- DATA INTEGRITY (ASCII)")
print("=" * 72)
# =============================================================================

print("\n--- B1. ASCII manifest ---")
ascii_rows = load_csv("ascii_dataset/manifest/ascii_manifest.csv")
if ascii_rows is None:
    check(False, "ASCII manifest loads")
else:
    check(True, f"ASCII manifest loads ({len(ascii_rows)} rows)")
    attacks = [r for r in ascii_rows if r["label"] == "attack"]
    benigns = [r for r in ascii_rows if r["label"] == "benign"]
    check(len(attacks) == len(benigns), f"Attack/benign balanced: {len(attacks)}/{len(benigns)}")
    check(len(ascii_rows) == 1368, f"Total rows 1368: {len(ascii_rows)}")
    check(len(set(r["pair_id"] for r in ascii_rows)) == len(attacks),
          f"Unique pair_ids match attack count: {len(set(r['pair_id'] for r in ascii_rows))}")

    # Every attack has exactly one benign with same pair_id
    pair_counts = Counter(r["pair_id"] for r in ascii_rows)
    bad_pairs = [p for p, c in pair_counts.items() if c != 2]
    check(len(bad_pairs) == 0, f"Every pair has exactly 2 rows", f"{len(bad_pairs)} bad pairs")

    # Every row has intent_id
    missing_intent = [r for r in ascii_rows if not r.get("intent_id", "").strip()]
    check(len(missing_intent) == 0, f"Every row has intent_id", f"{len(missing_intent)} missing")

    # Every row has a valid split
    valid_splits = {"train", "val", "test"}
    bad_splits = [r for r in ascii_rows if r.get("split", "") not in valid_splits]
    check(len(bad_splits) == 0, f"Every row has split in {{train,val,test}}", f"{len(bad_splits)} invalid")

    # No duplicates within or across labels
    seen = {}
    dup_count = 0
    for r in ascii_rows:
        key = (r["label"], r["text"])
        if key in seen:
            dup_count += 1
        seen[key] = True
    check(dup_count == 0, f"No duplicate (label,text) pairs", f"{dup_count} duplicates")

    # Fonts balanced
    font_counts = Counter(r["ascii_font"] for r in ascii_rows)
    expected_per_font = len(ascii_rows) // 4
    balanced_fonts = all(abs(c - expected_per_font) <= 2 for c in font_counts.values())
    check(balanced_fonts, f"Fonts balanced (~{expected_per_font} each)", str(dict(font_counts)))

    # Tiers balanced
    tier_counts = Counter(r["plaintext_leak"] for r in ascii_rows)
    expected_per_tier = len(ascii_rows) // 3
    balanced_tiers = all(abs(c - expected_per_tier) <= 2 for c in tier_counts.values())
    check(balanced_tiers, f"Leak tiers balanced (~{expected_per_tier} each)", str(dict(tier_counts)))

    # Unique intents
    unique_intents = set(r["intent_id"] for r in ascii_rows if r["label"] == "attack")
    check(len(unique_intents) == 21, f"21 unique attack intents: {len(unique_intents)}")

print("\n--- B2. ASCII fragments ---")
frags = load_csv("ascii_dataset/manifest/ascii_fragments.csv")
if frags is None:
    check(False, "ASCII fragments load")
else:
    check(True, f"ASCII fragments load ({len(frags)} rows)")
    check(len(frags) == 912, f"Total fragment rows 912: {len(frags)}")

    # Every attack has exactly 2 fragments
    attack_ids = set(r["id"] for r in ascii_rows 
                 if r["label"] == "attack" 
                 and r["plaintext_leak"] in ("art_only", "art+hint"))
    frags_by_sample = {}
    for f in frags:
        frags_by_sample.setdefault(f["sample_id"], []).append(f)
    bad_frag_counts = [s for s in attack_ids if len(frags_by_sample.get(s, [])) != 2]
    check(len(bad_frag_counts) == 0, "Every attack has exactly 2 fragments", f"{len(bad_frag_counts)} attacks with wrong count")

    # Every fragment is marked benign_alone
    not_benign = [f for f in frags if f.get("fragment_label_alone") != "benign"]
    check(len(not_benign) == 0, "All fragments marked benign_alone", f"{len(not_benign)} marked otherwise")

    # Fragment roles
    roles = Counter(f["fragment_role"] for f in frags)
    check(roles.get("wrapper", 0) == 456, f"456 wrapper fragments: {roles.get('wrapper', 0)}")
    check(roles.get("payload", 0) == 456, f"456 payload fragments: {roles.get('payload', 0)}")

print("\n--- B3. ASCII taxonomy ---")
tax = load_json("ascii_dataset/intent_taxonomy.json")
if tax is None:
    check(False, "Taxonomy loads")
else:
    check(True, f"Taxonomy loads ({len(tax['intents'])} intents)")
    check(len(tax["intents"]) == 21, f"21 intents: {len(tax['intents'])}")
    check(len(tax["categories"]) == 7, f"7 categories: {len(tax['categories'])}")
    intent_ids = [i["intent_id"] for i in tax["intents"]]
    check(len(intent_ids) == len(set(intent_ids)), "All intent_ids unique")

    # Every intent has art word candidates
    for i in tax["intents"]:
        if not i.get("art_word_candidates"):
            check(False, f"{i['intent_id']} has art_word_candidates")
            break
    else:
        check(True, "Every intent has art_word_candidates")

    # Manifest intents subset of taxonomy intents
    manifest_intents = set(r["intent_id"] for r in ascii_rows)
    taxonomy_intents = set(intent_ids)
    extra = manifest_intents - taxonomy_intents
    check(len(extra) == 0, "All manifest intents exist in taxonomy", f"extra: {extra}")

print("\n--- B4. ASCII coverage ---")
coverage = load_json("ascii_dataset/intent_coverage.json")
if coverage is None:
    check(False, "Coverage loads")
else:
    check(True, f"Coverage loads ({len(coverage)} intents)")
    qr_testable = sum(1 for v in coverage.values() if v.get("testable_in_qr_lofo"))
    ascii_testable = sum(1 for v in coverage.values() if v.get("testable_in_ascii_lofo"))
    check(qr_testable == 11, f"testable_in_qr_lofo = 11: {qr_testable}")
    check(ascii_testable == 11, f"testable_in_ascii_lofo = 11: {ascii_testable}")

print("\n--- B5. ASCII shortcut check ---")
shortcut = load_json("ascii_dataset/shortcut_check.json")
if shortcut is None:
    check(False, "ASCII shortcut check loads")
else:
    check(True, "ASCII shortcut check loads")
    auc = shortcut.get("logreg_auc_mean", 1.0)
    check(auc <= 0.60, f"ASCII shortcut AUC <= 0.60: {auc}")
    check(shortcut.get("verdict") == "PASS", f"Verdict PASS: {shortcut.get('verdict')}")

print("\n--- B6. ASCII verification ---")
verif = load_json("ascii_dataset/verification/verification_report.json")
if verif is None:
    check(False, "ASCII verification loads")
else:
    check(True, "ASCII verification loads")
    check(verif.get("verdict") == "PASS", f"Verdict PASS: {verif.get('verdict')}")
    check(len(verif.get("regen_failures", [])) == 0, "No regen failures")
    check(len(verif.get("duplicates_within_label", {})) == 0, "No within-label dups")
    check(len(verif.get("duplicates_across_labels", {})) == 0, "No across-label dups")

print("\n--- B7. ASCII hand review ---")
review = load_csv("ascii_dataset/verification/verification_log.csv")
if review is None:
    check(False, "ASCII hand review loads")
else:
    check(True, f"ASCII hand review loads ({len(review)} rows)")
    check(len(review) == 40, f"40 rows reviewed: {len(review)}")
    fails = [r for r in review
             if (r["label"] == "attack" and r["intent_correct"] == "no")
             or (r["label"] == "benign" and r["benign_actually_benign"] == "no")]
    check(len(fails) == 0, "No review failures", f"{len(fails)} failures")
    unfilled = [r for r in review
                if (r["label"] == "attack" and r["intent_correct"] not in ("yes", "no", "n/a"))
                or (r["label"] == "benign" and r["benign_actually_benign"] not in ("yes", "no", "n/a"))]
    check(len(unfilled) == 0, "No unfilled review cells", f"{len(unfilled)} unfilled")

# =============================================================================
print("\n" + "=" * 72)
print("PART C -- DATA INTEGRITY (QR)")
print("=" * 72)
# =============================================================================

print("\n--- C1. QR canonical manifest ---")
qr_rows = load_csv("qr_dataset/manifest_v3.csv")
if qr_rows is None:
    check(False, "QR manifest_v3 loads")
else:
    check(True, f"QR manifest_v3 loads ({len(qr_rows)} rows)")
    qr_attacks = [r for r in qr_rows if r["label"] == "attack"]
    qr_benigns = [r for r in qr_rows if r["label"] == "benign"]
    check(len(qr_attacks) == 15, f"15 attacks: {len(qr_attacks)}")
    check(len(qr_benigns) == 15, f"15 benigns: {len(qr_benigns)}")
    check(len(qr_rows) == 30, f"30 total rows: {len(qr_rows)}")

    # Every attack has intent_id
    missing = [r for r in qr_rows if not r.get("intent_id", "").strip()]
    check(len(missing) == 0, "Every QR row has intent_id", f"{len(missing)} missing")

    # Unique intents
    unique_qr_intents = set(r["intent_id"] for r in qr_attacks)
    check(len(unique_qr_intents) == 11, f"11 unique attack intents: {len(unique_qr_intents)}")

    # QR version uniform
    versions = set(r["qr_version"] for r in qr_rows)
    check(len(versions) == 1, f"QR version uniform: {versions}")

    # Round-trip status
    roundtrip_ok = sum(1 for r in qr_rows if r["roundtrip_ok"] in ("True", "true", "1", "yes"))
    check(roundtrip_ok == 30, f"All 30 rows roundtrip_ok: {roundtrip_ok}")

    # Every PNG path exists
    missing_pngs = []
    for r in qr_rows:
        png_path = r.get("png", "").strip()
        if png_path and not (ROOT / png_path).is_file():
            missing_pngs.append(png_path)
    check(len(missing_pngs) == 0, f"All PNG paths exist", f"{len(missing_pngs)} missing")

    # No duplicates
    seen = {}
    dup_count = 0
    for r in qr_rows:
        key = (r["label"], r["text"])
        if key in seen:
            dup_count += 1
        seen[key] = True
    check(dup_count == 0, "No duplicate (label,text) pairs", f"{dup_count} duplicates")

print("\n--- C2. QR coverage ---")
qr_cov = load_json("qr_dataset/intent_coverage.json")
if qr_cov is None:
    check(False, "QR coverage loads")
else:
    check(True, f"QR coverage loads ({len(qr_cov)} intents)")
    qr_test = sum(1 for v in qr_cov.values() if v.get("testable_in_qr_lofo"))
    ascii_test = sum(1 for v in qr_cov.values() if v.get("testable_in_ascii_lofo"))
    check(qr_test == 11, f"testable_in_qr_lofo = 11: {qr_test}")
    check(ascii_test == 11, f"testable_in_ascii_lofo = 11: {ascii_test}")

print("\n--- C3. QR shortcut check ---")
qr_shortcut = load_json("qr_dataset/shortcut_check.json")
if qr_shortcut is None:
    check(False, "QR shortcut check loads")
else:
    check(True, "QR shortcut check loads")
    auc = qr_shortcut.get("logreg_auc_mean", 1.0)
    check(auc <= 0.60, f"QR shortcut AUC <= 0.60: {auc}")
    check(qr_shortcut.get("verdict") == "PASS", f"Verdict PASS: {qr_shortcut.get('verdict')}")

print("\n--- C4. QR verification ---")
qr_verif = load_json("qr_dataset/verification/verification_report.json")
if qr_verif is None:
    check(False, "QR verification loads")
else:
    check(True, "QR verification loads")
    check(qr_verif.get("verdict") == "PASS", f"Verdict PASS: {qr_verif.get('verdict')}")
    check(len(qr_verif.get("roundtrip_failures", [])) == 0, "No roundtrip failures")
    check(qr_verif.get("qr_version_uniform") == True, "QR version uniform confirmed")

print("\n--- C5. QR hand review ---")
qr_review = load_csv("qr_dataset/verification/verification_log.csv")
if qr_review is None:
    check(False, "QR hand review loads")
else:
    check(True, f"QR hand review loads ({len(qr_review)} rows)")
    check(len(qr_review) == 30, f"30 rows reviewed: {len(qr_review)}")
    fails = [r for r in qr_review
             if (r["label"] == "attack" and r["intent_correct"] == "no")
             or (r["label"] == "benign" and r["benign_actually_benign"] == "no")]
    check(len(fails) == 0, "No review failures", f"{len(fails)} failures")

# =============================================================================
print("\n" + "=" * 72)
print("PART D -- FROZEN SNAPSHOT INTEGRITY (byte-identical to live)")
print("=" * 72)

print("\n--- D1. ASCII frozen matches live ---")
ascii_pairs = [
    ("frozen/ascii_v1/decisions.md", "ascii_dataset/decisions.md"),
    ("frozen/ascii_v1/dataset_revision.txt", "ascii_dataset/dataset_revision.txt"),
    ("frozen/ascii_v1/exclusions.csv", "ascii_dataset/exclusions.csv"),
    ("frozen/ascii_v1/generator_config.json", "ascii_dataset/generator_config.json"),
    ("frozen/ascii_v1/intent_taxonomy.json", "ascii_dataset/intent_taxonomy.json"),
    ("frozen/ascii_v1/intent_coverage.json", "ascii_dataset/intent_coverage.json"),
    ("frozen/ascii_v1/shortcut_check.json", "ascii_dataset/shortcut_check.json"),
    ("frozen/ascii_v1/summary_ascii.json", "ascii_dataset/summary_ascii.json"),
    ("frozen/ascii_v1/manifest/ascii_manifest.csv", "ascii_dataset/manifest/ascii_manifest.csv"),
    ("frozen/ascii_v1/manifest/ascii_fragments.csv", "ascii_dataset/manifest/ascii_fragments.csv"),
    ("frozen/ascii_v1/verification/verification_report.json", "ascii_dataset/verification/verification_report.json"),
    ("frozen/ascii_v1/verification/verification_log.csv", "ascii_dataset/verification/verification_log.csv"),
    ("frozen/ascii_v1/verification/hand_review_sample.csv", "ascii_dataset/verification/hand_review_sample.csv"),
    ("frozen/ascii_v1/splits/iid.json", "ascii_dataset/splits/iid.json"),
    ("frozen/ascii_v1/splits/lofo_channel.json", "ascii_dataset/splits/lofo_channel.json"),
    ("frozen/ascii_v1/splits/exploratory_ascii_leak_tier.json", "ascii_dataset/splits/exploratory_ascii_leak_tier.json"),
    ("frozen/ascii_v1/splits/exploratory_ascii_block_font.json", "ascii_dataset/splits/exploratory_ascii_block_font.json"),
]
ascii_mismatch = 0
for frozen, live in ascii_pairs:
    h1 = sha256(frozen)
    h2 = sha256(live)
    if h1 != h2:
        ascii_mismatch += 1
        check(False, f"Byte-identical: {frozen}", "differs from live")
check(ascii_mismatch == 0, f"All {len(ascii_pairs)} ASCII frozen files byte-identical to live")

print("\n--- D2. QR v2 frozen matches live ---")
qr_pairs = [
    ("frozen/qr_v2/dataset_revision.txt", "qr_dataset/dataset_revision.txt"),
    ("frozen/qr_v2/decisions.md", "qr_dataset/decisions.md"),
    ("frozen/qr_v2/full_payloads.txt", "qr_dataset/full_payloads.txt"),
    ("frozen/qr_v2/generator_config.json", "qr_dataset/generator_config.json"),
    ("frozen/qr_v2/intent_coverage.json", "qr_dataset/intent_coverage.json"),
    ("frozen/qr_v2/shortcut_check.json", "qr_dataset/shortcut_check.json"),
    ("frozen/qr_v2/summary_qr.json", "qr_dataset/summary_qr.json"),
    ("frozen/qr_v2/manifest/manifest_v3.csv", "qr_dataset/manifest_v3.csv"),
    ("frozen/qr_v2/verification/verification_report.json", "qr_dataset/verification/verification_report.json"),
    ("frozen/qr_v2/verification/verification_log.csv", "qr_dataset/verification/verification_log.csv"),
    ("frozen/qr_v2/verification/hand_review_sample.csv", "qr_dataset/verification/hand_review_sample.csv"),
    ("frozen/qr_v2/splits/iid_all_families.json", "qr_dataset/splits/iid_all_families.json"),
    ("frozen/qr_v2/splits/lofo_qr_held_out.json", "qr_dataset/splits/lofo_qr_held_out.json"),
    ("frozen/qr_v2/splits/lofo_ascii_held_out.json", "qr_dataset/splits/lofo_ascii_held_out.json"),
]
qr_mismatch = 0
for frozen, live in qr_pairs:
    h1 = sha256(frozen)
    h2 = sha256(live)
    if h1 != h2:
        qr_mismatch += 1
        check(False, f"Byte-identical: {frozen}", "differs from live")
check(qr_mismatch == 0, f"All {len(qr_pairs)} QR v2 frozen files byte-identical to live")

# =============================================================================
print("\n" + "=" * 72)
print("PART E -- SPLIT INTEGRITY")
print("=" * 72)

print("\n--- E1. IID splits match between families ---")
iid_ascii = load_json("ascii_dataset/splits/iid.json")
iid_qr = load_json("qr_dataset/splits/iid_all_families.json")
if iid_ascii and iid_qr:
    match_train = iid_ascii.get("train_intents") == iid_qr.get("train_intents")
    match_val = iid_ascii.get("val_intents") == iid_qr.get("val_intents")
    match_test = iid_ascii.get("test_intents") == iid_qr.get("test_intents")
    check(match_train, "train_intents match between ASCII and QR IID splits")
    check(match_val, "val_intents match")
    check(match_test, "test_intents match")
    total = len(iid_ascii["train_intents"]) + len(iid_ascii["val_intents"]) + len(iid_ascii["test_intents"])
    check(total == 21, f"Total IID intents = 21: {total}")
else:
    check(False, "Both IID split files load")

print("\n--- E2. LOFO splits name the right families ---")
lofo_qr = load_json("qr_dataset/splits/lofo_qr_held_out.json")
lofo_ascii = load_json("qr_dataset/splits/lofo_ascii_held_out.json")
if lofo_qr:
    check(lofo_qr.get("test_families") == ["qr"], f"QR LOFO test_families = ['qr']: {lofo_qr.get('test_families')}")
    check(lofo_qr.get("train_families") == ["ascii_art"], f"QR LOFO train_families = ['ascii_art']: {lofo_qr.get('train_families')}")
if lofo_ascii:
    check(lofo_ascii.get("test_families") == ["ascii_art"], f"ASCII LOFO test_families = ['ascii_art']: {lofo_ascii.get('test_families')}")
    check(lofo_ascii.get("train_families") == ["qr"], f"ASCII LOFO train_families = ['qr']: {lofo_ascii.get('train_families')}")

# =============================================================================
print("\n" + "=" * 72)
print("FINAL VERDICT")
print("=" * 72)

print(f"\nTotal checks passed: {sum(1 for _ in range(0))}")  # placeholder
print(f"Failures: {len(failures)}")
print(f"Warnings: {len(warnings)}")

if failures:
    print("\nFailures:")
    for f in failures:
        print(f"  - {f}")

if warnings:
    print("\nWarnings (not blocking):")
    for w in warnings:
        print(f"  - {w}")

if len(failures) == 0:
    print("\n" + "=" * 72)
    print("  DATASET STATUS: READY")
    print("  Both QR and ASCII channels are complete and internally consistent.")
    print("  You can proceed to the next channel (homoglyph, text, or cross-modal).")
    print("=" * 72)
    sys.exit(0)
else:
    print("\n" + "=" * 72)
    print("  DATASET STATUS: NOT READY")
    print("  Fix the failures above before proceeding.")
    print("=" * 72)
    sys.exit(1)
