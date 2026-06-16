#!/usr/bin/env python3
"""V2584 checked runner for the V2583 pre-init ACDB store_get probe.

This wrapper reuses the V2490 checked Android boot/stage/pull/rollback engine
but stages the V2583 helper and V2583 preload.  The preload is passed through
the V2490 ioctl-trace slot because it exports ioctl() plus the
acdb_loader_send_common_custom_topology() hook.  It does not export acdb_ioctl()
and it does not dump raw ACDB buffers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
from datetime import datetime
from pathlib import Path
from typing import Any

import build_android_acdb_preinit_store_get_probe_v2583 as v2583
import native_audio_acdb_ownprocess_get_live_handoff_v2490 as v2490

RUN_ID = "V2584"
BUILD_TAG = "v2584-audio-acdb-preinit-store-get-live-runner"
ROOT = v2583.ROOT
DEFAULT_OUT_BASE = ROOT / "workspace/private/runs/audio"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2584_AUDIO_ACDB_PREINIT_STORE_GET_RUNNER_2026-06-16.md"
EXACT_GATE = (
    "AUD-ACDB-V2584-preinit-store-get go: one-shot preinit store_get metadata "
    "capture on Android, fake allocate preload, no SET replay, no speaker write, rollback to V2321"
)
EVENTS_NAME = "acdb-v2583-preinit-storeget-events.jsonl"
INIT_EVENTS_NAME = "acdb-v2583-init-driver-events.jsonl"


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def default_live_out_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return DEFAULT_OUT_BASE / f"v2584-acdb-preinit-store-get-{stamp}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def int_or_none(value: Any) -> int | None:
    try:
        if isinstance(value, str):
            return int(value, 0)
        return int(value)
    except (TypeError, ValueError):
        return None


def int32_or_none(value: Any) -> int | None:
    parsed = int_or_none(value)
    if parsed is None:
        return None
    parsed &= 0xFFFFFFFF
    if parsed & 0x80000000:
        return parsed - 0x100000000
    return parsed


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_v2583_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    build_args = argparse.Namespace(
        build=True,
        write_report=False,
        build_root=args.v2583_build_root,
        manifest_path=args.v2583_manifest_path,
        report_path=v2583.DEFAULT_REPORT,
        clang=v2583.TOOLCHAIN_ROOT / "bin/clang",
        lld=v2583.TOOLCHAIN_ROOT / "bin/ld.lld",
        readelf=args.readelf,
        file=args.file,
    )
    payload = v2583.manifest(build_args)
    args.v2583_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    args.v2583_manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def read_v2583_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"ok": False, "error": f"manifest missing: {rel(path)}"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {"ok": False, "error": f"manifest json error: {error}"}
    build = payload.get("build", {}) if isinstance(payload.get("build"), dict) else {}
    artifacts = build.get("artifacts", {}) if isinstance(build.get("artifacts"), dict) else {}
    source = payload.get("source_state", {}) if isinstance(payload.get("source_state"), dict) else {}
    return {
        "ok": bool(payload.get("ok") and artifacts.get("helper", {}).get("ok") and artifacts.get("preload", {}).get("ok")),
        "path": rel(path),
        "manifest": payload,
        "helper_artifact": artifacts.get("helper", {}),
        "preload_artifact": artifacts.get("preload", {}),
        "source_required_ok": bool(source.get("required_ok")),
        "source_prohibited_ok": bool(source.get("prohibited_ok")),
        "cases": source.get("cases", []),
    }


def artifact_state(entry: dict[str, Any], explicit_path: Path | None, explicit_sha: str | None) -> dict[str, Any]:
    if explicit_path:
        path = explicit_path
        expected = explicit_sha
    else:
        raw_path = entry.get("path")
        path = ROOT / raw_path if raw_path else None
        expected = entry.get("sha256")
    state: dict[str, Any] = {
        "path": rel(path) if path else None,
        "exists": bool(path and path.exists()),
        "expected_sha256": expected,
    }
    if path and path.exists():
        stat = path.stat()
        digest = sha256_file(path)
        state.update({
            "size": stat.st_size,
            "mode": oct(stat.st_mode & 0o777),
            "sha256": digest,
            "sha256_ok": expected is None or digest == expected,
            "group_or_world_writable": bool(stat.st_mode & 0o022),
        })
    state["ok"] = bool(state.get("exists") and state.get("sha256_ok", True) and not state.get("group_or_world_writable"))
    return state


def selected_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    if args.build_v2583_artifacts:
        build_v2583_artifacts(args)
    manifest = read_v2583_manifest(args.v2583_manifest_path)
    helper = artifact_state(manifest.get("helper_artifact", {}), args.helper_path, args.helper_sha256)
    preload = artifact_state(manifest.get("preload_artifact", {}), args.preload_so, args.preload_sha256)
    preload["enabled"] = True
    return {
        "manifest": manifest,
        "helper": helper,
        "preload": preload,
        "ok": bool(manifest.get("ok") and helper.get("ok") and preload.get("ok")),
    }


def to_v2490_args(args: argparse.Namespace, artifacts: dict[str, Any]) -> argparse.Namespace:
    base = v2490.parse_args([])
    base.dry_run = args.dry_run
    base.run_live = args.run_live
    base.build_helper = False
    base.build_combined_preload = False
    base.build_acdbtap = False
    base.build_ioctl_trace = False
    base.use_combined_preload = False
    base.enable_acdbtap_preload = False
    base.disable_ioctl_trace = False
    base.fake_audio_cal_allocate = True
    base.out_dir = args.out_dir
    base.adb = args.adb
    base.serial = args.serial
    base.from_native = args.from_native
    base.android_timeout = args.android_timeout
    base.flash_timeout = args.flash_timeout
    base.adb_command_timeout = args.adb_command_timeout
    base.adb_pull_timeout = args.adb_pull_timeout
    base.helper_timeout = args.helper_timeout
    base.android_root_recheck_attempts = args.android_root_recheck_attempts
    base.android_root_recheck_sleep_sec = args.android_root_recheck_sleep_sec
    base.android_settle_adb_retry_attempts = args.android_settle_adb_retry_attempts
    base.android_settle_adb_retry_sleep_sec = args.android_settle_adb_retry_sleep_sec
    base.helper_path = ROOT / artifacts["helper"]["path"]
    base.helper_sha256 = artifacts["helper"]["sha256"]
    base.ioctl_trace_so = ROOT / artifacts["preload"]["path"]
    base.ioctl_trace_sha256 = artifacts["preload"]["sha256"]
    base.readelf = args.readelf
    base.file = args.file
    return base


def run_helper_command(args: argparse.Namespace) -> list[str]:
    ld_library_path = ":".join([v2490.REMOTE_DIR, "/vendor/lib", "/system/lib", "/system_ext/lib", "/product/lib"])
    preload_value = v2490.REMOTE_IOCTL_TRACE_SO
    script = f"""
