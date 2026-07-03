#!/usr/bin/env python3
"""Prepare a private WSTA3 Debian rootfs copy with Wi-Fi STA config staged.

This is host-only.  It copies a WSTA-ready D3 sysvinit rootfs into a private run
directory, writes the explicit opt-in files consumed by ``a90-dpublic-wifi-sta``,
and optionally creates a private D4C-compatible tarball.  It never prints SSID,
PSK, raw supplicant config text, or a secret-derived archive digest.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prepare_d4c_userdata_rootfs_tarball as d4c  # noqa: E402


DEFAULT_RUN_BASE = REPO_ROOT / "workspace/private/runs/server-distro"
DEFAULT_SOURCE_ROOTFS = (
    REPO_ROOT
    / "workspace/private/builds/server-distro/d3-sysvinit-usrmerge-wsta-20260704T0225Z-rootfs"
)
DEFAULT_WIFI_ENV = REPO_ROOT / "workspace/private/secrets/a90-wifi-test.env"
TARGET_CONFIG = Path("etc/a90-dpublic/wpa_supplicant-wlan0.conf")
TARGET_ENABLE = Path("etc/a90-dpublic/wifi-sta-enable")
TARGET_HELPER = Path("usr/local/bin/a90-dpublic-wifi-sta")
PRIVATE_FILE_MODE = 0o600
KEY_SSID = "ssid"
KEY_PSK = "psk"
KEY_MGMT = "key_mgmt"


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, sort_keys=True, ensure_ascii=False)
        fp.write("\n")
        fp.flush()
        os.fsync(fp.fileno())
    tmp.replace(path)


def is_owner_private(path: Path) -> bool:
    return bool(path.exists() and (path.stat().st_mode & 0o077) == 0)


def safe_env_value(raw: str) -> str:
    parts = shlex.split(raw, comments=False, posix=True)
    if len(parts) != 1:
        raise ValueError("env assignment must parse as exactly one shell token")
    if "=" not in parts[0]:
        raise ValueError("env assignment is missing '='")
    return parts[0].split("=", 1)[1]


def load_wifi_env(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"ok": False, "reason": "wifi-env-missing", "path": rel(path)}
    if not is_owner_private(path):
        return {"ok": False, "reason": "wifi-env-not-0600", "path": rel(path)}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if not (line.startswith("A90_WIFI_SSID=") or line.startswith("A90_WIFI_PSK=")):
            continue
        key = line.split("=", 1)[0]
        values[key] = safe_env_value(line)
    ssid = values.get("A90_WIFI_SSID", "")
    psk = values.get("A90_WIFI_PSK", "")
    ssid_len = len(ssid.encode("utf-8"))
    psk_len = len(psk)
    if not (1 <= ssid_len <= 32):
        return {"ok": False, "reason": "wifi-env-invalid-ssid", "path": rel(path), "secret_values_logged": 0}
    if not (8 <= psk_len <= 63 or re.fullmatch(r"[0-9a-fA-F]{64}", psk)):
        return {"ok": False, "reason": "wifi-env-invalid-psk", "path": rel(path), "secret_values_logged": 0}
    return {
        "ok": True,
        "path": rel(path),
        "ssid": ssid,
        "psk": psk,
        "ssid_len": ssid_len,
        "psk_len": psk_len,
        "secret_values_logged": 0,
    }


def quote_wpa(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def supplicant_text_from_env(env: dict[str, Any]) -> str:
    psk = str(env["psk"])
    psk_value = psk if re.fullmatch(r"[0-9a-fA-F]{64}", psk) else quote_wpa(psk)
    return "\n".join([
        "ctrl_interface=/run/wpa_supplicant",
        "update_config=0",
        "network={",
        "    " + KEY_SSID + "=" + quote_wpa(str(env["ssid"])),
        "    scan_ssid=1",
        "    " + KEY_MGMT + "=WPA-PSK",
        "    " + KEY_PSK + "=" + psk_value,
        "}",
        "",
    ])


def supplicant_config_metadata(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"ok": False, "reason": "wpa-conf-missing", "path": rel(path)}
    if not is_owner_private(path):
        return {"ok": False, "reason": "wpa-conf-not-0600", "path": rel(path)}
    keys: set[str] = set()
    has_network_block = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "network={":
            has_network_block = True
        if "=" in line and not line.startswith("#"):
            keys.add(line.split("=", 1)[0].strip())
    has_ssid = KEY_SSID in keys
    has_auth = KEY_PSK in keys or KEY_MGMT in keys
    return {
        "ok": bool(has_network_block and has_ssid and has_auth),
        "reason": "ok" if has_network_block and has_ssid and has_auth else "wpa-conf-missing-required-fields",
        "path": rel(path),
        "mode_private": True,
        "has_network_block": has_network_block,
        "has_ssid_field": has_ssid,
        "has_auth_field": has_auth,
        "secret_values_logged": 0,
    }


def copy_rootfs(source: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest, symlinks=True, copy_function=shutil.copy2)


def stage_config(rootfs: Path, config: Path) -> dict[str, Any]:
    config_target = rootfs / TARGET_CONFIG
    enable_target = rootfs / TARGET_ENABLE
    config_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config, config_target)
    config_target.chmod(PRIVATE_FILE_MODE)
    enable_target.write_text("1\n", encoding="utf-8")
    enable_target.chmod(PRIVATE_FILE_MODE)
    return {
        "config_target": str(TARGET_CONFIG),
        "enable_target": str(TARGET_ENABLE),
        "config_mode": oct(config_target.stat().st_mode & 0o777),
        "enable_mode": oct(enable_target.stat().st_mode & 0o777),
        "helper_present": (rootfs / TARGET_HELPER).is_file(),
        "secret_values_logged": 0,
    }


def create_private_tarball(rootfs: Path, tarball: Path, timeout: float) -> dict[str, Any]:
    tar = d4c.create_tarball(rootfs, tarball, timeout)
    tarball.chmod(PRIVATE_FILE_MODE)
    verified = d4c.verify_tarball(tarball, timeout)
    return {
        "tarball": rel(tarball),
        "size_bytes": tar["size_bytes"],
        "tarball_mode": oct(tarball.stat().st_mode & 0o777),
        "sha256_redacted": True,
        "required_entry_count": len(verified["required_entries_present"]),
        "secret_values_logged": 0,
    }


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    run_id = args.run_id or "wsta3-private-rootfs-" + utc_stamp()
    run_dir = (args.run_dir or (args.run_base / run_id))
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=False)
    run_dir.chmod(0o700)
    result: dict[str, Any] = {
        "run_id": run_id,
        "run_dir": rel(run_dir),
        "source_rootfs": rel(args.source_rootfs),
        "target_rootfs": rel(run_dir / "rootfs"),
        "tarball": rel(run_dir / "a90-wsta3-userdata-rootfs.tar"),
        "secret_values_logged": 0,
    }

    if args.wpa_conf:
        source_config = args.wpa_conf
        config_meta = supplicant_config_metadata(source_config)
        result["config_source"] = {"type": "wpa-conf", **{k: v for k, v in config_meta.items() if k != "path"}}
        if not config_meta.get("ok"):
            result.update({"ok": False, "decision": "wsta3-private-config-blocked-" + str(config_meta["reason"])})
            write_json(run_dir / "summary.json", result)
            return result
    else:
        env_meta = load_wifi_env(args.wifi_env)
        result["config_source"] = {
            "type": "wifi-env",
            "path": rel(args.wifi_env),
            "ok": bool(env_meta.get("ok")),
            "reason": env_meta.get("reason", "ok"),
            "ssid_len": env_meta.get("ssid_len"),
            "psk_len": env_meta.get("psk_len"),
            "secret_values_logged": 0,
        }
        if not env_meta.get("ok"):
            result.update({"ok": False, "decision": "wsta3-private-config-blocked-" + str(env_meta["reason"])})
            write_json(run_dir / "summary.json", result)
            return result
        source_config = run_dir / "generated-wpa_supplicant-wlan0.conf"
        source_config.write_text(supplicant_text_from_env(env_meta), encoding="utf-8")
        source_config.chmod(PRIVATE_FILE_MODE)
        config_meta = supplicant_config_metadata(source_config)
        if not config_meta.get("ok"):
            result.update({"ok": False, "decision": "wsta3-private-config-blocked-generated-invalid"})
            write_json(run_dir / "summary.json", result)
            return result

    d4c.verify_rootfs(args.source_rootfs)
    target_rootfs = run_dir / "rootfs"
    copy_rootfs(args.source_rootfs, target_rootfs)
    result["stage"] = stage_config(target_rootfs, source_config)
    d4c.verify_rootfs(target_rootfs)
    if not args.no_tarball:
        result["tarball_result"] = create_private_tarball(
            target_rootfs, run_dir / "a90-wsta3-userdata-rootfs.tar", args.tar_timeout
        )
    result.update({
        "ok": True,
        "decision": "wsta3-private-rootfs-prepared",
        "device_action": "none",
        "no_flash": True,
        "no_wifi_association": True,
        "no_dhcp": True,
        "no_ping": True,
        "no_public_tunnel": True,
    })
    write_json(run_dir / "summary.json", result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-rootfs", type=Path, default=DEFAULT_SOURCE_ROOTFS)
    parser.add_argument("--run-base", type=Path, default=DEFAULT_RUN_BASE)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--wifi-env", type=Path, default=DEFAULT_WIFI_ENV)
    parser.add_argument("--wpa-conf", type=Path)
    parser.add_argument("--no-tarball", action="store_true")
    parser.add_argument("--tar-timeout", type=float, default=900.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    args.source_rootfs = args.source_rootfs.resolve()
    args.wifi_env = args.wifi_env.resolve()
    if args.wpa_conf:
        args.wpa_conf = args.wpa_conf.resolve()
    try:
        result = prepare(args)
    except Exception as exc:  # noqa: BLE001 - persist bounded failure metadata.
        result = {
            "ok": False,
            "decision": "wsta3-private-rootfs-error",
            "error": str(exc),
            "secret_values_logged": 0,
        }
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
