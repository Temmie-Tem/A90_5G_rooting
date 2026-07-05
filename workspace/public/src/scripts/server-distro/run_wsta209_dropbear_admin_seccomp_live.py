#!/usr/bin/env python3
"""WSTA209: run Dropbear admin USB under real seccomp enforcement.

This live gate extends WSTA208 from the loopback smoke service to the
root-boundary Dropbear admin daemon:

  * build a fresh WSTA161 loader helper with exec-after-load support;
  * stage WSTA153/WSTA156/WSTA161 assets into the mounted Debian work image;
  * stage the WSTA120 ``a90admin`` key-only account model;
  * start Dropbear through the seccomp loader helper as
    ``dropbear-admin-usb``;
  * prove ``a90admin`` SSH reaches UID/GID 3903 and root SSH is rejected.

No boot image is built or flashed.  No native reboot, Wi-Fi association, DHCP,
public tunnel, public smoke, packet-filter mutation, userdata write, or
switch-root is performed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
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
import run_wsta119_dropbear_admin_model as wsta119  # noqa: E402
import run_wsta120_dropbear_admin_live_gate as wsta120  # noqa: E402
import run_wsta149_dpublic_hud_intent_syscall_trace as wsta149  # noqa: E402
import run_wsta160_seccomp_full_rootfs_chroot_dry_run as wsta160  # noqa: E402
import run_wsta161_seccomp_loader_gated_apply_helper as wsta161  # noqa: E402
import run_wsta193_seccomp_correct_token_canary_source as wsta193  # noqa: E402
import run_wsta196_seccomp_load_canary_execute as wsta196  # noqa: E402
import run_wsta208_real_service_seccomp_smoke_live as wsta208  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
DEFAULT_LOCAL_IMAGE = wsta149.WSTA115_STRACE_IMAGE
DEFAULT_REMOTE_CLEAN_IMAGE = wsta42.DEFAULT_REMOTE_CLEAN_IMAGE
DEFAULT_WSTA153_POLICY = wsta160.DEFAULT_WSTA153_POLICY
DEFAULT_WSTA156_MANIFEST = wsta160.DEFAULT_WSTA156_MANIFEST
DEFAULT_WSTA156_OBJECT = wsta160.DEFAULT_WSTA156_OBJECT
PASS_DECISION = "wsta209-dropbear-admin-seccomp-live-pass"
RESULT_NAME = "wsta209_result.json"
REMOTE_STAGE_SCRIPT = "/mnt/sdext/a90/runtime/a90_wsta209_dropbear_admin_seccomp_stage.sh"
REMOTE_ASSET_DIR = "/mnt/sdext/a90/runtime/wsta209-seccomp-assets"
REMOTE_POLICY = REMOTE_ASSET_DIR + "/seccomp-policy.json"
REMOTE_FILTER_MANIFEST = REMOTE_ASSET_DIR + "/seccomp-filter-manifest.json"
REMOTE_FILTER_OBJECT = REMOTE_ASSET_DIR + "/wsta156_seccomp_filters.o"
REMOTE_LOADER_MANIFEST = REMOTE_ASSET_DIR + "/seccomp-loader-helper-manifest.json"
REMOTE_LOADER_HELPER = REMOTE_ASSET_DIR + "/a90-seccomp-loader-gated-apply"
REMOTE_LOAD_TOKEN = REMOTE_ASSET_DIR + "/load-token"
FORBIDDEN_TOKEN_PREFIX = "WSTA161-" + "EXPLICIT"


ACK_FLAGS = [
    "--execute-dropbear-admin-seccomp-live",
    "--allow-correct-wsta161-token",
    "--ack-seccomp-load-risk",
    "--ack-root-boundary-daemon",
    "--ack-admin-key-material",
    "--ack-root-login-negative-test",
    "--ack-no-flash-no-reboot",
    "--ack-cleanup-required",
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
    if not args.execute_dropbear_admin_seccomp_live:
        return False, "wsta209-blocked-dropbear-admin-seccomp-live-required"
    if not args.allow_correct_wsta161_token:
        return False, "wsta209-blocked-correct-token-allow-required"
    if not args.ack_seccomp_load_risk:
        return False, "wsta209-blocked-seccomp-load-risk-ack-required"
    if not args.ack_root_boundary_daemon:
        return False, "wsta209-blocked-root-boundary-daemon-ack-required"
    if not args.ack_admin_key_material:
        return False, "wsta209-blocked-admin-key-material-ack-required"
    if not args.ack_root_login_negative_test:
        return False, "wsta209-blocked-root-login-negative-test-ack-required"
    if not args.ack_no_flash_no_reboot:
        return False, "wsta209-blocked-no-flash-no-reboot-ack-required"
    if not args.ack_cleanup_required:
        return False, "wsta209-blocked-cleanup-ack-required"
    return True, "ok"


def safety_flags(gate_ok: bool) -> dict[str, Any]:
    return {
        "device_action": gate_ok,
        "device_action_description": (
            "single-service-seccomp-load-enforce-dropbear-admin-usb-over-bridge-and-usb-ssh"
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
        "rootfs_chroot_mutation": "explicit-live-gated-sd-work-image-only" if gate_ok else False,
        "admin_key_material": "explicit-live-gated-private-run-key" if gate_ok else False,
        "root_boundary_daemon": "dropbear-admin-usb" if gate_ok else False,
        "root_login_negative_test": gate_ok,
        "fresh_native_health_checked": False,
        "post_run_native_health_checked": False,
        "live_command_executed": False,
        "correct_wsta161_token_supplied": False,
        "token_staged_private_runtime_file": False,
        "seccomp_assets_staged": False,
        "seccomp_filter_loaded": False,
        "seccomp_enforced": False,
        "service_functional_under_seccomp": False,
        "admin_public_key_value_logged": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def private_token_status() -> dict[str, bool]:
    value = os.environ.get(wsta193.PRIVATE_TOKEN_ENV)
    return {
        "private_token_env_present": value is not None,
        "private_token_matches_wsta161": value == wsta161.LOAD_TOKEN,
    }


def helper_result_ok(result: dict[str, Any]) -> bool:
    return wsta208.exec_loader_helper_ok(result)


def build_exec_loader_helper(args: argparse.Namespace, run_dir: Path) -> dict[str, Any]:
    return wsta208.build_exec_loader_helper(args, run_dir)


def seccomp_asset_paths(args: argparse.Namespace, helper_result: dict[str, Any]) -> dict[str, Path]:
    artifact = helper_result.get("artifact") if isinstance(helper_result.get("artifact"), dict) else {}
    return {
        "policy": resolve_path(args.wsta153_seccomp_policy_json),
        "filter_manifest": resolve_path(args.wsta156_filter_manifest_json),
        "filter_object": resolve_path(args.wsta156_filter_object),
        "loader_manifest": resolve_path(artifact.get("manifest") or ""),
        "loader_helper": resolve_path(artifact.get("helper_binary") or ""),
    }


def validate_seccomp_asset_inputs(paths: dict[str, Path]) -> dict[str, bool]:
    return wsta208.validate_seccomp_asset_inputs(paths)


def write_private_token_file(run_dir: Path) -> Path:
    path = run_dir / "wsta209_load_token.private"
    path.write_text(wsta161.LOAD_TOKEN, encoding="utf-8")
    path.chmod(0o600)
    return path


def install_file(args: argparse.Namespace,
                 local_path: Path,
                 remote_path: str,
                 *,
                 timeout: float) -> dict[str, Any]:
    return wsta120.install_remote_file(args, local_path, remote_path, timeout=timeout)


def install_seccomp_assets(args: argparse.Namespace,
                           run_dir: Path,
                           paths: dict[str, Path],
                           token_path: Path) -> dict[str, Any]:
    timeout = args.transfer_timeout + args.bridge_timeout + 120.0
    records = {
        "policy": install_file(args, paths["policy"], REMOTE_POLICY, timeout=timeout),
        "filter_manifest": install_file(args, paths["filter_manifest"], REMOTE_FILTER_MANIFEST, timeout=timeout),
        "filter_object": install_file(args, paths["filter_object"], REMOTE_FILTER_OBJECT, timeout=timeout),
        "loader_manifest": install_file(args, paths["loader_manifest"], REMOTE_LOADER_MANIFEST, timeout=timeout),
        "loader_helper": install_file(args, paths["loader_helper"], REMOTE_LOADER_HELPER, timeout=timeout),
        "load_token": install_file(args, token_path, REMOTE_LOAD_TOKEN, timeout=timeout),
    }
    records["installed"] = all(bool(item.get("installed")) for item in records.values() if isinstance(item, dict))
    records["token_input_redacted"] = True
    records["secret_values_logged"] = 0
    return records


def dropbear_seccomp_stage_script(mountpoint: str,
                                  public_key: str,
                                  bind_ip: str,
                                  port: int) -> str:
    command = " ".join(wsta119.dropbear_command(bind_ip, port))
    return f"""
