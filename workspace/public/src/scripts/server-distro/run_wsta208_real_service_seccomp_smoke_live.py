#!/usr/bin/env python3
"""WSTA208: run the loopback smoke service under real seccomp enforcement.

This live gate proves the first non-canary service path:

  * build a fresh WSTA161 loader helper with exec-after-load support;
  * mount the SD-backed Debian work image and start temporary Dropbear over NCM;
  * stage the service launcher, WSTA153 policy, WSTA156 filter, WSTA161 helper,
    and loopback smoke helpers;
  * run ``dpublic-smoke-httpd`` through ``a90-service-launch`` so the loader
    applies seccomp and then execs the real smoke server;
  * drive one loopback HTTP request while the service is running under the
    loaded filter.

No boot image is built or flashed.  No native reboot, Wi-Fi association, DHCP,
public tunnel, public smoke, packet-filter mutation, userdata write, or
switch-root is performed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REVAL_DIR = SCRIPT_DIR.parent / "revalidation"
for _path in (SCRIPT_DIR, REVAL_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import a90ctl  # noqa: E402
import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_d1_chroot_mvp as d1  # noqa: E402
import run_d2_ssh_in_chroot as d2  # noqa: E402
import run_wsta19_native_owned_chroot_wifi as wsta19  # noqa: E402
import run_wsta42_native_uplink_dpublic_tunnel as wsta42  # noqa: E402
import run_wsta94_packet_filter_live_gate as wsta94  # noqa: E402
import run_wsta149_dpublic_hud_intent_syscall_trace as wsta149  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta161_seccomp_loader_gated_apply_helper as wsta161  # noqa: E402
import run_wsta193_seccomp_correct_token_canary_source as wsta193  # noqa: E402
import run_wsta196_seccomp_load_canary_execute as wsta196  # noqa: E402
import run_wsta198_seccomp_load_canary_ssh_adapter as wsta198  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_LOCAL_IMAGE = wsta149.WSTA115_STRACE_IMAGE
DEFAULT_REMOTE_CLEAN_IMAGE = wsta42.DEFAULT_REMOTE_CLEAN_IMAGE
DEFAULT_WSTA153_POLICY = wsta160.DEFAULT_WSTA153_POLICY
DEFAULT_WSTA156_MANIFEST = wsta160.DEFAULT_WSTA156_MANIFEST
DEFAULT_WSTA156_OBJECT = wsta160.DEFAULT_WSTA156_OBJECT
PASS_DECISION = "wsta208-real-service-seccomp-smoke-live-pass"
RESULT_NAME = "wsta208_result.json"
FORBIDDEN_TOKEN_PREFIX = "WSTA161-" + "EXPLICIT"


ACK_FLAGS = [
    "--execute-real-service-seccomp-smoke-over-ssh",
    "--allow-correct-wsta161-token",
    "--ack-seccomp-load-risk",
    "--ack-single-service-smoke-only",
    "--ack-no-flash-no-reboot",
    "--ack-cleanup-required",
    "--ack-ssh-chroot-transport",
]


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path | str) -> Path:
    path_obj = path if isinstance(path, Path) else Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


def write_json(path: Path, payload: Any) -> None:
    wsta3.write_json(path, payload)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        raise ValueError(f"expected object JSON: {path}")
    return payload


def finish_result(out_path: Path, result: dict[str, Any]) -> dict[str, Any]:
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def explicit_live_gate(args: argparse.Namespace) -> tuple[bool, str]:
    if not args.execute_real_service_seccomp_smoke_over_ssh:
        return False, "wsta208-blocked-real-service-live-required"
    if not args.allow_correct_wsta161_token:
        return False, "wsta208-blocked-correct-token-allow-required"
    if not args.ack_seccomp_load_risk:
        return False, "wsta208-blocked-seccomp-load-risk-ack-required"
    if not args.ack_single_service_smoke_only:
        return False, "wsta208-blocked-single-service-smoke-ack-required"
    if not args.ack_no_flash_no_reboot:
        return False, "wsta208-blocked-no-flash-no-reboot-ack-required"
    if not args.ack_cleanup_required:
        return False, "wsta208-blocked-cleanup-ack-required"
    if not args.ack_ssh_chroot_transport:
        return False, "wsta208-blocked-ssh-chroot-transport-ack-required"
    return True, "ok"


def safety_flags(gate_ok: bool) -> dict[str, Any]:
    return {
        "device_action": gate_ok,
        "device_action_description": (
            "single-service-seccomp-load-enforce-dpublic-smoke-httpd-over-ssh-chroot"
            if gate_ok else False
        ),
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "dhcp": False,
        "public_tunnel": False,
        "public_smoke": False,
        "packet_filter_mutation": False,
        "userdata_touch": False,
        "switch_root": False,
        "ssh_chroot_transport": False,
        "dropbear_over_ncm": False,
        "fresh_native_health_checked": False,
        "post_run_native_health_checked": False,
        "live_command_executed": False,
        "correct_wsta161_token_supplied": False,
        "token_passed_over_stdin_redacted": False,
        "seccomp_assets_staged": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "service_functional_under_seccomp": False,
        "loopback_local_config": "runtime-loopback-only" if gate_ok else False,
        "post_run_audit_executed": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def private_token_status() -> dict[str, bool]:
    value = os.environ.get(wsta193.PRIVATE_TOKEN_ENV)
    return {
        "private_token_env_present": value is not None,
        "private_token_matches_wsta161": value == wsta161.LOAD_TOKEN,
    }


def seccomp_asset_paths(args: argparse.Namespace, helper_result: dict[str, Any]) -> dict[str, Path]:
    artifact = helper_result.get("artifact") if isinstance(helper_result.get("artifact"), dict) else {}
    helper_manifest = artifact.get("manifest")
    helper_binary = artifact.get("helper_binary")
    return {
        "policy": resolve_path(args.wsta153_seccomp_policy_json),
        "filter_manifest": resolve_path(args.wsta156_filter_manifest_json),
        "filter_object": resolve_path(args.wsta156_filter_object),
        "loader_manifest": resolve_path(helper_manifest or ""),
        "loader_helper": resolve_path(helper_binary or ""),
    }


def validate_seccomp_asset_inputs(paths: dict[str, Path]) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    for key, path in paths.items():
        checks[f"{key}_private"] = wsta160.is_under(path, PRIVATE_ROOT)
        checks[f"{key}_present"] = path.is_file()
    return checks


def build_exec_loader_helper(args: argparse.Namespace, run_dir: Path) -> dict[str, Any]:
    helper_dir = run_dir / "wsta161-loader-exec-after-load"
    helper_args = wsta161.build_arg_parser().parse_args([
        "--run-dir",
        str(helper_dir),
        "--wsta156-filter-manifest-json",
        str(resolve_path(args.wsta156_filter_manifest_json)),
        "--wsta156-filter-object",
        str(resolve_path(args.wsta156_filter_object)),
        "--emit-seccomp-loader-gated-apply-helper",
    ])
    return wsta161.run(helper_args)


def exec_loader_helper_ok(result: dict[str, Any]) -> bool:
    artifact = result.get("artifact") if isinstance(result.get("artifact"), dict) else {}
    checks = result.get("manifest_checks") if isinstance(result.get("manifest_checks"), dict) else {}
    manifest_path = resolve_path(artifact.get("manifest") or "")
    manifest = load_json(manifest_path) if manifest_path.is_file() else {}
    return bool(
        result.get("decision") == wsta161.PASS_DECISION
        and artifact.get("apply_code_compiled") is True
        and manifest.get("exec_after_load_compiled") is True
        and checks.get("exec_after_load_compiled") is True
    )


def stage_seccomp_assets(
    args: argparse.Namespace,
    run_dir: Path,
    paths: dict[str, Path],
) -> dict[str, Any]:
    return wsta198.stage_seccomp_canary_assets(args, run_dir, paths)


def remote_service_script() -> str:
    run_dir = wsta42.REMOTE_RUN_DIR + "/wsta208-seccomp-smoke"
    smoke_pid = run_dir + "/smoke.pid"
    smoke_log = run_dir + "/smoke.log"
    return f"""
