#!/usr/bin/env python3

import argparse
import hashlib
import os
import shlex
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_BRIDGE_HOST = "127.0.0.1"
DEFAULT_BRIDGE_PORT = 54321
DEFAULT_DEVICE_IP = "192.168.7.2"
DEFAULT_TCP_PORT = 2325
DEFAULT_TRANSFER_PORT = 18083
DEFAULT_DEVICE_BINARY = "/cache/bin/a90_tcpctl"
DEFAULT_TOYBOX = "/cache/bin/toybox"
DEFAULT_LOCAL_BINARY = ROOT_DIR / "external_tools/userland/bin/a90_tcpctl-aarch64-static"


def log(message: str) -> None:
    print(f"[tcpctl] {message}", file=sys.stderr, flush=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        while True:
            chunk = fp.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def bridge_command(host: str,
                   port: int,
                   command: str,
                   timeout_sec: float,
                   markers: tuple[bytes, ...] = (b"[done]", b"[err]", b"[busy]")) -> str:
    deadline = time.monotonic() + timeout_sec
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2.0) as sock:
                sock.settimeout(0.25)
                sock.sendall(("\n" + command + "\n").encode())
                data = bytearray()
                read_deadline = time.monotonic() + min(10.0, max(3.0, timeout_sec))
                while time.monotonic() < read_deadline:
                    try:
                        chunk = sock.recv(8192)
                    except socket.timeout:
                        continue
                    if not chunk:
                        break
                    data.extend(chunk)
                    if any(marker in data for marker in markers):
                        time.sleep(0.2)
                        try:
                            data.extend(sock.recv(8192))
                        except socket.timeout:
                            pass
                        return data.decode("utf-8", errors="replace")
        except OSError as exc:
            last_error = exc

        time.sleep(0.5)

    raise RuntimeError(f"bridge command timeout for {command!r}: {last_error}")


def best_effort_hide_menu(args: argparse.Namespace) -> None:
    try:
        output = bridge_command(
            args.bridge_host,
            args.bridge_port,
            "hide",
            args.bridge_timeout,
            markers=(b"[busy]", b"[done]", b"[err]"),
        )
    except RuntimeError:
        return

    if "[busy]" in output:
        log("auto menu hide requested")
        time.sleep(args.menu_hide_sleep)


class BridgeRunThread(threading.Thread):
    def __init__(self, args: argparse.Namespace, command: str, *, echo: bool = False) -> None:
        super().__init__(daemon=True)
        self.args = args
        self.command = command
        self.echo = echo
        self.buffer = bytearray()
        self.ready = threading.Event()
        self.done = threading.Event()
        self.error: Exception | None = None

    def run(self) -> None:
        try:
            with socket.create_connection(
                (self.args.bridge_host, self.args.bridge_port),
                timeout=self.args.connect_timeout,
            ) as sock:
                sock.settimeout(0.25)
                sock.sendall(("\n" + self.command + "\n").encode())
                while True:
                    try:
                        chunk = sock.recv(8192)
                    except socket.timeout:
                        continue
                    if not chunk:
                        break
                    self.buffer.extend(chunk)
                    if self.echo:
                        sys.stdout.buffer.write(chunk)
                        sys.stdout.buffer.flush()
                    if b"tcpctl: listening" in self.buffer:
                        self.ready.set()
                    if (b"[done] run" in self.buffer or
                            b"[err] run" in self.buffer or
                            b"[busy]" in self.buffer):
                        break
        except Exception as exc:
            self.error = exc
        finally:
            self.done.set()

    def text(self) -> str:
        return self.buffer.decode("utf-8", errors="replace")


def tcpctl_request(args: argparse.Namespace, command: str, *, timeout: float | None = None) -> str:
    timeout_sec = args.tcp_timeout if timeout is None else timeout
    with socket.create_connection((args.device_ip, args.tcp_port), timeout=timeout_sec) as sock:
        sock.settimeout(0.5)
        sock.sendall((command.rstrip("\n") + "\n").encode())
        data = bytearray()
        deadline = time.monotonic() + timeout_sec

        while time.monotonic() < deadline:
            try:
                chunk = sock.recv(8192)
            except socket.timeout:
                continue
            if not chunk:
                break
            data.extend(chunk)

        return data.decode("utf-8", errors="replace")


def tcpctl_expect_ok(args: argparse.Namespace, command: str) -> str:
    output = tcpctl_request(args, command)
    if "\nOK" not in output and not output.rstrip().endswith("OK"):
        raise RuntimeError(f"tcpctl command did not end with OK: {command}\n{output}")
    return output


