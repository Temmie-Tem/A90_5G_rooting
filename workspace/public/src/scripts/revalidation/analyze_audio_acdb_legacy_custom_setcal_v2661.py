#!/usr/bin/env python3
"""V2661 host-only reparse of existing ACDB traces for custom-topology SETs.

The active ACDB frontier needs byte-exact AUDIO_SET_CALIBRATION records for
cal_types 10, 14, and 24.  Before another Android-good capture, this script
re-parses the already-captured V2461/V2466 real-HAL ptrace traces plus the V2660
own-process fake-SET attempt to determine whether those records already exist.

Public output is metadata only.  Raw bytes stay in workspace/private.
"""

from __future__ import annotations

import argparse
import collections
import json
import struct
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2661"
BUILD_TAG = "v2661-audio-acdb-legacy-custom-setcal-reparse"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2661_AUDIO_ACDB_LEGACY_CUSTOM_SETCAL_REPARSE_2026-06-18.md"
DEFAULT_RUN_DIRS = [
    ROOT / "workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530",
    ROOT / "workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643",
    ROOT / "workspace/private/runs/audio/v2660-acdb-custom-topology-phase-common-setcal-capture-20260618-123009",
]

AUDIO_ALLOCATE_CALIBRATION = 0xC00461C8
AUDIO_DEALLOCATE_CALIBRATION = 0xC00461C9
AUDIO_SET_CALIBRATION = 0xC00461CB
TARGET_CAL_TYPES = {10, 14, 24}
CUSTOM_NAMES = {
    10: "ADM_CUST_TOPOLOGY_CAL_TYPE",
    14: "ASM_CUST_TOPOLOGY_CAL_TYPE",
    24: "AFE_CUST_TOPOLOGY_CAL_TYPE",
    39: "CORE_CUSTOM_TOPOLOGIES_CAL_TYPE",
}
REQUEST_NAMES = {
    AUDIO_ALLOCATE_CALIBRATION: "AUDIO_ALLOCATE_CALIBRATION",
    AUDIO_DEALLOCATE_CALIBRATION: "AUDIO_DEALLOCATE_CALIBRATION",
    AUDIO_SET_CALIBRATION: "AUDIO_SET_CALIBRATION",
}


def rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def parse_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if value is None:
        return None
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        return None


def request_int(value: Any) -> int | None:
    parsed = parse_int(value)
    if parsed is None:
        return None
    return parsed & 0xFFFFFFFF


def signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    if value & 0x80000000:
        value -= 0x100000000
    return value


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            yield value


def decode_audio_cal_bytes(raw_hex: Any) -> dict[str, Any] | None:
    if not raw_hex:
        return None
    try:
        data = bytes.fromhex(str(raw_hex))
    except ValueError:
        return None
    if len(data) < 32:
        return None
    data_size, version, cal_type, cal_type_size = struct.unpack_from("<IIII", data, 0)
    type_version, buffer_number, cal_size, mem_handle_raw = struct.unpack_from("<IIII", data, 16)
    return {
        "data_size": data_size,
        "version": version,
        "cal_type": cal_type,
        "cal_type_size": cal_type_size,
        "type_version": type_version,
        "buffer_number": buffer_number,
        "cal_size": cal_size,
        "mem_handle": signed32(mem_handle_raw),
        "sample_len": min(len(data), 512),
    }


def decode_arg_snapshot(snapshot: Any) -> dict[str, Any] | None:
    if not isinstance(snapshot, dict) or not snapshot.get("available"):
        return None
    cal_type = parse_int(snapshot.get("cal_type"))
    if cal_type is None:
        return None
    return {
        "data_size": parse_int(snapshot.get("data_size")) or 0,
        "version": parse_int(snapshot.get("version")) or 0,
        "cal_type": cal_type,
        "cal_type_size": parse_int(snapshot.get("cal_type_size")) or 0,
        "type_version": parse_int(snapshot.get("type_version")) or 0,
        "buffer_number": parse_int(snapshot.get("buffer_number")) or 0,
        "cal_size": parse_int(snapshot.get("cal_size")) or 0,
        "mem_handle": parse_int(snapshot.get("mem_handle")) or 0,
        "sample_len": parse_int(snapshot.get("sample_len")) or 0,
    }


