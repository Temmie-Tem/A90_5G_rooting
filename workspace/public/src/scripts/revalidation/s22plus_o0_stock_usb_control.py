#!/usr/bin/env python3
"""S22+ O0 zero-flash stock USB control proof.

The run path uses the known-good Android/Magisk USB gadget. It temporarily
stages one static echo daemon under /data/local/tmp, hands /dev/ttyGS0 ownership
from the stock DR-daemon to that helper, and verifies framed bidirectional
payloads through the matching host /dev/ttyACM node. DR-daemon is restored and
must reacquire /dev/ttyGS0 before PASS.

It does not flash, reboot, write configfs/sysfs, alter the active gadget, load a
module, or install a Magisk component. Generated binaries and raw observations
stay under workspace/private.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import math
import os
import queue
import re
import select
import shutil
import struct
import subprocess
import sys
import termios
import threading
import time
import tty
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V3403"
EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
EXPECTED_MODEL = "SM-S906N"
EXPECTED_DEVICE = "g0q"
EXPECTED_INCREMENTAL = "S906NKSS7FYG8"
EXPECTED_BOOT_SHA256 = "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
EXPECTED_USB_VENDOR_ID = "04e8"
EXPECTED_USB_PRODUCT_ID = "6860"
EXPECTED_USB_DRIVER = "cdc_acm"

SOURCE_REL = Path("workspace/public/src/android/s22plus_o0_tty_echo.c")
DEFAULT_BUILD_ROOT = Path("workspace/private/builds/s22plus/o0_stock_usb_control_v3403")
DEFAULT_RUN_ROOT = Path("workspace/private/runs")
DAEMON_NAME = "s22plus_o0_tty_echo_v3403"
REMOTE_DAEMON = f"/data/local/tmp/{DAEMON_NAME}"
STOCK_TTY_SERVICE = "DR-daemon"
STOCK_TTY_PROCESS = "ddexe"

MAGIC = b"S2O0"
VERSION = 1
REQUEST = 1
RESPONSE = 2
HEADER = struct.Struct("<4sBBHII")
MAX_PAYLOAD = 1024
DEFAULT_REQUEST_COUNT = 128
DEFAULT_PAYLOAD_SIZE = 256

SERIAL_RE = re.compile(r"RFCT[0-9A-Z]+")
USB_SERIAL_RE = re.compile(r"usb-SAMSUNG_SAMSUNG_Android_[^/\s]+")
MAC_RE = re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f])")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    candidate = Path(path)
    try:
        return str(candidate.resolve().relative_to(ROOT.resolve()))
    except (OSError, ValueError):
        return str(path)


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def redact(text: str, serial: str | None = None) -> str:
    if serial:
        text = text.replace(serial, "<S22_SERIAL_REDACTED>")
    text = SERIAL_RE.sub("<S22_SERIAL_REDACTED>", text)
    text = USB_SERIAL_RE.sub("usb-SAMSUNG_SAMSUNG_Android_<S22_SERIAL_REDACTED>", text)
    return MAC_RE.sub("<REDACTED_MAC>", text)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_result(
    argv: list[str],
    *,
    timeout: float = 30.0,
    serial: str | None = None,
    binary: bool = False,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            text=not binary,
        )
    except FileNotFoundError as exc:
        return {"argv": argv, "rc": 127, "stdout": "", "stderr": str(exc), "timeout": False}
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"") if binary else (exc.stdout or "")
        stderr = (exc.stderr or b"") if binary else (exc.stderr or "")
        if binary:
            stdout = bytes(stdout).decode("utf-8", errors="replace")
            stderr = bytes(stderr).decode("utf-8", errors="replace")
        return {
            "argv": argv,
            "rc": 124,
            "stdout": redact(str(stdout), serial),
            "stderr": redact(str(stderr), serial),
            "timeout": True,
        }
    stdout: str
    stderr: str
    if binary:
        stdout = completed.stdout.decode("utf-8", errors="replace")
        stderr = completed.stderr.decode("utf-8", errors="replace")
    else:
        stdout = completed.stdout
        stderr = completed.stderr
    return {
        "argv": argv,
        "rc": completed.returncode,
        "stdout": redact(stdout, serial),
        "stderr": redact(stderr, serial),
        "timeout": False,
    }


def parse_adb_devices(text: str) -> list[str]:
    devices: list[str] = []
    for line in text.splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 2 and fields[1] == "device":
            devices.append(fields[0])
    return devices


def select_adb_serial(requested: str | None) -> str:
    try:
        completed = subprocess.run(
            ["adb", "devices"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15.0,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"adb devices failed: {exc}") from exc
    if completed.returncode != 0:
        raise RuntimeError(f"adb devices failed: {completed.stderr}")
    devices = parse_adb_devices(completed.stdout)
    if requested:
        if requested not in devices:
            raise RuntimeError("requested ADB serial is not in device state")
        return requested
    if len(devices) != 1:
        raise RuntimeError(f"expected exactly one ADB device, found {len(devices)}")
    return devices[0]


def adb_text(serial: str, command: str, *, root: bool = False, timeout: float = 45.0) -> dict[str, Any]:
    argv = ["adb", "-s", serial, "exec-out"]
    if root:
        argv.extend(["su", "-c", command])
    else:
        argv.extend(["sh", "-c", command])
    return command_result(argv, timeout=timeout, serial=serial, binary=True)


def parse_key_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if re.fullmatch(r"[A-Za-z0-9_]+", key):
            values[key] = value.strip()
    return values


DEVICE_SNAPSHOT_COMMAND = "; ".join(
    [
        "printf 'model='; getprop ro.product.model",
        "printf 'device='; getprop ro.product.device",
        "printf 'incremental='; getprop ro.build.version.incremental",
        "printf 'boot_completed='; getprop sys.boot_completed",
        "printf 'boot_recovery='; getprop ro.boot.boot_recovery",
        "printf 'vbstate='; getprop ro.boot.verifiedbootstate",
        "printf 'usb_config='; getprop sys.usb.config",
        "printf 'ttyGS0_char='; if test -c /dev/ttyGS0; then echo 1; else echo 0; fi",
        "printf 'ttyGS0_stat='; stat -c '%F:%t:%T:%a' /dev/ttyGS0 2>/dev/null || echo __MISSING__",
        "printf 'udc='; cat /config/usb_gadget/g1/UDC 2>/dev/null || echo __MISSING__",
        "printf 'boot_sha256='; sha256sum /dev/block/by-name/boot 2>/dev/null | awk '{print $1}'",
        "printf 'uid='; id -u",
        "printf 'context='; id -Z 2>/dev/null || true",
    ]
)


def device_snapshot(serial: str) -> dict[str, str]:
    result = adb_text(serial, DEVICE_SNAPSHOT_COMMAND, root=True, timeout=60.0)
    if result["rc"] != 0:
        raise RuntimeError(f"device snapshot failed: {result['stderr'] or result['stdout']}")
    return parse_key_values(result["stdout"])


STOCK_SERVICE_COMMAND = "; ".join(
    [
        f"printf 'service_state='; getprop init.svc.{STOCK_TTY_SERVICE}",
        f"printf 'service_pid='; pidof {STOCK_TTY_PROCESS} 2>/dev/null || true; echo",
        "printf 'tty_owner_count='; count=0; "
        f"for pid in $(pidof {STOCK_TTY_PROCESS} 2>/dev/null); do "
        "for fd in /proc/$pid/fd/*; do target=$(readlink $fd 2>/dev/null || true); "
        "if test \"$target\" = /dev/ttyGS0; then count=$((count + 1)); fi; done; done; echo $count",
    ]
)


def stock_service_state(serial: str) -> dict[str, Any]:
    result = adb_text(serial, STOCK_SERVICE_COMMAND, root=True, timeout=15.0)
    values = parse_key_values(result["stdout"])
    pid_text = values.get("service_pid", "").strip()
    owner_text = values.get("tty_owner_count", "0").strip()
    return {
        "rc": result["rc"],
        "state": values.get("service_state", ""),
        "pid_present": bool(pid_text),
        "tty_owner_count": int(owner_text) if owner_text.isdigit() else -1,
    }


def wait_stock_service(serial: str, expected_state: str, *, timeout: float = 10.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last = stock_service_state(serial)
    while time.monotonic() < deadline:
        state_match = last["state"] == expected_state
        ownership_match = (
            last["pid_present"] and last["tty_owner_count"] > 0
            if expected_state == "running"
            else not last["pid_present"] and last["tty_owner_count"] == 0
        )
        if last["rc"] == 0 and state_match and ownership_match:
            return last
        time.sleep(0.1)
        last = stock_service_state(serial)
    raise TimeoutError(f"{STOCK_TTY_SERVICE} did not reach {expected_state}: {last}")


def set_stock_service(serial: str, action: str) -> dict[str, Any]:
    if action not in {"start", "stop"}:
        raise ValueError(action)
    return adb_text(serial, f"setprop ctl.{action} {STOCK_TTY_SERVICE}", root=True, timeout=15.0)


def verify_device_snapshot(snapshot: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    expected = {
        "model": EXPECTED_MODEL,
        "device": EXPECTED_DEVICE,
        "incremental": EXPECTED_INCREMENTAL,
        "boot_completed": "1",
        "boot_recovery": "0",
        "vbstate": "orange",
        "ttyGS0_char": "1",
        "boot_sha256": EXPECTED_BOOT_SHA256,
        "uid": "0",
    }
    for key, value in expected.items():
        if snapshot.get(key) != value:
            reasons.append(f"{key}-mismatch")
    if not snapshot.get("udc") or snapshot.get("udc") == "__MISSING__":
        reasons.append("udc-missing")
    if "adb" not in snapshot.get("usb_config", ""):
        reasons.append("stock-adb-config-missing")
    return reasons


def udev_properties(path: Path, serial: str | None = None) -> dict[str, str]:
    result = command_result(["udevadm", "info", "-q", "property", "-n", str(path)], serial=serial)
    if result["rc"] != 0:
        raise RuntimeError(f"udevadm failed for {path}: {result['stderr']}")
    return parse_key_values(result["stdout"])


def select_host_tty(requested: Path | None, serial: str | None = None) -> tuple[Path, dict[str, str]]:
    candidates = [requested] if requested else sorted(Path("/dev").glob("ttyACM*"))
    matches: list[tuple[Path, dict[str, str]]] = []
    for path in candidates:
        if path is None or not path.exists():
            continue
        props = udev_properties(path, serial)
        if (
            props.get("ID_VENDOR_ID") == EXPECTED_USB_VENDOR_ID
            and props.get("ID_MODEL_ID") == EXPECTED_USB_PRODUCT_ID
            and props.get("ID_USB_DRIVER") == EXPECTED_USB_DRIVER
        ):
            matches.append((path, props))
    if len(matches) != 1:
        raise RuntimeError(f"expected one Samsung CDC ACM tty, found {len(matches)}")
    return matches[0]


def build_daemon(build_root: Path, cc: str) -> dict[str, Any]:
    source = resolve(SOURCE_REL)
    output = build_root / "bin" / DAEMON_NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        cc,
        "-std=gnu11",
        "-static",
        "-Os",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-o",
        str(output),
        str(source),
    ]
    result = command_result(command, timeout=180.0)
    if result["rc"] != 0:
        raise RuntimeError(f"daemon build failed: {result['stderr']}")
    output.chmod(0o755)
    file_result = command_result(["file", str(output)])
    if file_result["rc"] != 0 or "ARM aarch64" not in file_result["stdout"] or "statically linked" not in file_result["stdout"]:
        raise RuntimeError(f"unexpected daemon artifact: {file_result['stdout']} {file_result['stderr']}")
    return {
        "source": rel(source),
        "path": rel(output),
        "sha256": sha256_file(output),
        "size": output.stat().st_size,
        "file": file_result["stdout"].strip(),
        "command": [rel(item) if item.startswith(str(ROOT)) else item for item in command],
    }


def frame_crc(prefix: bytes, payload: bytes) -> int:
    return binascii.crc32(payload, binascii.crc32(prefix)) & 0xFFFFFFFF


def encode_frame(frame_type: int, seq: int, payload: bytes) -> bytes:
    if frame_type not in (REQUEST, RESPONSE):
        raise ValueError("invalid frame type")
    if not 0 <= seq <= 0xFFFFFFFF:
        raise ValueError("sequence out of range")
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload too large")
    prefix = struct.pack("<4sBBHI", MAGIC, VERSION, frame_type, len(payload), seq)
    return prefix + struct.pack("<I", frame_crc(prefix, payload)) + payload


def decode_frame(data: bytes, expected_type: int | None = None) -> tuple[int, int, bytes]:
    if len(data) < HEADER.size:
        raise ValueError("short frame")
    magic, version, frame_type, payload_len, seq, received_crc = HEADER.unpack(data[: HEADER.size])
    payload = data[HEADER.size :]
    if magic != MAGIC or version != VERSION:
        raise ValueError("bad magic/version")
    if expected_type is not None and frame_type != expected_type:
        raise ValueError("unexpected frame type")
    if payload_len != len(payload) or payload_len > MAX_PAYLOAD:
        raise ValueError("bad payload length")
    if frame_crc(data[:12], payload) != received_crc:
        raise ValueError("bad crc")
    return frame_type, seq, payload


def deterministic_payload(seq: int, max_size: int) -> bytes:
    if not 0 <= max_size <= MAX_PAYLOAD:
        raise ValueError("invalid payload size")
    lengths = [0, 1, 7, 31, max_size]
    length = lengths[seq % len(lengths)]
    seed = struct.pack("<I", seq)
    output = bytearray()
    counter = 0
    while len(output) < length:
        output.extend(hashlib.sha256(seed + struct.pack("<I", counter)).digest())
        counter += 1
    return bytes(output[:length])


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("invalid quantile")
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def read_exact(fd: int, size: int, timeout: float) -> bytes:
    data = bytearray()
    deadline = time.monotonic() + timeout
    while len(data) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"serial read timeout after {len(data)}/{size} bytes")
        readable, _, _ = select.select([fd], [], [], remaining)
        if not readable:
            continue
        chunk = os.read(fd, size - len(data))
        if not chunk:
            raise OSError("serial endpoint returned EOF")
        data.extend(chunk)
    return bytes(data)


def read_frame(fd: int, timeout: float) -> bytes:
    header = read_exact(fd, HEADER.size, timeout)
    payload_len = struct.unpack_from("<H", header, 6)[0]
    if payload_len > MAX_PAYLOAD:
        raise ValueError("response payload too large")
    return header + read_exact(fd, payload_len, timeout)


def write_all(fd: int, data: bytes, timeout: float) -> None:
    offset = 0
    deadline = time.monotonic() + timeout
    while offset < len(data):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"serial write timeout after {offset}/{len(data)} bytes")
        _, writable, _ = select.select([], [fd], [], remaining)
        if not writable:
            continue
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError("serial endpoint made no write progress")
        offset += written


class HostTTY:
    def __init__(self, path: Path):
        self.path = path
        self.fd: int | None = None
        self.saved: list[Any] | None = None

    def open(self, *, flush: bool = True) -> int:
        if self.fd is not None:
            raise RuntimeError("tty already open")
        fd = os.open(self.path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        self.saved = termios.tcgetattr(fd)
        tty.setraw(fd, termios.TCSANOW)
        if flush:
            termios.tcflush(fd, termios.TCIOFLUSH)
        self.fd = fd
        return fd

    def close(self) -> None:
        if self.fd is None:
            return
        try:
            if self.saved is not None:
                termios.tcsetattr(self.fd, termios.TCSANOW, self.saved)
        finally:
            os.close(self.fd)
            self.fd = None
            self.saved = None


@dataclass
class ObserverState:
    name: str
    argv: list[str]
    log_path: str
    started: bool = False
    returncode: int | None = None
    start_error: str | None = None


class StreamObserver:
    def __init__(self, name: str, argv: list[str], log_path: Path, serial: str):
        self.state = ObserverState(name=name, argv=argv, log_path=rel(log_path))
        self.log_path = log_path
        self.serial = serial
        self.process: subprocess.Popen[str] | None = None
        self.thread: threading.Thread | None = None
        self.handle: TextIO | None = None

    def start(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.log_path.open("w", encoding="utf-8")
        try:
            self.process = subprocess.Popen(
                self.state.argv,
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except (FileNotFoundError, PermissionError, OSError) as exc:
            self.state.start_error = str(exc)
            self.handle.write(redact(str(exc), self.serial) + "\n")
            self.handle.close()
            self.handle = None
            return
        self.state.started = True
        self.thread = threading.Thread(target=self._pump, daemon=True)
        self.thread.start()

    def _pump(self) -> None:
        assert self.process is not None and self.process.stdout is not None and self.handle is not None
        for line in self.process.stdout:
            self.handle.write(redact(line, self.serial))
            self.handle.flush()

    def stop(self) -> ObserverState:
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=3.0)
            self.state.returncode = self.process.returncode
        if self.thread is not None:
            self.thread.join(timeout=3.0)
        if self.handle is not None:
            self.handle.close()
            self.handle = None
        return self.state


class DeviceDaemon:
    def __init__(self, serial: str, argv: list[str], log_path: Path):
        self.serial = serial
        self.argv = argv
        self.log_path = log_path
        self.process: subprocess.Popen[bytes] | None = None
        self.lines: queue.Queue[str] = queue.Queue()
        self.thread: threading.Thread | None = None
        self.handle: TextIO | None = None

    def start(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.log_path.open("w", encoding="utf-8")
        self.process = subprocess.Popen(
            self.argv,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.thread = threading.Thread(target=self._pump, daemon=True)
        self.thread.start()

    def _pump(self) -> None:
        assert self.process is not None and self.process.stdout is not None and self.handle is not None
        for raw in iter(self.process.stdout.readline, b""):
            line = redact(raw.decode("utf-8", errors="replace"), self.serial)
            self.handle.write(line)
            self.handle.flush()
            self.lines.put(line)

    def wait_for(self, marker: str, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process is not None and self.process.poll() is not None and self.lines.empty():
                raise RuntimeError(f"device daemon exited before {marker}")
            try:
                line = self.lines.get(timeout=min(0.2, deadline - time.monotonic()))
            except queue.Empty:
                continue
            if marker in line:
                return line.strip()
        raise TimeoutError(f"device daemon did not emit {marker}")

    def stop(self, timeout: float = 5.0) -> int | None:
        if self.process is not None and self.process.poll() is None:
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2.0)
        if self.thread is not None:
            self.thread.join(timeout=3.0)
        if self.handle is not None:
            self.handle.close()
            self.handle = None
        return None if self.process is None else self.process.returncode


def observer_specs(run_dir: Path) -> list[tuple[str, list[str], Path]]:
    specs = [
        (
            "udev_usb",
            ["udevadm", "monitor", "--kernel", "--property", "--subsystem-match=usb"],
            run_dir / "host" / "observer_udev_usb.txt",
        ),
        (
            "kernel_journal",
            ["journalctl", "-kf", "-o", "short-iso"],
            run_dir / "host" / "observer_kernel_journal.txt",
        ),
    ]
    usbmon = Path("/sys/kernel/debug/usb/usbmon/0u")
    if usbmon.is_file() and os.access(usbmon, os.R_OK):
        specs.append(("usbmon", ["cat", str(usbmon)], run_dir / "host" / "observer_usbmon.txt"))
    return specs


def start_observers(run_dir: Path, serial: str) -> list[StreamObserver]:
    observers: list[StreamObserver] = []
    for name, argv, path in observer_specs(run_dir):
        observer = StreamObserver(name, argv, path, serial)
        observer.start()
        observers.append(observer)
    return observers


def host_snapshot(run_dir: Path, label: str, tty_path: Path, serial: str) -> dict[str, Any]:
    commands = {
        "lsusb_tree": ["lsusb", "-t"],
        "tty_udev": ["udevadm", "info", "-q", "property", "-n", str(tty_path)],
        "tty_stat": ["stat", "-c", "%F:%t:%T:%a", str(tty_path)],
    }
    snapshot: dict[str, Any] = {"timestamp_utc": utc_now()}
    for name, argv in commands.items():
        result = command_result(argv, serial=serial)
        text = result["stdout"] + result["stderr"]
        path = run_dir / "host" / f"{label}_{name}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        snapshot[name] = {"rc": result["rc"], "bytes": len(text.encode()), "path": rel(path)}
    return snapshot


def allocate_run_dir(requested: Path | None) -> Path:
    if requested:
        run_dir = resolve(requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = resolve(DEFAULT_RUN_ROOT / f"s22plus_o0_stock_usb_control_{stamp}")
    for index in range(100):
        candidate = base if index == 0 else Path(f"{base}_{index:02d}")
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError("could not allocate run directory")


def timeline_event(events: list[dict[str, str]], name: str) -> None:
    events.append({"name": name, "timestamp_utc": utc_now()})


def run_roundtrips(
    tty_path: Path,
    *,
    count: int,
    payload_size: int,
    reopen_at: int | None,
    frame_timeout: float,
    events: list[dict[str, str]],
) -> dict[str, Any]:
    tty_handle = HostTTY(tty_path)
    latencies_ms: list[float] = []
    payload_bytes = 0
    reopen_completed = False
    try:
        fd = tty_handle.open(flush=True)
        timeline_event(events, "roundtrip_start")
        for seq in range(count):
            if reopen_at is not None and seq == reopen_at:
                timeline_event(events, "host_tty_reopen_start")
                tty_handle.close()
                time.sleep(0.25)
                fd = tty_handle.open(flush=True)
                reopen_completed = True
                timeline_event(events, "host_tty_reopen_done")
            payload = deterministic_payload(seq, payload_size)
            request = encode_frame(REQUEST, seq, payload)
            started = time.monotonic_ns()
            write_all(fd, request, frame_timeout)
            response = read_frame(fd, frame_timeout)
            elapsed_ms = (time.monotonic_ns() - started) / 1_000_000.0
            _, response_seq, response_payload = decode_frame(response, RESPONSE)
            if response_seq != seq:
                raise RuntimeError(f"sequence mismatch: expected {seq}, got {response_seq}")
            if response_payload != payload:
                raise RuntimeError(f"payload mismatch at sequence {seq}")
            latencies_ms.append(elapsed_ms)
            payload_bytes += len(payload)
        timeline_event(events, "roundtrip_end")
    finally:
        tty_handle.close()
    return {
        "requested": count,
        "completed": len(latencies_ms),
        "sequence_continuity": len(latencies_ms) == count,
        "payload_equality": len(latencies_ms) == count,
        "payload_bytes_each_direction": payload_bytes,
        "host_reopen_requested_at": reopen_at,
        "host_reopen_completed": reopen_completed if reopen_at is not None else None,
        "latency_ms": {
            "samples": [round(value, 6) for value in latencies_ms],
            "min": round(min(latencies_ms), 6) if latencies_ms else None,
            "p50": round(percentile(latencies_ms, 0.50) or 0.0, 6) if latencies_ms else None,
            "p95": round(percentile(latencies_ms, 0.95) or 0.0, 6) if latencies_ms else None,
            "p99": round(percentile(latencies_ms, 0.99) or 0.0, 6) if latencies_ms else None,
            "max": round(max(latencies_ms), 6) if latencies_ms else None,
        },
    }


def offline_check(cc: str) -> dict[str, Any]:
    source = resolve(SOURCE_REL)
    source_text = source.read_text(encoding="utf-8") if source.is_file() else ""
    required = [
        "O0_MAGIC",
        "O0_REQUEST",
        "O0_RESPONSE",
        "crc32_update",
        '"/dev/ttyGS0"',
        "S22_O0_DAEMON_READY",
        "S22_O0_DAEMON_DONE",
    ]
    prohibited = ["/config/", "/sys/", "reboot(", "finit_module", "system("]
    tools = {name: shutil.which(name) for name in [cc, "file", "adb", "udevadm", "journalctl"]}
    return {
        "run_id": RUN_ID,
        "target": EXPECTED_TARGET,
        "source": rel(source),
        "source_present": source.is_file(),
        "required_tokens": {token: token in source_text for token in required},
        "prohibited_tokens": {token: token in source_text for token in prohibited},
        "tools": tools,
        "ready": source.is_file()
        and all(token in source_text for token in required)
        and not any(token in source_text for token in prohibited)
        and all(tools.values()),
        "safety": {
            "flash": False,
            "reboot": False,
            "configfs_write": False,
            "sysfs_write": False,
            "module_load": False,
            "magisk_install": False,
            "temporary_data_local_tmp_only": True,
            "stock_tty_service_stop_start_restored": True,
            "active_gadget_change": False,
        },
    }


def execute(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = allocate_run_dir(args.run_dir)
    events: list[dict[str, str]] = []
    timeline_event(events, "o0_session_start")
    serial = select_adb_serial(args.serial)
    before = device_snapshot(serial)
    reasons = verify_device_snapshot(before)
    if reasons:
        raise RuntimeError(f"device preflight failed: {reasons}")
    tty_path, tty_props = select_host_tty(args.host_tty, serial)
    stock_service_before = stock_service_state(serial)
    if not (
        stock_service_before["rc"] == 0
        and stock_service_before["state"] == "running"
        and stock_service_before["pid_present"]
        and stock_service_before["tty_owner_count"] > 0
    ):
        raise RuntimeError(f"stock tty service preflight failed: {stock_service_before}")
    build = build_daemon(resolve(args.build_root), args.cc)

    private_preflight = {
        "target": EXPECTED_TARGET,
        "device": {**before, "serial": "<S22_SERIAL_REDACTED>"},
        "host_tty": str(tty_path),
        "host_tty_properties": {
            key: value
            for key, value in tty_props.items()
            if key in {"DEVNAME", "ID_BUS", "ID_MODEL", "ID_MODEL_ID", "ID_USB_DRIVER", "ID_VENDOR", "ID_VENDOR_ID"}
        },
        "stock_tty_service": stock_service_before,
        "build": build,
    }
    write_json(run_dir / "preflight.json", private_preflight)
    host_snapshot(run_dir, "before", tty_path, serial)

    local_daemon = resolve(Path(build["path"]))
    push = command_result(["adb", "-s", serial, "push", str(local_daemon), REMOTE_DAEMON], timeout=60.0, serial=serial)
    if push["rc"] != 0:
        raise RuntimeError(f"adb push failed: {push['stderr']}")
    chmod = adb_text(serial, f"chmod 0700 {REMOTE_DAEMON}", root=True)
    if chmod["rc"] != 0:
        raise RuntimeError(f"remote chmod failed: {chmod['stderr']}")
    timeline_event(events, "device_daemon_staged")

    observers = start_observers(run_dir, serial)
    timeline_event(events, "observer_start")
    daemon_command = (
        f"exec {REMOTE_DAEMON} --device /dev/ttyGS0 --max-requests {args.count} "
        f"--idle-timeout-ms {args.daemon_idle_timeout_ms}"
    )
    daemon_argv = ["adb", "-s", serial, "exec-out", "su", "-c", daemon_command]
    daemon = DeviceDaemon(serial, daemon_argv, run_dir / "android" / "daemon.txt")
    roundtrip: dict[str, Any] | None = None
    daemon_rc: int | None = None
    error: str | None = None
    service_touched = False
    service_stopped: dict[str, Any] | None = None
    service_after: dict[str, Any] | None = None
    cleanup: dict[str, Any] = {"rc": -1, "stdout": "", "stderr": "not-run"}
    try:
        service_touched = True
        stop_result = set_stock_service(serial, "stop")
        if stop_result["rc"] != 0:
            raise RuntimeError(f"failed to request {STOCK_TTY_SERVICE} stop: {stop_result['stderr']}")
        service_stopped = wait_stock_service(serial, "stopped")
        timeline_event(events, "stock_tty_service_stopped")
        daemon.start()
        daemon.wait_for("S22_O0_DAEMON_READY", 10.0)
        timeline_event(events, "device_daemon_ready")
        roundtrip = run_roundtrips(
            tty_path,
            count=args.count,
            payload_size=args.payload_size,
            reopen_at=args.reopen_at,
            frame_timeout=args.frame_timeout,
            events=events,
        )
        daemon.wait_for("S22_O0_DAEMON_DONE", 10.0)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        daemon_rc = daemon.stop()
        timeline_event(events, "device_daemon_end")
        cleanup = adb_text(
            serial,
            f"for p in $(pidof {DAEMON_NAME} 2>/dev/null); do kill $p 2>/dev/null || true; done; "
            f"rm -f {REMOTE_DAEMON}",
            root=True,
        )
        timeline_event(events, "device_cleanup_done")
        if service_touched:
            start_result = set_stock_service(serial, "start")
            if start_result["rc"] != 0 and error is None:
                error = f"RuntimeError: failed to request {STOCK_TTY_SERVICE} start"
            try:
                service_after = wait_stock_service(serial, "running")
                timeline_event(events, "stock_tty_service_restored")
            except Exception as exc:
                service_after = stock_service_state(serial)
                if error is None:
                    error = f"{type(exc).__name__}: {exc}"
        observer_states = [observer.stop().__dict__ for observer in observers]
        timeline_event(events, "observer_end")

    after = device_snapshot(serial)
    after_reasons = verify_device_snapshot(after)
    unchanged = {
        key: before.get(key) == after.get(key)
        for key in ["boot_sha256", "usb_config", "udc", "ttyGS0_char", "model", "device", "incremental"]
    }
    host_snapshot(run_dir, "after", tty_path, serial)
    pass_result = bool(
        error is None
        and roundtrip
        and roundtrip["completed"] == args.count
        and roundtrip["sequence_continuity"]
        and roundtrip["payload_equality"]
        and (args.reopen_at is None or roundtrip["host_reopen_completed"])
        and daemon_rc == 0
        and cleanup["rc"] == 0
        and service_stopped is not None
        and service_stopped["state"] == "stopped"
        and service_after is not None
        and service_after["state"] == "running"
        and service_after["tty_owner_count"] > 0
        and not after_reasons
        and all(unchanged.values())
    )
    timeline_event(events, "o0_session_end")
    result = {
        "schema": "s22plus_o0_stock_usb_control_v1",
        "run_id": RUN_ID,
        "target": EXPECTED_TARGET,
        "result": "pass" if pass_result else "fail",
        "rc": 0 if pass_result else 1,
        "run_dir": rel(run_dir),
        "host_tty": str(tty_path),
        "device_tty": "/dev/ttyGS0",
        "protocol": {
            "magic": MAGIC.decode("ascii"),
            "version": VERSION,
            "header_bytes": HEADER.size,
            "crc": "crc32-ieee",
            "max_payload": MAX_PAYLOAD,
        },
        "build": build,
        "roundtrip": roundtrip,
        "daemon_rc": daemon_rc,
        "stock_tty_service_before": stock_service_before,
        "stock_tty_service_stopped": service_stopped,
        "stock_tty_service_after": service_after,
        "observer_states": observer_states,
        "preflight_reasons": reasons,
        "postflight_reasons": after_reasons,
        "state_unchanged": unchanged,
        "cleanup_rc": cleanup["rc"],
        "error": error,
        "safety": offline_check(args.cc)["safety"],
    }
    write_json(run_dir / "result.json", result)
    write_json(run_dir / "timeline.json", {"events": events})
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="execute the zero-flash Android/ACM proof")
    parser.add_argument("--serial", help="ADB serial; default requires exactly one device")
    parser.add_argument("--host-tty", type=Path, help="explicit host tty; default auto-detects Samsung CDC ACM")
    parser.add_argument("--count", type=int, default=DEFAULT_REQUEST_COUNT)
    parser.add_argument("--payload-size", type=int, default=DEFAULT_PAYLOAD_SIZE)
    parser.add_argument("--reopen-at", type=int, default=DEFAULT_REQUEST_COUNT // 2)
    parser.add_argument("--frame-timeout", type=float, default=3.0)
    parser.add_argument("--daemon-idle-timeout-ms", type=int, default=60000)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    parser.add_argument("--cc", default="aarch64-linux-gnu-gcc")
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.count <= 0 or args.count > 10000:
        raise SystemExit("--count must be in 1..10000")
    if args.payload_size < 0 or args.payload_size > MAX_PAYLOAD:
        raise SystemExit(f"--payload-size must be in 0..{MAX_PAYLOAD}")
    if args.reopen_at is not None and not 0 < args.reopen_at < args.count:
        raise SystemExit("--reopen-at must be inside the request range")
    if args.frame_timeout <= 0:
        raise SystemExit("--frame-timeout must be positive")
    if args.daemon_idle_timeout_ms < 1000:
        raise SystemExit("--daemon-idle-timeout-ms must be at least 1000")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    validate_args(args)
    if not args.run:
        result = offline_check(args.cc)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ready"] else 1
    try:
        result = execute(args)
    except Exception as exc:
        print(f"O0 execution failed before result finalization: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(result["rc"])


if __name__ == "__main__":
    raise SystemExit(main())
