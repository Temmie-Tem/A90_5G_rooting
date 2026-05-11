#!/usr/bin/env python3
"""Host-local A90B1 command broker for A90 native-init control paths."""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import socket
import stat
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from a90ctl import ProtocolResult, run_cmdv1_command
from a90harness.evidence import append_private_jsonl, ensure_private_dir, write_private_json


PROTO = "A90B1"
DEFAULT_BRIDGE_HOST = "127.0.0.1"
DEFAULT_BRIDGE_PORT = 54321
DEFAULT_RUNTIME_DIR = Path("tmp/a90-broker")
DEFAULT_SOCKET_NAME = "a90b1.sock"
DEFAULT_AUDIT_NAME = "audit.jsonl"
MAX_REQUEST_BYTES = 64 * 1024
MAX_TIMEOUT_MS = 5 * 60 * 1000
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,96}$")
CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9_.:@%+=,-]{1,128}$")


OBSERVE_COMMANDS = {
    "version",
    "status",
    "bootstatus",
    "selftest",
    "pid1guard",
    "runtime",
    "storage",
    "mountsd",
    "helpers",
    "userland",
    "service",
    "netservice",
    "rshell",
    "diag",
    "wififeas",
    "wifiinv",
    "logpath",
    "hudlog",
    "timeline",
    "last",
    "pwd",
    "uname",
    "mounts",
    "ls",
    "cat",
    "stat",
    "exposure",
    "policycheck",
    "kernelinv",
    "sensormap",
    "pstore",
    "watchdoginv",
    "tracefs",
}

OPERATOR_COMMANDS = {
    "screenmenu",
    "menu",
    "hide",
    "hidemenu",
    "resume",
    "autohud",
    "stophud",
    "longsoak",
    "statushud",
    "watchhud",
}

EXCLUSIVE_COMMANDS = {
    "run",
    "runandroid",
    "cpustress",
    "mountsystem",
    "prepareandroid",
    "startadbd",
    "stopadbd",
    "netservice",
    "rshell",
    "usbacmreset",
    "helper",
    "helpers",
    "userland",
}

REBINDS_OR_DESTRUCTIVE_COMMANDS = {
    "reboot",
    "recovery",
    "poweroff",
}

OBSERVE_SUBCOMMANDS = {
    "mountsd": {"status"},
    "netservice": {"status"},
    "rshell": {"status", "audit"},
    "service": {"list", "status"},
    "helpers": {"status", "list", "verify"},
    "userland": {"status", "verbose"},
    "hudlog": {"status"},
    "longsoak": {"status"},
}

ABSENT_SUBCOMMAND_DEFAULTS_TO_STATUS = {
    "netservice",
    "rshell",
    "service",
    "helpers",
    "userland",
    "hudlog",
}


@dataclass(frozen=True)
class BrokerRequest:
    request_id: str
    client_id: str
    op: str
    argv: list[str]
    timeout_ms: int
    command_class: str


@dataclass
class BrokerResponse:
    proto: str
    request_id: str
    ok: bool
    rc: int | None
    status: str
    duration_ms: int
    backend: str
    command_class: str
    text: str
    error: str = ""

    def to_wire(self) -> dict[str, Any]:
        return {
            "proto": self.proto,
            "id": self.request_id,
            "ok": self.ok,
            "rc": self.rc,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "backend": self.backend,
            "class": self.command_class,
            "text": self.text,
            "error": self.error,
        }


@dataclass(frozen=True)
class WorkItem:
    request: BrokerRequest
    response_queue: "queue.Queue[BrokerResponse]"


class BrokerError(RuntimeError):
    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status


class Backend:
    name = "backend"

    def execute(self, request: BrokerRequest) -> tuple[int, str, str]:
        raise NotImplementedError


class AcmCmdv1Backend(Backend):
    name = "acm-cmdv1"

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def execute(self, request: BrokerRequest) -> tuple[int, str, str]:
        result: ProtocolResult = run_cmdv1_command(
            self.host,
            self.port,
            request.timeout_ms / 1000.0,
            request.argv,
            retry_unsafe=False,
        )
        return result.rc, result.status, result.text