def wait_for_tcpctl(args: argparse.Namespace, timeout_sec: float) -> str:
    deadline = time.monotonic() + timeout_sec
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            output = tcpctl_request(args, "ping", timeout=2.0)
            if "pong" in output and "OK" in output:
                return output
        except OSError as exc:
            last_error = exc
        time.sleep(0.5)

    raise RuntimeError(f"tcpctl did not become ready: {last_error}")


def tcpctl_listen_command(args: argparse.Namespace) -> str:
    return (
        f"run {args.device_binary} listen "
        f"{args.tcp_port} {args.idle_timeout} {args.max_clients}"
    )


def command_start(args: argparse.Namespace) -> int:
    best_effort_hide_menu(args)
    command = tcpctl_listen_command(args)
    log(f"starting via bridge: {command}")
    runner = BridgeRunThread(args, command, echo=True)
    runner.start()
    try:
        while not runner.done.is_set():
            time.sleep(0.2)
    except KeyboardInterrupt:
        log("interrupt: requesting tcpctl shutdown")
        try:
            print(tcpctl_request(args, "shutdown"), end="")
        except Exception as exc:
            log(f"shutdown request failed: {exc}")
        runner.join(args.bridge_timeout)
        return 130

    if runner.error is not None:
        raise RuntimeError(f"bridge run failed: {runner.error}")
    return 0


def command_call(args: argparse.Namespace) -> int:
    if not args.line:
        raise SystemExit("call requires a command line")
    command = " ".join(args.line)
    print(tcpctl_request(args, command), end="")
    return 0


def command_ping(args: argparse.Namespace) -> int:
    print(tcpctl_request(args, "ping"), end="")
    return 0


def command_version(args: argparse.Namespace) -> int:
    print(tcpctl_request(args, "version"), end="")
    return 0


def command_status(args: argparse.Namespace) -> int:
    print(tcpctl_request(args, "status"), end="")
    return 0


def command_run(args: argparse.Namespace) -> int:
    if not args.run_args:
        raise SystemExit("run requires an absolute path and optional args")
    run_args = args.run_args
    if run_args and run_args[0] == "--":
        run_args = run_args[1:]
    if not run_args:
        raise SystemExit("run requires an absolute path and optional args")
    command = "run " + " ".join(shlex.quote(part) for part in run_args)
    print(tcpctl_request(args, command), end="")
    return 0


def command_stop(args: argparse.Namespace) -> int:
    print(tcpctl_request(args, "shutdown"), end="")
    return 0


def command_install(args: argparse.Namespace) -> int:
    local_binary = Path(args.local_binary)
    if not local_binary.exists():
        raise FileNotFoundError(local_binary)

    local_hash = sha256_file(local_binary)
    best_effort_hide_menu(args)
    receive_command = (
        f"run {args.toybox} netcat -l -p {args.transfer_port} "
        f"{args.toybox} dd of={args.device_binary} bs=4096"
    )
    log(f"device receive command: {receive_command}")
    runner = BridgeRunThread(args, receive_command, echo=args.verbose)
    runner.start()
    time.sleep(args.transfer_delay)

    with socket.create_connection((args.device_ip, args.transfer_port), timeout=args.connect_timeout) as sock:
        with local_binary.open("rb") as fp:
            while True:
                chunk = fp.read(1024 * 1024)
                if not chunk:
                    break
                sock.sendall(chunk)
        sock.shutdown(socket.SHUT_WR)

    runner.join(args.transfer_timeout)
    if runner.is_alive():
        raise RuntimeError("device transfer did not finish")
    if runner.error is not None:
        raise RuntimeError(f"bridge transfer failed: {runner.error}")
    if "[done] run" not in runner.text():
        raise RuntimeError(f"device transfer did not report done:\n{runner.text()}")

    print(runner.text(), end="" if runner.text().endswith("\n") else "\n")
    chmod_output = bridge_command(
        args.bridge_host,
        args.bridge_port,
        f"run {args.toybox} chmod 755 {args.device_binary}",
        args.bridge_timeout,
    )
    print(chmod_output, end="" if chmod_output.endswith("\n") else "\n")
    sha_output = bridge_command(
        args.bridge_host,
        args.bridge_port,
        f"run {args.toybox} sha256sum {args.device_binary}",
        args.bridge_timeout,
    )
    print(sha_output, end="" if sha_output.endswith("\n") else "\n")
    if local_hash not in sha_output:
        raise RuntimeError(f"device sha256 did not match local {local_hash}")

    log(f"installed {args.device_binary} sha256={local_hash}")
    return 0