set -eu
M={d2.shell_quote(mountpoint)}
B={d2.shell_quote(f"{bind_ip}:{port}")}
PUBKEY={d2.shell_quote(public_key)}
ASSET_DIR={d2.shell_quote(REMOTE_ASSET_DIR)}
POLICY_SRC={d2.shell_quote(REMOTE_POLICY)}
FILTER_MANIFEST_SRC={d2.shell_quote(REMOTE_FILTER_MANIFEST)}
FILTER_OBJECT_SRC={d2.shell_quote(REMOTE_FILTER_OBJECT)}
LOADER_MANIFEST_SRC={d2.shell_quote(REMOTE_LOADER_MANIFEST)}
LOADER_HELPER_SRC={d2.shell_quote(REMOTE_LOADER_HELPER)}
TOKEN_FILE={d2.shell_quote(REMOTE_LOAD_TOKEN)}
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
SHADOW_LINE={d2.shell_quote(wsta120.admin_shadow_line())}
HOSTKEY=/tmp/a90_dropbear_admin_hostkey
PIDFILE=/tmp/a90_dropbear_admin.pid
LOG=/tmp/a90_dropbear_admin.log
HELPER=/{wsta3.TARGET_SECCOMP_LOADER_HELPER}
echo A90WSTA209_ADMIN_SECCOMP_STAGE_BEGIN
/bin/busybox grep -q " $M " /proc/mounts
for src in "$POLICY_SRC" "$FILTER_MANIFEST_SRC" "$FILTER_OBJECT_SRC" "$LOADER_MANIFEST_SRC" "$LOADER_HELPER_SRC" "$TOKEN_FILE"; do
  [ -s "$src" ] || {{ echo A90WSTA209_ASSET_PRESENT=0; exit 61; }}
