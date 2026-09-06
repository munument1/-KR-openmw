#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_text(data: bytes, mode: str) -> str:
    data = data.rstrip(b"\x00")
    encs = ["utf-8-sig", "utf-8", "cp1252", "latin1"] if mode == "openmw" else ["cp949", "utf-8-sig", "utf-8", "cp1252", "latin1"]
    for enc in encs:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("latin1", errors="replace")


def parse_subrecords(payload: bytes):
    out = []
    pos = 0
    while pos + 8 <= len(payload):
        name = payload[pos:pos+4].decode("ascii", errors="replace")
        size = struct.unpack_from("<I", payload, pos + 4)[0]
        pos += 8
        if pos + size > len(payload):
            out.append(("BROKEN", payload[pos:]))
            break
        out.append((name, payload[pos:pos+size]))
        pos += size
    return out


def parse_records(path: Path, mode: str):
    data = path.read_bytes()
    pos = 0
    records = []
    while pos + 16 <= len(data):
        rtype_b = data[pos:pos+4]
        try:
            rtype = rtype_b.decode("ascii")
        except UnicodeDecodeError:
            break
        size, unknown, flags = struct.unpack_from("<III", data, pos + 4)
        pos += 16
        if pos + size > len(data):
            break
        payload = data[pos:pos+size]
        pos += size
        records.append({"type": rtype, "size": size, "unknown": unknown, "flags": flags, "subs": parse_subrecords(payload), "raw_sha256": sha256(payload)})
    return data, records


def sub_first(rec, name):
    for n, d in rec["subs"]:
        if n == name:
            return d
    return None


def sub_all(rec, name):
    return [d for n, d in rec["subs"] if n == name]


def script_id(rec):
    schd = sub_first(rec, "SCHD") or b""
    return schd[:32].split(b"\x00", 1)[0].decode("ascii", errors="replace")


def build_model(path: Path, mode: str):
    data, records = parse_records(path, mode)
    dials = []
    infos = []
    scripts = {}
    current_dial = None
    info_ord = defaultdict(int)
    type_counts = Counter(r["type"] for r in records)
    for rec_index, rec in enumerate(records):
        if rec["type"] == "DIAL":
            name_b = sub_first(rec, "NAME") or b""
            current_dial = len(dials)
            dials.append({
                "dial_index": current_dial,
                "record_index": rec_index,
                "name": decode_text(name_b, mode),
                "data_hex": (sub_first(rec, "DATA") or b"").hex(),
                "raw_sha256": rec["raw_sha256"],
            })
        elif rec["type"] == "INFO":
            idx = current_dial if current_dial is not None else -1
            ordinal = info_ord[idx]
            info_ord[idx] += 1
            inam = decode_text(sub_first(rec, "INAM") or b"", mode)
            fields = {}
            for fn in ("PNAM","NNAM","DATA","ONAM","RNAM","CNAM","FNAM","ANAM","DNAM","SCVR","INTV","FLTV","QSTN","QSTF","QSTR"):
                vals = sub_all(rec, fn)
                if vals:
                    if fn in ("DATA","INTV","FLTV"):
                        fields[fn] = [v.hex() for v in vals]
                    else:
                        fields[fn] = [decode_text(v, mode) for v in vals]
            infos.append({
                "dial_index": idx,
                "info_ordinal": ordinal,
                "record_index": rec_index,
                "inam": inam,
                "response": decode_text(sub_first(rec, "NAME") or b"", mode),
                "result": decode_text(sub_first(rec, "BNAM") or b"", mode),
                "fields": fields,
                "raw_sha256": rec["raw_sha256"],
            })
        elif rec["type"] == "SCPT":
            sid = script_id(rec)
            scripts[sid] = {
                "record_index": rec_index,
                "sctx": decode_text(sub_first(rec, "SCTX") or b"", mode),
                "scdt_sha256": sha256(sub_first(rec, "SCDT") or b""),
                "raw_sha256": rec["raw_sha256"],
            }
    return {
        "path": str(path),
        "size": len(data),
        "sha256": sha256(data),
        "record_count": len(records),
        "type_counts": dict(type_counts),
        "dials": dials,
        "infos": infos,
        "scripts": scripts,
    }


def find_file(root: Path, suffix: str, prefer=None):
    matches = [p for p in root.rglob(f"*{suffix}") if p.is_file()]
    if prefer:
        preferred = [p for p in matches if prefer.lower() in p.name.lower()]
        if preferred:
            matches = preferred
    if not matches:
        return None
    matches.sort(key=lambda p: (len(str(p)), str(p)))
    return matches[0]


def info_key(i):
    return (i["dial_index"], i["inam"], i["info_ordinal"])


def known_hit(obj):
    blob = json.dumps(obj, ensure_ascii=False).lower()
    needles = ["hasphat", "antabolis", "ranis", "athrys", "ajira", "galbedir", "하스팟", "라니스", "아지라", "갈베디르"]
    return any(n in blob for n in needles)


