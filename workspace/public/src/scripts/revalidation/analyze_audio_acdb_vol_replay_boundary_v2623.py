#!/usr/bin/env python3
"""V2623 host-only ACDB VOL/replay-boundary reconciliation.

Reads private ACDB capture metadata from V2461/V2612/V2618/V2621/V2622 and
emits a public-safe report.  It does not run a device, does not copy raw ACDB
bytes into tracked paths, and does not mark native replay ready.
"""

from __future__ import annotations

import argparse
import collections
import json
import struct
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2623"
BUILD_TAG = "v2623-audio-acdb-vol-replay-boundary"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2623_AUDIO_ACDB_VOL_REPLAY_BOUNDARY_2026-06-16.md"
DEFAULT_V2461_DIR = ROOT / "workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530"
DEFAULT_V2612_RESULT = ROOT / "workspace/private/runs/audio/v2612-acdb-meta-list-postinit-send-v5-live-20260616-190143/result.json"
DEFAULT_V2618_RESULT = ROOT / "workspace/private/runs/audio/v2618-acdb-direct-matrix-20260616-203644/result.json"
DEFAULT_V2621_RESULT = ROOT / "workspace/private/runs/audio/v2621-acdb-vol-isolated-20260616-211611/result.json"
DEFAULT_V2622_MANIFEST = ROOT / "workspace/private/runs/audio/v2621-acdb-vol-isolated-20260616-211611/v2622-acdb-gate2-vol-status-manifest.json"

REQ_NAMES = {
    "0xc00461c8": "AUDIO_ALLOCATE_CALIBRATION",
    "0xc00461c9": "AUDIO_DEALLOCATE_CALIBRATION",
    "0xc00461cb": "AUDIO_SET_CALIBRATION",
}

CAL_NAMES = {
    10: "ADM_CUST_TOPOLOGY_CAL_TYPE",
    11: "ADM_AUDPROC_CAL_TYPE",
    12: "ADM_AUDVOL_CAL_TYPE",
    14: "ASM_CUST_TOPOLOGY_CAL_TYPE",
    15: "ASM_AUDSTRM_CAL_TYPE",
    16: "AFE_COMMON_RX_CAL_TYPE",
    17: "AFE_COMMON_TX_CAL_TYPE",
    24: "AFE_CUST_TOPOLOGY_CAL_TYPE",
    39: "CORE_CUSTOM_TOPOLOGIES_CAL_TYPE",
    40: "ADM_RTAC_AUDVOL_CAL_TYPE",
}

VOL_CMDS = {"0x0001326d", "0x0001326e"}
SUCCESS_RET = {0, "0", "0x00000000"}
NEG19_RET = {-19, "-19", "0xffffffed", "0xFFFFFFED"}


def rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def parse_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if value is None:
        return None
    try:
        return int(str(value), 0)
    except ValueError:
        return None


def hex32(value: int | None) -> str | None:
    if value is None:
        return None
    return f"0x{value & 0xffffffff:08x}"


def normalize_cmd(value: Any) -> str:
    parsed = parse_int(value)
    return hex32(parsed) if parsed is not None else str(value or "")


def signed_ret(value: Any) -> int | None:
    parsed = parse_int(value)
    if parsed is None:
        return None
    parsed &= 0xffffffff
    if parsed & 0x80000000:
        parsed -= 0x100000000
    return parsed


def decode_audio_cal_entry(event: dict[str, Any]) -> dict[str, Any] | None:
    raw_hex = event.get("bytes_hex")
    if not raw_hex:
        return None
    try:
        data = bytes.fromhex(str(raw_hex))
    except ValueError:
        return None
    if len(data) < 32:
        return None
    data_size, version, cal_type, cal_type_size = struct.unpack_from("<iiii", data, 0)
    type_version, buffer_number, cal_size, mem_handle = struct.unpack_from("<iiii", data, 16)
    info: dict[str, int] = {}
    if len(data) >= 48:
        words = struct.unpack_from("<iiii", data, 32)
        if cal_type == 11:
            info = {"acdb_id": words[0], "path": words[1], "app_type": words[2], "sample_rate": words[3]}
        elif cal_type == 12:
            info = {"acdb_id": words[0], "path": words[1], "app_type": words[2], "vol_index": words[3]}
        elif cal_type == 16:
            info = {"acdb_id": words[0], "path": words[1], "sample_rate": words[2]}
        elif cal_type == 15:
            info = {"app_type": words[0]}
        else:
            info = {"word0": words[0], "word1": words[1], "word2": words[2], "word3": words[3]}
    request = normalize_cmd(event.get("request"))
    return {
        "seq": event.get("seq"),
        "request": request,
        "request_name": REQ_NAMES.get(request, request),
        "data_size": data_size,
        "version": version,
        "cal_type": cal_type,
        "cal_type_name": CAL_NAMES.get(cal_type, f"CAL_TYPE_{cal_type}"),
        "cal_type_size": cal_type_size,
        "type_version": type_version,
        "buffer_number": buffer_number,
        "cal_size": cal_size,
        "mem_handle": mem_handle,
        "info": info,
    }


