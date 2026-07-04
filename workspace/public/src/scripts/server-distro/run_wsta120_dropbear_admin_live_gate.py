#!/usr/bin/env python3
"""Run WSTA120: bounded Dropbear admin user live gate.

WSTA119 defines the source model.  WSTA120 applies that model to the SD-backed
Debian work image without using the temporary root-authorized-keys SSH path:

  * prepare and mount the known Debian work image through native init;
  * stage ``a90admin`` key-only login in the mounted rootfs;
  * start Dropbear with password/root login and forwarding disabled;
  * prove SSH as ``a90admin`` reaches UID/GID 3903;
  * prove root SSH is rejected;
  * clean Dropbear/admin key material and chroot/loop state.

No boot image is built or flashed.  No Wi-Fi association, DHCP, public tunnel,
public smoke, packet-filter mutation, userdata write, native reboot, or
switch-root is performed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
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

import run_d1_chroot_mvp as d1  # noqa: E402
import run_d2_ssh_in_chroot as d2  # noqa: E402
import run_wsta19_native_owned_chroot_wifi as wsta19  # noqa: E402
import run_wsta2_native_materialization as wsta2  # noqa: E402
import run_wsta42_native_uplink_dpublic_tunnel as wsta42  # noqa: E402
import run_wsta94_packet_filter_live_gate as wsta94  # noqa: E402
import run_wsta119_dropbear_admin_model as wsta119  # noqa: E402


REPO_ROOT = wsta2.REPO_ROOT
DEFAULT_RUN_BASE = wsta2.DEFAULT_RUN_BASE
PASS_DECISION = "wsta120-dropbear-admin-live-pass"
RESULT_NAME = "wsta120_result.json"
REMOTE_ADMIN_STAGE_SCRIPT = "/mnt/sdext/a90/runtime/a90_wsta120_admin_stage.sh"


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
    if not args.execute_dropbear_admin_live:
        return False, "wsta120-blocked-dropbear-admin-live-required"
    if not args.allow_dropbear_admin_live:
        return False, "wsta120-blocked-dropbear-admin-live-allow-required"
    if not args.ack_admin_key_material:
        return False, "wsta120-blocked-admin-key-material-ack-required"
    if not args.ack_root_login_negative_test:
        return False, "wsta120-blocked-root-login-negative-test-ack-required"
    return True, "ok"


def install_remote_file(args: argparse.Namespace,
                        local_path: Path,
                        remote_path: str,
                        *,
                        timeout: float) -> dict[str, Any]:
    tcpctl_host = REVAL_DIR / "tcpctl_host.py"
    command = [
        sys.executable,
        str(tcpctl_host),
        "--bridge-host",
        args.bridge_host,
        "--bridge-port",
        str(args.bridge_port),
        "--device-ip",
        args.device_ip,
        "--bridge-timeout",
        str(args.bridge_timeout),
        "--connect-timeout",
        str(args.connect_timeout),
        "--tcp-timeout",
        str(args.tcp_timeout),
        "--toybox",
        args.toybox,
        "--device-binary",
        remote_path,
        "install",
        "--local-binary",
        str(local_path),
        "--transfer-timeout",
        str(args.transfer_timeout),
        "--transfer-delay",
        str(args.transfer_delay),
        "--install-control-channel",
        "bridge",
    ]
    env = os.environ.copy()
    env.setdefault("PYTHONPYCACHEPREFIX", "/tmp/a90_pycache")
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=env,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "elapsed_sec": round(time.monotonic() - started, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "local_path": rel(local_path),
        "remote_path": remote_path,
        "local_sha256": sha256_file(local_path),
        "installed": completed.returncode == 0,
        "secret_values_logged": 0,
    }


def bridge_run_script_file(args: argparse.Namespace,
                           remote_path: str,
                           *,
                           timeout: float,
                           allow_error: bool = False) -> dict[str, Any]:
    return d1.run_cmd(
        args.bridge_host,
        args.bridge_port,
        timeout,
        ["run", "/bin/busybox", "sh", remote_path],
        retry_unsafe=True,
        allow_error=allow_error,
    )


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
        "admin_key_material": "explicit-live-gated-private-run-key" if gate_ok else False,
        "root_login_negative_test": gate_ok,
        "public_url_value_logged": False,
        "admin_public_key_value_logged": False,
        "secret_values_logged": 0,
    }


def admin_shadow_line() -> str:
    return "a90admin:*:19700:0:99999:7:::"


def admin_native_stage_and_start_script(mountpoint: str,
                                        public_key: str,
                                        bind_ip: str,
                                        port: int) -> str:
    command = " ".join(wsta119.dropbear_command(bind_ip, port))
    return f"""
