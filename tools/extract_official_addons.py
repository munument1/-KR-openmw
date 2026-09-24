#!/usr/bin/env python3
"""Extract and validate Bethesda Morrowind official-addon localization targets.

This tool is intentionally read-only. It parses the eight official ESPs, checks
their SHA-256 values against korean/official-addons/manifest.json, and emits a
JSON report containing dialogue topology plus display-name strings.

DIAL NAME values are topic identities and are never treated as translatable
display strings here. INFO NAME is the player-visible response/journal text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_text(data: bytes) -> str:
    raw = data.rstrip(b"\x00")
    for enc in ("cp1252", "utf-8", "latin1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin1", errors="replace")


def parse_subrecords(payload: bytes):
    pos = 0
    out = []
    while pos < len(payload):
        if pos + 8 > len(payload):
            raise ValueError(f"truncated subrecord header at {pos}")
        name = payload[pos:pos + 4].decode("ascii", errors="strict")
        size = struct.unpack_from("<I", payload, pos + 4)[0]
        start = pos + 8
        end = start + size
        if end > len(payload):
            raise ValueError(f"truncated subrecord {name}")
        out.append((name, payload[start:end]))
        pos = end
    return out


def iter_records(blob: bytes):
    pos = 0
    while pos < len(blob):
        if pos + 16 > len(blob):
            raise ValueError(f"truncated record header at {pos}")
        rtype = blob[pos:pos + 4].decode("ascii", errors="strict")
        size, unknown, flags = struct.unpack_from("<III", blob, pos + 4)
        start = pos + 16
        end = start + size
        if end > len(blob):
            raise ValueError(f"truncated {rtype} record")
        payload = blob[start:end]
        subs = parse_subrecords(payload)
        yield {
            "type": rtype,
            "unknown": unknown,
            "flags": flags,
            "subs": subs,
        }
        pos = end


def first_sub(subs, name: str) -> bytes | None:
    for stype, data in subs:
        if stype == name:
            return data
    return None


def sub_map(subs):
    out = defaultdict(list)
    for name, data in subs:
        out[name].append(data)
    return out


def find_plugin(root: Path, filename: str) -> Path:
    matches = [p for p in root.rglob(filename) if p.is_file()]
    if not matches:
        raise FileNotFoundError(f"missing required plugin: {filename}")
    matches.sort(key=lambda p: (len(p.parts), str(p).lower()))
    return matches[0]


def analyze_plugin(path: Path):
    blob = path.read_bytes()
    current_dial = None
    ordinal = Counter()
    dials = []
    infos = []
    display = []

    for rec in iter_records(blob):
        rtype = rec["type"]
        subs = rec["subs"]
        smap = sub_map(subs)

        if rtype == "DIAL":
            current_dial = decode_text(first_sub(subs, "NAME") or b"")
            data = first_sub(subs, "DATA") or b""
            dials.append({"name": current_dial, "data": data.hex()})
            continue

        if rtype == "INFO":
            idx = ordinal[current_dial]
            ordinal[current_dial] += 1
            infos.append(
                {
                    "dial": current_dial,
                    "ordinal": idx,
                    "inam": decode_text(first_sub(subs, "INAM") or b""),
                    "pnam": decode_text(first_sub(subs, "PNAM") or b""),
                    "nnam": decode_text(first_sub(subs, "NNAM") or b""),
                    "response": decode_text(first_sub(subs, "NAME") or b""),
                    "result": decode_text(first_sub(subs, "BNAM") or b""),
                    "subrecords": [name for name, _ in subs],
                }
            )
            continue

        # Common object records use NAME as the technical ID and FNAM as the
        # player-visible name. CELL/DIAL identities are deliberately excluded.
        if "FNAM" in smap:
            display.append(
                {
                    "type": rtype,
                    "id": decode_text(first_sub(subs, "NAME") or b""),
                    "text": decode_text(first_sub(subs, "FNAM") or b""),
                }
            )

    topic_counts = Counter(info["dial"] for info in infos)
    return {
        "path": str(path),
        "size": len(blob),
        "sha256": sha256(blob),
        "counts": {
            "DIAL": len(dials),
            "INFO": len(infos),
            "display_name_records": len(display),
        },
        "dialogue_topics": [
            {"name": dial["name"], "info_count": topic_counts[dial["name"]]}
            for dial in dials
        ],
        "dials": dials,
        "infos": infos,
        "display_names": display,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument(
        "--manifest",
        type=Path,
        default=Path("korean/official-addons/manifest.json"),
    )
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = {
        "status": "PASS",
        "output_plugin": manifest["output_plugin"],
        "plugins": {},
        "totals": {"DIAL": 0, "INFO": 0, "display_name_records": 0},
    }

    for item in manifest["required_plugins"]:
        filename = item["plugin"]
        path = find_plugin(args.root, filename)
        result = analyze_plugin(path)

        expected = item["sha256"].lower()
        actual = result["sha256"].lower()
        if actual != expected:
            raise SystemExit(
                f"{filename}: SHA-256 mismatch: expected {expected}, got {actual}"
            )

        report["plugins"][filename] = result
        for key in report["totals"]:
            report["totals"][key] += result["counts"][key]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": "PASS", "totals": report["totals"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
