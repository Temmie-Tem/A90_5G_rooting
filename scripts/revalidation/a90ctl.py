#!/usr/bin/env python3

import argparse
import json
import re
import socket
import sys
import time
from dataclasses import dataclass


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 54321
CMDV1_RETRY_INTERVAL_SEC = 0.5
BRIDGE_SERIAL_MISSING_TEXT = "serial device is not connected"
END_RE = re.compile(r"^A90P1 END (?P<fields>.+)$", re.MULTILINE)
BEGIN_RE = re.compile(r"^A90P1 BEGIN (?P<fields>.+)$", re.MULTILINE)


@dataclass
class ProtocolResult:
    begin: dict[str, str]
    end: dict[str, str]
    text: str

    @property
    def rc(self) -> int:
        return int(self.end.get("rc", "1"), 0)

    @property
    def status(self) -> str:
        return self.end.get("status", "missing")


def log(message: str) -> None:
    print(f"[a90ctl] {message}", file=sys.stderr, flush=True)


def parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in text.split():
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        fields[key] = value
    return fields


def require_shell_safe_args(command: list[str]) -> None:
    for arg in command:
        if not arg:
            raise SystemExit("empty arguments are not supported by native split_args")
        if any(ch.isspace() for ch in arg):
            raise SystemExit(f"argument contains whitespace and cannot be sent safely: {arg!r}")


def read_until(sock: socket.socket, markers: tuple[bytes, ...], timeout_sec: float) -> bytes:
    deadline = time.monotonic() + timeout_sec
    data = bytearray()
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(8192)
        except socket.timeout:
            continue
        if not chunk:
            break
        data.extend(chunk)
        if any(marker in data for marker in markers):
            time.sleep(0.15)
            try:
                data.extend(sock.recv(8192))
            except socket.timeout:
                pass
            break
    return bytes(data)


def bridge_exchange(host: str,
                    port: int,
                    line: str,
                    timeout_sec: float,
                    markers: tuple[bytes, ...]) -> str:
    connect_timeout = min(3.0, max(0.1, timeout_sec))
    with socket.create_connection((host, port), timeout=connect_timeout) as sock:
        sock.settimeout(0.25)
        sock.sendall(("\n" + line + "\n").encode("utf-8"))
        data = read_until(sock, markers, timeout_sec)
    return data.decode("utf-8", errors="replace")


def should_retry_cmdv1_exchange(text: str) -> bool:
    return text.strip() == "" or BRIDGE_SERIAL_MISSING_TEXT in text


def sleep_before_retry(deadline: float) -> None:
    remaining = deadline - time.monotonic()
    if remaining > 0:
        time.sleep(min(CMDV1_RETRY_INTERVAL_SEC, remaining))


def parse_protocol_output(text: str) -> ProtocolResult:
    begin_match = BEGIN_RE.search(text)
    end_match = END_RE.search(text)
    if end_match is None:
        raise RuntimeError(f"A90P1 END marker not found\n{text}")
    return ProtocolResult(
        begin=parse_fields(begin_match.group("fields")) if begin_match else {},
        end=parse_fields(end_match.group("fields")),
        text=text,
    )


def run_cmdv1(args: argparse.Namespace, command: list[str]) -> ProtocolResult:
    return run_cmdv1_command(args.host, args.port, args.timeout, command)


def run_cmdv1_command(host: str,
                      port: int,
                      timeout_sec: float,
                      command: list[str]) -> ProtocolResult:
    deadline = time.monotonic() + timeout_sec
    last_error: OSError | None = None
    last_text = ""

    require_shell_safe_args(command)
    line = "cmdv1 " + " ".join(command)
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        try:
            text = bridge_exchange(
                host,
                port,
                line,
                remaining,
                markers=(b"A90P1 END ",),
            )
        except OSError as exc:
            last_error = exc
            sleep_before_retry(deadline)
            continue

        if END_RE.search(text) is not None:
            return parse_protocol_output(text)
        if not should_retry_cmdv1_exchange(text):
            return parse_protocol_output(text)

        last_text = text
        sleep_before_retry(deadline)

    detail = f"A90P1 END marker not found before timeout ({timeout_sec:.1f}s)"
    if last_error is not None:
        detail += f"\nlast socket error: {last_error}"
    if last_text:
        detail += f"\nlast bridge output:\n{last_text}"
    raise RuntimeError(detail)


def send_hide(args: argparse.Namespace) -> None:
    text = bridge_exchange(
        args.host,
        args.port,
        "hide",
        min(args.timeout, 8.0),
        markers=(b"[busy]", b"[done]", b"[err]"),
    )
    if args.verbose:
        print(text, end="" if text.endswith("\n") else "\n", file=sys.stderr)


def result_to_json(result: ProtocolResult) -> str:
    return json.dumps(
        {
            "begin": result.begin,
            "end": result.end,
            "rc": result.rc,
            "status": result.status,
            "text": result.text,
        },
        ensure_ascii=False,
        indent=2,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one native-init shell command through cmdv1/A90P1 framing."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--allow-error", action="store_true")
    parser.add_argument("--hide-on-busy", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("command is required, e.g. a90ctl.py status")

    result = run_cmdv1(args, command)
    if args.hide_on_busy and result.status == "busy":
        log("command was busy; sending hide and retrying once")
        send_hide(args)
        result = run_cmdv1(args, command)

    if args.as_json:
        print(result_to_json(result))
    elif not args.quiet:
        print(result.text, end="" if result.text.endswith("\n") else "\n")

    if result.rc != 0 and not args.allow_error:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