class FakeBackend(Backend):
    name = "fake"

    def execute(self, request: BrokerRequest) -> tuple[int, str, str]:
        if request.argv and request.argv[0] == "fail":
            return 1, "error", "fake failure\n"
        return 0, "ok", f"fake {' '.join(request.argv)}\n"


def log(message: str) -> None:
    print(f"[a90-broker] {message}", file=sys.stderr, flush=True)


def now_ms() -> int:
    return int(time.time() * 1000)


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000)


def command_subcommand(argv: list[str]) -> str | None:
    return argv[1] if len(argv) > 1 else None


def classify_command(argv: list[str]) -> str:
    if not argv:
        raise BrokerError("bad-request", "argv must not be empty")

    name = argv[0]
    if name in REBINDS_OR_DESTRUCTIVE_COMMANDS:
        return "rebind-destructive"

    allowed_subcommands = OBSERVE_SUBCOMMANDS.get(name)
    if allowed_subcommands is not None:
        subcommand = command_subcommand(argv)
        if subcommand is not None and subcommand in allowed_subcommands:
            return "observe"
        if subcommand is None and name in ABSENT_SUBCOMMAND_DEFAULTS_TO_STATUS:
            return "observe"
        return "exclusive"

    if name in OPERATOR_COMMANDS:
        return "operator-action"
    if name in EXCLUSIVE_COMMANDS:
        return "exclusive"
    if name in OBSERVE_COMMANDS:
        return "observe"
    return "exclusive"


def validate_id(value: Any, label: str, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str):
        raise BrokerError("bad-request", f"{label} must be a string")
    if not pattern.match(value):
        raise BrokerError("bad-request", f"{label} contains unsupported characters or length")
    return value