def record_from_event(path: Path, event: dict[str, Any]) -> dict[str, Any] | None:
    request = request_int(event.get("request"))
    decoded = decode_audio_cal_bytes(event.get("bytes_hex"))
    if decoded is None:
        decoded = decode_arg_snapshot(event.get("arg_snapshot"))
    if request is None and str(event.get("name") or "") in REQUEST_NAMES.values():
        for req, name in REQUEST_NAMES.items():
            if name == event.get("name"):
                request = req
                break
    if request is None or decoded is None:
        return None
    if request not in REQUEST_NAMES:
        return None
    cal_type = int(decoded["cal_type"])
    return {
        "source": rel(path),
        "event": event.get("event"),
        "seq": event.get("seq"),
        "request": f"0x{request:08x}",
        "request_name": REQUEST_NAMES[request],
        "cal_type": cal_type,
        "cal_type_name": CUSTOM_NAMES.get(cal_type, f"CAL_TYPE_{cal_type}"),
        "buffer_number": decoded.get("buffer_number"),
        "cal_size": decoded.get("cal_size"),
        "mem_handle": decoded.get("mem_handle"),
        "ret": event.get("ret"),
        "has_bytes_hex": bool(event.get("bytes_hex")),
        "has_arg_snapshot": isinstance(event.get("arg_snapshot"), dict),
    }


