#!/usr/bin/env python3
"""Run WSTA110: service launcher proof inside the Debian chroot.

WSTA109 stages the service-hardening rootfs assets.  WSTA110 is the bounded
live proof that those assets can execute inside the SD-backed Debian chroot:

  * mount the known Debian image as the chroot service surface,
  * start temporary key-only dropbear using the existing D2 pattern,
  * stage the WSTA109 service users, launcher, policy, and markers,
  * run ``a90-service-launch dpublic-smoke-httpd ...`` from inside the chroot,
  * prove the child process is a90www/a90www with NoNewPrivs=1,
  * keep public exposure default-off and clean chroot/dropbear/loop state.

No boot image is built or flashed.  No Wi-Fi association, DHCP, public tunnel,
public smoke, packet-filter mutation, userdata write, native reboot, or
switch-root is performed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REVAL_DIR = SCRIPT_DIR.parent / "revalidation"
for _path in (SCRIPT_DIR, REVAL_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402
import run_d1_chroot_mvp as d1  # noqa: E402
import run_d2_ssh_in_chroot as d2  # noqa: E402
import run_wsta19_native_owned_chroot_wifi as wsta19  # noqa: E402
import run_wsta2_native_materialization as wsta2  # noqa: E402
import run_wsta42_native_uplink_dpublic_tunnel as wsta42  # noqa: E402
import run_wsta94_packet_filter_live_gate as wsta94  # noqa: E402


REPO_ROOT = wsta2.REPO_ROOT
DEFAULT_RUN_BASE = wsta2.DEFAULT_RUN_BASE
PASS_DECISION = "wsta110-service-launcher-chroot-live-pass"
RESULT_NAME = "wsta110_result.json"
REMOTE_SERVICE_LAUNCHER = "/" + str(wsta3.TARGET_SERVICE_LAUNCHER)
REMOTE_SERVICE_POLICY = "/" + str(wsta3.TARGET_SERVICE_HARDENING_POLICY)
REMOTE_STAGE_MARKER = "/" + str(wsta3.TARGET_STAGE_MARKER)


def rel(path: Path) -> str:
    return wsta2.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: Any) -> None:
    d1.write_json(path, payload)


def finish_result(out_path: Path, result: dict[str, Any]) -> dict[str, Any]:
    result["ended_utc"] = utc_stamp()
    write_json(out_path, result)
    return result


def sha256_file(path: Path) -> str:
    return d1.sha256_file(path)


def explicit_live_gate(args: argparse.Namespace) -> tuple[bool, str]:
    if not args.execute_service_launcher_chroot_live:
        return False, "wsta110-blocked-service-launcher-chroot-live-required"
    if not args.allow_service_launcher_live:
        return False, "wsta110-blocked-service-launcher-live-allow-required"
    return True, "ok"


def safety(gate_ok: bool) -> dict[str, Any]:
    return {
        "device_action": gate_ok,
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "dhcp": False,
        "public_tunnel": False,
        "public_smoke": False,
        "external_ping": False,
        "packet_filter_mutation": False,
        "userdata_touch": False,
        "switch_root": False,
        "rootfs_chroot_mutation": "explicit-live-gated-sd-work-image-only" if gate_ok else False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def service_policy_payload() -> dict[str, Any]:
    services = {
        service: {
            "user": identity["user"],
            "group": identity["group"],
            "uid": identity["uid"],
            "gid": identity["gid"],
            "network_intent": identity["network_intent"],
            "no_new_privs": True,
            "ambient_capabilities": [],
            "bounding_capabilities": [],
        }
        for service, identity in wsta3.SERVICE_IDENTITIES.items()
    }
    return {
        "schema": "a90-service-hardening-v1",
        "default_public_off": True,
        "launcher": str(wsta3.TARGET_SERVICE_LAUNCHER),
        "launcher_requires": ["setpriv", "no-new-privs"],
        "services": services,
        "root_boundary_services": list(wsta3.ROOT_BOUNDARY_SERVICES),
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def write_remote_bytes(args: argparse.Namespace,
                       run_dir: Path,
                       remote_path: str,
                       data: bytes,
                       *,
                       mode: str,
                       timeout: float) -> dict[str, Any]:
    command = [
        *wsta42.ssh_command(args, run_dir),
        (
            "set -eu; "
            f"TARGET={shlex.quote(remote_path)}; "
            "TMP=\"${TARGET}.wsta110-tmp.$$\"; "
            f"/bin/mkdir -p {shlex.quote(str(Path(remote_path).parent))}; "
            "/bin/rm -f \"$TMP\"; "
            "/bin/cat > \"$TMP\"; "
            f"/bin/chmod {shlex.quote(mode)} \"$TMP\"; "
            "/bin/mv -f \"$TMP\" \"$TARGET\"; "
            f"/usr/bin/test -f {shlex.quote(remote_path)}; "
            "echo A90WSTA110_FILE_STAGED"
        ),
    ]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    return {
        "command": command,
        "input_bytes": len(data),
        "returncode": completed.returncode,
        "elapsed_sec": round(time.monotonic() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "staged": completed.returncode == 0 and "A90WSTA110_FILE_STAGED" in stdout,
        "remote_path": remote_path,
        "mode": mode,
        "input_redacted": False,
    }


def account_line(identity: dict[str, Any]) -> str:
    return (
        f"{identity['user']}:x:{identity['uid']}:{identity['gid']}:"
        f"A90 service {identity['user']}:/nonexistent:/usr/sbin/nologin"
    )


def group_line(identity: dict[str, Any]) -> str:
    return f"{identity['group']}:x:{identity['gid']}:"


def service_identity_stage_script() -> str:
    lines = [
        "set -eu",
        "echo A90WSTA110_IDENTITY_STAGE_BEGIN",
        "/bin/mkdir -p /etc /etc/a90-dpublic",
        "touch /etc/passwd /etc/group",
        "ensure_account_line() {",
        "  file=$1",
        "  name=$2",
        "  expected=$3",
        "  if /bin/grep -q \"^${name}:\" \"$file\"; then",
        "    existing=$(/bin/grep \"^${name}:\" \"$file\" | /usr/bin/head -n 1)",
        "    if [ \"$existing\" != \"$expected\" ]; then",
        "      echo \"A90WSTA110_ACCOUNT_CONFLICT name=$name\"",
        "      exit 64",
        "    fi",
        "  else",
        "    /bin/printf '%s\\n' \"$expected\" >> \"$file\"",
        "  fi",
        "}",
    ]
    for identity in wsta3.SERVICE_IDENTITIES.values():
        lines.append(
            "ensure_account_line /etc/group "
            f"{shlex.quote(str(identity['group']))} {shlex.quote(group_line(identity))}"
        )
        lines.append(
            "ensure_account_line /etc/passwd "
            f"{shlex.quote(str(identity['user']))} {shlex.quote(account_line(identity))}"
        )
    marker_keys = "|".join(item.split("=", 1)[0] for item in wsta3.SERVICE_HARDENING_STAGE_MARKERS)
    lines.extend([
        "/bin/chmod 0644 /etc/passwd /etc/group",
        f"MARKER={shlex.quote(REMOTE_STAGE_MARKER)}",
        "TMP=\"${MARKER}.wsta110-tmp.$$\"",
        "/bin/mkdir -p \"$(/usr/bin/dirname \"$MARKER\")\"",
        f"if [ -f \"$MARKER\" ]; then /bin/grep -v -E '^({marker_keys})=' \"$MARKER\" > \"$TMP\" || true; else : > \"$TMP\"; fi",
    ])
    for marker in wsta3.SERVICE_HARDENING_STAGE_MARKERS:
        lines.append(f"/bin/printf '%s\\n' {shlex.quote(marker)} >> \"$TMP\"")
    lines.extend([
        "/bin/mv -f \"$TMP\" \"$MARKER\"",
        "/bin/chmod 0644 \"$MARKER\"",
        "echo A90WSTA110_IDENTITY_STAGE_DONE",
    ])
    return "\n".join(lines)


def stage_service_hardening_assets(args: argparse.Namespace, run_dir: Path) -> dict[str, Any]:
    launcher = write_remote_bytes(
        args,
        run_dir,
        REMOTE_SERVICE_LAUNCHER,
        wsta3.launcher_script().encode("utf-8"),
        mode="0755",
        timeout=args.ssh_timeout,
    )
    policy = write_remote_bytes(
        args,
        run_dir,
        REMOTE_SERVICE_POLICY,
        (json.dumps(service_policy_payload(), indent=2, sort_keys=True) + "\n").encode("utf-8"),
        mode="0644",
        timeout=args.ssh_timeout,
    )
    identities = wsta42.ssh_exec(
        args,
        run_dir,
        service_identity_stage_script(),
        timeout=args.ssh_timeout,
    )
    text = str(identities.get("stdout") or "")
    identities["staged"] = identities.get("returncode") == 0 and "A90WSTA110_IDENTITY_STAGE_DONE" in text
    return {
        "launcher": launcher,
        "policy": policy,
        "identities": identities,
        "secret_values_logged": 0,
    }


def launcher_probe_script() -> str:
    child_script = (
        "echo A90WSTA110_CHILD_BEGIN; "
        "echo child_uid=$(id -u); "
        "echo child_gid=$(id -g); "
        "echo child_user=$(id -un); "
        "echo child_group=$(id -gn); "
        "awk '/^NoNewPrivs:/{print \"child_no_new_privs=\" $2}' /proc/self/status; "
        "awk '/^CapEff:/{print \"child_cap_eff=\" $2}' /proc/self/status; "
        "echo A90WSTA110_CHILD_DONE"
    )
    return f"""