set -eu
M={d2.shell_quote(mountpoint)}
B={d2.shell_quote(f"{bind_ip}:{port}")}
PUBKEY={d2.shell_quote(public_key)}
ADMIN_USER=a90admin
ADMIN_GROUP=a90admin
ADMIN_UID=3903
ADMIN_GID=3903
ADMIN_HOME=/home/a90admin
ADMIN_KEYS=/home/a90admin/.ssh/authorized_keys
ROOT_KEYS=/root/.ssh/authorized_keys
PASSWD_LINE={d2.shell_quote(wsta119.admin_passwd_line())}
PLACEHOLDER_LINE={d2.shell_quote(wsta119.admin_placeholder_passwd_line())}
GROUP_LINE={d2.shell_quote(wsta119.admin_group_line())}
SHADOW_LINE={d2.shell_quote(admin_shadow_line())}
HOSTKEY=/tmp/a90_dropbear_admin_hostkey
PIDFILE=/tmp/a90_dropbear_admin.pid
LOG=/tmp/a90_dropbear_admin.log
echo A90WSTA120_ADMIN_STAGE_BEGIN
/bin/busybox grep -q " $M " /proc/mounts
replace_or_append_line() {{
  file=$1
  name=$2
  expected=$3
  placeholder=$4
  /bin/busybox touch "$file"
  if /bin/busybox grep -q "^${{name}}:" "$file"; then
    existing=$(/bin/busybox grep "^${{name}}:" "$file" | /bin/busybox head -n 1)
    if [ "$existing" = "$expected" ]; then
      return 0
    fi
    if [ "$existing" = "$placeholder" ]; then
      /bin/busybox grep -v "^${{name}}:" "$file" > "$file.wsta120"
      /bin/busybox printf '%s\\n' "$expected" >> "$file.wsta120"
      /bin/busybox mv -f "$file.wsta120" "$file"
      return 0
    fi
    echo "A90WSTA120_ACCOUNT_CONFLICT name=$name"
    exit 64
  fi
  /bin/busybox printf '%s\\n' "$expected" >> "$file"
}}
/bin/busybox mkdir -p "$M/etc" "$M$ADMIN_HOME/.ssh" "$M/root/.ssh" "$M/tmp"
/bin/busybox touch "$M/etc/shadow"
/bin/busybox cp "$M/etc/shadow" "$M/tmp/a90_d2_shadow.bak"
replace_or_append_line "$M/etc/group" "$ADMIN_GROUP" "$GROUP_LINE" "$GROUP_LINE"
replace_or_append_line "$M/etc/passwd" "$ADMIN_USER" "$PASSWD_LINE" "$PLACEHOLDER_LINE"
replace_or_append_line "$M/etc/shadow" "$ADMIN_USER" "$SHADOW_LINE" "$SHADOW_LINE"
/bin/busybox chmod 0644 "$M/etc/passwd" "$M/etc/group"
/bin/busybox chmod 0600 "$M/etc/shadow"
/bin/busybox chown "$ADMIN_UID:$ADMIN_GID" "$M$ADMIN_HOME" "$M$ADMIN_HOME/.ssh"
/bin/busybox chmod 0700 "$M$ADMIN_HOME" "$M$ADMIN_HOME/.ssh"
/bin/busybox printf '%s\\n' "$PUBKEY" > "$M$ADMIN_KEYS"
/bin/busybox chown "$ADMIN_UID:$ADMIN_GID" "$M$ADMIN_KEYS"
/bin/busybox chmod 0600 "$M$ADMIN_KEYS"
/bin/busybox rm -f "$M$ROOT_KEYS" "$M$HOSTKEY" "$M$PIDFILE" "$M$LOG"
if [ -e "$M$ROOT_KEYS" ]; then echo A90WSTA120_ROOT_AUTHORIZED_KEYS_ABSENT=0; exit 65; else echo A90WSTA120_ROOT_AUTHORIZED_KEYS_ABSENT=1; fi
if /bin/busybox grep -Fqx "$PASSWD_LINE" "$M/etc/passwd"; then echo A90WSTA120_ADMIN_PASSWD_LINE=1; else echo A90WSTA120_ADMIN_PASSWD_LINE=0; exit 66; fi
if /bin/busybox grep -Fqx "$GROUP_LINE" "$M/etc/group"; then echo A90WSTA120_ADMIN_GROUP_LINE=1; else echo A90WSTA120_ADMIN_GROUP_LINE=0; exit 67; fi
if /bin/busybox grep -Fqx "$SHADOW_LINE" "$M/etc/shadow"; then echo A90WSTA120_ADMIN_SHADOW_LINE=1; else echo A90WSTA120_ADMIN_SHADOW_LINE=0; exit 68; fi
[ -s "$M$ADMIN_KEYS" ] && echo A90WSTA120_ADMIN_AUTHORIZED_KEYS=1 || {{ echo A90WSTA120_ADMIN_AUTHORIZED_KEYS=0; exit 69; }}
[ -x "$M/usr/sbin/dropbear" ] && echo A90WSTA120_DROPBEAR_PRESENT=1 || {{ echo A90WSTA120_DROPBEAR_PRESENT=0; exit 70; }}
if /bin/busybox chroot "$M" /usr/bin/dropbearkey -t ed25519 -f "$HOSTKEY" >/tmp/a90_wsta120_dropbearkey.log 2>&1; then
  echo A90WSTA120_HOSTKEY_TYPE=ed25519
