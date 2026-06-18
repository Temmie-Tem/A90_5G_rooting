#!/usr/bin/env python3
"""V2710 host-only reparse of legacy Android-good ACDB ioctl traces.

This script scans existing private V2461/V2466 `/dev/msm_audio_cal` ptrace JSONL
captures and answers one narrow question: do those traces already contain
byte-exact AUDIO_SET_CALIBRATION records for the missing subsystem custom
topology cal_types 10, 14, and 24?

It decodes only the public 32-byte `struct cal_block_data`-style ioctl header
metadata from the saved JSONL records. It does not read dma-buf payloads, emit
raw bytes, touch a device, or issue any ioctl.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2710"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2710_AUDIO_ACDB_LEGACY_TRACE_SETCAL_REPARSE_2026-06-18.md"
DEFAULT_TRACE_GLOBS = (
    ROOT / "workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530/device-artifacts/msm-audio-cal-diag-threadset-*.jsonl",
    ROOT / "workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643/device-artifacts/msm-audio-cal-diag-threadset-*.jsonl",
)

AUDIO_ALLOCATE_CALIBRATION = "0xc00461c8"
AUDIO_DEALLOCATE_CALIBRATION = "0xc00461c9"
AUDIO_SET_CALIBRATION = "0xc00461cb"
REQUEST_NAMES = {
    AUDIO_ALLOCATE_CALIBRATION: "AUDIO_ALLOCATE_CALIBRATION",
    AUDIO_DEALLOCATE_CALIBRATION: "AUDIO_DEALLOCATE_CALIBRATION",
    AUDIO_SET_CALIBRATION: "AUDIO_SET_CALIBRATION",
}
TARGET_CAL_TYPES = (10, 14, 24)
TARGET_ROLES = {
    10: "ADM_CUST_TOPOLOGY",
    14: "ASM_CUST_TOPOLOGY",
    24: "AFE_CUST_TOPOLOGY",
}
CONTROL_CAL_TYPES = {
    39: "CORE_CUSTOM_TOPOLOGIES",
    20: "AFE_FB_SPKR_PROT",
}


def rel(path: Path | str) -> str:
    target = Path(path)
    try:
        return str(target.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_request(value: Any) -> str:
    if isinstance(value, int):
        return f"0x{value:08x}"
    text = str(value or "").strip().lower()
    if not text:
        return ""
    try:
        return f"0x{int(text, 0):08x}"
    except ValueError:
        return text


def decode_cal_header(bytes_hex: str) -> dict[str, int] | None:
    try:
        raw = bytes.fromhex(bytes_hex or "")
    except ValueError:
        return None
    if len(raw) < 32:
        return None
    words = struct.unpack("<8i", raw[:32])
    return {
        "data_size": words[0],
        "version": words[1],
        "cal_type": words[2],
        "cal_type_size": words[3],
        "cal_hdr_version": words[4],
        "buffer_number": words[5],
        "cal_size": words[6],
        "mem_handle": words[7],
    }


def run_label(path: Path) -> str:
    match = re.search(r"(v\d{4})-", str(path))
    return match.group(1).upper() if match else "UNKNOWN"


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                rows.append({"event": "json_decode_error", "line_number": line_number})
                continue
            row["_line_number"] = line_number
            rows.append(row)
    return rows


def parse_trace_file(path: Path) -> dict[str, Any]:
    rows = iter_jsonl(path)
    exits: dict[int, dict[str, Any]] = {}
    for row in rows:
        if row.get("event") != "ioctl_exit":
            continue
        try:
            exits[int(row.get("seq"))] = row
        except (TypeError, ValueError):
            continue

    entries: list[dict[str, Any]] = []
    decode_errors = 0
    for row in rows:
        if row.get("event") != "ioctl_entry":
            continue
        if "msm_audio_cal" not in str(row.get("fd_target") or ""):
            continue
        request = normalize_request(row.get("request"))
        if request not in REQUEST_NAMES:
            continue
        header = decode_cal_header(str(row.get("bytes_hex") or ""))
        if header is None:
            decode_errors += 1
            continue
        try:
            seq = int(row.get("seq"))
        except (TypeError, ValueError):
            seq = -1
        exit_row = exits.get(seq, {})
        entries.append(
            {
                "file": rel(path),
                "run": run_label(path),
                "line": row.get("_line_number"),
                "seq": seq,
                "tid": row.get("tid"),
                "fd_pid": row.get("fd_pid"),
                "abi": row.get("abi"),
                "request": request,
                "request_name": REQUEST_NAMES[request],
                "ret": exit_row.get("ret"),
                **header,
            }
        )
    return {
        "path": rel(path),
        "run": run_label(path),
        "entries": entries,
        "entry_count": len(entries),
        "decode_errors": decode_errors,
    }


def discover_trace_files(trace_files: list[str] | None, trace_globs: list[str] | None) -> list[Path]:
    paths: list[Path] = []
    if trace_files:
        paths.extend(Path(item) for item in trace_files)
    globs = [Path(item) for item in trace_globs] if trace_globs else list(DEFAULT_TRACE_GLOBS)
    for pattern in globs:
        paths.extend(pattern.parent.glob(pattern.name))
    deduped = sorted({path.resolve() for path in paths if path.exists()})
    return deduped


def aggregate(file_results: list[dict[str, Any]]) -> dict[str, Any]:
    entries = [entry for result in file_results for entry in result["entries"]]
    by_request = Counter(entry["request_name"] for entry in entries)
    by_request_cal_type = Counter((entry["request_name"], entry["cal_type"]) for entry in entries)
    by_run_request_cal_type = Counter((entry["run"], entry["request_name"], entry["cal_type"]) for entry in entries)
    set_entries = [entry for entry in entries if entry["request"] == AUDIO_SET_CALIBRATION]
    allocate_entries = [entry for entry in entries if entry["request"] == AUDIO_ALLOCATE_CALIBRATION]

    target_rows = []
    for cal_type in TARGET_CAL_TYPES:
        allocs = [entry for entry in allocate_entries if entry["cal_type"] == cal_type]
        sets = [entry for entry in set_entries if entry["cal_type"] == cal_type]
        target_rows.append(
            {
                "cal_type": cal_type,
                "role": TARGET_ROLES[cal_type],
                "allocate_count": len(allocs),
                "set_count": len(sets),
                "allocate_mem_handles": sorted({entry["mem_handle"] for entry in allocs}),
                "set_cal_sizes": sorted({entry["cal_size"] for entry in sets}),
                "set_ret_values": sorted({entry["ret"] for entry in sets}, key=lambda value: str(value)),
            }
        )

    control_rows = []
    for cal_type, role in CONTROL_CAL_TYPES.items():
        control_rows.append(
            {
                "cal_type": cal_type,
                "role": role,
                "allocate_count": sum(1 for entry in allocate_entries if entry["cal_type"] == cal_type),
                "set_count": sum(1 for entry in set_entries if entry["cal_type"] == cal_type),
                "set_cal_sizes": sorted({entry["cal_size"] for entry in set_entries if entry["cal_type"] == cal_type}),
            }
        )

    set_cal_type_counts = Counter(entry["cal_type"] for entry in set_entries)
    target_set_count = sum(row["set_count"] for row in target_rows)
    target_allocate_count = sum(row["allocate_count"] for row in target_rows)
    control_39_set_count = set_cal_type_counts.get(39, 0)

    classification = {
        "decision": "v2710-legacy-trace-frontier-unknown",
        "legacy_traces_have_target_setcal": target_set_count > 0,
        "legacy_traces_have_target_allocations": target_allocate_count > 0,
        "legacy_traces_have_core_topology_setcal_39": control_39_set_count > 0,
        "same_private_traces_can_supply_byte_exact_10_14_24_set": False,
        "fresh_capture_or_re_required": True,
    }
    if target_set_count == 0 and target_allocate_count > 0 and control_39_set_count > 0:
        classification.update(
            {
                "decision": "v2710-legacy-real-hal-traces-have-no-subsystem-topology-setcal",
                "same_private_traces_can_supply_byte_exact_10_14_24_set": False,
                "fresh_capture_or_re_required": True,
                "native_replay_should_remain_parked_until_new_set_geometry": True,
            }
        )
    elif target_set_count > 0:
        classification.update(
            {
                "decision": "v2710-legacy-traces-contain-target-setcal-candidate",
                "same_private_traces_can_supply_byte_exact_10_14_24_set": all(row["set_count"] > 0 for row in target_rows),
                "fresh_capture_or_re_required": not all(row["set_count"] > 0 for row in target_rows),
                "native_replay_should_remain_parked_until_new_set_geometry": not all(row["set_count"] > 0 for row in target_rows),
            }
        )

    return {
        "entry_count": len(entries),
        "file_count": len(file_results),
        "by_request": dict(sorted(by_request.items())),
        "by_request_cal_type": [
            {"request_name": name, "cal_type": cal_type, "count": count}
            for (name, cal_type), count in sorted(by_request_cal_type.items(), key=lambda item: (item[0][0], item[0][1]))
        ],
        "by_run_request_cal_type": [
            {"run": run, "request_name": name, "cal_type": cal_type, "count": count}
            for (run, name, cal_type), count in sorted(by_run_request_cal_type.items(), key=lambda item: (item[0][0], item[0][1], item[0][2]))
        ],
        "target_rows": target_rows,
        "control_rows": control_rows,
        "set_cal_type_counts": dict(sorted(set_cal_type_counts.items())),
        "classification": classification,
    }


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    trace_files = discover_trace_files(args.trace_file, args.trace_glob)
    file_results = [parse_trace_file(path) for path in trace_files]
    return {
        "run_id": RUN_ID,
        "created_at": now_iso(),
        "host_only": True,
        "device_action": False,
        "raw_payload_read": False,
        "inputs": [rel(path) for path in trace_files],
        "file_results": [
            {
                "path": result["path"],
                "run": result["run"],
                "entry_count": result["entry_count"],
                "decode_errors": result["decode_errors"],
            }
            for result in file_results
        ],
        "aggregate": aggregate(file_results),
        "next_requirements": [
            "Do not replay the V2707/V2708 manifest unchanged.",
            "Do not spend another iteration reparsing V2461/V2466 for cal_type 10/14/24 SET; this audit exhausts that source.",
            "Next useful input is a byte-exact Android-good SET event for cal_type 10, 14, and 24, or a source-backed reconstruction that changes the replay contract.",
        ],
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    aggregate_summary = summary["aggregate"]
    classification = aggregate_summary["classification"]
    lines = [
        "# NATIVE_INIT V2710 — Legacy ACDB trace SET-cal reparse",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only reparse of the existing V2461/V2466 Android-good `/dev/msm_audio_cal` ptrace JSONL captures. The parser decodes only the first 32 bytes of each ioctl argument as header metadata. It does not read dma-buf payloads, write raw bytes, run a device step, or issue any ioctl.",
        "",
        "## Inputs",
        "",
    ]
    for path_text in summary["inputs"]:
        lines.append(f"- `{path_text}`")
    lines.extend(
        [
            "",
            "## Result",
            "",
            f"- Decision: `{classification['decision']}`",
            f"- Parsed files: `{aggregate_summary['file_count']}`",
            f"- Parsed `/dev/msm_audio_cal` entries: `{aggregate_summary['entry_count']}`",
            f"- Existing traces contain target cal_type 10/14/24 `AUDIO_SET_CALIBRATION`: `{classification['legacy_traces_have_target_setcal']}`",
            f"- Existing traces contain target cal_type 10/14/24 allocations: `{classification['legacy_traces_have_target_allocations']}`",
            f"- Existing traces contain core topology cal_type 39 SET: `{classification['legacy_traces_have_core_topology_setcal_39']}`",
            f"- Same traces can supply byte-exact 10/14/24 SET geometry: `{classification['same_private_traces_can_supply_byte_exact_10_14_24_set']}`",
            "",
            "## Target Cal Types",
            "",
            "| cal_type | role | allocate_count | set_count | allocate_mem_handles | set_cal_sizes |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for row in aggregate_summary["target_rows"]:
        lines.append(
            f"| `{row['cal_type']}` | `{row['role']}` | `{row['allocate_count']}` | `{row['set_count']}` | `{row['allocate_mem_handles']}` | `{row['set_cal_sizes']}` |"
        )
    lines.extend(
        [
            "",
            "## Control Cal Types",
            "",
            "| cal_type | role | allocate_count | set_count | set_cal_sizes |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in aggregate_summary["control_rows"]:
        lines.append(
            f"| `{row['cal_type']}` | `{row['role']}` | `{row['allocate_count']}` | `{row['set_count']}` | `{row['set_cal_sizes']}` |"
        )
    lines.extend(
        [
            "",
            "## Full Request/Cal-Type Counts",
            "",
            "| request | cal_type | count |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in aggregate_summary["by_request_cal_type"]:
        lines.append(f"| `{row['request_name']}` | `{row['cal_type']}` | `{row['count']}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The legacy traces do show the ACDB loader allocating handles for cal_types `10`, `14`, and `24`, so the subsystem custom-topology cal types were part of initialization state.",
            "- The same traces do not contain any `AUDIO_SET_CALIBRATION` for cal_types `10`, `14`, or `24`; only cal_type `39` core custom topology appears as a large SET record, plus cal_type `20` speaker-protection headers in V2466.",
            "- Therefore V2461/V2466 cannot provide the byte-exact subsystem custom-topology SET records needed after V2708. This host-only reparse exhausts the operator-proposed legacy-trace shortcut.",
            "- Native replay remains parked until a new Android-good capture or source-backed reconstruction produces exact SET arg/payload geometry for cal_types `10`, `14`, and `24`.",
            "",
            "## Next Requirements",
            "",
        ]
    )
    for item in summary["next_requirements"]:
        lines.append(f"- {item}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-file", action="append", help="Specific private JSONL trace file to parse")
    parser.add_argument("--trace-glob", action="append", help="Glob pattern for private JSONL traces")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_summary(args)
    if args.write_report:
        write_report(summary, args.report)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