def command_smoke(args: argparse.Namespace) -> int:
    if args.install_first:
        command_install(args)

    best_effort_hide_menu(args)
    runner = BridgeRunThread(args, tcpctl_listen_command(args), echo=args.verbose)
    runner.start()
    wait_for_tcpctl(args, args.ready_timeout)

    checks = [
        ("ping", "ping"),
        ("version", "version"),
        ("status", "status"),
        ("run-uname", f"run {args.toybox} uname -a"),
        ("run-ifconfig", f"run {args.toybox} ifconfig ncm0"),
    ]
    for label, command in checks:
        print(f"--- {label} ---")
        output = tcpctl_expect_ok(args, command)
        print(output, end="" if output.endswith("\n") else "\n")

    print("--- shutdown ---")
    shutdown_output = tcpctl_expect_ok(args, "shutdown")
    print(shutdown_output, end="" if shutdown_output.endswith("\n") else "\n")

    runner.join(args.bridge_timeout)
    if runner.is_alive():
        raise RuntimeError("tcpctl serial run did not finish after shutdown")
    if runner.error is not None:
        raise RuntimeError(f"bridge run failed: {runner.error}")

    print("--- serial-run ---")
    print(runner.text(), end="" if runner.text().endswith("\n") else "\n")
    if "[done] run" not in runner.text():
        raise RuntimeError("tcpctl serial run did not finish cleanly")

    print("--- bridge-version ---")
    bridge_output = bridge_command(
        args.bridge_host,
        args.bridge_port,
        "version",
        args.bridge_timeout,
        markers=(b"[done] version", b"[err] version"),
    )
    print(bridge_output, end="" if bridge_output.endswith("\n") else "\n")

    print("--- ncm-ping ---")
    result = subprocess.run(
        ["ping", "-c", "3", "-W", "2", args.device_ip],
        check=False,
        text=True,
        capture_output=True,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"ping failed rc={result.returncode}")

    return 0


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--bridge-host", default=DEFAULT_BRIDGE_HOST)
    parser.add_argument("--bridge-port", type=int, default=DEFAULT_BRIDGE_PORT)
    parser.add_argument("--device-ip", default=DEFAULT_DEVICE_IP)
    parser.add_argument("--tcp-port", type=int, default=DEFAULT_TCP_PORT)
    parser.add_argument("--device-binary", default=DEFAULT_DEVICE_BINARY)
    parser.add_argument("--toybox", default=DEFAULT_TOYBOX)
    parser.add_argument("--idle-timeout", type=int, default=60)
    parser.add_argument("--max-clients", type=int, default=8)
    parser.add_argument("--connect-timeout", type=float, default=5.0)
    parser.add_argument("--tcp-timeout", type=float, default=10.0)
    parser.add_argument("--bridge-timeout", type=float, default=30.0)
    parser.add_argument("--menu-hide-sleep", type=float, default=3.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Host helper for the A90 native-init NCM tcpctl service."
    )
    add_common_args(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="start tcpctl through the serial bridge and stream logs")
    start.set_defaults(func=command_start)

    call = subparsers.add_parser("call", help="send one raw tcpctl command line")
    call.add_argument("line", nargs=argparse.REMAINDER)
    call.set_defaults(func=command_call)

    subparsers.add_parser("ping", help="send ping").set_defaults(func=command_ping)
    subparsers.add_parser("version", help="send version").set_defaults(func=command_version)
    subparsers.add_parser("status", help="send status").set_defaults(func=command_status)
    subparsers.add_parser("stop", help="send shutdown").set_defaults(func=command_stop)

    run = subparsers.add_parser("run", help="run an absolute-path command through tcpctl")
    run.add_argument("run_args", nargs=argparse.REMAINDER)
    run.set_defaults(func=command_run)

    install = subparsers.add_parser("install", help="install a90_tcpctl to /cache/bin over NCM")
    install.add_argument("--local-binary", default=str(DEFAULT_LOCAL_BINARY))
    install.add_argument("--transfer-port", type=int, default=DEFAULT_TRANSFER_PORT)
    install.add_argument("--transfer-delay", type=float, default=2.0)
    install.add_argument("--transfer-timeout", type=float, default=90.0)
    install.add_argument("--verbose", action="store_true")
    install.set_defaults(func=command_install)

    smoke = subparsers.add_parser("smoke", help="start tcpctl, run checks, stop it")
    smoke.add_argument("--install-first", action="store_true")
    smoke.add_argument("--local-binary", default=str(DEFAULT_LOCAL_BINARY))
    smoke.add_argument("--transfer-port", type=int, default=DEFAULT_TRANSFER_PORT)
    smoke.add_argument("--transfer-delay", type=float, default=2.0)
    smoke.add_argument("--transfer-timeout", type=float, default=90.0)
    smoke.add_argument("--ready-timeout", type=float, default=15.0)
    smoke.add_argument("--verbose", action="store_true")
    smoke.set_defaults(func=command_smoke)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        raise SystemExit(130)