set -eu
echo A90WSTA110_PROOF_BEGIN
PROC_MOUNTED=0
cleanup_proc() {{
  if [ "$PROC_MOUNTED" = "1" ]; then
    /bin/umount /proc
    echo A90WSTA110_PROC_UNMOUNTED=1
    PROC_MOUNTED=0
  fi
}}
trap cleanup_proc EXIT
/bin/mkdir -p /proc
/bin/mount -t proc proc /proc
PROC_MOUNTED=1
echo A90WSTA110_PROC_MOUNTED=1
if [ ! -e /etc/a90-dpublic/cloudflared-quick-enable ]; then echo A90WSTA110_PUBLIC_ENABLE_ABSENT=1; else echo A90WSTA110_PUBLIC_ENABLE_ABSENT=0; exit 30; fi
[ -x {shlex.quote(REMOTE_SERVICE_LAUNCHER)} ] && echo A90WSTA110_LAUNCHER_PRESENT=1
[ -f {shlex.quote(REMOTE_SERVICE_POLICY)} ] && echo A90WSTA110_POLICY_PRESENT=1
if command -v setpriv >/dev/null 2>&1; then echo A90WSTA110_SETPRIV_PRESENT=1; else echo A90WSTA110_SETPRIV_PRESENT=0; exit 31; fi
set +e
UNKNOWN_OUT=$({shlex.quote(REMOTE_SERVICE_LAUNCHER)} not-a-service /bin/true 2>&1)
UNKNOWN_RC=$?
MISSING_OUT=$({shlex.quote(REMOTE_SERVICE_LAUNCHER)} dpublic-smoke-httpd 2>&1)
MISSING_RC=$?
set -e
echo "$UNKNOWN_OUT"
echo "$MISSING_OUT"
if [ "$UNKNOWN_RC" = "0" ]; then echo A90WSTA110_UNKNOWN_BLOCKED=0; exit 32; fi
case "$UNKNOWN_OUT" in *blocked-unknown-service*) echo A90WSTA110_UNKNOWN_BLOCKED=1;; *) echo A90WSTA110_UNKNOWN_BLOCKED=0; exit 33;; esac
if [ "$MISSING_RC" = "0" ]; then echo A90WSTA110_COMMAND_REQUIRED_BLOCKED=0; exit 34; fi
case "$MISSING_OUT" in *blocked-command-required*) echo A90WSTA110_COMMAND_REQUIRED_BLOCKED=1;; *) echo A90WSTA110_COMMAND_REQUIRED_BLOCKED=0; exit 35;; esac
{shlex.quote(REMOTE_SERVICE_LAUNCHER)} dpublic-smoke-httpd /bin/sh -c {shlex.quote(child_script)}
cleanup_proc
trap - EXIT
echo A90WSTA110_PROOF_DONE
""".strip()


def parse_launcher_probe(record: dict[str, Any]) -> dict[str, Any]:
    stdout = str(record.get("stdout") or "")
    return {
        "proof_begin": "A90WSTA110_PROOF_BEGIN" in stdout,
        "proof_done": "A90WSTA110_PROOF_DONE" in stdout,
        "proc_mounted": "A90WSTA110_PROC_MOUNTED=1" in stdout,
        "proc_unmounted": "A90WSTA110_PROC_UNMOUNTED=1" in stdout,
        "public_enable_absent": "A90WSTA110_PUBLIC_ENABLE_ABSENT=1" in stdout,
        "launcher_present": "A90WSTA110_LAUNCHER_PRESENT=1" in stdout,
        "policy_present": "A90WSTA110_POLICY_PRESENT=1" in stdout,
        "setpriv_present": "A90WSTA110_SETPRIV_PRESENT=1" in stdout,
        "unknown_service_blocks": "A90WSTA110_UNKNOWN_BLOCKED=1" in stdout,
        "command_required_blocks": "A90WSTA110_COMMAND_REQUIRED_BLOCKED=1" in stdout,
        "launcher_exec": "a90_service_launcher_decision=exec" in stdout,
        "launcher_service": "a90_service_launcher_service=dpublic-smoke-httpd" in stdout,
        "launcher_user": "a90_service_launcher_user=a90www" in stdout,
        "launcher_network_intent": "a90_service_launcher_network_intent=bind-loopback-127.0.0.1:8080-only" in stdout,
        "launcher_no_new_privs_marker": "a90_service_launcher_no_new_privs=1" in stdout,
        "child_begin": "A90WSTA110_CHILD_BEGIN" in stdout,
        "child_done": "A90WSTA110_CHILD_DONE" in stdout,
        "child_uid": "child_uid=3901" in stdout,
        "child_gid": "child_gid=3901" in stdout,
        "child_user": "child_user=a90www" in stdout,
        "child_group": "child_group=a90www" in stdout,
        "child_no_new_privs": "child_no_new_privs=1" in stdout,
        "secret_values_logged": 0,
    }


def run_launcher_probe(args: argparse.Namespace, run_dir: Path) -> dict[str, Any]:
    record = wsta42.ssh_exec(args, run_dir, launcher_probe_script(), timeout=args.launcher_timeout)
    record["parsed"] = parse_launcher_probe(record)
    return record


def service_probe_cleanup_script(mountpoint: str) -> str:
    proc = mountpoint.rstrip("/") + "/proc"
    return f"""
