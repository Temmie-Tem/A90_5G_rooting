#!/usr/bin/env python3
"""V2616 host-only ACDB request-geometry analyzer.

Consumes the private V2614 ACDB tap run and decodes only metadata-sized
acdb_ioctl input/output words.  It does not copy public raw ACDB payload bytes,
does not touch a device, and does not authorize native replay.
"""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2616"
BUILD_TAG = "v2616-audio-acdb-request-geometry"
RUNS_ROOT = ROOT / "workspace/private/runs/audio"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2616_AUDIO_ACDB_REQUEST_GEOMETRY_2026-06-16.md"
DEFAULT_JSON = ROOT / "workspace/private/runs/audio/v2616-acdb-request-geometry/request-geometry.json"


@dataclass(frozen=True)
class CommandInfo:
    cmd: str
    name: str
    role: str
    fields: tuple[str, ...]
    candidate_cal_type: int | None
    note: str


COMMANDS: dict[str, CommandInfo] = {
    "0x0001122e": CommandInfo(
        cmd="0x0001122e",
        name="send_audio_cal_v5 first app metadata",
        role="metadata",
        fields=("app_id",),
        candidate_cal_type=None,
        note="V2597 proved this direct metadata row returns 0x10005000 for app_id 0x11135.",
    ),
    "0x0001122d": CommandInfo(
        cmd="0x0001122d",
        name="device/app metadata",
        role="metadata",
        fields=("acdb_id", "app_id"),
        candidate_cal_type=None,
        note="Consumed before AUDPROC common dispatch.",
    ),
    "0x00013267": CommandInfo(
        cmd="0x00013267",
        name="AUDPROC instance common size",
        role="size-query",
        fields=("acdb_id", "sample_rate", "app_id"),
        candidate_cal_type=11,
        note="Paired with 0x13265; Android-good logs map this branch to AUDIO_SET_AUDPROC_CAL.",
    ),
    "0x00013265": CommandInfo(
        cmd="0x00013265",
        name="AUDPROC instance common data",
        role="indirect-data",
        fields=("acdb_id", "sample_rate", "app_id", "capacity", "out_ptr"),
        candidate_cal_type=11,
        note="V2614 captured the indirect payload as ind-ap-common.",
    ),
    "0x0001326d": CommandInfo(
        cmd="0x0001326d",
        name="AUDPROC gain-dependent step size",
        role="size-query",
        fields=("acdb_id", "app_id", "gain_step"),
        candidate_cal_type=12,
        note="V2614 returned -19 for the observed speaker/app/gain_step tuple.",
    ),
    "0x0001326e": CommandInfo(
        cmd="0x0001326e",
        name="AUDPROC gain-dependent step data",
        role="indirect-data",
        fields=("acdb_id", "app_id", "gain_step", "capacity", "out_ptr"),
        candidate_cal_type=12,
        note="No valid VOL payload was captured because the size/data row returned -19.",
    ),
    "0x00013268": CommandInfo(
        cmd="0x00013268",
        name="AUDPROC stream size",
        role="size-query",
        fields=("app_id",),
        candidate_cal_type=15,
        note="Paired with 0x13269; V2393 showed q6asm stream cal missing at pcm_prepare.",
    ),
    "0x00013269": CommandInfo(
        cmd="0x00013269",
        name="AUDPROC stream data",
        role="indirect-data",
        fields=("app_id", "capacity", "out_ptr"),
        candidate_cal_type=15,
        note="V2614 captured the indirect payload as ind-ap-stream.",
    ),
    "0x000130d8": CommandInfo(
        cmd="0x000130d8",
        name="AFE metadata",
        role="metadata",
        fields=("acdb_id",),
        candidate_cal_type=None,
        note="Returned 0x1001025d before the AFE common table query.",
    ),
    "0x00013271": CommandInfo(
        cmd="0x00013271",
        name="AFE instance common size",
        role="size-query",
        fields=("acdb_id", "sample_rate"),
        candidate_cal_type=16,
        note="Paired with 0x1326f; Android-good logs map this branch to AUDIO_SET_AFE_CAL.",
    ),
    "0x0001326f": CommandInfo(
        cmd="0x0001326f",
        name="AFE instance common data",
        role="indirect-data",
        fields=("acdb_id", "sample_rate", "capacity", "out_ptr"),
        candidate_cal_type=16,
        note="V2614 captured the indirect payload as ind-afe-common.",
    ),
    "0x00012eeb": CommandInfo(
        cmd="0x00012eeb",
        name="tail metadata row",
        role="metadata",
        fields=("acdb_id", "path", "word2", "word3"),
        candidate_cal_type=None,
        note="Observed after AFE common; command semantics remain unassigned.",
    ),
}