def v2461_msm_audio_cal_summary(v2461_dir: Path) -> dict[str, Any]:
    artifact_dir = v2461_dir / "device-artifacts"
    entries: list[dict[str, Any]] = []
    for path in sorted(artifact_dir.glob("*.jsonl")):
        for event in read_jsonl(path):
            if event.get("event") != "ioctl_entry":
                continue
            if event.get("fd_target") != "/dev/msm_audio_cal":
                continue
            decoded = decode_audio_cal_entry(event)
            if decoded:
                entries.append(decoded)
    by_request: dict[str, int] = dict(collections.Counter(item["request"] for item in entries))
    by_cal_type: dict[str, int] = dict(collections.Counter(str(item["cal_type"]) for item in entries))
    set_entries = [item for item in entries if item["request"] == "0xc00461cb"]
    alloc_entries = [item for item in entries if item["request"] == "0xc00461c8"]
    dealloc_entries = [item for item in entries if item["request"] == "0xc00461c9"]
    allocated_required = sorted({item["cal_type"] for item in alloc_entries if item["cal_type"] in {11, 12, 15, 16, 39}})
    return {
        "source_dir": rel(v2461_dir),
        "entry_count": len(entries),
        "by_request": by_request,
        "by_cal_type": by_cal_type,
        "set_count": len(set_entries),
        "set_cal_types": sorted({item["cal_type"] for item in set_entries}),
        "set_entries": set_entries,
        "allocate_count": len(alloc_entries),
        "deallocate_count": len(dealloc_entries),
        "allocated_required_cal_types": allocated_required,
        "allocated_vol_buffers": [item for item in alloc_entries if item["cal_type"] == 12],
        "android_set_payload_stream_has_vol": any(item["cal_type"] == 12 for item in set_entries),
        "android_set_payload_stream_has_audproc_or_afe": any(item["cal_type"] in {11, 16} for item in set_entries),
    }


def ownget_rows(result_path: Path) -> list[dict[str, Any]]:
    data = read_json(result_path)
    summary = data.get("ownget_summary", {})
    rows = summary.get("acdbtap_rows", [])
    return rows if isinstance(rows, list) else []