else
  /bin/busybox chroot "$M" /usr/bin/dropbearkey -t rsa -s 2048 -f "$HOSTKEY" >/tmp/a90_wsta120_dropbearkey.log 2>&1
  echo A90WSTA120_HOSTKEY_TYPE=rsa
fi
echo A90WSTA120_DROPBEAR_COMMAND={d2.shell_quote(command)}
/bin/busybox chroot "$M" /usr/sbin/dropbear -F -E -r "$HOSTKEY" -p "$B" -P "$PIDFILE" -s -w -j -k </dev/null >"$M$LOG" 2>&1 &
PID=$!
/bin/busybox printf '%s\\n' "$PID" > "$M$PIDFILE"
/bin/busybox sleep 1
if ! /bin/busybox kill -0 "$PID" >/dev/null 2>&1; then
  echo A90WSTA120_DROPBEAR_ALIVE=0
  /bin/busybox tail -n 8 "$M$LOG" 2>/dev/null || true
  exit 71
fi
echo A90WSTA120_DROPBEAR_ALIVE=1
if /bin/busybox netstat -ltn 2>/dev/null | /bin/busybox grep -q ":{port} "; then echo A90WSTA120_DROPBEAR_LISTEN=1; else echo A90WSTA120_DROPBEAR_LISTEN=0; /bin/busybox tail -n 8 "$M$LOG" 2>/dev/null || true; exit 72; fi
echo A90WSTA120_ADMIN_STAGE_DONE
""".strip()


def parse_stage(record: dict[str, Any]) -> dict[str, bool]:
    text = str(record.get("text") or "")
    return {
        "stage_begin": "A90WSTA120_ADMIN_STAGE_BEGIN" in text,
        "stage_done": "A90WSTA120_ADMIN_STAGE_DONE" in text,
        "root_authorized_keys_absent": "A90WSTA120_ROOT_AUTHORIZED_KEYS_ABSENT=1" in text,
        "admin_passwd_line": "A90WSTA120_ADMIN_PASSWD_LINE=1" in text,
        "admin_group_line": "A90WSTA120_ADMIN_GROUP_LINE=1" in text,
        "admin_shadow_line": "A90WSTA120_ADMIN_SHADOW_LINE=1" in text,
        "admin_authorized_keys": "A90WSTA120_ADMIN_AUTHORIZED_KEYS=1" in text,
        "dropbear_present": "A90WSTA120_DROPBEAR_PRESENT=1" in text,
        "dropbear_key_generated": "A90WSTA120_HOSTKEY_TYPE=" in text,
        "dropbear_command_safe": " -s -w -j -k" in text,
        "dropbear_alive": "A90WSTA120_DROPBEAR_ALIVE=1" in text,
        "dropbear_listen": "A90WSTA120_DROPBEAR_LISTEN=1" in text,
        "secret_values_logged": False,
    }


def ssh_command(args: argparse.Namespace, run_dir: Path, user: str) -> list[str]:
    key_path = run_dir / "d2_ssh_key_ed25519"
    known_hosts = run_dir / "wsta120_known_hosts"
    return [
        "ssh",
        "-i",
        str(key_path),
        "-p",
        str(args.ssh_port),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
        "-o",
        f"ConnectTimeout={args.ssh_connect_timeout}",
        "-o",
        "PreferredAuthentications=publickey",
        f"{user}@{args.device_ip}",
    ]


def ssh_probe(args: argparse.Namespace,
              run_dir: Path,
              user: str,
              remote_command: str,
              *,
              timeout: float) -> dict[str, Any]:
    command = [*ssh_command(args, run_dir, user), remote_command]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "elapsed_sec": round(time.monotonic() - started, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "user": user,
        "secret_values_logged": 0,
    }


def parse_admin_ssh(record: dict[str, Any]) -> dict[str, bool]:
    stdout = str(record.get("stdout") or "")
    return {
        "ssh_ok": record.get("returncode") == 0,
        "uid_3903": "A90WSTA120_ADMIN_UID=3903" in stdout,
        "gid_3903": "A90WSTA120_ADMIN_GID=3903" in stdout,
        "user_a90admin": "A90WSTA120_ADMIN_USER=a90admin" in stdout,
        "group_a90admin": "A90WSTA120_ADMIN_GROUP=a90admin" in stdout,
        "secret_values_logged": False,
    }


def admin_key_cleanup_script(mountpoint: str) -> str:
    return f"""