set +e
P={shlex.quote(proc)}
echo A90WSTA110_SERVICE_PROBE_CLEANUP_BEGIN
if /bin/busybox grep -q " $P " /proc/mounts; then
  /bin/busybox umount "$P" || /bin/busybox umount -l "$P"
fi
if /bin/busybox grep -q " $P " /proc/mounts; then echo A90WSTA110 proc_mount_absent=0; else echo A90WSTA110 proc_mount_absent=1; fi
echo A90WSTA110_SERVICE_PROBE_CLEANUP_DONE
""".strip()


def stage_ok(stage: dict[str, Any]) -> bool:
    return bool(
        stage.get("launcher", {}).get("staged")
        and stage.get("policy", {}).get("staged")
        and stage.get("identities", {}).get("staged")
    )


def chroot_cleanup_ok(result: dict[str, Any]) -> bool:
    return wsta94.chroot_cleanup_ok(result)


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_live_gate", "wsta110-blocked-explicit-live-gate"),
        ("local_image_present", "wsta110-blocked-local-image-missing"),
        ("baseline_selftest_fail_zero", "wsta110-blocked-baseline-selftest"),
        ("native_stale_cleanup_ok", "wsta110-blocked-native-stale-cleanup"),
        ("remote_image_ready", "wsta110-blocked-remote-image"),
        ("chroot_mount_ready", "wsta110-blocked-chroot-mount"),
        ("dropbear_started", "wsta110-blocked-dropbear-start"),
        ("debian_ssh_marker", "wsta110-blocked-debian-ssh"),
        ("service_hardening_assets_staged", "wsta110-blocked-service-hardening-stage"),
        ("public_default_off", "wsta110-blocked-public-default-off"),
        ("launcher_fail_closed_blocks", "wsta110-blocked-launcher-fail-closed"),
        ("launcher_exec_pass", "wsta110-blocked-launcher-exec"),
        ("launcher_uid_gid_pass", "wsta110-blocked-launcher-uid-gid"),
        ("launcher_no_new_privs_pass", "wsta110-blocked-launcher-no-new-privs"),
        ("chroot_cleanup_ok", "wsta110-blocked-chroot-cleanup"),
        ("final_selftest_fail_zero", "wsta110-blocked-final-selftest"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return decision
    return PASS_DECISION


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta110-service-launcher-chroot-proof-{ts}"
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / run_id)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / RESULT_NAME

    gate_ok, gate_decision = explicit_live_gate(args)
    result: dict[str, Any] = {
        "scope": "WSTA110 service launcher chroot live proof",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "gate_decision": gate_decision,
        "remote_image": args.remote_image,
        "remote_clean_image": args.remote_clean_image if wsta42.remote_clean_image_enabled(args) else None,
        "mountpoint": args.mountpoint,
        "safety": safety(gate_ok),
        "checks": {
            "explicit_live_gate": gate_ok,
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        },
    }
    write_json(out_path, result)
    if not gate_ok:
        result["decision"] = gate_decision
        return finish_result(out_path, result)

    local_image = args.local_image
    if not local_image.is_file():
        result["checks"]["local_image_present"] = False
        result["decision"] = classify(result)
        return finish_result(out_path, result)

    local_sha = sha256_file(local_image)
    result["local_image"] = rel(local_image)
    result["local_image_sha256"] = local_sha
    result["checks"]["local_image_present"] = True
    if args.local_image_sha256 and args.local_image_sha256 != local_sha:
        result["local_image_expected_sha256"] = args.local_image_sha256
        result["checks"]["remote_image_ready"] = False
        result["decision"] = "wsta110-blocked-local-image-sha"
        return finish_result(out_path, result)

    mounted = False
    try:
        result["bridge_status"] = wsta2.run_host([sys.executable, str(wsta2.BRIDGE), "status", "--json"], timeout=10.0)
        result["version"] = wsta19.try_cmdv1_retry(args, ["version"], timeout=args.timeout)
        result["status"] = wsta19.try_cmdv1_retry(args, ["status"], timeout=args.timeout)
        result["baseline_selftest"] = wsta19.try_cmdv1_retry(args, ["selftest"], timeout=args.timeout)
        result["checks"]["baseline_selftest_fail_zero"] = wsta2.selftest_passed(result["baseline_selftest"].get("text", ""))
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

        result["keygen"] = d2.generate_ssh_key(run_dir, run_id)
        public_key = d2.read_public_key(run_dir)
        write_json(out_path, result)

        mount_record = wsta19.bridge_shell(
            args,
            wsta94.wsta94_mount_script(args.remote_image, args.mountpoint, args.ssh_port),
            timeout=args.setup_timeout,
        )
        mounted = True
        result["mount"] = mount_record
        result["mount_parse"] = d2.parse_setup(str(mount_record.get("text") or ""))
        result["checks"]["chroot_mount_ready"] = bool(
            result["mount_parse"].get("mount_ready") and result["mount_parse"].get("mounted")
        )
        write_json(out_path, result)
        if not result["checks"]["chroot_mount_ready"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        start_record = wsta19.bridge_shell(
            args,
            wsta94.wsta94_start_dropbear_script(args.mountpoint, public_key, args.device_ip, args.ssh_port),
            timeout=args.setup_timeout,
            allow_error=True,
        )
        result["dropbear_start"] = start_record
        result["dropbear_parse"] = d2.parse_setup(str(start_record.get("text") or ""))
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

        result["service_hardening_stage"] = stage_service_hardening_assets(args, run_dir)
        result["checks"]["service_hardening_assets_staged"] = stage_ok(result["service_hardening_stage"])
        write_json(out_path, result)
        if not result["checks"]["service_hardening_assets_staged"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["launcher_probe"] = run_launcher_probe(args, run_dir)
        parsed = result["launcher_probe"].get("parsed", {})
        result["checks"].update({
            "public_default_off": bool(parsed.get("public_enable_absent")),
            "launcher_fail_closed_blocks": bool(
                parsed.get("unknown_service_blocks") and parsed.get("command_required_blocks")
            ),
            "launcher_exec_pass": bool(
                parsed.get("proof_done")
                and parsed.get("proc_mounted")
                and parsed.get("proc_unmounted")
                and parsed.get("launcher_exec")
                and parsed.get("launcher_service")
                and parsed.get("launcher_user")
                and parsed.get("launcher_network_intent")
                and parsed.get("launcher_no_new_privs_marker")
            ),
            "launcher_uid_gid_pass": bool(
                parsed.get("child_uid")
                and parsed.get("child_gid")
                and parsed.get("child_user")
                and parsed.get("child_group")
            ),
            "launcher_no_new_privs_pass": bool(parsed.get("child_no_new_privs")),
        })
        write_json(out_path, result)
    finally:
        if mounted:
            result["service_probe_cleanup"] = wsta19.bridge_shell(
                args,
                service_probe_cleanup_script(args.mountpoint),
                timeout=args.cleanup_timeout,
                allow_error=True,
            )
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
        else:
            result["cleanup"] = {"skipped": True, "reason": "chroot-not-mounted"}
            result["cleanup_parse"] = {}
            result["postcheck"] = {"skipped": True, "reason": "chroot-not-mounted"}
            result["postcheck_parse"] = {}

        result["final_version"] = wsta19.try_cmdv1_retry(args, ["version"], timeout=args.timeout)
        result["final_selftest"] = wsta19.try_cmdv1_retry(args, ["selftest"], timeout=args.timeout)
        result["checks"]["chroot_cleanup_ok"] = bool(not mounted or chroot_cleanup_ok(result))
        result["checks"]["final_selftest_fail_zero"] = wsta2.selftest_passed(result["final_selftest"].get("text", ""))
        write_json(out_path, result)

    result["decision"] = classify(result)
    return finish_result(out_path, result)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--device-ip", default="192.168.7.2")
    parser.add_argument("--ssh-port", type=int, default=2222)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--sha-timeout", type=float, default=180.0)
    parser.add_argument("--setup-timeout", type=float, default=180.0)
    parser.add_argument("--cleanup-timeout", type=float, default=120.0)
    parser.add_argument("--ssh-timeout", type=float, default=45.0)
    parser.add_argument("--launcher-timeout", type=float, default=45.0)
    parser.add_argument("--ssh-connect-timeout", type=int, default=8)
    parser.add_argument("--bridge-timeout", type=float, default=60.0)
    parser.add_argument("--connect-timeout", type=float, default=10.0)
    parser.add_argument("--tcp-timeout", type=float, default=30.0)
    parser.add_argument("--transfer-timeout", type=float, default=900.0)
    parser.add_argument("--transfer-delay", type=float, default=2.0)
    parser.add_argument("--toybox", default="/bin/toybox")
    parser.add_argument("--local-image", type=Path, default=d1.DEFAULT_LOCAL_IMAGE)
    parser.add_argument("--local-image-sha256", default=d1.EXPECTED_IMAGE_SHA256)
    parser.add_argument("--remote-image", default=d1.DEFAULT_REMOTE_IMAGE)
    parser.add_argument("--remote-clean-image", default=wsta42.DEFAULT_REMOTE_CLEAN_IMAGE)
    parser.add_argument("--mountpoint", default=d1.DEFAULT_MOUNTPOINT)
    parser.add_argument("--execute-service-launcher-chroot-live", action="store_true")
    parser.add_argument("--allow-service-launcher-live", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        ts = utc_stamp()
        run_dir = args.run_dir or (DEFAULT_RUN_BASE / (args.run_id or f"wsta110-service-launcher-chroot-proof-{ts}"))
        if not run_dir.is_absolute():
            run_dir = REPO_ROOT / run_dir
        run_dir.mkdir(parents=True, exist_ok=True)
        out_path = run_dir / RESULT_NAME
        if out_path.is_file():
            try:
                result = json.loads(out_path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                result = {
                    "scope": "WSTA110 service launcher chroot live proof",
                    "run_dir": rel(run_dir),
                }
        else:
            result = {
                "scope": "WSTA110 service launcher chroot live proof",
                "run_dir": rel(run_dir),
            }
        result["decision"] = "wsta110-runner-error"
        result["error"] = str(exc)
        finish_result(out_path, result)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