def validate_argv(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise BrokerError("bad-request", "argv must be a non-empty list")
    argv: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise BrokerError("bad-request", f"argv[{index}] must be a string")
        if not item or "\x00" in item or "\r" in item or "\n" in item:
            raise BrokerError("bad-request", f"argv[{index}] is empty or contains control separators")
        argv.append(item)
    return argv


def parse_timeout_ms(value: Any) -> int:
    if value is None:
        return 10_000
    if not isinstance(value, int):
        raise BrokerError("bad-request", "timeout_ms must be an integer")
    if value <= 0 or value > MAX_TIMEOUT_MS:
        raise BrokerError("bad-request", f"timeout_ms must be 1..{MAX_TIMEOUT_MS}")
    return value


def parse_wire_request(payload: dict[str, Any]) -> BrokerRequest:
    if payload.get("proto") != PROTO:
        raise BrokerError("bad-request", f"proto must be {PROTO}")
    request_id = validate_id(payload.get("id"), "id", REQUEST_ID_RE)
    client_id = payload.get("client_id", f"pid:{os.getpid()}")
    client_id = validate_id(client_id, "client_id", CLIENT_ID_RE)
    op = payload.get("op")
    if op != "cmd":
        raise BrokerError("bad-request", "only op=cmd is supported")
    argv = validate_argv(payload.get("argv"))
    timeout_ms = parse_timeout_ms(payload.get("timeout_ms"))
    actual_class = classify_command(argv)
    requested_class = payload.get("class")
    if requested_class is not None and requested_class != actual_class:
        raise BrokerError(
            "bad-request",
            f"class mismatch: requested {requested_class!r}, actual {actual_class!r}",
        )
    return BrokerRequest(
        request_id=request_id,
        client_id=client_id,
        op=op,
        argv=argv,
        timeout_ms=timeout_ms,
        command_class=actual_class,
    )


def response_from_error(request_id: str,
                        status: str,
                        message: str,
                        *,
                        command_class: str = "unknown",
                        backend: str = "broker",
                        duration_ms: int = 0) -> BrokerResponse:
    return BrokerResponse(
        proto=PROTO,
        request_id=request_id,
        ok=False,
        rc=None,
        status=status,
        duration_ms=duration_ms,
        backend=backend,
        command_class=command_class,
        text="",
        error=message,
    )


def read_json_line(conn: socket.socket) -> dict[str, Any]:
    data = bytearray()
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data.extend(chunk)
        if b"\n" in chunk:
            break
        if len(data) > MAX_REQUEST_BYTES:
            raise BrokerError("bad-request", "request exceeds maximum size")
    line = bytes(data).split(b"\n", 1)[0]
    if not line:
        raise BrokerError("bad-request", "empty request")
    try:
        payload = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BrokerError("bad-request", f"invalid JSON request: {exc}") from exc
    if not isinstance(payload, dict):
        raise BrokerError("bad-request", "request must be a JSON object")
    return payload


def write_json_line(conn: socket.socket, payload: dict[str, Any]) -> None:
    conn.sendall((json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))


def safe_unlink_socket(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode):
        raise RuntimeError(f"refusing symlink socket path: {path}")
    if not stat.S_ISSOCK(info.st_mode):
        raise RuntimeError(f"refusing to replace non-socket path: {path}")
    path.unlink()


def prepare_runtime_paths(runtime_dir: Path,
                          socket_name: str,
                          audit_name: str) -> tuple[Path, Path]:
    ensure_private_dir(runtime_dir)
    socket_path = runtime_dir / socket_name
    audit_path = runtime_dir / audit_name
    if socket_path.name != socket_name or "/" in socket_name or socket_name in {"", ".", ".."}:
        raise RuntimeError("socket name must be one path component")
    if audit_path.name != audit_name or "/" in audit_name or audit_name in {"", ".", ".."}:
        raise RuntimeError("audit name must be one path component")
    safe_unlink_socket(socket_path)
    return socket_path, audit_path


class BrokerServer:
    def __init__(self, backend: Backend, socket_path: Path, audit_path: Path) -> None:
        self.backend = backend
        self.socket_path = socket_path
        self.audit_path = audit_path
        self.work_queue: "queue.Queue[WorkItem | None]" = queue.Queue()
        self.audit_lock = threading.Lock()
        self.worker = threading.Thread(target=self.worker_loop, name="a90-broker-worker", daemon=True)

    def audit(self, event: str, payload: dict[str, Any]) -> None:
        record = {"ts_ms": now_ms(), "event": event, **payload}
        with self.audit_lock:
            append_private_jsonl(self.audit_path, record)

    def worker_loop(self) -> None:
        while True:
            item = self.work_queue.get()
            if item is None:
                self.work_queue.task_done()
                return
            started = monotonic_ms()
            request = item.request
            self.audit(
                "dispatch",
                {
                    "id": request.request_id,
                    "client_id": request.client_id,
                    "argv": request.argv,
                    "class": request.command_class,
                    "backend": self.backend.name,
                },
            )
            try:
                if request.command_class == "rebind-destructive":
                    raise BrokerError(
                        "operator-required",
                        "rebind/destructive command is not broker-multiplexed; use foreground raw control",
                    )
                rc, status, text = self.backend.execute(request)
                duration_ms = monotonic_ms() - started
                response = BrokerResponse(
                    proto=PROTO,
                    request_id=request.request_id,
                    ok=rc == 0 and status == "ok",
                    rc=rc,
                    status=status,
                    duration_ms=duration_ms,
                    backend=self.backend.name,
                    command_class=request.command_class,
                    text=text,
                )
            except BrokerError as exc:
                duration_ms = monotonic_ms() - started
                response = response_from_error(
                    request.request_id,
                    exc.status,
                    str(exc),
                    command_class=request.command_class,
                    backend=self.backend.name,
                    duration_ms=duration_ms,
                )
            except Exception as exc:  # noqa: BLE001 - broker must report backend failures
                duration_ms = monotonic_ms() - started
                response = response_from_error(
                    request.request_id,
                    "transport-error",
                    f"{type(exc).__name__}: {exc}",
                    command_class=request.command_class,
                    backend=self.backend.name,
                    duration_ms=duration_ms,
                )
            self.audit(
                "result",
                {
                    "id": request.request_id,
                    "client_id": request.client_id,
                    "class": request.command_class,
                    "backend": response.backend,
                    "ok": response.ok,
                    "rc": response.rc,
                    "status": response.status,
                    "duration_ms": response.duration_ms,
                    "error": response.error,
                },
            )
            item.response_queue.put(response)
            self.work_queue.task_done()

    def handle_client(self, conn: socket.socket) -> None:
        request_id = "missing"
        try:
            conn.settimeout(1.0)
            payload = read_json_line(conn)
            request_id = str(payload.get("id", "missing"))
            request = parse_wire_request(payload)
            response_queue: "queue.Queue[BrokerResponse]" = queue.Queue(maxsize=1)
            self.audit(
                "accept",
                {
                    "id": request.request_id,
                    "client_id": request.client_id,
                    "argv": request.argv,
                    "class": request.command_class,
                },
            )
            self.work_queue.put(WorkItem(request, response_queue))
            response = response_queue.get(timeout=(request.timeout_ms / 1000.0) + 5.0)
        except BrokerError as exc:
            response = response_from_error(request_id, exc.status, str(exc))
        except queue.Empty:
            response = response_from_error(request_id, "timeout", "broker response wait timed out")
        except Exception as exc:  # noqa: BLE001 - keep broker alive after client errors
            response = response_from_error(request_id, "broker-error", f"{type(exc).__name__}: {exc}")
        try:
            write_json_line(conn, response.to_wire())
        finally:
            conn.close()

    def serve_forever(self) -> None:
        self.worker.start()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(self.socket_path))
            os.chmod(self.socket_path, 0o600)
            server.listen(16)
            self.audit("start", {"socket": str(self.socket_path), "backend": self.backend.name})
            log(f"ready socket={self.socket_path} backend={self.backend.name}")
            while True:
                conn, _ = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn,), daemon=True)
                thread.start()