set +e
M={d2.shell_quote(mountpoint)}
echo A90WSTA120_ADMIN_CLEANUP_BEGIN
for i in 1 2 3 4 5; do
  for p in $(/bin/busybox pidof dropbear 2>/dev/null); do /bin/busybox kill "$p" >/dev/null 2>&1 || true; done
  /bin/busybox sleep 1
  if ! /bin/busybox pidof dropbear >/dev/null 2>&1; then break; fi
  for p in $(/bin/busybox pidof dropbear 2>/dev/null); do /bin/busybox kill -9 "$p" >/dev/null 2>&1 || true; done
  /bin/busybox sleep 1
  if ! /bin/busybox pidof dropbear >/dev/null 2>&1; then break; fi
done
/bin/busybox rm -f "$M/home/a90admin/.ssh/authorized_keys" "$M/tmp/a90_dropbear_admin_hostkey" "$M/tmp/a90_dropbear_admin.pid" "$M/tmp/a90_dropbear_admin.log"
/bin/busybox rm -f {d2.shell_quote(REMOTE_ADMIN_STAGE_SCRIPT)}
if [ -e "$M/home/a90admin/.ssh/authorized_keys" ]; then echo A90WSTA120 admin_keys_absent=0; else echo A90WSTA120 admin_keys_absent=1; fi
if /bin/busybox pidof dropbear >/dev/null 2>&1; then echo A90WSTA120 dropbear_absent=0; else echo A90WSTA120 dropbear_absent=1; fi
echo A90WSTA120_ADMIN_CLEANUP_DONE
""".strip()


def parse_admin_cleanup(record: dict[str, Any]) -> dict[str, bool]:
    text = str(record.get("text") or "")
    return {
        "cleanup_begin": "A90WSTA120_ADMIN_CLEANUP_BEGIN" in text,
        "cleanup_done": "A90WSTA120_ADMIN_CLEANUP_DONE" in text,
        "admin_keys_absent": "A90WSTA120 admin_keys_absent=1" in text,
        "dropbear_absent": "A90WSTA120 dropbear_absent=1" in text,
    }


def admin_key_cleanup_ok(result: dict[str, Any]) -> bool:
    cleanup = result.get("admin_key_cleanup_parse", {})
    return bool(cleanup.get("cleanup_done") and cleanup.get("admin_keys_absent"))


def chroot_cleanup_ok(result: dict[str, Any]) -> bool:
    cleanup = result.get("cleanup_parse", {})
    postcheck = result.get("postcheck_parse", {})
    return bool(
        cleanup.get("shadow_restored")
        and cleanup.get("mount_cleanup_ok")
        and cleanup.get("loop_cleanup_ok")
        and postcheck.get("mount_absent")
        and postcheck.get("loop_node_absent")
        and postcheck.get("dropbear_absent")
    )


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_live_gate", "wsta120-blocked-explicit-live-gate"),
        ("local_image_present", "wsta120-blocked-local-image-missing"),
        ("baseline_selftest_fail_zero", "wsta120-blocked-baseline-selftest"),
        ("native_stale_cleanup_ok", "wsta120-blocked-native-stale-cleanup"),
        ("remote_image_ready", "wsta120-blocked-remote-image"),
        ("admin_stage_script_uploaded", "wsta120-blocked-admin-stage-script-upload"),
        ("chroot_mount_ready", "wsta120-blocked-chroot-mount"),
        ("admin_stage_pass", "wsta120-blocked-admin-stage"),
        ("admin_ssh_pass", "wsta120-blocked-admin-ssh"),
        ("root_ssh_rejected", "wsta120-blocked-root-ssh-not-rejected"),
        ("admin_key_cleanup_ok", "wsta120-blocked-admin-key-cleanup"),
        ("chroot_cleanup_ok", "wsta120-blocked-chroot-cleanup"),
        ("final_selftest_fail_zero", "wsta120-blocked-final-selftest"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return decision
    return PASS_DECISION


def run(args: argparse.Namespace) -> dict[str, Any]:
    ts = utc_stamp()
    run_id = args.run_id or f"wsta120-dropbear-admin-live-{ts}"
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / run_id)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / RESULT_NAME

    gate_ok, gate_decision = explicit_live_gate(args)
    result: dict[str, Any] = {
        "scope": "WSTA120 Dropbear admin user live gate",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "gate_decision": gate_decision,
        "admin_model": wsta119.dropbear_admin_model(args.device_ip, args.ssh_port),
        "remote_image": args.remote_image,
        "remote_clean_image": args.remote_clean_image if wsta42.remote_clean_image_enabled(args) else None,
        "mountpoint": args.mountpoint,
        "safety": safety(gate_ok),
        "checks": {
            "explicit_live_gate": gate_ok,
            "public_url_value_logged": False,
            "admin_public_key_value_logged": False,
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
        result["decision"] = "wsta120-blocked-local-image-sha"
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
        stage_script_path = run_dir / "wsta120_admin_stage.sh"
        stage_script_path.write_text(
            admin_native_stage_and_start_script(args.mountpoint, public_key, args.device_ip, args.ssh_port) + "\n",
            encoding="utf-8",
        )
        stage_script_path.chmod(0o700)
        result["admin_stage_script_upload"] = install_remote_file(
            args,
            stage_script_path,
            REMOTE_ADMIN_STAGE_SCRIPT,
            timeout=args.transfer_timeout + args.bridge_timeout + 120.0,
        )
        result["checks"]["admin_stage_script_uploaded"] = bool(
            result["admin_stage_script_upload"].get("installed")
        )
        write_json(out_path, result)
        if not result["checks"]["admin_stage_script_uploaded"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

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

        stage_record = bridge_run_script_file(
            args,
            REMOTE_ADMIN_STAGE_SCRIPT,
            timeout=args.setup_timeout,
            allow_error=True,
        )
        result["admin_stage"] = stage_record
        result["admin_stage_parse"] = parse_stage(stage_record)
        stage = result["admin_stage_parse"]
        result["checks"]["admin_stage_pass"] = bool(
            stage.get("stage_done")
            and stage.get("root_authorized_keys_absent")
            and stage.get("admin_passwd_line")
            and stage.get("admin_group_line")
            and stage.get("admin_shadow_line")
            and stage.get("admin_authorized_keys")
            and stage.get("dropbear_present")
            and stage.get("dropbear_key_generated")
            and stage.get("dropbear_command_safe")
            and stage.get("dropbear_alive")
            and stage.get("dropbear_listen")
        )
        write_json(out_path, result)
        if not result["checks"]["admin_stage_pass"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        admin_cmd = (
            "echo A90WSTA120_ADMIN_UID=$(id -u); "
            "echo A90WSTA120_ADMIN_GID=$(id -g); "
            "echo A90WSTA120_ADMIN_USER=$(id -un); "
            "echo A90WSTA120_ADMIN_GROUP=$(id -gn)"
        )
        result["admin_ssh"] = ssh_probe(args, run_dir, "a90admin", admin_cmd, timeout=args.ssh_timeout)
        result["admin_ssh_parse"] = parse_admin_ssh(result["admin_ssh"])
        admin = result["admin_ssh_parse"]
        result["checks"]["admin_ssh_pass"] = bool(
            admin.get("ssh_ok")
            and admin.get("uid_3903")
            and admin.get("gid_3903")
            and admin.get("user_a90admin")
            and admin.get("group_a90admin")
        )
        write_json(out_path, result)
        if not result["checks"]["admin_ssh_pass"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["root_ssh"] = ssh_probe(args, run_dir, "root", "id -u", timeout=args.ssh_timeout)
        result["checks"]["root_ssh_rejected"] = result["root_ssh"].get("returncode") != 0
        write_json(out_path, result)
    finally:
        if mounted:
            result["admin_key_cleanup"] = wsta19.bridge_shell(
                args,
                admin_key_cleanup_script(args.mountpoint),
                timeout=args.cleanup_timeout,
                allow_error=True,
            )
            result["admin_key_cleanup_parse"] = parse_admin_cleanup(result["admin_key_cleanup"])
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
            result["admin_key_cleanup"] = {"skipped": True, "reason": "chroot-not-mounted"}
            result["admin_key_cleanup_parse"] = {}
            result["cleanup"] = {"skipped": True, "reason": "chroot-not-mounted"}
            result["cleanup_parse"] = {}
            result["postcheck"] = {"skipped": True, "reason": "chroot-not-mounted"}
            result["postcheck_parse"] = {}

        result["checks"]["admin_key_cleanup_ok"] = bool(not mounted or admin_key_cleanup_ok(result))
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
    parser.add_argument("--execute-dropbear-admin-live", action="store_true")
    parser.add_argument("--allow-dropbear-admin-live", action="store_true")
    parser.add_argument("--ack-admin-key-material", action="store_true")
    parser.add_argument("--ack-root-login-negative-test", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        ts = utc_stamp()
        run_dir = args.run_dir or (DEFAULT_RUN_BASE / (args.run_id or f"wsta120-dropbear-admin-live-{ts}"))
        if not run_dir.is_absolute():
            run_dir = REPO_ROOT / run_dir
        run_dir.mkdir(parents=True, exist_ok=True)
        out_path = run_dir / RESULT_NAME
        if out_path.is_file():
            try:
                result = json.loads(out_path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                result = {"scope": "WSTA120 Dropbear admin user live gate", "run_dir": rel(run_dir)}
        else:
            result = {"scope": "WSTA120 Dropbear admin user live gate", "run_dir": rel(run_dir)}
        result["decision"] = "wsta120-runner-error"
        result["error"] = str(exc)
        finish_result(out_path, result)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


if __name__ == "__main__":
    raise SystemExit(main_with_args())