set +e
RUN_DIR={shlex.quote(run_dir)}
SMOKE={shlex.quote(wsta42.REMOTE_SMOKE)}
HTTP_GET={shlex.quote(wsta42.REMOTE_HTTP_GET)}
LAUNCHER=/{shlex.quote(str(wsta3.TARGET_SERVICE_LAUNCHER))}
SMOKE_PID={shlex.quote(smoke_pid)}
SMOKE_LOG={shlex.quote(smoke_log)}
LO_ADDR_ADDED=0
echo A90WSTA208_REAL_SERVICE_BEGIN
: "${{A90_SERVICE_LAUNCH_SECCOMP_LOAD_TOKEN:?load-token-required}}"
ip_cmd() {{
  if [ -x /sbin/ip ]; then /sbin/ip "$@"; return $?; fi
  if [ -x /usr/sbin/ip ]; then /usr/sbin/ip "$@"; return $?; fi
  if [ -x /bin/busybox ]; then /bin/busybox ip "$@"; return $?; fi
  return 127
}}
cleanup() {{
  if [ -s "$SMOKE_PID" ]; then /bin/kill "$(/bin/cat "$SMOKE_PID")" >/dev/null 2>&1 || true; fi
  /usr/bin/pkill -f '[a]90-dpublic-smoke-httpd' >/dev/null 2>&1 || true
  if [ "$LO_ADDR_ADDED" = "1" ]; then ip_cmd addr del 127.0.0.1/8 dev lo >/dev/null 2>&1 || true; fi
}}
fail() {{
  rc=$1
  reason=$2
  echo "A90WSTA208_FAIL reason=$reason rc=$rc"
  [ -s "$SMOKE_LOG" ] && {{ echo A90WSTA208_SMOKE_LOG_BEGIN; /bin/cat "$SMOKE_LOG"; echo A90WSTA208_SMOKE_LOG_END; }}
  exit "$rc"
}}
trap cleanup EXIT INT TERM
/bin/mkdir -p "$RUN_DIR" {shlex.quote(wsta42.REMOTE_RUN_DIR)}
/bin/rm -f "$SMOKE_PID" "$SMOKE_LOG"
LO_UP_RC=0
ip_cmd link set lo up >/dev/null 2>&1 || LO_UP_RC=$?
echo A90WSTA208_LOOPBACK_UP_RC=$LO_UP_RC
if ip_cmd addr show lo 2>/dev/null | /bin/grep -q '127.0.0.1'; then
  echo A90WSTA208_LOOPBACK_ADDR_PRESENT=1
