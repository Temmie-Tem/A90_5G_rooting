#!/usr/bin/env python3
"""Collect the server-distro D0 device-live inventory.

D0 is read-only.  This script runs only observation commands through the
resident native-init serial bridge, writes raw command output to a private run
directory, and prints a redacted classification summary suitable for a public
report.  It does not mount, format, flash, or write to the device.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[5]
REVAL_DIR = REPO_ROOT / "workspace" / "public" / "src" / "scripts" / "revalidation"
if str(REVAL_DIR) not in sys.path:
    sys.path.insert(0, str(REVAL_DIR))

import a90ctl  # noqa: E402


DEFAULT_RUN_BASE = REPO_ROOT / "workspace" / "private" / "runs" / "server-distro"
DEFAULT_HOST_BUILD = REPO_ROOT / "workspace" / "private" / "builds" / "server-distro"
REQUIRED_APPLETS = ("losetup", "mount", "chroot", "switch_root", "mkfs.ext4", "tar", "unshare")
CONFIG_KEYS = (
    "CONFIG_NAMESPACES",
    "CONFIG_UTS_NS",
    "CONFIG_IPC_NS",
    "CONFIG_USER_NS",
    "CONFIG_PID_NS",
    "CONFIG_NET_NS",
    "CONFIG_SECCOMP",
    "CONFIG_SECCOMP_FILTER",
    "CONFIG_TUN",
    "CONFIG_VETH",
    "CONFIG_BLK_DEV_LOOP",
    "CONFIG_BLK_DEV_DM",
    "CONFIG_DM_CRYPT",
    "CONFIG_EXT4_FS",
    "CONFIG_OVERLAY_FS",
)


@dataclass(frozen=True)
class Observation:
    name: str
    command: str
    why: str


OBSERVATIONS = (
    Observation(
        "df",
        "/bin/busybox df -h; echo __A90_D0_DF_K__; /bin/busybox df -k",
        "SD present and size/free for C.1 loop-image fit",
    ),
    Observation(
        "blkid_partitions",
        "/bin/busybox blkid 2>/dev/null || true; "
        "echo __A90_D0_PARTITIONS__; cat /proc/partitions",
        "SD block device, fs, and partition sizes",
    ),
    Observation(
        "userdata_identity",
        "p=/dev/block/by-name/userdata; "
        "echo userdata_path=$p; "
        "ls -l $p 2>/dev/null || true; "
        "r=$(/bin/busybox readlink -f $p 2>/dev/null || true); "
        "echo userdata_real=$r; "
        "b=$(/bin/busybox basename \"$r\" 2>/dev/null || true); "
        "echo userdata_block=$b; "
        "if [ -n \"$b\" ] && [ -r /sys/class/block/$b/size ]; then "
        "echo userdata_sectors=$(cat /sys/class/block/$b/size); fi; "
        "echo __A90_D0_USERDATA_SYSFS__; "
        "for u in /sys/class/block/*/uevent; do "
        "[ -r \"$u\" ] || continue; "
        "/bin/busybox grep -q '^PARTNAME=userdata$' \"$u\" || continue; "
        "d=${u#/sys/class/block/}; d=${d%/uevent}; "
        "echo userdata_sysfs=$u; echo userdata_device=/dev/block/$d; echo userdata_block=$d; "
        "cat \"$u\"; "
        "[ -r /sys/class/block/$d/size ] && echo userdata_sectors=$(cat /sys/class/block/$d/size); "
        "done; "
        "cat /proc/partitions",
        "Identify userdata block device and size without mounting or formatting it",
    ),
    Observation(
        "by_name_map",
        "ls -ld /dev/block /dev/block/by-name /dev/block/bootdevice "
        "/dev/block/platform/*/*/by-name 2>/dev/null || true; "
        "for d in /dev/block/by-name /dev/block/bootdevice/by-name "
        "/dev/block/platform/*/*/by-name; do "
        "[ -d \"$d\" ] || continue; echo __A90_D0_BY_NAME_DIR__=$d; ls -l \"$d\"; done",
        "Confirm partition-by-name map; only userdata is the later D4 target",
    ),
    Observation(
        "mounts",
        "cat /proc/mounts",
        "Find current native-init writable mounts for SD rootfs staging",
    ),
    Observation(
        "busybox_applets",
        "/bin/busybox --list",
        "Determine whether D1 can rely on losetup/mount/chroot/switch_root/tar/unshare",
    ),
    Observation(
        "loop_dm_filesystems",
        "ls -l /dev/loop* /dev/mapper 2>/dev/null || true; "
        "echo __A90_D0_PROC_DEVICES__; cat /proc/devices; "
        "echo __A90_D0_FILESYSTEMS__; cat /proc/filesystems",
        "Loop/dm device node and ext4/filesystem support",
    ),
    Observation(
        "kernel_config",
        "(/bin/busybox zcat /proc/config.gz 2>/dev/null || zcat /proc/config.gz 2>/dev/null || true) "
        "| /bin/busybox grep -E 'NAMESPACES|_NS=|SECCOMP|VETH|TUN|LOOP|DM_|EXT4|OVERLAY' || true",
        "Seccomp, namespace, tun, veth, ext4, and overlay feasibility",
    ),
    Observation(
        "tun_device",
        "ls -l /dev/net/tun 2>/dev/null || true",
        "Tunnel client feasibility for later D-public",
    ),
    Observation(
        "mem_cpu",
        "cat /proc/meminfo; echo __A90_D0_CPU_COUNT__; "
        "(/bin/busybox nproc 2>/dev/null || /bin/busybox grep -c '^processor' /proc/cpuinfo || true)",
        "RAM and CPU sizing",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, sort_keys=True, ensure_ascii=False)
        fp.write("\n")
        fp.flush()
        os.fsync(fp.fileno())
    tmp.replace(path)


def shell_command(command: str) -> list[str]:
    return ["run", "/bin/busybox", "sh", "-c", command]


def run_cmd(host: str,
            port: int,
            timeout: float,
            command: list[str],
            *,
            retry_unsafe: bool = False) -> dict[str, Any]:
    result = a90ctl.run_cmdv1_command(
        host,
        port,
        timeout,
        command,
        retry_unsafe=retry_unsafe,
        require_prompt_after_end=True,
    )
    return {
        "command": command,
        "rc": result.rc,
        "status": result.status,
        "begin": result.begin,
        "end": result.end,
        "text": result.text,
    }


def run_observation(host: str, port: int, timeout: float, obs: Observation) -> dict[str, Any]:
    payload = run_cmd(host, port, timeout, shell_command(obs.command), retry_unsafe=True)
    payload["name"] = obs.name
    payload["why"] = obs.why
    payload["read_only"] = True
    return payload


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


def section_text(record: dict[str, Any]) -> str:
    return "\n".join(clean_lines(str(record.get("text") or "")))


def parse_df_k(df_text: str) -> list[dict[str, Any]]:
    lines = df_text.splitlines()
    if "__A90_D0_DF_K__" not in lines:
        return []
    start = lines.index("__A90_D0_DF_K__") + 1
    rows: list[dict[str, Any]] = []
    for line in lines[start:]:
        parts = line.split()
        if len(parts) < 6 or parts[0].lower().startswith("filesystem"):
            continue
        try:
            rows.append({
                "filesystem": parts[0],
                "blocks_1k": int(parts[1]),
                "used_1k": int(parts[2]),
                "available_1k": int(parts[3]),
                "use_percent": parts[4],
                "mountpoint": parts[5],
            })
        except ValueError:
            continue
    return rows


def find_sd_mount(df_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    preferred = ["/mnt/sdext", "/mnt/sdext/a90"]
    for mount in preferred:
        for row in df_rows:
            if row.get("mountpoint") == mount:
                return row
    for row in df_rows:
        mount = str(row.get("mountpoint", ""))
        if mount.startswith("/mnt/sd"):
            return row
    return None


def parse_userdata(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for line in text.splitlines():
        if line.startswith("userdata_real="):
            value = line.split("=", 1)[1].strip()
            if value:
                out["realpath"] = value
        elif line.startswith("userdata_device="):
            value = line.split("=", 1)[1].strip()
            if value:
                out["realpath"] = value
        elif line.startswith("userdata_block="):
            value = line.split("=", 1)[1].strip()
            if value:
                out["block"] = value
        elif line.startswith("userdata_sectors="):
            raw = line.split("=", 1)[1].strip()
            try:
                sectors = int(raw)
            except ValueError:
                continue
            out["sectors_512"] = sectors
            out["bytes"] = sectors * 512
            out["gib"] = round((sectors * 512) / (1024 ** 3), 2)
    return out


def parse_mounts(text: str) -> list[dict[str, str]]:
    mounts: list[dict[str, str]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        opts = parts[3].split(",")
        if "rw" not in opts:
            continue
        mountpoint = parts[1]
        if mountpoint.startswith(("/proc", "/sys", "/dev", "/run")):
            continue
        mounts.append({
            "source": parts[0],
            "mountpoint": mountpoint,
            "fstype": parts[2],
            "rw": "yes",
        })
    return mounts


def parse_applets(text: str) -> dict[str, bool]:
    applets = {line.strip() for line in text.splitlines() if line.strip()}
    return {name: name in applets for name in REQUIRED_APPLETS}


def parse_filesystems(text: str) -> dict[str, bool]:
    filesystems = {line.split()[-1] for line in text.splitlines() if line.strip()}
    return {
        "ext4": "ext4" in filesystems,
        "overlay": "overlay" in filesystems,
        "tmpfs": "tmpfs" in filesystems,
    }


def parse_loop_dm(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    before_devices = (
        lines[: lines.index("__A90_D0_PROC_DEVICES__")]
        if "__A90_D0_PROC_DEVICES__" in lines else lines
    )
    proc_devices = ""
    if "__A90_D0_PROC_DEVICES__" in lines:
        start = lines.index("__A90_D0_PROC_DEVICES__") + 1
        end = lines.index("__A90_D0_FILESYSTEMS__") if "__A90_D0_FILESYSTEMS__" in lines else len(lines)
        proc_devices = "\n".join(lines[start:end])
    joined = "\n".join(before_devices)
    loop_nodes = sorted(set(re.findall(r"/dev/loop(?:-control|\d+)", joined)))
    return {
        "loop_nodes": loop_nodes,
        "loop_node_count": len([node for node in loop_nodes if re.search(r"/dev/loop\d+$", node)]),
        "loop_control_present": "/dev/loop-control" in loop_nodes,
        "dev_mapper_present": "/dev/mapper" in joined,
        "loop_block_major_present": re.search(r"(?m)^\s*\d+\s+loop$", proc_devices) is not None,
        "device_mapper_present": re.search(r"(?m)^\s*\d+\s+device-mapper$", proc_devices) is not None,
    }


def parse_config(text: str) -> dict[str, str]:
    values = {key: "missing" for key in CONFIG_KEYS}
    for line in text.splitlines():
        line = line.strip()
        for key in CONFIG_KEYS:
            if line == f"{key}=y":
                values[key] = "y"
            elif line == f"{key}=m":
                values[key] = "m"
            elif line == f"# {key} is not set":
                values[key] = "n"
    return values


def parse_tun(text: str) -> bool:
    return "/dev/net/tun" in text or re.search(r"\btun\b", text) is not None


def parse_mem_cpu(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    match = re.search(r"^MemTotal:\s+(\d+)\s+kB", text, flags=re.MULTILINE)
    if match:
        out["mem_total_kb"] = int(match.group(1))
        out["mem_total_mib"] = round(int(match.group(1)) / 1024, 1)
    if "__A90_D0_CPU_COUNT__" in text:
        tail = text.split("__A90_D0_CPU_COUNT__", 1)[1]
        for line in tail.splitlines():
            line = line.strip()
            if line.isdigit():
                out["cpu_count"] = int(line)
                break
    return out


def host_staging_summary(base: Path = DEFAULT_HOST_BUILD) -> dict[str, Any]:
    images = sorted(base.glob("debian-*-arm64-*.img"))
    rootfs_candidates = sorted(base.glob("debian-*-arm64-rootfs"))
    tunnel = base / "tunnel" / "cloudflared-linux-arm64"
    summary: dict[str, Any] = {
        "base": str(base.relative_to(REPO_ROOT)) if base.is_relative_to(REPO_ROOT) else str(base),
        "rootfs_present": bool(rootfs_candidates),
        "image_present": bool(images),
        "cloudflared_present": tunnel.is_file(),
    }
    if images:
        image = images[-1]
        summary["image"] = str(image.relative_to(REPO_ROOT))
        summary["image_size_bytes"] = image.stat().st_size
        summary["image_sha256"] = sha256_file(image)
    if rootfs_candidates:
        rootfs = rootfs_candidates[-1]
        summary["rootfs"] = str(rootfs.relative_to(REPO_ROOT))
        marker = rootfs / "etc" / "a90-server-distro-stage"
        passwd = rootfs / "etc" / "shadow"
        summary["stage_marker_present"] = marker.is_file()
        summary["root_password_locked_marker"] = marker.read_text(errors="replace").find("root-password=LOCKED") >= 0 if marker.is_file() else False
        if passwd.is_file():
            root_line = next((line for line in passwd.read_text(errors="replace").splitlines() if line.startswith("root:")), "")
            summary["root_shadow_locked"] = root_line.startswith("root:!")
    if tunnel.is_file():
        summary["cloudflared"] = str(tunnel.relative_to(REPO_ROOT))
        summary["cloudflared_size_bytes"] = tunnel.stat().st_size
        summary["cloudflared_sha256"] = sha256_file(tunnel)
    return summary


def classify_inventory(raw: dict[str, Any]) -> dict[str, Any]:
    observations = {item["name"]: item for item in raw.get("observations", [])}
    df_rows = parse_df_k(section_text(observations.get("df", {})))
    sd = find_sd_mount(df_rows)
    userdata = parse_userdata(section_text(observations.get("userdata_identity", {})))
    mounts = parse_mounts(section_text(observations.get("mounts", {})))
    applets = parse_applets(section_text(observations.get("busybox_applets", {})))
    loop_dm = parse_loop_dm(section_text(observations.get("loop_dm_filesystems", {})))
    filesystems = parse_filesystems(section_text(observations.get("loop_dm_filesystems", {})))
    config = parse_config(section_text(observations.get("kernel_config", {})))
    tun = parse_tun(section_text(observations.get("tun_device", {})))
    mem_cpu = parse_mem_cpu(section_text(observations.get("mem_cpu", {})))
    host = raw.get("host_staging", {})
    loop_available = bool(
        loop_dm.get("loop_control_present")
        or loop_dm.get("loop_node_count", 0) > 0
        or loop_dm.get("loop_block_major_present")
        or config.get("CONFIG_BLK_DEV_LOOP") in {"y", "m"}
    )

    d1_ready = bool(
        sd
        and sd.get("available_1k", 0) * 1024 >= int(host.get("image_size_bytes") or 0)
        and userdata.get("block")
        and filesystems.get("ext4")
        and loop_available
        and applets.get("mount")
        and applets.get("chroot")
        and host.get("image_present")
    )
    d1_notes = [
        "Use SD-backed ext4 image for D1; do not touch userdata.",
        "D1 still requires an explicit non-destructive mount/chroot unit.",
    ]
    if loop_available and not (loop_dm.get("loop_control_present") or loop_dm.get("loop_node_count", 0) > 0):
        d1_notes.append(
            "Loop support is present in kernel/proc-devices but /dev/loop* nodes are absent; D1 must materialize runtime loop nodes or prove mount -o loop handles them."
        )
    if config.get("CONFIG_TUN") in {"y", "m"} and not tun:
        d1_notes.append(
            "CONFIG_TUN is enabled but /dev/net/tun is absent; D-public must materialize the tun node before tunnel-client use."
        )
    return {
        "decision": "server-distro-d0-device-live-read-only-inventory-pass",
        "read_only": True,
        "flash_performed": False,
        "rollback_action": "not-needed-resident-v2321-maintained",
        "sd": sd or {},
        "userdata": userdata,
        "writable_mounts": mounts,
        "required_applets": applets,
        "loop_dm": loop_dm,
        "loop_available": loop_available,
        "filesystems": filesystems,
        "kernel_config": config,
        "tun_device_present": tun,
        "mem_cpu": mem_cpu,
        "host_staging": host,
        "d1_chroot_mvp_ready": d1_ready,
        "d1_notes": d1_notes,
    }


def collect(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    now_utc = _dt.datetime.now(_dt.UTC).replace(microsecond=0)
    run_id = args.run_id or "d0-device-live-" + now_utc.strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    try:
        a90ctl.bridge_exchange(
            args.host,
            args.port,
            "hide",
            min(args.timeout, 8.0),
            markers=(b"[busy]", b"[done]", b"[err]"),
        )
    except OSError:
        pass

    baseline = {
        "version": run_cmd(args.host, args.port, args.timeout, ["version"]),
        "status": run_cmd(args.host, args.port, args.timeout, ["status"]),
        "selftest": run_cmd(args.host, args.port, args.timeout, ["selftest"]),
    }
    if "v2321-usb-clean-identity-rodata" not in baseline["version"]["text"]:
        raise RuntimeError("resident device is not v2321; refusing D0 read-only inventory")
    if "fail=0" not in baseline["selftest"]["text"]:
        raise RuntimeError("baseline selftest is not fail=0; refusing D0 read-only inventory")

    observations = [run_observation(args.host, args.port, args.timeout, obs) for obs in OBSERVATIONS]

    final = {
        "version": run_cmd(args.host, args.port, args.timeout, ["version"]),
        "status": run_cmd(args.host, args.port, args.timeout, ["status"]),
        "selftest": run_cmd(args.host, args.port, args.timeout, ["selftest"]),
    }
    if "v2321-usb-clean-identity-rodata" not in final["version"]["text"]:
        raise RuntimeError("final resident device is not v2321")
    if "fail=0" not in final["selftest"]["text"]:
        raise RuntimeError("final selftest is not fail=0")

    raw = {
        "run_id": run_id,
        "run_dir": str(run_dir.relative_to(REPO_ROOT)) if run_dir.is_relative_to(REPO_ROOT) else str(run_dir),
        "timestamp_utc": now_utc.isoformat().replace("+00:00", "Z"),
        "scope": "server-distro D0 device-live read-only inventory",
        "safety": {
            "read_only": True,
            "no_flash": True,
            "no_mount": True,
            "no_format": True,
            "userdata_identify_only": True,
        },
        "baseline": baseline,
        "observations": observations,
        "final": final,
        "host_staging": host_staging_summary(args.host_build_dir),
    }
    summary = classify_inventory(raw)
    summary["run_dir"] = raw["run_dir"]
    summary["final_v2321"] = "v2321-usb-clean-identity-rodata" in final["version"]["text"]
    summary["final_selftest_fail0"] = "fail=0" in final["selftest"]["text"]

    write_json(run_dir / "inventory_private.json", raw)
    write_json(run_dir / "inventory_public_summary.json", summary)
    return raw, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=a90ctl.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=a90ctl.DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--host-build-dir", type=Path, default=DEFAULT_HOST_BUILD)
    args = parser.parse_args(argv)
    _raw, summary = collect(args)
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