set +e
cd {shlex.quote(v2490.REMOTE_DIR)} || exit 61
rm -f ownget.stdout.txt ownget.stderr.txt ownget.rc ownget-run-context.txt ioctl-trace-events.jsonl {shlex.quote(EVENTS_NAME)} {shlex.quote(INIT_EVENTS_NAME)}
rm -f {shlex.quote(v2490.REMOTE_ACDBTAP_DIR)}/* 2>/dev/null || true
{{
  echo '### run-shell-id'
  id 2>&1 || true
  id -Z 2>&1 || true
  echo '### run-env'
  echo 'LD_PRELOAD={preload_value}'
  echo 'A90_ACDB_FAKE_ALLOCATE=1'
  echo 'V2583_PREINIT_STORE_GET=enabled'
  echo 'LD_LIBRARY_PATH={ld_library_path}'
  echo '### run-proc-self-status'
  grep -E '^(Name|Uid|Gid|Groups|Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs|Seccomp):' /proc/self/status 2>&1 || true
}} > ownget-run-context.txt 2>&1
A90_ACDB_FAKE_ALLOCATE=1 LD_PRELOAD={shlex.quote(preload_value)} LD_LIBRARY_PATH={shlex.quote(ld_library_path)} {shlex.quote(v2490.REMOTE_HELPER)} > ownget.stdout.txt 2> ownget.stderr.txt
rc=$?
echo "$rc" > ownget.rc
cat ownget.rc
exit 0
""".strip()
    return v2490.adb_su(args, script)


def require_live_gate(args: argparse.Namespace) -> None:
    if args.exact_gate != EXACT_GATE:
        raise RuntimeError("V2584 live requires the exact gate phrase")


def parse_v2583_events(artifact_dir: Path) -> dict[str, Any]:
    events_path = artifact_dir / EVENTS_NAME
    init_events_path = artifact_dir / INIT_EVENTS_NAME
    rows = read_jsonl(events_path)
    init_rows = read_jsonl(init_events_path)
    stages = [row.get("stage") for row in rows if row.get("event") == "v2583_preinit_store_get"]
    init_stages = [row.get("stage") for row in init_rows if row.get("event") == "v2583_init_driver"]
    case_rows = [row for row in rows if row.get("event") == "v2583_preinit_store_get" and row.get("stage") == "case_return"]
    case_states: list[dict[str, Any]] = []
    for row in case_rows:
        ret = int32_or_none(row.get("ret"))
        out_len = int_or_none(row.get("out_len"))
        all_zero = bool(row.get("all_zero"))
        case_states.append({
            "case": row.get("case"),
            "selector": int_or_none(row.get("selector")),
            "instance": int_or_none(row.get("instance")),
            "ret": ret,
            "out_len": out_len,
            "all_zero": all_zero,
            "fnv1a32": row.get("fnv1a32"),
            "success_metadata": bool(ret == 0 and out_len is not None and out_len > 0 and not all_zero),
        })
    successes = [state for state in case_states if state["success_metadata"]]
    if not rows and not init_rows:
        classification = "v2584-preinit-storeget-no-events"
    elif successes:
        classification = "v2584-preinit-storeget-nonzero-metadata-captured"
    elif case_states:
        classification = "v2584-preinit-storeget-case-returns-no-nonzero"
    elif "before_store_get_cases" in stages:
        classification = "v2584-preinit-storeget-no-case-return"
    elif "entered_common_topology_hook" in stages:
        classification = "v2584-preinit-storeget-hook-entered-no-cases"
    elif "before_init_v3" in init_stages:
        classification = "v2584-preinit-storeget-init-entered-no-hook"
    else:
        classification = "v2584-preinit-storeget-no-case-return"
    return {
        "events_path": rel(events_path),
        "init_events_path": rel(init_events_path),
        "event_count": len(rows),
        "init_event_count": len(init_rows),
        "stages": stages,
        "init_stages": init_stages,
        "case_return_count": len(case_states),
        "success_count": len(successes),
        "case_results": case_states,
        "classification": classification,
        "success": bool(successes),
    }


def summarize_v2583_probe(artifact_dir: Path) -> dict[str, Any]:
    base_summary = v2490.parse_ownget_artifacts(artifact_dir)
    store = parse_v2583_events(artifact_dir)
    ioctl_events = base_summary.get("ioctl_trace_events", [])
    pass_through_set_events = [
        event for event in ioctl_events
        if event.get("name") == "AUDIO_SET_CALIBRATION" and event.get("intercept") != "fake-success"
    ]
    if pass_through_set_events:
        classification = "v2584-boundary-violation-real-audio-set-passthrough"
        success = False
    else:
        classification = store["classification"]
        success = bool(store["success"])
    return {
        "classification": classification,
        "success": success,
        "real_audio_set_pass_through_count": len(pass_through_set_events),
        "store_get": store,
        "base_summary": base_summary,
    }


def select_pulled_dir_from_result(result: dict[str, Any]) -> Path | None:
    out_dir_raw = result.get("out_dir")
    if not out_dir_raw:
        return None
    pulled = ROOT / str(out_dir_raw) / "ownget-device-artifacts"
    if not pulled.exists():
        return None
    return v2490.select_pulled_artifact_dir(pulled)


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = selected_artifacts(args)
    base_args = to_v2490_args(args, artifacts) if artifacts.get("ok") else None
    base_payload = v2490.dry_run_payload(base_args) if base_args else {}
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": "v2584-acdb-preinit-store-get-live-runner-dry-run",
        "host_only": True,
        "device_action": "none",
        "operator_spec": "docs/OPERATOR_ACDB_IOCTL_INTERPOSE_CAPTURE_SPEC_2026-06-15.md",
        "prior_build_report": "docs/reports/NATIVE_INIT_V2583_AUDIO_ACDB_PREINIT_STORE_GET_BUILD_2026-06-16.md",
        "v2583_artifacts": artifacts,
        "exact_gate_required": EXACT_GATE,
        "v2490_engine": {
            "run_id": "V2490",
            "decision": base_payload.get("decision"),
            "live_ready": base_payload.get("live_ready", False),
            "command_safety": base_payload.get("command_safety"),
            "commands": base_payload.get("commands", {}),
        },
        "v2584_live_override": {
            "reason": "V2490 stages the selected helper and selected ioctl-trace slot; V2584 maps that slot to the V2583 preload and overrides only helper execution metadata cleanup/context.",
            "run_helper": run_helper_command(args),
        },
        "capture_contract": {
            "target_function": "acdb_loader_store_get_audio_cal from common-topology hook",
            "request_cases": artifacts.get("manifest", {}).get("cases", []),
            "fake_audio_cal_allocate": True,
            "preload_slot": "V2490 ioctl_trace slot contains V2583 ioctl+common_topology preload",
            "success_requires": "ret==0 and all_zero=false in V2583 case_return metadata; requested length alone is not success",
            "metadata_only_public": True,
            "raw_payload_dump": False,
            "no_native_msm_audio_cal_set": True,
            "no_speaker_write": True,
        },
    }
    payload["live_ready"] = bool(artifacts.get("ok") and base_payload.get("live_ready"))
    payload["live_blockers"] = []
    if not artifacts.get("ok"):
        payload["live_blockers"].append("V2583 preinit store-get helper/preload artifacts are not ready")
    payload["live_blockers"].extend(base_payload.get("live_blockers", []))
    payload["command_safety"] = v2490.command_safety({
        "commands": {
            "v2490_engine": base_payload.get("commands", {}),
            "v2584_live_override": payload["v2584_live_override"]["run_helper"],
        }
    })
    payload["ok"] = bool(payload["live_ready"] and payload["command_safety"].get("ok"))
    return payload


def run_live(args: argparse.Namespace) -> dict[str, Any]:
    require_live_gate(args)
    if args.out_dir is None:
        args.out_dir = default_live_out_dir()
    dry = dry_run_payload(args)
    if not dry.get("ok"):
        raise RuntimeError(f"V2584 live inputs are not ready: {dry.get('live_blockers')}")
    artifacts = dry["v2583_artifacts"]
    base_args = to_v2490_args(args, artifacts)
    original = v2490.run_helper_command
    try:
        v2490.run_helper_command = lambda _base_args: run_helper_command(args)  # type: ignore[assignment]
        result = v2490.run_live(base_args)
    finally:
        v2490.run_helper_command = original  # type: ignore[assignment]
    pulled_dir = select_pulled_dir_from_result(result)
    summary = summarize_v2583_probe(pulled_dir) if pulled_dir else {
        "classification": "v2584-no-pulled-artifacts",
        "success": False,
        "real_audio_set_pass_through_count": 0,
        "store_get": {},
    }
    wrapper = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": f"{summary['classification']}-rollback-{'pass' if result.get('rolled_back') else 'unknown'}",
        "out_dir": result.get("out_dir"),
        "v2583_artifacts": artifacts,
        "v2490_engine_result": result,
        "store_get_summary": summary,
        "ok": bool(result.get("rolled_back") and summary.get("success")),
    }
    if result.get("out_dir"):
        write_json(ROOT / str(result["out_dir"]) / "v2584-result.json", wrapper)
    return wrapper


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload.get("store_get_summary", {})
    dry = payload if payload.get("decision") == "v2584-acdb-preinit-store-get-live-runner-dry-run" else None
    artifacts = payload.get("v2583_artifacts", {})
    lines = [
        "# NATIVE_INIT V2584 — ACDB pre-init store-get runner",
        "",
        "Date: 2026-06-16",
        "",
        "## Scope",
        "",
        "Host-only runner unit after V2583. No live Android handoff, native calibration SET, speaker write, or raw ACDB payload publication was performed in this iteration.",
        "",
        "## Decision",
        "",
        f"- decision: `{payload.get('decision')}`",
        f"- ok: `{payload.get('ok')}`",
        f"- live_ready: `{payload.get('live_ready')}`" if dry else f"- out_dir: `{payload.get('out_dir')}`",
        f"- live_blockers: `{payload.get('live_blockers')}`" if dry else f"- classification: `{summary.get('classification')}`",
        "",
        "## Runner Contract",
        "",
        f"- exact live gate: `{EXACT_GATE}`",
        "- V2584 stages the V2583 preload through the V2490 ioctl-trace preload slot.",
        "- The helper only enters `acdb_loader_init_v3()`; the pre-init hook runs the five V2580 store-get metadata cases before the known init-tail crash.",
        "- Success requires `ret==0` plus `all_zero=false` in V2583 `case_return` metadata; requested length alone is not success.",
        "- Native replay SET, speaker playback, and raw payload publication remain blocked.",
        "",
        "## Artifacts",
        "",
        f"- helper_sha256: `{artifacts.get('helper', {}).get('sha256')}`",
        f"- preload_sha256: `{artifacts.get('preload', {}).get('sha256')}`",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_preinit_store_get_live_handoff_v2584.py tests/test_native_audio_acdb_preinit_store_get_live_handoff_v2584.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_preinit_store_get_live_handoff_v2584`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_preinit_store_get_live_handoff_v2584.py --write-report`",
        "- `git diff --check`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--exact-gate")
    parser.add_argument("--build-v2583-artifacts", action="store_true")
    parser.add_argument("--v2583-build-root", type=Path, default=v2583.DEFAULT_BUILD_ROOT)
    parser.add_argument("--v2583-manifest-path", type=Path, default=v2583.DEFAULT_MANIFEST)
    parser.add_argument("--helper-path", type=Path)
    parser.add_argument("--helper-sha256")
    parser.add_argument("--preload-so", type=Path)
    parser.add_argument("--preload-sha256")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial")
    parser.add_argument("--from-native", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--android-timeout", type=float, default=240.0)
    parser.add_argument("--flash-timeout", type=float, default=420.0)
    parser.add_argument("--adb-command-timeout", type=float, default=90.0)
    parser.add_argument("--adb-pull-timeout", type=float, default=120.0)
    parser.add_argument("--helper-timeout", type=float, default=90.0)
    parser.add_argument("--android-root-recheck-attempts", type=int, default=v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_ATTEMPTS)
    parser.add_argument("--android-root-recheck-sleep-sec", type=float, default=v2490.v2396.DEFAULT_ANDROID_ROOT_RECHECK_SLEEP_SEC)
    parser.add_argument("--android-settle-adb-retry-attempts", type=int, default=v2490.DEFAULT_SETTLE_ADB_RETRY_ATTEMPTS)
    parser.add_argument("--android-settle-adb-retry-sleep-sec", type=float, default=v2490.DEFAULT_SETTLE_ADB_RETRY_SLEEP_SEC)
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--file", default="file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.run_live:
        payload = run_live(args)
    else:
        payload = dry_run_payload(args)
    if args.write_report:
        write_report(args.report_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