else
  if ip_cmd addr add 127.0.0.1/8 dev lo >/dev/null 2>&1; then
    LO_ADDR_ADDED=1
    echo A90WSTA208_LOOPBACK_ADDR_ADDED=1
    echo A90WSTA208_LOOPBACK_ADDR_PRESENT=1
  else
    echo A90WSTA208_LOOPBACK_ADDR_PRESENT=0
    fail 61 loopback-addr
  fi
fi
[ -x "$LAUNCHER" ] || fail 62 launcher-missing
[ -x "$SMOKE" ] || fail 63 smoke-missing
[ -x "$HTTP_GET" ] || fail 64 http-get-missing
[ -r /etc/a90-dpublic/seccomp-policy.json ] && echo A90WSTA208_SECCOMP_POLICY_PRESENT=1 || fail 65 policy-missing
[ -r /etc/a90-dpublic/seccomp-filter-manifest.json ] && echo A90WSTA208_FILTER_MANIFEST_PRESENT=1 || fail 66 filter-manifest-missing
/usr/bin/env -i \\
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \\
  A90_SERVICE_LAUNCH_SECCOMP_DRY_RUN=1 \\
  A90_SERVICE_LAUNCH_SECCOMP_ENFORCE=1 \\
  A90_SERVICE_LAUNCH_SECCOMP_HELPER_MODE=apply \\
  A90_SERVICE_LAUNCH_SECCOMP_HELPER_APPLY_GATE=WSTA163-ALLOW-HELPER-APPLY \\
  A90_SERVICE_LAUNCH_SECCOMP_LOAD_GATE=WSTA164-ALLOW-SECCOMP-LOAD-ENV \\
  A90_SERVICE_LAUNCH_SECCOMP_LOAD_TOKEN="$A90_SERVICE_LAUNCH_SECCOMP_LOAD_TOKEN" \\
  A90_SERVICE_LAUNCH_SECCOMP_EXEC_AFTER_LOAD=1 \\
  "$LAUNCHER" dpublic-smoke-httpd "$SMOKE" 127.0.0.1 8080 \\
  </dev/null >"$SMOKE_LOG" 2>&1 &