def successful_nonzero_payloads(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for row in rows:
        ret = signed_ret(row.get("ret"))
        out_len = parse_int(row.get("out_len"))
        buffer_name = str(row.get("buffer") or "")
        if ret != 0 or row.get("all_zero") is not False or out_len is None or out_len <= 4:
            continue
        if not buffer_name.startswith("ind-"):
            continue
        payloads.append({
            "seq": row.get("seq"),
            "cmd": normalize_cmd(row.get("cmd")),
            "buffer": buffer_name,
            "out_len": out_len,
            "sha256": row.get("sha256"),
        })
    return payloads


def vol_ret_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    vol_out_rows = [row for row in rows if normalize_cmd(row.get("cmd")) in VOL_CMDS and str(row.get("buffer") or "") == "out"]
    rets = sorted({signed_ret(row.get("ret")) for row in vol_out_rows})
    nonzero_payload_rows = [
        row for row in rows
        if normalize_cmd(row.get("cmd")) in VOL_CMDS
        and str(row.get("buffer") or "").startswith("ind-")
        and signed_ret(row.get("ret")) == 0
        and row.get("all_zero") is False
    ]
    return {
        "vol_out_row_count": len(vol_out_rows),
        "vol_ret_values": rets,
        "vol_ret_all_negative_19": bool(vol_out_rows) and rets == [-19],
        "vol_nonzero_payload_count": len(nonzero_payload_rows),
    }


def v2622_status(path: Path) -> dict[str, Any]:
    data = read_json(path)
    summary = data.get("summary", {})
    return {
        "source": rel(path),
        "ok": data.get("ok"),
        "native_replay_ready": data.get("native_replay_ready"),
        "payload_candidate_count": summary.get("payload_candidate_count"),
        "payload_verified_count": summary.get("payload_verified_count"),
        "audproc_candidate_count": summary.get("audproc_candidate_count"),
        "afe_candidate_count": summary.get("afe_candidate_count"),
        "vol_candidate_count": summary.get("vol_candidate_count"),
        "vol_direct_get_exhausted_for_current_tuple": summary.get("vol_direct_get_exhausted_for_current_tuple"),
        "vol_status_ret_values": summary.get("vol_status_ret_values"),
        "payload_candidates_redacted": data.get("payload_candidates_redacted", []),
        "replay_blockers": data.get("replay_blockers", []),
    }


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    v2461 = v2461_msm_audio_cal_summary(args.v2461_dir)
    v2612_rows = ownget_rows(args.v2612_result)
    v2618_rows = ownget_rows(args.v2618_result)
    v2621_rows = ownget_rows(args.v2621_result)
    v2622 = v2622_status(args.v2622_manifest)
    v2612_vol = vol_ret_summary(v2612_rows)
    v2618_vol = vol_ret_summary(v2618_rows)
    v2621_vol = vol_ret_summary(v2621_rows)
    payloads_v2618 = successful_nonzero_payloads(v2618_rows)
    conclusion = {
        "android_good_set_stream_vol_payload_absent_in_v2461": not v2461["android_set_payload_stream_has_vol"],
        "direct_get_vol_exhausted_in_v2621": bool(v2622["vol_direct_get_exhausted_for_current_tuple"]),
        "audproc_afe_candidates_present": v2622["payload_candidate_count"] == 3 and v2622["payload_verified_count"] == 3,
        "safe_to_run_native_replay_without_operator_gate2": False,
        "recommended_next_gate": "operator-gate2-decision-on-vol-negative-manifest",
    }
    ok = bool(
        conclusion["android_good_set_stream_vol_payload_absent_in_v2461"]
        and conclusion["direct_get_vol_exhausted_in_v2621"]
        and conclusion["audproc_afe_candidates_present"]
    )
    return {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "host_only": True,
        "device_action": "none",
        "ok": ok,
        "decision": "v2623-vol-negative-boundary-pinned" if ok else "v2623-vol-boundary-needs-review",
        "native_replay_ready": False,
        "v2461_msm_audio_cal": v2461,
        "ownprocess_get_summary": {
            "v2612_vol": v2612_vol,
            "v2618_vol": v2618_vol,
            "v2621_vol": v2621_vol,
            "v2618_successful_nonzero_payloads": payloads_v2618,
        },
        "v2622_gate2_status": v2622,
        "conclusion": conclusion,
        "boundary": [
            "V2623 does not run native replay or issue calibration ioctls.",
            "V2461 shows Android-good SET payload capture for topology cal_type 39 only; VOL cal_type 12 was allocated but not SET in that captured payload stream.",
            "V2621 shows current-tuple direct VOL GET returned -19 for all 16 gain steps.",
            "Native replay remains blocked until operator Gate-2 accepts the VOL-negative manifest or supplies a different VOL route.",
        ],
    }


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    v2461 = manifest["v2461_msm_audio_cal"]
    own = manifest["ownprocess_get_summary"]
    gate2 = manifest["v2622_gate2_status"]
    lines = [
        "# NATIVE_INIT V2623 — ACDB VOL replay-boundary reconciliation",
        "",
        "Date: 2026-06-16",
        "",
        "## Scope",
        "",
        "Host-only reconciliation of the VOL/per-device replay boundary after V2622.",
        "This reads private metadata from V2461, V2612, V2618, V2621, and V2622,",
        "but emits only public-safe counts, command IDs, lengths, and SHA-256 values.",
        "No device action, raw payload copy, native replay, speaker write, or calibration ioctl runs here.",
        "",
        "## Result",
        "",
        f"- decision: `{manifest.get('decision')}`",
        f"- ok: `{manifest.get('ok')}`",
        f"- native_replay_ready: `{manifest.get('native_replay_ready')}`",
        f"- recommended_next_gate: `{manifest['conclusion']['recommended_next_gate']}`",
        f"- safe_to_run_native_replay_without_operator_gate2: `{manifest['conclusion']['safe_to_run_native_replay_without_operator_gate2']}`",
        "",
        "## Android-good `/dev/msm_audio_cal` stream cross-check (V2461)",
        "",
        f"- source_dir: `{v2461['source_dir']}`",
        f"- decoded_ioctl_entries: `{v2461['entry_count']}`",
        f"- by_request: `{v2461['by_request']}`",
        f"- allocate_count: `{v2461['allocate_count']}`",
        f"- deallocate_count: `{v2461['deallocate_count']}`",
        f"- set_count: `{v2461['set_count']}`",
        f"- set_cal_types: `{v2461['set_cal_types']}`",
        f"- allocated_required_cal_types: `{v2461['allocated_required_cal_types']}`",
        f"- android_set_payload_stream_has_vol: `{v2461['android_set_payload_stream_has_vol']}`",
        f"- android_set_payload_stream_has_audproc_or_afe: `{v2461['android_set_payload_stream_has_audproc_or_afe']}`",
        "",
        "| seq | request | cal_type | name | buffer | cal_size | mem_handle |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for item in v2461["set_entries"]:
        lines.append(
            f"| {item.get('seq')} | `{item.get('request_name')}` | {item.get('cal_type')} | "
            f"`{item.get('cal_type_name')}` | {item.get('buffer_number')} | {item.get('cal_size')} | "
            f"{item.get('mem_handle')} |"
        )
    lines.extend([
        "",
        "## Own-process GET cross-check",
        "",
        "| run | VOL out rows | VOL ret values | VOL payloads | note |",
        "| --- | ---: | --- | ---: | --- |",
        f"| V2612 send_audio_cal_v5 | {own['v2612_vol']['vol_out_row_count']} | `{own['v2612_vol']['vol_ret_values']}` | {own['v2612_vol']['vol_nonzero_payload_count']} | first post-init send path; gain step 0 returned -19 |",
        f"| V2618 direct matrix | {own['v2618_vol']['vol_out_row_count']} | `{own['v2618_vol']['vol_ret_values']}` | {own['v2618_vol']['vol_nonzero_payload_count']} | captured AUDPROC/AFE candidates, no VOL candidate |",
        f"| V2621 VOL-isolated sweep | {own['v2621_vol']['vol_out_row_count']} | `{own['v2621_vol']['vol_ret_values']}` | {own['v2621_vol']['vol_nonzero_payload_count']} | 16 gain steps, size+data, all -19 |",
        "",
        "## Current Gate-2 candidate set",
        "",
        f"- source: `{gate2['source']}`",
        f"- ok: `{gate2['ok']}`",
        f"- payload_candidate_count: `{gate2['payload_candidate_count']}`",
        f"- payload_verified_count: `{gate2['payload_verified_count']}`",
        f"- audproc_candidate_count: `{gate2['audproc_candidate_count']}`",
        f"- afe_candidate_count: `{gate2['afe_candidate_count']}`",
        f"- vol_candidate_count: `{gate2['vol_candidate_count']}`",
        f"- vol_direct_get_exhausted_for_current_tuple: `{gate2['vol_direct_get_exhausted_for_current_tuple']}`",
        "",
        "| category | cmd | buffer | bytes | sha256 |",
        "| --- | --- | --- | ---: | --- |",
    ])
    for item in gate2["payload_candidates_redacted"]:
        lines.append(
            f"| `{item.get('category')}` | `{item.get('cmd')}` | `{item.get('buffer')}` | "
            f"{item.get('out_len')} | `{item.get('sha256')}` |"
        )
    lines.extend([
        "",
        "## Conclusion",
        "",
        "- V2461 proves the captured Android-good `/dev/msm_audio_cal` SET payload stream contains the custom topology SET only (`cal_type=39`), while VOL (`cal_type=12`) appears only as allocation metadata in that stream.",
        "- V2612 and V2621 independently show the current speaker tuple's VOL GET path returning `-19`; V2621 extends this through all 16 gain steps.",
        "- The current replay candidate remains topology plus the three verified AUDPROC/AFE candidates. This may be enough to test the V2393 `pcm_prepare` blockers, but it is not authorized by this unit.",
        "- Native replay remains blocked until operator Gate-2 explicitly accepts the VOL-negative manifest or provides a new VOL route.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_vol_replay_boundary_v2623.py tests/test_analyze_audio_acdb_vol_replay_boundary_v2623.py`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_vol_replay_boundary_v2623 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_vol_replay_boundary_v2623.py --write-report`",
        "- `git diff --check`",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2461-dir", type=Path, default=DEFAULT_V2461_DIR)
    parser.add_argument("--v2612-result", type=Path, default=DEFAULT_V2612_RESULT)
    parser.add_argument("--v2618-result", type=Path, default=DEFAULT_V2618_RESULT)
    parser.add_argument("--v2621-result", type=Path, default=DEFAULT_V2621_RESULT)
    parser.add_argument("--v2622-manifest", type=Path, default=DEFAULT_V2622_MANIFEST)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_manifest(args)
    if args.write_report:
        write_report(args.report_path, manifest)
    print(json.dumps({
        "decision": manifest["decision"],
        "ok": manifest["ok"],
        "native_replay_ready": manifest["native_replay_ready"],
        "v2461_set_cal_types": manifest["v2461_msm_audio_cal"]["set_cal_types"],
        "v2621_vol_ret_values": manifest["ownprocess_get_summary"]["v2621_vol"]["vol_ret_values"],
        "gate2_payload_candidate_count": manifest["v2622_gate2_status"]["payload_candidate_count"],
    }, indent=2, sort_keys=True))
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