done
echo A90WSTA209_ASSET_PRESENT=1
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
      /bin/busybox grep -v "^${{name}}:" "$file" > "$file.wsta209"
      /bin/busybox printf '%s\\n' "$expected" >> "$file.wsta209"
      /bin/busybox mv -f "$file.wsta209" "$file"
      return 0
    fi
    echo "A90WSTA209_ACCOUNT_CONFLICT name=$name"
    exit 64
  fi
  /bin/busybox printf '%s\\n' "$expected" >> "$file"
}}
/bin/busybox mkdir -p "$M/etc/a90-dpublic" "$M/usr/lib/a90-dpublic/seccomp" "$M/etc" "$M$ADMIN_HOME/.ssh" "$M/root/.ssh" "$M/tmp"
/bin/busybox cp "$POLICY_SRC" "$M/{wsta3.TARGET_SECCOMP_POLICY}"
/bin/busybox cp "$FILTER_MANIFEST_SRC" "$M/{wsta3.TARGET_SECCOMP_FILTER_MANIFEST}"
/bin/busybox cp "$FILTER_OBJECT_SRC" "$M/{wsta3.TARGET_SECCOMP_FILTER_OBJECT}"
/bin/busybox cp "$LOADER_MANIFEST_SRC" "$M/{wsta3.TARGET_SECCOMP_LOADER_HELPER_MANIFEST}"
/bin/busybox cp "$LOADER_HELPER_SRC" "$M/{wsta3.TARGET_SECCOMP_LOADER_HELPER}"
/bin/busybox chmod 0644 "$M/{wsta3.TARGET_SECCOMP_POLICY}" "$M/{wsta3.TARGET_SECCOMP_FILTER_MANIFEST}" "$M/{wsta3.TARGET_SECCOMP_FILTER_OBJECT}" "$M/{wsta3.TARGET_SECCOMP_LOADER_HELPER_MANIFEST}"
/bin/busybox chmod 0755 "$M/{wsta3.TARGET_SECCOMP_LOADER_HELPER}"
echo A90WSTA209_SECCOMP_ASSETS_STAGED=1
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
if [ -e "$M$ROOT_KEYS" ]; then echo A90WSTA209_ROOT_AUTHORIZED_KEYS_ABSENT=0; exit 65; else echo A90WSTA209_ROOT_AUTHORIZED_KEYS_ABSENT=1; fi
if /bin/busybox grep -Fqx "$PASSWD_LINE" "$M/etc/passwd"; then echo A90WSTA209_ADMIN_PASSWD_LINE=1; else echo A90WSTA209_ADMIN_PASSWD_LINE=0; exit 66; fi
if /bin/busybox grep -Fqx "$GROUP_LINE" "$M/etc/group"; then echo A90WSTA209_ADMIN_GROUP_LINE=1; else echo A90WSTA209_ADMIN_GROUP_LINE=0; exit 67; fi
if /bin/busybox grep -Fqx "$SHADOW_LINE" "$M/etc/shadow"; then echo A90WSTA209_ADMIN_SHADOW_LINE=1; else echo A90WSTA209_ADMIN_SHADOW_LINE=0; exit 68; fi
[ -s "$M$ADMIN_KEYS" ] && echo A90WSTA209_ADMIN_AUTHORIZED_KEYS=1 || {{ echo A90WSTA209_ADMIN_AUTHORIZED_KEYS=0; exit 69; }}
[ -x "$M/usr/sbin/dropbear" ] && echo A90WSTA209_DROPBEAR_PRESENT=1 || {{ echo A90WSTA209_DROPBEAR_PRESENT=0; exit 70; }}
[ -x "$M$HELPER" ] && echo A90WSTA209_LOADER_HELPER_PRESENT=1 || {{ echo A90WSTA209_LOADER_HELPER_PRESENT=0; exit 71; }}
if /bin/busybox chroot "$M" /usr/bin/dropbearkey -t ed25519 -f "$HOSTKEY" >/tmp/a90_wsta209_dropbearkey.log 2>&1; then
  echo A90WSTA209_HOSTKEY_TYPE=ed25519