EXPECTED_ORDER = (
    "0x0001122e",
    "0x0001122d",
    "0x00013267",
    "0x00013265",
    "0x0001326d",
    "0x0001326e",
    "0x00013268",
    "0x00013269",
    "0x000130d8",
    "0x00013271",
    "0x0001326f",
    "0x00012eeb",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path | str) -> str:
    target = Path(path)
    try:
        return str(target.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def latest_v2614_run(runs_root: Path = RUNS_ROOT) -> Path | None:
    candidates = sorted(runs_root.glob("v2614-acdb-meta-list-indirect-layout-live-*"))
    return candidates[-1] if candidates else None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            return None
    return None


def signed32(value: int | None) -> int | None:
    if value is None:
        return None
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def words_from_file(path: Path) -> list[int]:
    data = path.read_bytes()
    return [struct.unpack_from("<I", data, offset)[0] for offset in range(0, len(data) - (len(data) % 4), 4)]


def raw_path_for_row(run_dir: Path, row: dict[str, Any]) -> Path:
    return run_dir / "ownget-device-artifacts" / "acdbtap" / Path(str(row.get("raw_path") or "")).name


def row_key(row: dict[str, Any]) -> tuple[int, str]:
    return (parse_int(row.get("seq")) or 0, str(row.get("buffer") or ""))


def format_word(value: int | None) -> str | None:
    if value is None:
        return None
    return f"0x{value & 0xFFFFFFFF:08x}"


def annotate_fields(info: CommandInfo, words: list[int]) -> dict[str, str]:
    return {field: format_word(words[index]) or "" for index, field in enumerate(info.fields) if index < len(words)}


def analyze_run(run_dir: Path) -> dict[str, Any]:
    result_path = run_dir / "result.json"
    if not result_path.exists():
        return {
            "run_id": RUN_ID,
            "build_tag": BUILD_TAG,
            "created_at": now_iso(),
            "ok": False,
            "decision": "v2616-blocked-missing-v2614-result",
            "run_dir": rel(run_dir),
        }

    result = load_json(result_path)
    summary = result.get("ownget_summary", {}) if isinstance(result.get("ownget_summary"), dict) else {}
    rows = summary.get("acdbtap_rows", []) if isinstance(summary.get("acdbtap_rows"), list) else []
    by_seq_cmd: dict[tuple[int, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        seq = parse_int(row.get("seq"))
        cmd = str(row.get("cmd") or "")
        if seq is None or not cmd:
            continue
        entry = by_seq_cmd.setdefault((seq, cmd), {"seq": seq, "cmd": cmd, "rows": []})
        entry["rows"].append(row)

    calls: list[dict[str, Any]] = []
    for key in sorted(by_seq_cmd):
        entry = by_seq_cmd[key]
        cmd = str(entry["cmd"])
        info = COMMANDS.get(cmd)
        input_row = next((row for row in entry["rows"] if row.get("buffer") == "in"), None)
        output_row = next((row for row in entry["rows"] if row.get("buffer") == "out"), None)
        indirect_rows = [row for row in entry["rows"] if str(row.get("buffer", "")).startswith("ind-")]
        input_words: list[int] = []
        output_words: list[int] = []
        if input_row is not None:
            path = raw_path_for_row(run_dir, input_row)
            if path.exists():
                input_words = words_from_file(path)
        if output_row is not None:
            path = raw_path_for_row(run_dir, output_row)
            if path.exists():
                output_words = words_from_file(path)
        ret = parse_int(output_row.get("ret") if output_row else (input_row or {}).get("ret"))
        call = {
            "seq": f"0x{int(entry['seq']):08x}",
            "cmd": cmd,
            "name": info.name if info else "unknown",
            "role": info.role if info else "unknown",
            "candidate_cal_type": info.candidate_cal_type if info else None,
            "note": info.note if info else "command is not classified in V2616",
            "ret": format_word(ret),
            "ret_signed": signed32(ret),
            "input_words": [format_word(word) for word in input_words],
            "output_words": [format_word(word) for word in output_words],
            "fields": annotate_fields(info, input_words) if info else {},
            "output_word0": format_word(output_words[0]) if output_words else None,
            "indirect_payloads": [
                {
                    "buffer": row.get("buffer"),
                    "out_len": row.get("out_len"),
                    "sha256": row.get("sha256"),
                    "all_zero": row.get("all_zero"),
                    "private_only": True,
                }
                for row in indirect_rows
            ],
            "ok_ret0": ret == 0,
        }
        calls.append(call)

    commands_seen = [call["cmd"] for call in calls]
    missing = [cmd for cmd in EXPECTED_ORDER if cmd not in commands_seen]
    successful_indirect = [
        call
        for call in calls
        if call["role"] == "indirect-data" and call["ok_ret0"] and call["indirect_payloads"]
    ]
    failed_indirect = [
        call
        for call in calls
        if call["role"] == "indirect-data" and not call["ok_ret0"]
    ]
    vol_size = next((call for call in calls if call["cmd"] == "0x0001326d"), None)
    vol_data = next((call for call in calls if call["cmd"] == "0x0001326e"), None)
    checks = {
        "source_run_ok": result.get("ok") is True,
        "rolled_back": result.get("rolled_back") is True,
        "complete_expected_order": not missing,
        "audproc_common_payload_captured": any(call["cmd"] == "0x00013265" for call in successful_indirect),
        "audproc_stream_payload_captured": any(call["cmd"] == "0x00013269" for call in successful_indirect),
        "afe_common_payload_captured": any(call["cmd"] == "0x0001326f" for call in successful_indirect),
        "vol_size_ret_minus_19": bool(vol_size and vol_size["ret_signed"] == -19),
        "vol_data_ret_minus_19": bool(vol_data and vol_data["ret_signed"] == -19),
    }
    return {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": now_iso(),
        "ok": all(checks.values()),
        "decision": "v2616-request-geometry-pinned" if all(checks.values()) else "v2616-request-geometry-incomplete",
        "host_only": True,
        "device_action": "none",
        "source_run": rel(run_dir),
        "source_decision": result.get("decision"),
        "checks": checks,
        "missing_expected_commands": missing,
        "calls": calls,
        "successful_indirect_commands": [call["cmd"] for call in successful_indirect],
        "failed_indirect_commands": [call["cmd"] for call in failed_indirect],
        "native_replay_ready": False,
        "native_replay_blocked_reason": "operator Gate-2 mapping plus missing VOL/Afe topology decision are unresolved",
        "next_recommended_unit": (
            "V2617 host-only design/build for a bounded lower-getter or send_v5 matrix focused on "
            "VOL cal_type 12 and AFE cal_type 8/9 coverage; do not run native SET replay yet"
        ),
        "operator_questions": [
            "Is VOL cal_type 12 mandatory when 0x1326d/0x1326e return -19 for speaker app_type 0x11135 gain_step 0?",
            "Does the captured topology plus AFE common table cover the V2393 cal_type 8/9 topology-id errors, or is a separate table required?",
            "Can the V2614 command order be mapped directly to the V2461/V2462 SET sequence before constructing a live replay manifest?",
        ],
    }


def report_lines(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# NATIVE_INIT V2616 — ACDB request geometry",
        "",
        "Date: 2026-06-16",
        "",
        "## Scope",
        "",
        "Host-only analysis of the V2614 private `acdbtap` run. This decodes metadata-sized",
        "input/output words from ACDB GET calls so the next capture/replay design can use exact",
        "request geometry. It does not touch the device, issue calibration `SET`, copy raw payload",
        "bytes into public files, or mark native replay ready.",
        "",
        "## Decision",
        "",
        f"- decision: `{payload.get('decision')}`",
        f"- ok: `{payload.get('ok')}`",
        f"- source_run: `{payload.get('source_run')}`",
        f"- source_decision: `{payload.get('source_decision')}`",
        f"- native_replay_ready: `{payload.get('native_replay_ready')}`",
        f"- native_replay_blocked_reason: `{payload.get('native_replay_blocked_reason')}`",
        "",
        "## Ordered ACDB GET Geometry",
        "",
        "| seq | cmd | role | ret | input words | output word0 | candidate cal_type | note |",
        "| --- | --- | --- | ---: | --- | --- | ---: | --- |",
    ]
    for call in payload.get("calls", []):
        words = ", ".join(str(word) for word in call.get("input_words", []))
        candidate = call.get("candidate_cal_type")
        lines.append(
            f"| `{call.get('seq')}` | `{call.get('cmd')}` | {call.get('role')} | "
            f"`{call.get('ret_signed')}` | `{words}` | `{call.get('output_word0')}` | "
            f"{'' if candidate is None else candidate} | {call.get('name')} |"
        )
    lines.extend(
        [
            "",
            "## Pinned Request Fields",
            "",
        ]
    )
    for call in payload.get("calls", []):
        fields = call.get("fields", {})
        if not fields:
            continue
        field_text = ", ".join(f"{key}={value}" for key, value in fields.items())
        lines.append(f"- `{call.get('cmd')}` {call.get('name')}: {field_text}")
    lines.extend(
        [
            "",
            "## Capture Interpretation",
            "",
            "- AUDPROC common (`0x13265`) captured a valid non-zero indirect payload for candidate cal_type 11.",
            "- AUDPROC stream (`0x13269`) captured a valid non-zero indirect payload for candidate stream/ASM cal.",
            "- AFE common (`0x1326f`) captured a valid non-zero indirect payload for candidate cal_type 16.",
            "- VOL/gain (`0x1326d`/`0x1326e`) returned `-19` for `acdb_id=15`, `app_id=0x11135`, `gain_step=0`; no VOL payload exists in V2614.",
            "- `0x130d8` returned AFE metadata `0x1001025d`; its relation to the V2393 cal_type 8/9 topology errors remains an operator Gate-2 question.",
            "",
            "## Checks",
            "",
        ]
    )
    checks = payload.get("checks", {}) if isinstance(payload.get("checks"), dict) else {}
    for key, value in checks.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Next Boundary",
            "",
            f"- next_recommended_unit: {payload.get('next_recommended_unit')}",
            "- Native replay remains blocked. This report supplies request geometry and operator questions only.",
            "",
            "## Operator Questions",
            "",
        ]
    )
    for question in payload.get("operator_questions", []):
        lines.append(f"- {question}")
    lines.extend(
        [
            "",
            "## Validation Commands",
            "",
            "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_request_geometry_v2616.py tests/test_analyze_audio_acdb_request_geometry_v2616.py`",
            "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_request_geometry_v2616 -v`",
            "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_request_geometry_v2616.py --write-report`",
            "- `git diff --check`",
            "",
        ]
    )
    return lines


def write_report(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(report_lines(payload)), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, help="private V2614 run directory; defaults to latest")
    parser.add_argument("--json-path", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir or latest_v2614_run()
    if run_dir is None:
        payload = {
            "run_id": RUN_ID,
            "build_tag": BUILD_TAG,
            "created_at": now_iso(),
            "ok": False,
            "decision": "v2616-blocked-no-v2614-run",
        }
    else:
        payload = analyze_run(run_dir)
    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.write_report:
        write_report(payload, args.report_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