echo $! > "$SMOKE_PID"
echo A90WSTA208_SMOKE_PID=$(/bin/cat "$SMOKE_PID")
/bin/sleep 1
if /bin/kill -0 "$(/bin/cat "$SMOKE_PID")" >/dev/null 2>&1; then
  echo A90WSTA208_SMOKE_STARTED=1
else
  echo A90WSTA208_SMOKE_STARTED=0
  fail 67 smoke-start
fi
HTTP_OUT=$(/usr/bin/timeout 10s "$HTTP_GET" 127.0.0.1 8080 2>&1)
HTTP_RC=$?
echo A90WSTA208_HTTP_RC=$HTTP_RC
echo A90WSTA208_HTTP_OUT_BEGIN
/bin/printf '%s\\n' "$HTTP_OUT"
echo A90WSTA208_HTTP_OUT_END
echo A90WSTA208_SMOKE_LOG_BEGIN
/bin/cat "$SMOKE_LOG"
echo A90WSTA208_SMOKE_LOG_END
if /bin/printf '%s\\n' "$HTTP_OUT" | /bin/grep -q 'A90_DPUBLIC_SMOKE_OK'; then
  echo A90WSTA208_LOOPBACK_OK=1
else
  echo A90WSTA208_LOOPBACK_OK=0
  fail 68 loopback-http
fi
if /bin/grep -q 'A90WSTA161_SECCOMP_LOAD=1' "$SMOKE_LOG" \\
   && /bin/grep -q 'a90_seccomp_loader_decision=loaded' "$SMOKE_LOG" \\
   && /bin/grep -q 'A90WSTA208_EXEC_AFTER_LOAD=1' "$SMOKE_LOG"; then
  echo A90WSTA208_SECCOMP_REAL_SERVICE_MARKERS=1
else
  echo A90WSTA208_SECCOMP_REAL_SERVICE_MARKERS=0
  fail 69 seccomp-markers