else
  /bin/busybox chroot "$M" /usr/bin/dropbearkey -t rsa -s 2048 -f "$HOSTKEY" >/tmp/a90_wsta209_dropbearkey.log 2>&1
  echo A90WSTA209_HOSTKEY_TYPE=rsa
fi
LOAD_TOKEN=$(/bin/busybox cat "$TOKEN_FILE")
echo A90WSTA209_DROPBEAR_COMMAND={d2.shell_quote(command)}
echo A90WSTA209_SECCOMP_EXEC_COMMAND="$HELPER --service dropbear-admin-usb --apply --exec -- /usr/sbin/dropbear ..."
/bin/busybox chroot "$M" /usr/bin/env -i \\
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \\
  A90WSTA161_ALLOW_LOAD=1 \\
  A90WSTA161_LOAD_TOKEN="$LOAD_TOKEN" \\
  "$HELPER" --service dropbear-admin-usb --apply --exec -- \\
  /usr/sbin/dropbear -F -E -r "$HOSTKEY" -p "$B" -P "$PIDFILE" -s -w -j -k \\
  </dev/null >"$M$LOG" 2>&1 &
PID=$!
/bin/busybox printf '%s\\n' "$PID" > "$M$PIDFILE"
/bin/busybox sleep 1
if ! /bin/busybox kill -0 "$PID" >/dev/null 2>&1; then
  echo A90WSTA209_DROPBEAR_ALIVE=0
  /bin/busybox tail -n 16 "$M$LOG" 2>/dev/null || true
  exit 72
