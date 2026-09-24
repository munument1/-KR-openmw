#!/usr/bin/env python3
"""Validate Morrowind_OfficialAddon_KR against Bethesda's eight official addons.

The validator is deliberately strict around dialogue topology. It permits only:
- INFO NAME response translation;
- INFO BNAM changes that translate Choice labels and/or redirect addtopic to the
  Korean duplicate topic ID;
- player-visible FNAM/TEXT translation on copied object records;
- the ten Master Index Warp_* scripts to drop compiled SCDT and translate only
  the MessageBox text while preserving executable source logic.

Everything else must remain byte-identical to the official source records.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import struct
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode(raw: bytes) -> str:
    raw = raw.rstrip(b"\x00")
    for enc in ("utf-8", "cp1252", "latin1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin1", errors="replace")


def parse_subrecords(payload: bytes):
    out = []
    pos = 0
    while pos < len(payload):
        if pos + 8 > len(payload):
            raise ValueError(f"truncated subrecord header at {pos}")
        name = payload[pos:pos + 4].decode("ascii")
        size = struct.unpack_from("<I", payload, pos + 4)[0]
        start = pos + 8
        end = start + size
        if end > len(payload):
            raise ValueError(f"truncated subrecord {name}")
        out.append((name, payload[start:end]))
        pos = end
    return out


def parse_records(blob: bytes):
    out = []
    pos = 0
    current_dial = None
    while pos < len(blob):
        if pos + 16 > len(blob):
            raise ValueError(f"truncated record header at {pos}")
        rtype = blob[pos:pos + 4].decode("ascii")
        size, unknown, flags = struct.unpack_from("<III", blob, pos + 4)
        start = pos + 16
        end = start + size
        if end > len(blob):
            raise ValueError(f"truncated {rtype} record")
        subs = parse_subrecords(blob[start:end])
        rec = {"type": rtype, "unknown": unknown, "flags": flags, "subs": subs}
        if rtype == "DIAL":
            current_dial = decode(first_sub(subs, "NAME") or b"")
        rec["parent_dial"] = current_dial
        out.append(rec)
        pos = end
    return out


def first_sub(subs, name: str):
    for stype, data in subs:
        if stype == name:
            return data
    return None


def fixed_script_id(subs) -> str:
    raw = first_sub(subs, "SCHD") or b""
    return raw[:32].split(b"\x00", 1)[0].decode("cp1252", errors="replace")


def record_id(rec) -> str:
    if rec["type"] == "SCPT":
        return fixed_script_id(rec["subs"])
    return decode(first_sub(rec["subs"], "NAME") or b"")


def find_plugin(root: Path, name: str) -> Path:
    matches = [p for p in root.rglob(name) if p.is_file()]
    if not matches:
        raise FileNotFoundError(name)
    matches.sort(key=lambda p: (len(p.parts), str(p).lower()))
    return matches[0]


CHOICE_RE = re.compile(r'(?i)\bChoice\s+"[^"]*"\s+(-?\d+)')
ADDTOPIC_RE = re.compile(r'(?i)\baddtopic\s+"[^"]*"')


def normalize_result_script(text: str) -> str:
    text = CHOICE_RE.sub(lambda m: f"Choice <TEXT> {m.group(1)}", text)
    text = ADDTOPIC_RE.sub('addtopic "<TOPIC>"', text)
    return text


def normalize_warp_script(text: str) -> str:
    return re.sub(
        r'(?i)MessageBox\s+"[^"]*"',
        'MessageBox "<TEXT>"',
        text,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", required=True, type=Path)
    ap.add_argument("--output-root", required=True, type=Path)
    ap.add_argument(
        "--manifest",
        type=Path,
        default=Path("korean/official-addons/manifest.json"),
    )
    ap.add_argument("--report", required=True, type=Path)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    esp = args.output_root / "Morrowind_OfficialAddon_KR.esp"
    top = args.output_root / "Morrowind_OfficialAddon_KR.top"
    mrk = args.output_root / "Morrowind_OfficialAddon_KR.mrk"
    cel = args.output_root / "Morrowind_OfficialAddon_KR.cel"

    checks = {}
    source_records = []
    source_infos = {}
    source_normal = collections.defaultdict(list)
    source_scripts = {}

    expected_masters = ["Morrowind.esm"]
    for item in manifest["required_plugins"]:
        p = find_plugin(args.source_root, item["plugin"])
        blob = p.read_bytes()
        actual = sha256(blob)
        checks[f"source_hash:{item['plugin']}"] = actual == item["sha256"]
        expected_masters.append(item["plugin"])
        for rec in parse_records(blob):
            source_records.append((item["plugin"], rec))
            if rec["type"] == "INFO":
                iid = decode(first_sub(rec["subs"], "INAM") or b"")
                if iid in source_infos:
                    raise RuntimeError(f"duplicate source INFO id: {iid}")
                source_infos[iid] = (item["plugin"], rec)
            elif rec["type"] == "SCPT":
                source_scripts[record_id(rec)] = (item["plugin"], rec)
            elif rec["type"] not in ("TES3", "DIAL"):
                rid = record_id(rec)
                if rid:
                    source_normal[(rec["type"], rid)].append((item["plugin"], rec))

    out_blob = esp.read_bytes()
    out_records = parse_records(out_blob)
    type_counts = collections.Counter(r["type"] for r in out_records)

    header = out_records[0]
    masters = [decode(data) for name, data in header["subs"] if name == "MAST"]
    checks["masters_exact"] = masters == expected_masters
    checks["info_count"] = type_counts["INFO"] == 346
    checks["dial_count"] = type_counts["DIAL"] == 48
    checks["warp_script_count"] = type_counts["SCPT"] == 10

    out_infos = {}
    output_dials = set()
    for rec in out_records:
        if rec["type"] == "DIAL":
            output_dials.add(record_id(rec))
        elif rec["type"] == "INFO":
            iid = decode(first_sub(rec["subs"], "INAM") or b"")
            if iid in out_infos:
                raise RuntimeError(f"duplicate output INFO id: {iid}")
            out_infos[iid] = rec

    checks["all_source_info_ids_present_once"] = set(source_infos) == set(out_infos)

    info_structural_mismatches = []
    result_script_mismatches = []
    untranslated_info = []
    parent_mapping = collections.Counter()

    for iid, (plugin, src) in source_infos.items():
        out = out_infos[iid]
        parent_mapping[(src["parent_dial"], out["parent_dial"])] += 1

        src_struct = [x for x in src["subs"] if x[0] not in ("NAME", "BNAM")]
        out_struct = [x for x in out["subs"] if x[0] not in ("NAME", "BNAM")]
        if (
            src_struct != out_struct
            or src["unknown"] != out["unknown"]
            or src["flags"] != out["flags"]
        ):
            info_structural_mismatches.append(iid)

        src_result = decode(first_sub(src["subs"], "BNAM") or b"")
        out_result = decode(first_sub(out["subs"], "BNAM") or b"")
        if normalize_result_script(src_result) != normalize_result_script(out_result):
            result_script_mismatches.append(iid)

        response = decode(first_sub(out["subs"], "NAME") or b"")
        if not response or not re.search(r"[가-힣]", response):
            untranslated_info.append(iid)

    checks["info_nontext_structure_identical"] = not info_structural_mismatches
    checks["info_result_changes_limited_to_choice_addtopic"] = not result_script_mismatches
    checks["all_info_responses_korean"] = not untranslated_info

    display_structural_mismatches = []
    untranslated_names = []
    book_count = 0
    normal_count = 0

    for rec in out_records:
        if rec["type"] in ("TES3", "DIAL", "INFO", "SCPT"):
            continue
        rid = record_id(rec)
        candidates = source_normal.get((rec["type"], rid), [])
        if not candidates:
            display_structural_mismatches.append(f"{rec['type']}:{rid}:missing-source")
            continue

        allowed = {"FNAM"}
        if rec["type"] == "BOOK":
            allowed.add("TEXT")
            book_count += 1

        out_struct = [x for x in rec["subs"] if x[0] not in allowed]
        matched = False
        for _, src in candidates:
            src_struct = [x for x in src["subs"] if x[0] not in allowed]
            if (
                src_struct == out_struct
                and src["unknown"] == rec["unknown"]
                and src["flags"] == rec["flags"]
            ):
                matched = True
                break
        if not matched:
            display_structural_mismatches.append(f"{rec['type']}:{rid}")

        fnam = first_sub(rec["subs"], "FNAM")
        if fnam is not None:
            normal_count += 1
            if not re.search(r"[가-힣]", decode(fnam)):
                untranslated_names.append(f"{rec['type']}:{rid}")

    checks["object_nontext_structure_identical"] = not display_structural_mismatches
    checks["all_display_names_korean"] = not untranslated_names
    checks["display_name_count"] = normal_count == 144
    checks["translated_book_count"] = book_count == 3

    warp_mismatches = []
    warp_ids = set()
    for rec in out_records:
        if rec["type"] != "SCPT":
            continue
        sid = record_id(rec)
        warp_ids.add(sid)
        source = source_scripts.get(sid)
        if source is None or source[0].lower() != "master_index.esp":
            warp_mismatches.append(f"{sid}:missing-source")
            continue
        src = source[1]
        if not sid.startswith("Warp_"):
            warp_mismatches.append(f"{sid}:unexpected-script")
            continue

        src_text = decode(first_sub(src["subs"], "SCTX") or b"")
        out_text = decode(first_sub(rec["subs"], "SCTX") or b"")
        if normalize_warp_script(src_text) != normalize_warp_script(out_text):
            warp_mismatches.append(f"{sid}:logic")
        if first_sub(rec["subs"], "SCDT") not in (b"", None):
            warp_mismatches.append(f"{sid}:compiled-data-not-stripped")
        if "이 프로필론의 색인이 없습니다." not in out_text:
            warp_mismatches.append(f"{sid}:message-not-korean")

    checks["master_index_warp_scripts_safe"] = (
        len(warp_ids) == 10 and not warp_mismatches
    )

    top_rows = []
    for line in top.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        if "\t" not in line:
            raise RuntimeError(f"bad TOP row: {line!r}")
        key, value = line.split("\t", 1)
        top_rows.append((key, value))
    bad_top_targets = [value for _, value in top_rows if value not in output_dials]
    checks["top_row_count"] = len(top_rows) == 13
    checks["all_top_targets_are_dials"] = not bad_top_targets
    checks["mrk_intentionally_empty"] = mrk.read_bytes() == b""
    checks["cel_row_count"] = len([x for x in cel.read_text("utf-8").splitlines() if x]) == 11

    status = "PASS" if all(checks.values()) else "FAIL"
    report = {
        "status": status,
        "output": {
            "esp_sha256": sha256(out_blob),
            "esp_size": len(out_blob),
            "type_counts": dict(type_counts),
            "masters": masters,
            "top_sha256": sha256(top.read_bytes()),
            "mrk_sha256": sha256(mrk.read_bytes()),
            "cel_sha256": sha256(cel.read_bytes()),
        },
        "checks": checks,
        "details": {
            "source_info_count": len(source_infos),
            "output_info_count": len(out_infos),
            "info_structural_mismatches": info_structural_mismatches,
            "result_script_mismatches": result_script_mismatches,
            "untranslated_info": untranslated_info,
            "display_structural_mismatches": display_structural_mismatches,
            "untranslated_display_names": untranslated_names,
            "warp_mismatches": warp_mismatches,
            "bad_top_targets": bad_top_targets,
            "parent_mapping": [
                {"source": a, "output": b, "info_count": n}
                for (a, b), n in sorted(parent_mapping.items())
            ],
        },
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": status, "checks": checks}, ensure_ascii=False))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