def connect_and_call(socket_path: Path, payload: dict[str, Any], timeout_sec: float) -> dict[str, Any]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout_sec)
        client.connect(str(socket_path))
        write_json_line(client, payload)
        response = read_json_line(client)
    return response


def build_request(args: argparse.Namespace, argv: list[str]) -> dict[str, Any]:
    request_id = args.request_id or f"req-{uuid.uuid4().hex}"
    payload = {
        "proto": PROTO,
        "id": request_id,
        "client_id": args.client_id,
        "op": "cmd",
        "argv": argv,
        "timeout_ms": int(args.timeout * 1000),
    }
    if args.command_class:
        payload["class"] = args.command_class
    return payload


def make_backend(args: argparse.Namespace) -> Backend:
    if args.backend == "fake":
        return FakeBackend()
    return AcmCmdv1Backend(args.bridge_host, args.bridge_port)


def cmd_serve(args: argparse.Namespace) -> int:
    socket_path, audit_path = prepare_runtime_paths(args.runtime_dir, args.socket_name, args.audit_name)
    metadata = {
        "proto": PROTO,
        "backend": args.backend,
        "bridge_host": args.bridge_host,
        "bridge_port": args.bridge_port,
        "socket": str(socket_path),
        "audit": str(audit_path),
    }
    write_private_json(args.runtime_dir / "broker.json", metadata)
    server = BrokerServer(make_backend(args), socket_path, audit_path)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("stopping on interrupt")
        return 130
    return 0


def cmd_call(args: argparse.Namespace) -> int:
    argv = args.command
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        raise SystemExit("command is required")
    socket_path = args.socket if args.socket else args.runtime_dir / args.socket_name
    payload = build_request(args, argv)
    response = connect_and_call(socket_path, payload, args.timeout + 5.0)
    if args.json:
        print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if response.get("text"):
            print(response["text"], end="" if response["text"].endswith("\n") else "\n")
        if response.get("error"):
            print(response["error"], file=sys.stderr)
    return 0 if response.get("ok") or args.allow_error else 1