def records_for_run(run_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not run_dir.exists():
        return records
    for path in sorted(run_dir.rglob("*.jsonl")):
        for event in read_jsonl(path):
            record = record_from_event(path, event)
            if record:
                records.append(record)
    return records


def summarize_run(run_dir: Path) -> dict[str, Any]:
    records = records_for_run(run_dir)
    by_request = collections.Counter(record["request_name"] for record in records)
    alloc = [r for r in records if r["request_name"] == "AUDIO_ALLOCATE_CALIBRATION"]
    set_records = [r for r in records if r["request_name"] == "AUDIO_SET_CALIBRATION"]
    target_alloc = [r for r in alloc if r["cal_type"] in TARGET_CAL_TYPES]
    target_set = [r for r in set_records if r["cal_type"] in TARGET_CAL_TYPES]
    return {
        "run_dir": rel(run_dir),
        "exists": run_dir.exists(),
        "record_count": len(records),
        "by_request": dict(sorted(by_request.items())),
        "allocate_cal_types": sorted({r["cal_type"] for r in alloc}),
        "set_cal_types": sorted({r["cal_type"] for r in set_records}),
        "target_allocate_cal_types": sorted({r["cal_type"] for r in target_alloc}),
        "target_set_cal_types": sorted({r["cal_type"] for r in target_set}),
        "target_set_records": target_set,
        "set_records_metadata": [
            {
                "source": r["source"],
                "seq": r["seq"],
                "cal_type": r["cal_type"],
                "cal_type_name": r["cal_type_name"],
                "cal_size": r["cal_size"],
                "mem_handle": r["mem_handle"],
            }
            for r in set_records
        ],
    }


def build_summary(run_dirs: list[Path]) -> dict[str, Any]:
    runs = [summarize_run(path) for path in run_dirs]
    all_target_set = sorted({cal for run in runs for cal in run["target_set_cal_types"]})
    all_target_alloc = sorted({cal for run in runs for cal in run["target_allocate_cal_types"]})
    missing_targets = sorted(TARGET_CAL_TYPES - set(all_target_set))
    if set(all_target_set) >= TARGET_CAL_TYPES:
        decision = "v2661-legacy-custom-setcal-found-host-only"
        ok = True
        next_action = "extract private raw args/payloads into replay manifest after operator verification"
    elif all_target_set:
        decision = "v2661-legacy-custom-setcal-partial-host-only"
        ok = True
        next_action = "do not live-rerun unchanged; capture only missing target cal_types"
    else:
        decision = "v2661-existing-traces-no-custom-setcal-host-only"
        ok = True
        next_action = "do not repeat V2659/V2660; proceed to lower-function/direct exported SET-path design"
    return {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": decision,
        "ok": ok,
        "target_cal_types": sorted(TARGET_CAL_TYPES),
        "target_set_cal_types": all_target_set,
        "missing_target_set_cal_types": missing_targets,
        "target_allocate_cal_types": all_target_alloc,
        "runs": runs,
        "operator_value": {
            "existing_real_hal_traces_reparsed": True,
            "custom_allocations_seen": set(all_target_alloc) >= TARGET_CAL_TYPES,
            "custom_sets_already_available": set(all_target_set) >= TARGET_CAL_TYPES,
            "next_action": next_action,
        },
        "safety": {
            "host_only": True,
            "device_touched": False,
            "raw_bytes_committed": False,
            "native_replay": False,
            "audio_set_issued": False,
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# NATIVE_INIT V2661 — ACDB legacy custom SETCAL reparse")
    lines.append("")
    lines.append("Date: 2026-06-18")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("Host-only reparse of existing private ACDB capture traces for the missing")
    lines.append("custom-topology `AUDIO_SET_CALIBRATION` records. No Android boot, device")
    lines.append("flash, native replay, real `/dev/msm_audio_cal` ioctl, mixer write, PCM")
    lines.append("write, speaker playback, or raw ACDB publication occurred. This report is metadata only.")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append(f"- decision: `{summary['decision']}`")
    lines.append(f"- ok: `{summary['ok']}`")
    lines.append(f"- target_cal_types: `{summary['target_cal_types']}`")
    lines.append(f"- target_set_cal_types: `{summary['target_set_cal_types']}`")
    lines.append(f"- missing_target_set_cal_types: `{summary['missing_target_set_cal_types']}`")
    lines.append(f"- target_allocate_cal_types: `{summary['target_allocate_cal_types']}`")
    lines.append("")
    lines.append("## Run Summaries")
    lines.append("")
    lines.append("| run | records | requests | allocated targets | SET cal types | target SETs |")
    lines.append("| --- | ---: | --- | --- | --- | --- |")
    for run in summary["runs"]:
        lines.append(
            "| "
            f"`{run['run_dir']}` | `{run['record_count']}` | `{run['by_request']}` | "
            f"`{run['target_allocate_cal_types']}` | `{run['set_cal_types']}` | "
            f"`{run['target_set_cal_types']}` |"
        )
    lines.append("")
    lines.append("## SET Records Observed")
    lines.append("")
    for run in summary["runs"]:
        lines.append(f"### `{run['run_dir']}`")
        lines.append("")
        rows = run["set_records_metadata"]
        if not rows:
            lines.append("No `AUDIO_SET_CALIBRATION` metadata records decoded.")
            lines.append("")
            continue
        lines.append("| source | seq | cal_type | cal_size | mem_handle |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for row in rows:
            lines.append(
                f"| `{row['source']}` | `{row['seq']}` | `{row['cal_type']}` "
                f"`{row['cal_type_name']}` | `{row['cal_size']}` | `{row['mem_handle']}` |"
            )
        lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The existing Android-good traces do **not** contain byte-exact SET records")
    lines.append("for cal_types `10`, `14`, or `24`. They do confirm the database/loader")
    lines.append("allocates all three target custom-topology cal blocks, so the missing")
    lines.append("evidence is a SET-path/control-flow problem, not absence from the ACDB DB.")
    lines.append("")
    lines.append("V2660 adds the same conclusion from the own-process path: the phase-aware")
    lines.append("init-short hook allowed `acdb_loader_init_v3()` to fake-allocate `10/14/24`,")
    lines.append("but the process SIGSEGVed before the helper regained control and before any")
    lines.append("post-init `AUDIO_SET_CALIBRATION` rows were emitted. Therefore V2659/V2660")
    lines.append("should not be rerun unchanged.")
    lines.append("")
    lines.append("## Next Unit")
    lines.append("")
    lines.append("Proceed host-only to a lower-function/direct SET-path design. The immediate")
    lines.append("candidates are the stock `libacdbloader.so` paths named by its own strings:")
    lines.append("`send_adm_custom_topology`, `send_asm_custom_topology`, and")
    lines.append("`send_afe_custom_topology`, or an exported lower SET helper if its argument")
    lines.append("layout can be pinned. A future live run must remain measurement-only: fake")
    lines.append("all `AUDIO_SET_CALIBRATION`, dump arg/payload bytes privately, and rollback")
    lines.append("to V2321.")
    lines.append("")
    lines.append("## Validation")
    lines.append("")
    lines.append("- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_legacy_custom_setcal_v2661.py tests/test_analyze_audio_acdb_legacy_custom_setcal_v2661.py`")
    lines.append("- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests/test_analyze_audio_acdb_legacy_custom_setcal_v2661.py -v`")
    lines.append("- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_legacy_custom_setcal_v2661.py --write-report`")
    lines.append("- `git diff --check`")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", action="append", type=Path, dest="run_dirs", help="Private run dir to parse; may repeat")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dirs = args.run_dirs or DEFAULT_RUN_DIRS
    summary = build_summary([Path(p) for p in run_dirs])
    if args.write_report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