def dump_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def strip_markers(text: str) -> str:
    return re.sub(r"@([^#]*)#", r"\1", text)


def marker_phrases(text: str):
    return re.findall(r"@([^#]+)#", text)


def load_sidecar(root: Path, ext: str, mode: str):
    p = find_file(root, ext, "ReTranslation") or find_file(root, ext)
    if not p:
        return {"path": None, "sha256": None, "line_count": 0, "entries": []}
    raw = p.read_bytes()
    text = decode_text(raw, mode)
    entries = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line:
            continue
        if "\t" in line:
            key, value = line.split("\t", 1)
        else:
            key, value = line, ""
        entries.append({"line": line_no, "key": key, "value": value})
    return {"path": str(p.relative_to(root)), "sha256": sha256(raw), "line_count": len(text.splitlines()), "entries": entries}


def mapping(side):
    out = {}
    for e in side["entries"]:
        if e["key"] and e["value"] and e["key"] not in out:
            out[e["key"]] = e["value"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--openmw", required=True)
    ap.add_argument("--cp949", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    openmw_root = Path(args.openmw)
    cp949_root = Path(args.cp949)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    openmw_esp = find_file(openmw_root, ".esp", "ReTranslation") or find_file(openmw_root, ".esp")
    cp949_esp = find_file(cp949_root, ".esp", "ReTranslation") or find_file(cp949_root, ".esp")

    inventory = {
        "openmw_files": sorted(str(p.relative_to(openmw_root)) for p in openmw_root.rglob("*") if p.is_file()),
        "cp949_files": sorted(str(p.relative_to(cp949_root)) for p in cp949_root.rglob("*") if p.is_file()),
        "openmw_esp": str(openmw_esp.relative_to(openmw_root)) if openmw_esp else None,
        "cp949_esp": str(cp949_esp.relative_to(cp949_root)) if cp949_esp else None,
    }
    dump_json(out / "inventory.json", inventory)
    if not openmw_esp or not cp949_esp:
        dump_json(out / "summary.json", {"status":"NO_ESP", **inventory})
        return

    omw = build_model(openmw_esp, "openmw")
    cp = build_model(cp949_esp, "cp949")
    omw_top = load_sidecar(openmw_root, ".top", "openmw")
    omw_mrk = load_sidecar(openmw_root, ".mrk", "openmw")
    cp_top = load_sidecar(cp949_root, ".top", "cp949")
    cp_mrk = load_sidecar(cp949_root, ".mrk", "cp949")
    top_map = mapping(omw_top)
    mrk_map = mapping(omw_mrk)

    dial_diffs = []
    for idx in range(max(len(omw["dials"]), len(cp["dials"]))):
        a = omw["dials"][idx] if idx < len(omw["dials"]) else None
        b = cp["dials"][idx] if idx < len(cp["dials"]) else None
        if a != b:
            if a and b and a["name"] == b["name"] and a["data_hex"] == b["data_hex"]:
                continue
            dial_diffs.append({"dial_index":idx,"openmw":a,"cp949":b})

    omw_info = {info_key(i): i for i in omw["infos"]}
    cp_info = {info_key(i): i for i in cp["infos"]}
    info_logic = []
    info_text = []
    marker_only = []
    content_changed = []
    known = []
    known_marker_only = []
    for key in sorted(set(omw_info) | set(cp_info), key=lambda x:(x[0],x[2],x[1])):
        a, b = omw_info.get(key), cp_info.get(key)
        if a is None or b is None:
            row = {"key":key,"kind":"missing_record","openmw":a,"cp949":b}
            info_logic.append(row)
            if known_hit(row): known.append(row)
            continue
        logic_changed = a["fields"] != b["fields"] or a["result"] != b["result"]
        text_changed = a["response"] != b["response"]
        if logic_changed:
            row = {"key":key,"kind":"info_logic","dial_openmw":omw["dials"][a["dial_index"]]["name"] if a["dial_index"] >= 0 else None,"dial_cp949":cp["dials"][b["dial_index"]]["name"] if b["dial_index"] >= 0 else None,"openmw":{"fields":a["fields"],"result":a["result"],"response":a["response"]},"cp949":{"fields":b["fields"],"result":b["result"],"response":b["response"]}}
            info_logic.append(row)
            if known_hit(row): known.append(row)
        if text_changed:
            marker_only_change = strip_markers(a["response"]) == b["response"] and bool(marker_phrases(a["response"]))
            row = {"key":key,"kind":"marker_only" if marker_only_change else "info_response","dial_openmw":omw["dials"][a["dial_index"]]["name"] if a["dial_index"] >= 0 else None,"dial_cp949":cp["dials"][b["dial_index"]]["name"] if b["dial_index"] >= 0 else None,"openmw":a["response"],"cp949":b["response"],"markers":marker_phrases(a["response"])}
            info_text.append(row)
            (marker_only if marker_only_change else content_changed).append(row)
            if known_hit(row):
                known.append(row)
                if marker_only_change: known_marker_only.append(row)

    script_diffs = []
    for sid in sorted(set(omw["scripts"]) | set(cp["scripts"])):
        a, b = omw["scripts"].get(sid), cp["scripts"].get(sid)
        if not a or not b or a["sctx"] != b["sctx"]:
            row = {"script":sid,"openmw":a,"cp949":b}
            script_diffs.append(row)
            if known_hit(row): known.append(row)

    for row in dial_diffs:
        if known_hit(row): known.append(row)

    dial_names = {d["name"] for d in omw["dials"]}
    marker_counter = Counter()
    for i in omw["infos"]:
        marker_counter.update(marker_phrases(i["response"]))
    marker_resolution = []
    resolution_counts = Counter()
    for phrase, count in marker_counter.most_common():
        if phrase in top_map:
            target = top_map[phrase]
            method = "top"
        elif phrase in dial_names:
            target = phrase
            method = "direct_dial"
        else:
            target = None
            method = "unresolved"
        resolution_counts[method] += 1
        marker_resolution.append({"phrase":phrase,"occurrences":count,"method":method,"target":target,"mrk_keyword":mrk_map.get(target) if target else None})

    omw_mrk_map = mapping(omw_mrk)
    cp_mrk_map = mapping(cp_mrk)
    mrk_added = {k:v for k,v in omw_mrk_map.items() if k not in cp_mrk_map}
    mrk_removed = {k:v for k,v in cp_mrk_map.items() if k not in omw_mrk_map}
    mrk_changed = {k:{"openmw":omw_mrk_map[k],"cp949":cp_mrk_map[k]} for k in omw_mrk_map.keys() & cp_mrk_map.keys() if omw_mrk_map[k] != cp_mrk_map[k]}

    sidecar_summary = {
        "openmw_top":{"path":omw_top["path"],"sha256":omw_top["sha256"],"line_count":omw_top["line_count"],"entry_count":len(omw_top["entries"])},
        "openmw_mrk":{"path":omw_mrk["path"],"sha256":omw_mrk["sha256"],"line_count":omw_mrk["line_count"],"entry_count":len(omw_mrk["entries"])},
        "cp949_top":{"path":cp_top["path"],"sha256":cp_top["sha256"],"line_count":cp_top["line_count"],"entry_count":len(cp_top["entries"])},
        "cp949_mrk":{"path":cp_mrk["path"],"sha256":cp_mrk["sha256"],"line_count":cp_mrk["line_count"],"entry_count":len(cp_mrk["entries"])},
        "mrk_diff_counts":{"added":len(mrk_added),"removed":len(mrk_removed),"changed":len(mrk_changed)},
        "marker_resolution_counts":dict(resolution_counts),
        "marker_unique_phrases":len(marker_counter),
        "marker_occurrences":sum(marker_counter.values()),
    }

    summary = {
        "status":"OK",
        "openmw":{"esp":inventory["openmw_esp"],"sha256":omw["sha256"],"size":omw["size"],"dials":len(omw["dials"]),"infos":len(omw["infos"]),"scripts":len(omw["scripts"])},
        "cp949":{"esp":inventory["cp949_esp"],"sha256":cp["sha256"],"size":cp["size"],"dials":len(cp["dials"]),"infos":len(cp["infos"]),"scripts":len(cp["scripts"])},
        "diff_counts":{"dial":len(dial_diffs),"info_logic":len(info_logic),"info_response":len(info_text),"marker_only_response":len(marker_only),"content_changed_response":len(content_changed),"script_sctx":len(script_diffs),"known_regression_hits":len(known),"known_marker_only_hits":len(known_marker_only)},
        "sidecars":sidecar_summary,
    }
    dump_json(out / "summary.json", summary)
    dump_json(out / "dial_diffs.json", dial_diffs)
    dump_json(out / "info_logic_diffs.json", info_logic)
    dump_json(out / "info_response_diffs.json", info_text)
    dump_json(out / "marker_only_diffs.json", marker_only)
    dump_json(out / "content_changed_diffs.json", content_changed)
    dump_json(out / "script_diffs.json", script_diffs)
    dump_json(out / "known_regressions.json", known)
    dump_json(out / "known_marker_only.json", known_marker_only)
    dump_json(out / "sidecar_summary.json", sidecar_summary)
    dump_json(out / "marker_resolution.json", marker_resolution)
    dump_json(out / "mrk_diffs.json", {"added":mrk_added,"removed":mrk_removed,"changed":mrk_changed})
    dump_json(out / "openmw_top_entries.json", omw_top["entries"])


if __name__ == "__main__":
    main()
