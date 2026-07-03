#!/usr/bin/env python3
"""Run the WSTA2 native wlan0 materialization gate.

WSTA2 is intentionally below association: it proves the native side can expose
``wlan0`` and the Stage0 server-distro hardware contract, without starting a
native STA session, DHCP, ping, AP/NAT service, or public tunnel.

Default mode performs only a read-only cmdv1 live probe against an already
running native-init.  ``--flash-v3384`` may flash the pinned V3384 candidate, but
only through ``native_init_flash.py`` and only when recovery ADB is already
present or native cmdv1 can ask for recovery.  If the device is already in the
Debian appliance handoff state, this runner records a blocked result instead of
inventing a recovery path.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[5]
REVAL_DIR = REPO_ROOT / "workspace" / "public" / "src" / "scripts" / "revalidation"
if str(REVAL_DIR) not in sys.path:
    sys.path.insert(0, str(REVAL_DIR))

import a90ctl  # noqa: E402


DEFAULT_RUN_BASE = REPO_ROOT / "workspace/private/runs/server-distro"
BRIDGE = REVAL_DIR / "a90_bridge.py"
FLASH_HELPER = REVAL_DIR / "native_init_flash.py"
V3384_BOOT_IMAGE = (
    REPO_ROOT / "workspace/private/inputs/boot_images/boot_linux_v3384_server_distro_hardware_contract.img"
)
V3384_SHA256 = "47890d04219837af3acb96ad8e281ad4eab0ea3a73ae2641e05633d014979178"
V3384_VERSION = "0.11.140"
V3384_BUILD = "v3384-server-distro-hardware-contract"
ROLLBACK_IMAGES = {
    "v2321": (
        REPO_ROOT / "workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img",
        "ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb",
    ),
    "v2237": (
        REPO_ROOT / "workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img",
        "b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f",
    ),
    "v48": (
        REPO_ROOT / "workspace/private/inputs/boot_images/boot_linux_v48.img",
        None,
    ),
}
CONTRACT_REQUIRED = (
    "A90DHW contract.version=1",
    "A90DHW next.required=wifi-sta-upstream",
    "A90DHW next.wifi_sta=native-wlan0-materialization,debian-ip-route-tunnel",
    "A90DHW public_tunnel.owner=debian native=off inbound_public_ports=0",
    "A90DHW safety.no=forbidden-partitions,raw-nonboot-flash,pmic-regulator-gdsc-gpio-backlight,panel-reinit",
    "A90DHW end=1",
)
FORBIDDEN_NATIVE_WORKERS = (
    "wpa_supplicant",
    "dhclient",
    "udhcpc",
    "udhcpd",
    "hostapd",
    "dnsmasq",
    "cloudflared",
)
PS_SCRIPT = """
BB=/bin/busybox
echo A90WSTA2_PS_BEGIN
$BB ps 2>/dev/null || ps 2>/dev/null || true
echo A90WSTA2_PS_END
""".strip()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, sort_keys=True, ensure_ascii=False)
        fp.write("\n")
        fp.flush()
        os.fsync(fp.fileno())
    tmp.replace(path)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip("\r")
        if not line or line.startswith("A90P1 BEGIN ") or line.startswith("A90P1 END "):
            continue
        if line.startswith("a90:/#") or line in {"AT", "T"}:
            continue
        if line.startswith("cmdv1 ") or line.startswith("cmdv1x "):
            continue
        lines.append(line)
    return lines


def parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in clean_lines(text):
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def run_host(cmd: list[str],
             *,
             timeout: float,
             allow_error: bool = True) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    payload = {
        "cmd": cmd,
        "rc": completed.returncode,
        "elapsed_sec": round(time.monotonic() - started, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if not allow_error and completed.returncode != 0:
        raise RuntimeError(f"host command failed rc={completed.returncode}: {cmd}\n{completed.stderr}")
    return payload


def send_bridge_line(args: argparse.Namespace, line: str, *, timeout: float = 3.0) -> dict[str, Any]:
    started = time.monotonic()
    chunks: list[bytes] = []
    try:
        with socket.create_connection((args.bridge_host, args.bridge_port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall((line.rstrip("\r\n") + "\n").encode("utf-8"))
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    chunk = sock.recv(4096)
                except TimeoutError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                if b"a90:/#" in chunk or b"hide requested" in chunk:
                    break
        return {
            "ok": True,
            "line": line,
            "elapsed_sec": round(time.monotonic() - started, 3),
            "text": b"".join(chunks).decode("utf-8", errors="replace"),
        }
    except Exception as exc:  # noqa: BLE001 - menu-hide is opportunistic and recorded.
        return {
            "ok": False,
            "line": line,
            "elapsed_sec": round(time.monotonic() - started, 3),
            "error": str(exc),
        }


def is_auto_menu_busy(payload: dict[str, Any]) -> bool:
    return (
        payload.get("status") == "busy"
        and payload.get("rc") == -16
        and "auto menu active" in str(payload.get("text", ""))
    )


def adb_recovery_available(adb: str) -> bool:
    record = run_host([adb, "devices"], timeout=5.0)
    return "\trecovery" in record["stdout"] or " recovery " in f" {record['stdout']} "


def verify_rollback_images() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, (path, expected_sha) in ROLLBACK_IMAGES.items():
        item: dict[str, Any] = {"path": rel(path), "exists": path.is_file()}
        if path.is_file() and expected_sha:
            actual = sha256_file(path)
            item["sha256"] = actual
            item["sha256_ok"] = actual == expected_sha
        elif expected_sha:
            item["sha256_ok"] = False
        else:
            item["sha256_ok"] = None
        out[name] = item
    out["ok"] = all(item["exists"] and item["sha256_ok"] is not False for item in out.values())
    return out


def run_cmdv1(args: argparse.Namespace,
              command: list[str],
              *,
              timeout: float | None = None,
              allow_error: bool = False) -> dict[str, Any]:
    started = time.monotonic()
    result = a90ctl.run_cmdv1_command(
        args.bridge_host,
        args.bridge_port,
        timeout if timeout is not None else args.timeout,
        command,
        retry_unsafe=False,
        require_prompt_after_end=True,
    )
    payload = {
        "command": command,
        "rc": result.rc,
        "status": result.status,
        "elapsed_sec": round(time.monotonic() - started, 3),
        "text": result.text,
    }
    if is_auto_menu_busy(payload):
        first = payload
        hide = send_bridge_line(args, "hide", timeout=3.0)
        started = time.monotonic()
        result = a90ctl.run_cmdv1_command(
            args.bridge_host,
            args.bridge_port,
            timeout if timeout is not None else args.timeout,
            command,
            retry_unsafe=False,
            require_prompt_after_end=True,
        )
        payload = {
            "command": command,
            "rc": result.rc,
            "status": result.status,
            "elapsed_sec": round(time.monotonic() - started, 3),
            "text": result.text,
            "auto_menu_retry": True,
            "auto_menu_first_attempt": first,
            "auto_menu_hide": hide,
        }
    if not allow_error and (result.rc != 0 or result.status != "ok"):
        raise RuntimeError(f"cmdv1 failed rc={result.rc} status={result.status}: {command}\n{result.text}")
    return payload


def try_cmdv1(args: argparse.Namespace, command: list[str], *, timeout: float | None = None) -> dict[str, Any]:
    try:
        payload = run_cmdv1(args, command, timeout=timeout, allow_error=True)
        payload["transport_ok"] = True
        return payload
    except Exception as exc:  # noqa: BLE001 - this is the fail-closed probe surface.
        return {
            "command": command,
            "transport_ok": False,
            "error": str(exc),
        }


def contract_passed(text: str) -> bool:
    return all(needle in text for needle in CONTRACT_REQUIRED)


def selftest_passed(text: str) -> bool:
    kv = parse_kv(text)
    return kv.get("fail") == "0" or "fail=0" in text


def native_is_v3384(text: str) -> bool:
    return V3384_VERSION in text and V3384_BUILD in text


def wlan0_present(text: str) -> bool:
    kv = parse_kv(text)
    return kv.get("wlan0_present") == "1" or "wlan0_present=1" in text


def forbidden_workers(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for needle in FORBIDDEN_NATIVE_WORKERS:
        if needle.lower() in lowered:
            found.append(needle)
    return found


def flash_v3384(args: argparse.Namespace, result: dict[str, Any]) -> bool:
    rollback = verify_rollback_images()
    result["rollback_images"] = rollback
    if not rollback["ok"]:
        result["decision"] = "wsta2-blocked-rollback-image-precondition"
        return False

    if not V3384_BOOT_IMAGE.is_file() or sha256_file(V3384_BOOT_IMAGE) != V3384_SHA256:
        result["decision"] = "wsta2-blocked-v3384-image-precondition"
        result["v3384_image"] = {"path": rel(V3384_BOOT_IMAGE), "exists": V3384_BOOT_IMAGE.is_file()}
        return False

    recovery = adb_recovery_available(args.adb)
    native = try_cmdv1(args, ["version"], timeout=args.timeout)
    result["preflash_native_version_probe"] = native
    result["preflash_recovery_adb_available"] = recovery

    if not recovery and not native.get("transport_ok"):
        result["decision"] = "wsta2-blocked-no-native-cmdv1-or-recovery-adb"
        return False

    cmd = [
        sys.executable,
        str(FLASH_HELPER),
        str(V3384_BOOT_IMAGE),
        "--expect-version",
        V3384_VERSION,
        "--expect-sha256",
        V3384_SHA256,
        "--verify-protocol",
        "cmdv1",
    ]
    if not recovery:
        cmd.append("--from-native")
    flash_record = run_host(cmd, timeout=args.flash_timeout)
    result["flash"] = flash_record
    if flash_record["rc"] != 0:
        result["decision"] = "wsta2-blocked-v3384-flash-failed"
        return False
    return True


def run_gate(args: argparse.Namespace, result: dict[str, Any], out_path: Path) -> dict[str, Any]:
    result["bridge_status"] = run_host([sys.executable, str(BRIDGE), "status", "--json"], timeout=10.0)
    write_json(out_path, result)

    if args.flash_v3384 and not flash_v3384(args, result):
        write_json(out_path, result)
        return result
    write_json(out_path, result)

    version = try_cmdv1(args, ["version"], timeout=args.timeout)
    result["version"] = version
    write_json(out_path, result)
    if not version.get("transport_ok"):
        result["decision"] = "wsta2-blocked-native-cmdv1-unavailable"
        write_json(out_path, result)
        return result
    if not native_is_v3384(version.get("text", "")):
        result["decision"] = "wsta2-blocked-v3384-not-resident"
        write_json(out_path, result)
        return result

    status = run_cmdv1(args, ["status"], timeout=args.timeout)
    selftest = run_cmdv1(args, ["selftest"], timeout=args.timeout)
    contract = run_cmdv1(args, ["server-distro", "hardware-contract"], timeout=args.timeout)
    wifi_status = run_cmdv1(args, ["wifi", "status"], timeout=args.timeout, allow_error=True)
    result.update({
        "status": status,
        "selftest": selftest,
        "hardware_contract": contract,
        "wifi_status": wifi_status,
    })
    write_json(out_path, result)

    if args.probe_iftype and not wlan0_present(wifi_status["text"]):
        probe_timeout = max(args.timeout, (args.probe_timeout_ms / 1000.0) + 30.0)
        result["iftype_probe"] = run_cmdv1(
            args,
            ["wifi", "softap", "iftype-probe", str(args.probe_timeout_ms)],
            timeout=probe_timeout,
            allow_error=True,
        )
        result["wifi_status_after_probe"] = run_cmdv1(
            args, ["wifi", "status"], timeout=args.timeout, allow_error=True
        )
        write_json(out_path, result)

    ps = run_cmdv1(args, ["run", "/bin/busybox", "sh", "-c", PS_SCRIPT], timeout=args.timeout, allow_error=True)
    result["process_table"] = ps
    write_json(out_path, result)

    active_wifi_status = result.get("wifi_status_after_probe", wifi_status)
    workers = forbidden_workers(ps["text"])
    result["checks"] = {
        "selftest_fail_zero": selftest_passed(selftest["text"]),
        "hardware_contract_ok": contract_passed(contract["text"]),
        "wlan0_present": wlan0_present(active_wifi_status["text"]),
        "forbidden_native_workers": workers,
    }
    if all((
        result["checks"]["selftest_fail_zero"],
        result["checks"]["hardware_contract_ok"],
        result["checks"]["wlan0_present"],
        not result["checks"]["forbidden_native_workers"],
    )):
        result["decision"] = "wsta2-native-materialization-pass"
    else:
        result["decision"] = "wsta2-native-materialization-fail"
    write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--flash-timeout", type=float, default=180.0)
    parser.add_argument("--flash-v3384", action="store_true")
    parser.add_argument("--probe-iftype", action="store_true")
    parser.add_argument("--probe-timeout-ms", type=int, default=220000)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / f"wsta2-native-materialization-{ts}")
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / "wsta2_result.json"
    result: dict[str, Any] = {
        "scope": "WSTA2 native wlan0 materialization gate",
        "started_utc": ts,
        "run_dir": rel(run_dir),
        "flash_requested": bool(args.flash_v3384),
        "iftype_probe_requested": bool(args.probe_iftype),
        "candidate": {
            "path": rel(V3384_BOOT_IMAGE),
            "sha256": V3384_SHA256,
            "version": V3384_VERSION,
            "build": V3384_BUILD,
        },
        "safety": {
            "boot_flash_only_via_checked_helper": True,
            "no_wifi_association": True,
            "no_dhcp": True,
            "no_ping": True,
            "no_public_tunnel": True,
            "no_forbidden_partition_write": True,
        },
    }
    try:
        result = run_gate(args, result, out_path)
    except Exception as exc:  # noqa: BLE001 - record partial state for handoff.
        result["decision"] = "wsta2-runner-error"
        result["error"] = str(exc)
        write_json(out_path, result)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if str(result.get("decision", "")).endswith("-pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