fi
echo A90WSTA209_DROPBEAR_ALIVE=1
if /bin/busybox netstat -ltn 2>/dev/null | /bin/busybox grep -q ":{port} "; then echo A90WSTA209_DROPBEAR_LISTEN=1; else echo A90WSTA209_DROPBEAR_LISTEN=0; /bin/busybox tail -n 16 "$M$LOG" 2>/dev/null || true; exit 73; fi
if /bin/busybox grep -q 'A90WSTA161_SECCOMP_LOAD=1' "$M$LOG" && /bin/busybox grep -q 'a90_seccomp_loader_decision=loaded' "$M$LOG" && /bin/busybox grep -q 'A90WSTA208_EXEC_AFTER_LOAD=1' "$M$LOG"; then
  echo A90WSTA209_SECCOMP_DROPBEAR_MARKERS=1
else
  echo A90WSTA209_SECCOMP_DROPBEAR_MARKERS=0
  /bin/busybox tail -n 16 "$M$LOG" 2>/dev/null || true
  exit 74
fi
echo A90WSTA209_ADMIN_SECCOMP_STAGE_DONE
""".strip()


def parse_stage(record: dict[str, Any]) -> dict[str, bool]:
    text = str(record.get("text") or "")
    return {
        "stage_begin": "A90WSTA209_ADMIN_SECCOMP_STAGE_BEGIN" in text,
        "stage_done": "A90WSTA209_ADMIN_SECCOMP_STAGE_DONE" in text,
        "assets_present": "A90WSTA209_ASSET_PRESENT=1" in text,
        "seccomp_assets_staged": "A90WSTA209_SECCOMP_ASSETS_STAGED=1" in text,
        "root_authorized_keys_absent": "A90WSTA209_ROOT_AUTHORIZED_KEYS_ABSENT=1" in text,
        "admin_passwd_line": "A90WSTA209_ADMIN_PASSWD_LINE=1" in text,
        "admin_group_line": "A90WSTA209_ADMIN_GROUP_LINE=1" in text,
        "admin_shadow_line": "A90WSTA209_ADMIN_SHADOW_LINE=1" in text,
        "admin_authorized_keys": "A90WSTA209_ADMIN_AUTHORIZED_KEYS=1" in text,
        "dropbear_present": "A90WSTA209_DROPBEAR_PRESENT=1" in text,
        "loader_helper_present": "A90WSTA209_LOADER_HELPER_PRESENT=1" in text,
        "dropbear_key_generated": "A90WSTA209_HOSTKEY_TYPE=" in text,
        "dropbear_command_safe": " -s -w -j -k" in text,
        "dropbear_alive": "A90WSTA209_DROPBEAR_ALIVE=1" in text,
        "dropbear_listen": "A90WSTA209_DROPBEAR_LISTEN=1" in text,
        "seccomp_dropbear_markers": "A90WSTA209_SECCOMP_DROPBEAR_MARKERS=1" in text,
        "token_literal_absent": wsta161.LOAD_TOKEN not in text and FORBIDDEN_TOKEN_PREFIX not in text,
        "secret_values_logged": False,
    }


def cleanup_script(mountpoint: str) -> str:
    return f"""
set +e
M={d2.shell_quote(mountpoint)}
ASSET_DIR={d2.shell_quote(REMOTE_ASSET_DIR)}
SCRIPT={d2.shell_quote(REMOTE_STAGE_SCRIPT)}
echo A90WSTA209_ADMIN_SECCOMP_CLEANUP_BEGIN
for i in 1 2 3 4 5; do
  for p in $(/bin/busybox pidof dropbear 2>/dev/null); do /bin/busybox kill "$p" >/dev/null 2>&1 || true; done
  /bin/busybox sleep 1
  if ! /bin/busybox pidof dropbear >/dev/null 2>&1; then break; fi
  for p in $(/bin/busybox pidof dropbear 2>/dev/null); do /bin/busybox kill -9 "$p" >/dev/null 2>&1 || true; done
  /bin/busybox sleep 1