fi
echo A90WSTA208_REAL_SERVICE_PASS
exit 0
""".strip()


def parse_service_probe(record: dict[str, Any]) -> dict[str, Any]:
    stdout = str(record.get("stdout") or "")
    stderr = str(record.get("stderr") or "")
    combined = stdout + "\n" + stderr
    return {
        "returncode_zero": record.get("returncode") == 0,
        "begin": "A90WSTA208_REAL_SERVICE_BEGIN" in stdout,
        "loopback_up": "A90WSTA208_LOOPBACK_UP_RC=0" in stdout,
        "loopback_addr_present": "A90WSTA208_LOOPBACK_ADDR_PRESENT=1" in stdout,
        "smoke_started": "A90WSTA208_SMOKE_STARTED=1" in stdout,
        "http_response_ok": "A90_DPUBLIC_SMOKE_OK" in stdout,
        "loopback_ok": "A90WSTA208_LOOPBACK_OK=1" in stdout,
        "launcher_exec_seccomp": "a90_service_launcher_decision=exec-seccomp" in stdout,
        "launcher_service": "a90_service_launcher_service=dpublic-smoke-httpd" in stdout,
        "launcher_user": "a90_service_launcher_user=a90www" in stdout,
        "load_attempt_marker": "A90WSTA161_SECCOMP_LOAD_ATTEMPT=1" in stdout,
        "loaded_marker": "A90WSTA161_SECCOMP_LOAD=1" in stdout,
        "loaded_decision": "a90_seccomp_loader_decision=loaded" in stdout,
        "exec_after_load_marker": "A90WSTA208_EXEC_AFTER_LOAD=1" in stdout,
        "real_service_markers": "A90WSTA208_SECCOMP_REAL_SERVICE_MARKERS=1" in stdout,
        "pass_marker": "A90WSTA208_REAL_SERVICE_PASS" in stdout,
        "token_literal_absent": wsta161.LOAD_TOKEN not in combined and FORBIDDEN_TOKEN_PREFIX not in combined,
        "no_external_network_inputs": wsta198.no_external_network_inputs(combined),
        "secret_values_logged": 0,
    }


def ssh_exec_token_script(
    args: argparse.Namespace,
    run_dir: Path,
    script: str,
    *,
    token: str,
    timeout: float,
) -> dict[str, Any]:
    return wsta198.ssh_exec_token_script(args, run_dir, script, token=token, timeout=timeout)


def chroot_cleanup_ok(result: dict[str, Any]) -> bool:
    return wsta94.chroot_cleanup_ok(result)


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_live_gate", str(result.get("gate_decision") or "wsta208-blocked-explicit-live-gate")),
        ("private_run_dir", "wsta208-blocked-nonprivate-run-dir"),
        ("private_token_env_present", "wsta208-blocked-private-token-env-missing"),
        ("private_token_matches_wsta161", "wsta208-blocked-private-token-invalid"),
        ("fresh_health_valid", "wsta208-blocked-fresh-health-invalid"),
        ("helper_built", "wsta208-blocked-helper-build"),
        ("helper_exec_after_load_compiled", "wsta208-blocked-helper-exec-after-load"),
        ("dpublic_helpers_built", "wsta208-blocked-dpublic-helper-build"),
        ("local_image_present", "wsta208-blocked-local-image-missing"),
        ("local_image_expected_sha", "wsta208-blocked-local-image-sha"),
        ("ssh_key_generated", "wsta208-blocked-ssh-keygen"),
        ("native_stale_cleanup_ok", "wsta208-blocked-native-stale-cleanup"),
        ("remote_image_ready", "wsta208-blocked-remote-image"),
        ("chroot_mount_ready", "wsta208-blocked-chroot-mount"),
        ("dropbear_started", "wsta208-blocked-dropbear-start"),
        ("debian_ssh_marker", "wsta208-blocked-debian-ssh-marker"),
        ("seccomp_asset_inputs_valid", "wsta208-blocked-seccomp-asset-inputs"),
        ("seccomp_assets_staged", "wsta208-blocked-seccomp-assets-stage"),
        ("loopback_binaries_staged", "wsta208-blocked-loopback-binaries-stage"),
        ("execution_returncode_zero", "wsta208-blocked-service-returncode"),
        ("seccomp_real_service_markers", "wsta208-blocked-service-seccomp-markers"),
        ("service_functional_under_seccomp", "wsta208-blocked-service-functional"),
        ("chroot_cleanup_ok", "wsta208-blocked-chroot-cleanup"),
        ("post_health_valid", "wsta208-blocked-post-health-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return decision
    return PASS_DECISION


def execute_live(args: argparse.Namespace, result: dict[str, Any], out_path: Path, run_dir: Path, run_id: str) -> dict[str, Any]:
    token = os.environ[wsta193.PRIVATE_TOKEN_ENV]
    mounted = False
    try:
        result["fresh_health"] = wsta196.run_readonly_health_checks(args.health_timeout)
        result["checks"]["fresh_health_valid"] = all(result["fresh_health"]["checks"].values())
        result["safety"]["fresh_native_health_checked"] = True
        write_json(out_path, result)
        if not result["checks"]["fresh_health_valid"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["loader_helper_build"] = build_exec_loader_helper(args, run_dir)
        result["checks"]["helper_built"] = result["loader_helper_build"].get("decision") == wsta161.PASS_DECISION
        result["checks"]["helper_exec_after_load_compiled"] = exec_loader_helper_ok(result["loader_helper_build"])
        write_json(out_path, result)
        if not (result["checks"]["helper_built"] and result["checks"]["helper_exec_after_load_compiled"]):
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["dpublic_helpers"] = wsta42.build_dpublic_helpers(run_dir)
        result["checks"]["dpublic_helpers_built"] = bool(result["dpublic_helpers"].get("ok"))
        write_json(out_path, result)
        if not result["checks"]["dpublic_helpers_built"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        if not args.local_image.is_file():
            result["checks"]["local_image_present"] = False
            result["decision"] = classify(result)
            return finish_result(out_path, result)
        local_sha = d1.sha256_file(args.local_image)
        result["local_image"] = rel(args.local_image)
        result["local_image_sha256"] = local_sha
        result["checks"]["local_image_present"] = True
        result["checks"]["local_image_expected_sha"] = (
            not args.local_image_sha256 or local_sha == args.local_image_sha256
        )
        write_json(out_path, result)
        if not result["checks"]["local_image_expected_sha"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["keygen"] = d2.generate_ssh_key(run_dir, run_id)
        result["checks"]["ssh_key_generated"] = result["keygen"].get("returncode") == 0
        public_key = d2.read_public_key(run_dir)
        write_json(out_path, result)
        if not result["checks"]["ssh_key_generated"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["native_stale_cleanup"] = wsta94.native_stale_cleanup(args)
        result["checks"]["native_stale_cleanup_ok"] = bool(result["native_stale_cleanup"].get("cleaned"))
        write_json(out_path, result)
        if not result["checks"]["native_stale_cleanup_ok"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        image_ready = wsta42.prepare_remote_work_image(args, result, out_path, run_dir, local_sha=local_sha)
        result["checks"]["remote_image_ready"] = bool(image_ready)
        write_json(out_path, result)
        if not image_ready:
            result["decision"] = result.get("decision") or classify(result)
            return finish_result(out_path, result)

        result["mount"] = wsta19.bridge_shell(
            args,
            wsta94.wsta94_mount_script(args.remote_image, args.mountpoint, args.ssh_port),
            timeout=args.setup_timeout,
        )
        mounted = True
        result["mount_parse"] = d2.parse_setup(str(result["mount"].get("text") or ""))
        result["checks"]["chroot_mount_ready"] = bool(
            result["mount_parse"].get("mount_ready") and result["mount_parse"].get("mounted")
        )
        write_json(out_path, result)
        if not result["checks"]["chroot_mount_ready"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["dropbear_start"] = wsta19.bridge_shell(
            args,
            wsta94.wsta94_start_dropbear_script(args.mountpoint, public_key, args.device_ip, args.ssh_port),
            timeout=args.setup_timeout,
            allow_error=True,
        )
        result["dropbear_parse"] = d2.parse_setup(str(result["dropbear_start"].get("text") or ""))
        result["checks"]["dropbear_started"] = bool(
            result["dropbear_parse"].get("started")
            and result["dropbear_parse"].get("authorized_keys")
            and result["dropbear_parse"].get("shadow_temp_key_only")
        )
        write_json(out_path, result)
        if not result["checks"]["dropbear_started"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["ssh"] = wsta19.ssh_chroot_marker(args, run_dir)
        result["ssh_parse"] = result["ssh"].get("marker", {})
        result["checks"]["debian_ssh_marker"] = bool(result["ssh_parse"].get("marker"))
        write_json(out_path, result)
        if not result["checks"]["debian_ssh_marker"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        asset_paths = seccomp_asset_paths(args, result["loader_helper_build"])
        asset_checks = validate_seccomp_asset_inputs(asset_paths)
        result["seccomp_asset_input_checks"] = asset_checks
        result["checks"]["seccomp_asset_inputs_valid"] = all(asset_checks.values())
        write_json(out_path, result)
        if not result["checks"]["seccomp_asset_inputs_valid"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["seccomp_assets_stage"] = stage_seccomp_assets(args, run_dir, asset_paths)
        result["checks"]["seccomp_assets_staged"] = bool(result["seccomp_assets_stage"].get("staged"))
        result["safety"]["seccomp_assets_staged"] = result["checks"]["seccomp_assets_staged"]
        write_json(out_path, result)
        if not result["checks"]["seccomp_assets_staged"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["loopback_stage"] = wsta94.stage_loopback_binaries(args, run_dir)
        result["checks"]["loopback_binaries_staged"] = wsta94.stage_ok(result["loopback_stage"])
        write_json(out_path, result)
        if not result["checks"]["loopback_binaries_staged"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["safety"]["ssh_chroot_transport"] = True
        result["safety"]["dropbear_over_ncm"] = True
        result["safety"]["live_command_executed"] = True
        result["safety"]["correct_wsta161_token_supplied"] = True
        result["safety"]["token_passed_over_stdin_redacted"] = True
        result["execution"] = ssh_exec_token_script(
            args,
            run_dir,
            remote_service_script(),
            token=token,
            timeout=args.execution_timeout,
        )
        parsed = parse_service_probe(result["execution"])
        result["service_parse"] = parsed
        result["checks"]["execution_returncode_zero"] = bool(parsed["returncode_zero"])
        result["checks"]["seccomp_real_service_markers"] = bool(
            parsed["load_attempt_marker"]
            and parsed["loaded_marker"]
            and parsed["loaded_decision"]
            and parsed["exec_after_load_marker"]
            and parsed["real_service_markers"]
            and parsed["token_literal_absent"]
            and parsed["no_external_network_inputs"]
        )
        result["checks"]["service_functional_under_seccomp"] = bool(
            parsed["returncode_zero"]
            and parsed["loopback_up"]
            and parsed["loopback_addr_present"]
            and parsed["smoke_started"]
            and parsed["http_response_ok"]
            and parsed["loopback_ok"]
            and parsed["pass_marker"]
        )
        if result["checks"]["seccomp_real_service_markers"]:
            result["safety"]["seccomp_filter_loaded"] = True
            result["safety"]["seccomp_enforced"] = True
        result["safety"]["service_functional_under_seccomp"] = result["checks"]["service_functional_under_seccomp"]
        write_json(out_path, result)
    finally:
        if mounted:
            result["dpublic_cleanup"] = wsta42.cleanup_dpublic(args, run_dir)
            result["cleanup"] = wsta19.bridge_shell(
                args,
                wsta94.wsta94_cleanup_script(args.mountpoint),
                timeout=args.cleanup_timeout,
                allow_error=True,
            )
            result["cleanup_parse"] = d2.parse_cleanup(str(result["cleanup"].get("text") or ""))
            result["postcheck"] = wsta19.bridge_shell(
                args,
                wsta94.wsta94_postcheck_script(args.mountpoint),
                timeout=args.cleanup_timeout,
                allow_error=True,
            )
            result["postcheck_parse"] = d2.parse_postcheck(str(result["postcheck"].get("text") or ""))
            result["checks"]["chroot_cleanup_ok"] = bool(chroot_cleanup_ok(result))
        else:
            result["dpublic_cleanup"] = {"skipped": True, "reason": "chroot-not-mounted", "cleaned": True}
            result["cleanup"] = {"skipped": True, "reason": "chroot-not-mounted"}
            result["postcheck"] = {"skipped": True, "reason": "chroot-not-mounted"}
            result["checks"]["chroot_cleanup_ok"] = True
        result["post_health"] = wsta196.run_readonly_health_checks(args.health_timeout)
        result["checks"]["post_health_valid"] = all(result["post_health"]["checks"].values())
        result["safety"]["post_run_native_health_checked"] = True
        result["safety"]["post_run_audit_executed"] = True
        write_json(out_path, result)

    result["decision"] = classify(result)
    result["gate_decision"] = "ok" if result["decision"] == PASS_DECISION else result["decision"]
    return finish_result(out_path, result)


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta208-real-service-seccomp-smoke-live-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    gate_ok, gate_decision = explicit_live_gate(args)
    result: dict[str, Any] = {
        "scope": "WSTA208 real dpublic-smoke-httpd service under seccomp live gate",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "gate_decision": gate_decision,
        "safety": safety_flags(gate_ok),
        "inputs": {
            "local_image": rel(resolve_path(args.local_image)),
            "remote_image": args.remote_image,
            "remote_clean_image": args.remote_clean_image,
            "wsta153_seccomp_policy_json": rel(resolve_path(args.wsta153_seccomp_policy_json)),
            "wsta156_filter_manifest_json": rel(resolve_path(args.wsta156_filter_manifest_json)),
            "wsta156_filter_object": rel(resolve_path(args.wsta156_filter_object)),
        },
        "checks": {
            "explicit_live_gate": gate_ok,
            "private_run_dir": wsta160.is_under(run_dir, PRIVATE_ROOT),
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        },
    }
    if not result["checks"]["private_run_dir"]:
        result["decision"] = classify(result)
        result["ended_utc"] = utc_stamp()
        return result
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / RESULT_NAME
    write_json(out_path, result)
    if not gate_ok:
        result["decision"] = classify(result)
        return finish_result(out_path, result)

    token_checks = private_token_status()
    result["token_checks"] = token_checks
    result["checks"].update(token_checks)
    write_json(out_path, result)
    if not (token_checks["private_token_env_present"] and token_checks["private_token_matches_wsta161"]):
        result["decision"] = classify(result)
        return finish_result(out_path, result)

    return execute_live(args, result, out_path, run_dir, run_id)


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "run_dir": result.get("run_dir"),
        "gate_decision": result.get("gate_decision"),
        "service_parse": result.get("service_parse", {}),
        "checks": result.get("checks", {}),
        "safety": result.get("safety", {}),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--host", default=a90ctl.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=a90ctl.DEFAULT_PORT)
    parser.add_argument("--bridge-host", default=a90ctl.DEFAULT_HOST)
    parser.add_argument("--bridge-port", type=int, default=a90ctl.DEFAULT_PORT)
    parser.add_argument("--device-ip", default="192.168.7.2")
    parser.add_argument("--ssh-port", type=int, default=d2.DEFAULT_SSH_PORT)
    parser.add_argument("--ssh-connect-timeout", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--health-timeout", type=float, default=20.0)
    parser.add_argument("--setup-timeout", type=float, default=180.0)
    parser.add_argument("--cleanup-timeout", type=float, default=120.0)
    parser.add_argument("--execution-timeout", type=float, default=120.0)
    parser.add_argument("--ssh-timeout", type=float, default=45.0)
    parser.add_argument("--sha-timeout", type=float, default=180.0)
    parser.add_argument("--bridge-timeout", type=float, default=60.0)
    parser.add_argument("--connect-timeout", type=float, default=10.0)
    parser.add_argument("--tcp-timeout", type=float, default=30.0)
    parser.add_argument("--transfer-timeout", type=float, default=900.0)
    parser.add_argument("--transfer-delay", type=float, default=2.0)
    parser.add_argument("--local-image", type=Path, default=DEFAULT_LOCAL_IMAGE)
    parser.add_argument("--local-image-sha256", default=wsta149.WSTA115_STRACE_IMAGE_SHA256)
    parser.add_argument("--remote-image", default=d1.DEFAULT_REMOTE_IMAGE)
    parser.add_argument("--remote-clean-image", default=DEFAULT_REMOTE_CLEAN_IMAGE)
    parser.add_argument("--mountpoint", default=d1.DEFAULT_MOUNTPOINT)
    parser.add_argument("--wsta153-seccomp-policy-json", type=Path, default=DEFAULT_WSTA153_POLICY)
    parser.add_argument("--wsta156-filter-manifest-json", type=Path, default=DEFAULT_WSTA156_MANIFEST)
    parser.add_argument("--wsta156-filter-object", type=Path, default=DEFAULT_WSTA156_OBJECT)
    parser.add_argument("--toybox", default="/bin/toybox")
    parser.add_argument("--execute-real-service-seccomp-smoke-over-ssh", action="store_true")
    parser.add_argument("--allow-correct-wsta161-token", action="store_true")
    parser.add_argument("--ack-seccomp-load-risk", action="store_true")
    parser.add_argument("--ack-single-service-smoke-only", action="store_true")
    parser.add_argument("--ack-no-flash-no-reboot", action="store_true")
    parser.add_argument("--ack-cleanup-required", action="store_true")
    parser.add_argument("--ack-ssh-chroot-transport", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        ts = utc_stamp()
        run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / (args.run_id or f"wsta208-real-service-seccomp-smoke-live-{ts}")))
        if wsta160.is_under(run_dir, PRIVATE_ROOT):
            run_dir.mkdir(parents=True, exist_ok=True)
            out_path = run_dir / RESULT_NAME
            if out_path.is_file():
                try:
                    result = json.loads(out_path.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    result = {"scope": "WSTA208 real dpublic-smoke-httpd service under seccomp live gate"}
            else:
                result = {"scope": "WSTA208 real dpublic-smoke-httpd service under seccomp live gate"}
            result["decision"] = "wsta208-runner-error"
            result["error"] = str(exc)
            finish_result(out_path, result)
        else:
            result = {"decision": "wsta208-runner-error", "error": str(exc)}
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
