#!/usr/bin/env python3
"""V2558 host-only reconciliation of ACDB capture and replay readiness.

This script consumes private V2557/V2552/V2548 evidence and emits a public-safe
manifest.  It never emits raw ACDB bytes and never touches a device.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2558"
BUILD_TAG = "v2558-audio-acdb-replay-manifest-reconciliation"
EXPECTED_TOPOLOGY_LEN = 4916
EXPECTED_TOPOLOGY_SHA256 = "7c5d45efa40944bc23dcc83af9f0046249499bb13d1a03c3470c287127992b89"
ZERO_4916_SHA256 = "9af4895ee511379e7a2d0620ea158c535f88c853de6df2eb2cd32f0cb4a2cb8c"
DEFAULT_V2557_RESULT = (
    ROOT
    / "workspace/private/runs/audio/v2555-acdb-full-manifest-20260616-100802/v2555-result.json"
)
DEFAULT_STABLE_PAYLOAD = ROOT / "workspace/private/inputs/audio/acdb_replay/payloads/core_custom_topologies_v2547.bin"
DEFAULT_V2552_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2552_AUDIO_ACDB_TOPOLOGY_REPLAY_ION_LIVE_HANDOFF_2026-06-16.md"
DEFAULT_V2557_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2557_AUDIO_ACDB_FULL_MANIFEST_POST_INIT_AUTO_ARM_LIVE_2026-06-16.md"
DEFAULT_LIBACDBLOADER = ROOT / "workspace/private/inputs/audio/acdb-deps-v2506/vendor-lib/libacdbloader.so"
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_MANIFEST = DEFAULT_BUILD_ROOT / "manifest.json"
REQUIRED_PREPARE_CAL_TYPES = [
    {"cal_type": 11, "name": "ADM_AUDPROC_CAL_TYPE", "reason": "Android-good AUDPROC log and native q6asm/adm prepare dependency"},
    {"cal_type": 12, "name": "ADM_AUDVOL_CAL_TYPE", "reason": "Android-good VOL log appears in ACDB speaker edge"},
    {"cal_type": 15, "name": "ASM_AUDSTRM_CAL_TYPE", "reason": "V2393 q6asm_send_cal cal_block NULL after topology/app-type"},
    {"cal_type": 16, "name": "AFE_COMMON_RX_CAL_TYPE", "reason": "V2393 send_afe_cal_type cal_block missing for RX port"},
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            return None
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_all_zero(path: Path) -> bool:
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            if any(chunk):
                return False
    return True


def payload_state(path: Path, *, expected_sha256: str = EXPECTED_TOPOLOGY_SHA256) -> dict[str, Any]:
    state: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
        "expected_size": EXPECTED_TOPOLOGY_LEN,
        "expected_sha256": expected_sha256,
        "zero_sha256": ZERO_4916_SHA256,
        "private_only": True,
        "committable": False,
    }
    if not path.exists() or not path.is_file():
        return state | {"ok": False, "reason": "missing-or-not-file"}
    size = path.stat().st_size
    digest = sha256_file(path)
    all_zero = is_all_zero(path)
    checks = {
        "size_ok": size == EXPECTED_TOPOLOGY_LEN,
        "sha256_ok": digest == expected_sha256,
        "nonzero_ok": not all_zero,
        "zero_hash_rejected": digest != ZERO_4916_SHA256,
    }
    return state | {
        "ok": all(checks.values()),
        "reason": "ok" if all(checks.values()) else "payload-validation-failed",
        "size": size,
        "sha256": digest,
        "mode": oct(path.stat().st_mode & 0o777),
        "all_zero": all_zero,
        "checks": checks,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def row_is_successful_nonzero(row: dict[str, Any]) -> bool:
    ret = parse_int(row.get("ret"))
    out_len = parse_int(row.get("out_len"))
    return bool(
        ret == 0
        and out_len is not None
        and out_len > 0
        and row.get("all_zero") is False
        and row.get("sha256") not in {None, ZERO_4916_SHA256}
    )


def v2557_capture_state(result_path: Path, *, expected_sha256: str = EXPECTED_TOPOLOGY_SHA256) -> dict[str, Any]:
    state: dict[str, Any] = {"path": rel(result_path), "exists": result_path.exists()}
    if not result_path.exists():
        return state | {"ok": False, "reason": "missing-result"}
    result = load_json(result_path)
    full = result.get("full_manifest_summary", {})
    base = full.get("base_summary", {})
    rows = list(base.get("acdbtap_rows", []))
    target_rows = [
        row
        for row in rows
        if parse_int(row.get("out_len")) == EXPECTED_TOPOLOGY_LEN
        and parse_int(row.get("ret")) == 0
        and row.get("sha256") == expected_sha256
        and row.get("all_zero") is False
    ]
    successful_nonzero = [row for row in rows if row_is_successful_nonzero(row)]
    raw_validation: list[dict[str, Any]] = []
    run_root = result_path.parent
    for row in target_rows:
        raw_path_value = row.get("raw_path")
        if not raw_path_value:
            raw_validation.append({"ok": False, "reason": "row-missing-raw-path", "seq": row.get("seq")})
            continue
        raw_name = Path(str(raw_path_value)).name
        candidates = list((run_root / "ownget-device-artifacts").glob(f"**/{raw_name}"))
        raw_path = candidates[0] if candidates else run_root / "ownget-device-artifacts/acdbtap" / raw_name
        raw = payload_state(raw_path, expected_sha256=expected_sha256)
        raw_validation.append({"seq": row.get("seq"), "cmd": row.get("cmd"), "raw": raw})
    return state | {
        "ok": bool(target_rows) and all(item.get("raw", {}).get("ok") for item in raw_validation),
        "reason": "ok" if target_rows else "no-validated-4916-row",
        "decision": result.get("decision"),
        "classification": full.get("classification"),
        "topology_success_count": full.get("topology_success_count"),
        "per_device_success_count": full.get("per_device_success_count"),
        "successful_nonzero_count": len(successful_nonzero),
        "row_count": len(rows),
        "target_4916_count": len(target_rows),
        "successful_rows": [
            {
                "seq": row.get("seq"),
                "cmd": row.get("cmd"),
                "out_len": parse_int(row.get("out_len")),
                "sha256": row.get("sha256"),
                "target_4916": parse_int(row.get("out_len")) == EXPECTED_TOPOLOGY_LEN,
            }
            for row in successful_nonzero
        ],
        "raw_validation": raw_validation,
    }


def report_text_state(path: Path, needles: dict[str, str]) -> dict[str, Any]:
    state: dict[str, Any] = {"path": rel(path), "exists": path.exists()}
    if not path.exists():
        return state | {"ok": False, "checks": {key: False for key in needles}}
    text = path.read_text(encoding="utf-8", errors="replace")
    checks = {key: needle in text for key, needle in needles.items()}
    return state | {"ok": all(checks.values()), "checks": checks}


def logcat_state(result_path: Path) -> dict[str, Any]:
    log_paths = [
        result_path.parent / "ownget-device-artifacts/logcat-acdb-loader.txt",
        result_path.parent / "ownget-device-artifacts/logcat-avc-acdb-filter.txt",
    ]
    needles = {
        "common_topology_entered": "ACDB -> send_common_custom_topology",
        "topology_returned": "ACDB -> acdb_loader_send_common_custom_topology: Common custom topology in use",
        "fatal_sigsegv_after_topology": "Fatal signal 11 (SIGSEGV)",
    }
    existing_paths = [path for path in log_paths if path.exists()]
    text_parts = [path.read_text(encoding="utf-8", errors="replace") for path in existing_paths]
    text = "\n".join(text_parts)
    checks = {key: needle in text for key, needle in needles.items()}
    return {
        "paths": [rel(path) for path in log_paths],
        "existing_paths": [rel(path) for path in existing_paths],
        "exists": bool(existing_paths),
        "ok": bool(existing_paths) and all(checks.values()),
        "checks": checks,
        "send_audio_cal_v5_reached": "send_audio_cal" in text,
    }


def libacdbloader_interpose_state(path: Path, *, readelf: str = "readelf") -> dict[str, Any]:
    state: dict[str, Any] = {"path": rel(path), "exists": path.exists()}
    if not path.exists():
        return state | {"ok": False, "reason": "missing-lib"}
    try:
        symbols = subprocess.run([readelf, "-Ws", str(path)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
        relocs = subprocess.run([readelf, "-rW", str(path)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
    except Exception as exc:  # pragma: no cover - defensive host diagnostic
        return state | {"ok": False, "reason": f"readelf-error:{exc}"}
    symbols_text = symbols.stdout
    relocs_text = relocs.stdout
    checks = {
        "exports_send_common_custom_topology": " acdb_loader_send_common_custom_topology" in symbols_text,
        "exports_send_audio_cal_v5": " acdb_loader_send_audio_cal_v5" in symbols_text,
        "exports_init_v3": " acdb_loader_init_v3" in symbols_text,
        "jump_slot_send_common_custom_topology": "R_ARM_JUMP_SLOT" in relocs_text and "acdb_loader_send_common_custom_topology" in relocs_text,
    }
    return state | {
        "ok": all(checks.values()),
        "checks": checks,
        "symbol_lines": [line.strip() for line in symbols_text.splitlines() if "acdb_loader_send" in line or "acdb_loader_init_v3" in line],
        "reloc_lines": [line.strip() for line in relocs_text.splitlines() if "acdb_loader_send_common_custom_topology" in line],
    }


def manifest(args: argparse.Namespace) -> dict[str, Any]:
    started = time.monotonic()
    v2557 = v2557_capture_state(args.v2557_result_path, expected_sha256=args.expected_topology_sha256)
    stable = payload_state(args.stable_payload_path, expected_sha256=args.expected_topology_sha256)
    v2552 = report_text_state(
        args.v2552_report_path,
        {
            "topology_set_ok": "AUDIO_SET_CALIBRATION ok cal_type=39",
            "pcm_prepare_still_failed": "A90_PCM_PROBE_WRITE_ERROR",
            "topology_only_insufficient": "topology-only calibration",
        },
    )
    v2557_report = report_text_state(
        args.v2557_report_path,
        {
            "ret_zero_nonzero_4916": "The `out_len==4916` record passes",
            "real_set_pass_zero": "real `AUDIO_SET_CALIBRATION` pass-through: `0`",
        },
    )
    logcat = logcat_state(args.v2557_result_path)
    lib = libacdbloader_interpose_state(args.libacdbloader_path, readelf=args.readelf)
    topology_ready = bool(v2557.get("ok") and stable.get("ok") and stable.get("sha256") == v2557.get("raw_validation", [{}])[0].get("raw", {}).get("sha256"))
    full_cal_ready = False
    payload: dict[str, Any] = {
        "decision": "v2558-topology-payload-confirmed-full-cal-replay-still-gated",
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": now_iso(),
        "elapsed_sec": round(time.monotonic() - started, 3),
        "ok": topology_ready,
        "host_only": True,
        "device_action": "none",
        "flash_action": "none",
        "native_calibration_ioctls": "none",
        "speaker_or_pcm_action": "none",
        "topology_payload_ready": topology_ready,
        "full_calibration_replay_ready": full_cal_ready,
        "v2557_capture": v2557,
        "stable_payload": stable,
        "prior_topology_replay_evidence": v2552,
        "v2557_public_report_evidence": v2557_report,
        "v2557_logcat_boundary": logcat,
        "libacdbloader_interpose_feasibility": lib,
        "required_per_device_cal_types_not_pinned": REQUIRED_PREPARE_CAL_TYPES,
        "replay_boundary": {
            "topology_only_native_replay_already_tested": True,
            "topology_only_native_replay_result": "AUDIO_SET_CALIBRATION ok, then pcm_prepare EINVAL",
            "safe_to_repeat_topology_only_live": False,
            "safe_to_run_full_cal_replay_live": False,
            "reason_full_cal_blocked": "V2557 crashed immediately after common topology and did not reach helper-side send_audio_cal_v5; AFE/AUDPROC/ASM/VOL raw payload set is not pinned.",
            "next_unit": "host-only design/build of a capture path that skips or safely short-circuits common topology after the already-pinned payload, then reaches acdb_loader_send_audio_cal_v5 to dump per-device GET records",
        },
        "boundaries": {
            "raw_bytes_private_only": True,
            "no_raw_payload_committed": True,
            "no_dev_msm_audio_cal_open": True,
            "no_audio_set_calibration": True,
            "no_mixer_write": True,
            "no_pcm_playback": True,
        },
        "manifest_path": rel(args.manifest_path),
    }
    args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2557-result-path", type=Path, default=DEFAULT_V2557_RESULT)
    parser.add_argument("--stable-payload-path", type=Path, default=DEFAULT_STABLE_PAYLOAD)
    parser.add_argument("--v2552-report-path", type=Path, default=DEFAULT_V2552_REPORT)
    parser.add_argument("--v2557-report-path", type=Path, default=DEFAULT_V2557_REPORT)
    parser.add_argument("--libacdbloader-path", type=Path, default=DEFAULT_LIBACDBLOADER)
    parser.add_argument("--expected-topology-sha256", default=EXPECTED_TOPOLOGY_SHA256)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--readelf", default="readelf")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = manifest(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