def cmd_selftest(_: argparse.Namespace) -> int:
    temp_dir = Path(tempfile.mkdtemp(prefix="a90-broker-selftest."))
    try:
        socket_path, audit_path = prepare_runtime_paths(temp_dir, DEFAULT_SOCKET_NAME, DEFAULT_AUDIT_NAME)
        server = BrokerServer(FakeBackend(), socket_path, audit_path)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        deadline = time.monotonic() + 5.0
        while not socket_path.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        if not socket_path.exists():
            raise RuntimeError("selftest server did not create socket")

        status_request = {
            "proto": PROTO,
            "id": "selftest-status",
            "client_id": "selftest",
            "op": "cmd",
            "argv": ["status"],
            "timeout_ms": 1000,
            "class": "observe",
        }
        status_response = connect_and_call(socket_path, status_request, 3.0)
        if not status_response.get("ok"):
            raise RuntimeError(f"status response failed: {status_response}")
        if status_response.get("class") != "observe":
            raise RuntimeError(f"unexpected status class: {status_response}")

        mountsd_request = {
            "proto": PROTO,
            "id": "selftest-mountsd",
            "client_id": "selftest",
            "op": "cmd",
            "argv": ["mountsd"],
            "timeout_ms": 1000,
            "class": "exclusive",
        }
        mountsd_response = connect_and_call(socket_path, mountsd_request, 3.0)
        if not mountsd_response.get("ok") or mountsd_response.get("class") != "exclusive":
            raise RuntimeError(f"bare mountsd was not classified exclusive: {mountsd_response}")

        blocked_request = {
            "proto": PROTO,
            "id": "selftest-reboot",
            "client_id": "selftest",
            "op": "cmd",
            "argv": ["reboot"],
            "timeout_ms": 1000,
            "class": "rebind-destructive",
        }
        blocked_response = connect_and_call(socket_path, blocked_request, 3.0)
        if blocked_response.get("status") != "operator-required":
            raise RuntimeError(f"reboot was not blocked: {blocked_response}")

        print("a90_broker selftest: PASS")
        return 0
    finally:
        try:
            socket_file = temp_dir / DEFAULT_SOCKET_NAME
            if socket_file.exists() and not socket_file.is_symlink():
                socket_file.unlink()
            audit_file = temp_dir / DEFAULT_AUDIT_NAME
            if audit_file.exists() and not audit_file.is_symlink():
                audit_file.unlink()
            meta_file = temp_dir / "broker.json"
            if meta_file.exists() and not meta_file.is_symlink():
                meta_file.unlink()
            temp_dir.rmdir()
        except OSError:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A90B1 host-local command broker.")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    serve = subparsers.add_parser("serve", help="run the host-local broker")
    serve.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR)
    serve.add_argument("--socket-name", default=DEFAULT_SOCKET_NAME)
    serve.add_argument("--audit-name", default=DEFAULT_AUDIT_NAME)
    serve.add_argument("--backend", choices=("acm-cmdv1", "fake"), default="acm-cmdv1")
    serve.add_argument("--bridge-host", default=DEFAULT_BRIDGE_HOST)
    serve.add_argument("--bridge-port", type=int, default=DEFAULT_BRIDGE_PORT)
    serve.set_defaults(func=cmd_serve)

    call = subparsers.add_parser("call", help="send one command through the broker")
    call.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR)
    call.add_argument("--socket-name", default=DEFAULT_SOCKET_NAME)
    call.add_argument("--socket", type=Path)
    call.add_argument("--timeout", type=float, default=10.0)
    call.add_argument("--request-id")
    call.add_argument("--client-id", default=f"cli:{os.getpid()}")
    call.add_argument("--class", dest="command_class")
    call.add_argument("--json", action="store_true")
    call.add_argument("--allow-error", action="store_true")
    call.add_argument("command", nargs=argparse.REMAINDER)
    call.set_defaults(func=cmd_call)

    selftest = subparsers.add_parser("selftest", help="run broker fake-backend selftest")
    selftest.set_defaults(func=cmd_selftest)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