done
/bin/busybox rm -f "$M/home/a90admin/.ssh/authorized_keys" "$M/tmp/a90_dropbear_admin_hostkey" "$M/tmp/a90_dropbear_admin.pid" "$M/tmp/a90_dropbear_admin.log"
/bin/busybox rm -rf "$ASSET_DIR"
/bin/busybox rm -f "$SCRIPT"
if [ -e "$M/home/a90admin/.ssh/authorized_keys" ]; then echo A90WSTA209 admin_keys_absent=0; else echo A90WSTA209 admin_keys_absent=1; fi
if /bin/busybox pidof dropbear >/dev/null 2>&1; then echo A90WSTA209 dropbear_absent=0; else echo A90WSTA209 dropbear_absent=1; fi
if [ -e "$ASSET_DIR" ]; then echo A90WSTA209 asset_dir_absent=0; else echo A90WSTA209 asset_dir_absent=1; fi
echo A90WSTA209_ADMIN_SECCOMP_CLEANUP_DONE
""".strip()


def parse_cleanup(record: dict[str, Any]) -> dict[str, bool]:
    text = str(record.get("text") or "")
    return {
        "cleanup_begin": "A90WSTA209_ADMIN_SECCOMP_CLEANUP_BEGIN" in text,
        "cleanup_done": "A90WSTA209_ADMIN_SECCOMP_CLEANUP_DONE" in text,
        "admin_keys_absent": "A90WSTA209 admin_keys_absent=1" in text,
        "dropbear_absent": "A90WSTA209 dropbear_absent=1" in text,
        "asset_dir_absent": "A90WSTA209 asset_dir_absent=1" in text,
    }


def cleanup_ok(result: dict[str, Any]) -> bool:
    cleanup = result.get("admin_seccomp_cleanup_parse", {})
    chroot_cleanup = result.get("cleanup_parse", {})
    return bool(
        cleanup.get("cleanup_done")
        and cleanup.get("admin_keys_absent")
        and cleanup.get("asset_dir_absent")
        and (cleanup.get("dropbear_absent") or chroot_cleanup.get("dropbear_cleanup_ok"))
    )


def chroot_cleanup_ok(result: dict[str, Any]) -> bool:
    return wsta120.chroot_cleanup_ok(result)


def classify(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    ordered = (
        ("explicit_live_gate", str(result.get("gate_decision") or "wsta209-blocked-explicit-live-gate")),
        ("private_run_dir", "wsta209-blocked-nonprivate-run-dir"),
        ("private_token_env_present", "wsta209-blocked-private-token-env-missing"),
        ("private_token_matches_wsta161", "wsta209-blocked-private-token-invalid"),
        ("fresh_health_valid", "wsta209-blocked-fresh-health-invalid"),
        ("helper_built", "wsta209-blocked-helper-build"),
        ("helper_exec_after_load_compiled", "wsta209-blocked-helper-exec-after-load"),
        ("local_image_present", "wsta209-blocked-local-image-missing"),
        ("local_image_expected_sha", "wsta209-blocked-local-image-sha"),
        ("ssh_key_generated", "wsta209-blocked-ssh-keygen"),
        ("native_stale_cleanup_ok", "wsta209-blocked-native-stale-cleanup"),
        ("remote_image_ready", "wsta209-blocked-remote-image"),
        ("seccomp_asset_inputs_valid", "wsta209-blocked-seccomp-asset-inputs"),
        ("seccomp_assets_installed", "wsta209-blocked-seccomp-assets-install"),
        ("stage_script_uploaded", "wsta209-blocked-stage-script-upload"),
        ("chroot_mount_ready", "wsta209-blocked-chroot-mount"),
        ("admin_seccomp_stage_pass", "wsta209-blocked-admin-seccomp-stage"),
        ("seccomp_dropbear_markers", "wsta209-blocked-dropbear-seccomp-markers"),
        ("admin_ssh_pass", "wsta209-blocked-admin-ssh"),
        ("root_ssh_rejected", "wsta209-blocked-root-ssh-not-rejected"),
        ("admin_seccomp_cleanup_ok", "wsta209-blocked-admin-seccomp-cleanup"),
        ("chroot_cleanup_ok", "wsta209-blocked-chroot-cleanup"),
        ("post_health_valid", "wsta209-blocked-post-health-invalid"),
    )
    for key, decision in ordered:
        if not checks.get(key):
            return str(decision)
    return PASS_DECISION


def execute_live(args: argparse.Namespace,
                 result: dict[str, Any],
                 out_path: Path,
                 run_dir: Path,
                 run_id: str) -> dict[str, Any]:
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
        result["checks"]["helper_exec_after_load_compiled"] = helper_result_ok(result["loader_helper_build"])
        write_json(out_path, result)
        if not (result["checks"]["helper_built"] and result["checks"]["helper_exec_after_load_compiled"]):
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

        asset_paths = seccomp_asset_paths(args, result["loader_helper_build"])
        asset_checks = validate_seccomp_asset_inputs(asset_paths)
        result["seccomp_asset_input_checks"] = asset_checks
        result["checks"]["seccomp_asset_inputs_valid"] = all(asset_checks.values())
        write_json(out_path, result)
        if not result["checks"]["seccomp_asset_inputs_valid"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        token_path = write_private_token_file(run_dir)
        result["seccomp_assets_install"] = install_seccomp_assets(args, run_dir, asset_paths, token_path)
        result["checks"]["seccomp_assets_installed"] = bool(result["seccomp_assets_install"].get("installed"))
        result["safety"]["token_staged_private_runtime_file"] = result["checks"]["seccomp_assets_installed"]
        write_json(out_path, result)
        if not result["checks"]["seccomp_assets_installed"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        stage_script_path = run_dir / "wsta209_dropbear_admin_seccomp_stage.sh"
        stage_script_path.write_text(
            dropbear_seccomp_stage_script(args.mountpoint, public_key, args.device_ip, args.ssh_port) + "\n",
            encoding="utf-8",
        )
        stage_script_path.chmod(0o700)
        result["stage_script_upload"] = install_file(
            args,
            stage_script_path,
            REMOTE_STAGE_SCRIPT,
            timeout=args.transfer_timeout + args.bridge_timeout + 120.0,
        )
        result["checks"]["stage_script_uploaded"] = bool(result["stage_script_upload"].get("installed"))
        write_json(out_path, result)
        if not result["checks"]["stage_script_uploaded"]:
            result["decision"] = classify(result)
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

        result["admin_seccomp_stage"] = wsta120.bridge_run_script_file(
            args,
            REMOTE_STAGE_SCRIPT,
            timeout=args.setup_timeout,
            allow_error=True,
        )
        result["admin_seccomp_stage_parse"] = parse_stage(result["admin_seccomp_stage"])
        stage = result["admin_seccomp_stage_parse"]
        result["checks"]["admin_seccomp_stage_pass"] = bool(
            stage.get("stage_done")
            and stage.get("assets_present")
            and stage.get("seccomp_assets_staged")
            and stage.get("root_authorized_keys_absent")
            and stage.get("admin_passwd_line")
            and stage.get("admin_group_line")
            and stage.get("admin_shadow_line")
            and stage.get("admin_authorized_keys")
            and stage.get("dropbear_present")
            and stage.get("loader_helper_present")
            and stage.get("dropbear_key_generated")
            and stage.get("dropbear_command_safe")
            and stage.get("dropbear_alive")
            and stage.get("dropbear_listen")
            and stage.get("token_literal_absent")
        )
        result["checks"]["seccomp_dropbear_markers"] = bool(stage.get("seccomp_dropbear_markers"))
        if result["checks"]["seccomp_dropbear_markers"]:
            result["safety"]["seccomp_assets_staged"] = True
            result["safety"]["seccomp_filter_loaded"] = True
            result["safety"]["seccomp_enforced"] = True
        result["safety"]["live_command_executed"] = True
        result["safety"]["correct_wsta161_token_supplied"] = True
        write_json(out_path, result)
        if not (result["checks"]["admin_seccomp_stage_pass"] and result["checks"]["seccomp_dropbear_markers"]):
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        admin_cmd = (
            "echo A90WSTA120_ADMIN_UID=$(id -u); "
            "echo A90WSTA120_ADMIN_GID=$(id -g); "
            "echo A90WSTA120_ADMIN_USER=$(id -un); "
            "echo A90WSTA120_ADMIN_GROUP=$(id -gn)"
        )
        result["admin_ssh"] = wsta120.ssh_probe(args, run_dir, "a90admin", admin_cmd, timeout=args.ssh_timeout)
        result["admin_ssh_parse"] = wsta120.parse_admin_ssh(result["admin_ssh"])
        admin = result["admin_ssh_parse"]
        result["checks"]["admin_ssh_pass"] = bool(
            admin.get("ssh_ok")
            and admin.get("uid_3903")
            and admin.get("gid_3903")
            and admin.get("user_a90admin")
            and admin.get("group_a90admin")
        )
        result["safety"]["service_functional_under_seccomp"] = result["checks"]["admin_ssh_pass"]
        write_json(out_path, result)
        if not result["checks"]["admin_ssh_pass"]:
            result["decision"] = classify(result)
            return finish_result(out_path, result)

        result["root_ssh"] = wsta120.ssh_probe(args, run_dir, "root", "id -u", timeout=args.ssh_timeout)
        result["checks"]["root_ssh_rejected"] = result["root_ssh"].get("returncode") != 0
        write_json(out_path, result)
    finally:
        if mounted:
            result["admin_seccomp_cleanup"] = wsta19.bridge_shell(
                args,
                cleanup_script(args.mountpoint),
                timeout=args.cleanup_timeout,
                allow_error=True,
            )
            result["admin_seccomp_cleanup_parse"] = parse_cleanup(result["admin_seccomp_cleanup"])
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
            result["checks"]["admin_seccomp_cleanup_ok"] = bool(cleanup_ok(result))
            result["checks"]["chroot_cleanup_ok"] = bool(chroot_cleanup_ok(result))
        else:
            result["admin_seccomp_cleanup"] = {"skipped": True, "reason": "chroot-not-mounted", "cleaned": True}
            result["cleanup"] = {"skipped": True, "reason": "chroot-not-mounted"}
            result["postcheck"] = {"skipped": True, "reason": "chroot-not-mounted"}
            result["checks"]["admin_seccomp_cleanup_ok"] = True
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
    run_id = args.run_id or f"wsta209-dropbear-admin-seccomp-live-{ts}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    gate_ok, gate_decision = explicit_live_gate(args)
    result: dict[str, Any] = {
        "scope": "WSTA209 Dropbear admin USB under real seccomp live gate",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "gate_decision": gate_decision,
        "admin_model": wsta119.dropbear_admin_model(args.device_ip, args.ssh_port),
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
            "admin_public_key_value_logged": False,
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
        "admin_seccomp_stage_parse": result.get("admin_seccomp_stage_parse", {}),
        "admin_ssh_parse": result.get("admin_ssh_parse", {}),
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
    parser.add_argument("--device-ip", default=wsta119.DEFAULT_BIND_IP)
    parser.add_argument("--ssh-port", type=int, default=wsta119.DEFAULT_PORT)
    parser.add_argument("--ssh-connect-timeout", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--health-timeout", type=float, default=20.0)
    parser.add_argument("--setup-timeout", type=float, default=180.0)
    parser.add_argument("--cleanup-timeout", type=float, default=120.0)
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
    parser.add_argument("--execute-dropbear-admin-seccomp-live", action="store_true")
    parser.add_argument("--allow-correct-wsta161-token", action="store_true")
    parser.add_argument("--ack-seccomp-load-risk", action="store_true")
    parser.add_argument("--ack-root-boundary-daemon", action="store_true")
    parser.add_argument("--ack-admin-key-material", action="store_true")
    parser.add_argument("--ack-root-login-negative-test", action="store_true")
    parser.add_argument("--ack-no-flash-no-reboot", action="store_true")
    parser.add_argument("--ack-cleanup-required", action="store_true")
    parser.add_argument("--print-full-json", action="store_true")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        result = run(args)
    except Exception as exc:  # noqa: BLE001
        ts = utc_stamp()
        run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / (args.run_id or f"wsta209-dropbear-admin-seccomp-live-{ts}")))
        if wsta160.is_under(run_dir, PRIVATE_ROOT):
            run_dir.mkdir(parents=True, exist_ok=True)
            out_path = run_dir / RESULT_NAME
            if out_path.is_file():
                try:
                    result = json.loads(out_path.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    result = {"scope": "WSTA209 Dropbear admin USB under real seccomp live gate"}
            else:
                result = {"scope": "WSTA209 Dropbear admin USB under real seccomp live gate"}
            result["decision"] = "wsta209-runner-error"
            result["error"] = str(exc)
            finish_result(out_path, result)
        else:
            result = {"decision": "wsta209-runner-error", "error": str(exc)}
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1
    payload = result if args.print_full_json else public_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("decision") == PASS_DECISION else 2


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
