#!/usr/bin/env python3

import argparse
import errno
import glob
import os
import selectors
import signal
import socket
import sys
import termios
import time
from pathlib import Path


DEFAULT_DEVICE_GLOB = "/dev/serial/by-id/usb-SAMSUNG_SAMSUNG_Android_*"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 54321
DEFAULT_BAUD = 115200

BAUD_MAP = {
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
    230400: termios.B230400,
    460800: termios.B460800,
    921600: termios.B921600,
}


class Bridge:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.selector = selectors.DefaultSelector()
        self.server = self._open_server()
        self.selector.register(self.server, selectors.EVENT_READ, "server")
        self.serial_fd = None
        self.serial_device = None
        self.serial_stat = None
        self.client = None
        self.client_addr = None
        self.capture_fp = None
        self.stop_requested = False
        self.next_serial_retry = 0.0
        self.next_serial_identity_check = 0.0

        if self.args.capture:
            capture_path = Path(self.args.capture)
            capture_path.parent.mkdir(parents=True, exist_ok=True)
            self.capture_fp = capture_path.open("ab", buffering=0)

    def _open_server(self) -> socket.socket:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.args.host, self.args.port))
        server.listen(1)
        server.setblocking(False)
        self.log(f"tcp listener ready on {self.args.host}:{self.args.port}")
        return server

    def log(self, message: str) -> None:
        print(f"[bridge] {message}", file=sys.stderr, flush=True)

    def resolve_device(self) -> str | None:
        if self.args.device != "auto":
            return self.args.device

        matches = sorted(glob.glob(self.args.device_glob))
        if not matches:
            return None
        return matches[0]

    def configure_serial(self, fd: int) -> None:
        attrs = termios.tcgetattr(fd)
        baud = BAUD_MAP[self.args.baud]

        attrs[0] = termios.IGNBRK
        attrs[1] = 0
        attrs[2] &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
        attrs[2] |= termios.CLOCAL | termios.CREAD | termios.CS8
        attrs[3] = 0
        attrs[4] = baud
        attrs[5] = baud
        attrs[6][termios.VMIN] = 1
        attrs[6][termios.VTIME] = 0

        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        termios.tcflush(fd, termios.TCIOFLUSH)

    def open_serial(self) -> None:
        device = self.resolve_device()
        if device is None:
            return

        try:
            fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            self.configure_serial(fd)
            serial_stat = os.fstat(fd)
        except OSError as exc:
            if exc.errno in {errno.ENOENT, errno.ENODEV, errno.EACCES, errno.EBUSY}:
                self.log(f"serial not ready at {device}: {exc.strerror}")
                return
            raise

        self.serial_fd = fd
        self.serial_device = device
        self.serial_stat = (
            serial_stat.st_dev,
            serial_stat.st_ino,
            serial_stat.st_rdev,
        )
        self.next_serial_identity_check = time.monotonic() + 0.5
        self.selector.register(fd, selectors.EVENT_READ, "serial")
        self.log(f"serial connected: {device}")

    def close_serial(self) -> None:
        if self.serial_fd is None:
            return

        try:
            self.selector.unregister(self.serial_fd)
        except Exception:
            pass

        try:
            os.close(self.serial_fd)
        except OSError:
            pass

        self.serial_fd = None
        self.serial_device = None
        self.serial_stat = None
        self.next_serial_retry = time.monotonic() + self.args.retry_interval
        self.log("serial disconnected")
        self.close_client()

    def check_serial_identity(self) -> None:
        if self.serial_fd is None:
            return

        now = time.monotonic()
        if now < self.next_serial_identity_check:
            return

        self.next_serial_identity_check = now + 0.5
        device = self.resolve_device()
        if device is None:
            self.log("serial device path disappeared")
            self.close_serial()
            return

        try:
            current_stat = os.stat(device)
        except OSError as exc:
            if exc.errno in {errno.ENOENT, errno.ENODEV, errno.EACCES}:
                self.log(f"serial device path is no longer valid: {exc.strerror}")
                self.close_serial()
                return
            raise

        current_identity = (
            current_stat.st_dev,
            current_stat.st_ino,
            current_stat.st_rdev,
        )
        if current_identity != self.serial_stat:
            self.log(f"serial device was re-enumerated: {device}")
            self.close_serial()

    def accept_client(self) -> None:
        conn, addr = self.server.accept()
        conn.setblocking(False)

        if self.serial_fd is None and not self.args.allow_client_without_serial:
            self.log(f"rejecting client from {addr[0]}:{addr[1]}: serial not connected")
            try:
                conn.sendall(b"[bridge] serial device is not connected; retry later\r\n")
            except OSError:
                pass
            conn.close()
            return

        if self.client is not None:
            self.log(f"rejecting extra client from {addr[0]}:{addr[1]}")
            conn.close()
            return

        self.client = conn
        self.client_addr = addr
        self.selector.register(conn, selectors.EVENT_READ, "client")
        self.log(f"client connected: {addr[0]}:{addr[1]}")

    def close_client(self) -> None:
        if self.client is None:
            return

        try:
            self.selector.unregister(self.client)
        except Exception:
            pass

        try:
            self.client.close()
        except OSError:
            pass

        if self.client_addr is not None:
            self.log(f"client disconnected: {self.client_addr[0]}:{self.client_addr[1]}")

        self.client = None
        self.client_addr = None

    def forward_serial(self) -> None:
        assert self.serial_fd is not None

        try:
            data = os.read(self.serial_fd, 8192)
        except OSError as exc:
            if exc.errno in {errno.EAGAIN, errno.EWOULDBLOCK}:
                return
            self.log(f"serial read failed: {exc}")
            self.close_serial()
            return

        if not data:
            self.close_serial()
            return

        if self.capture_fp is not None:
            self.capture_fp.write(b"\n--- serial->tcp ---\n")
            self.capture_fp.write(data)

        if self.client is not None:
            try:
                self.client.sendall(data)
            except OSError as exc:
                self.log(f"client write failed: {exc}")
                self.close_client()

    def forward_client(self) -> None:
        assert self.client is not None

        try:
            data = self.client.recv(8192)
        except OSError as exc:
            self.log(f"client read failed: {exc}")
            self.close_client()
            return

        if not data:
            self.close_client()
            return

        if self.capture_fp is not None:
            self.capture_fp.write(b"\n--- tcp->serial ---\n")
            self.capture_fp.write(data)

        if self.serial_fd is None:
            return

        try:
            os.write(self.serial_fd, data)
        except OSError as exc:
            self.log(f"serial write failed: {exc}")
            self.close_serial()

    def tick(self) -> None:
        self.check_serial_identity()

        if self.serial_fd is None and time.monotonic() >= self.next_serial_retry:
            self.open_serial()
            if self.serial_fd is None:
                self.next_serial_retry = time.monotonic() + self.args.retry_interval

        events = self.selector.select(timeout=1.0)
        for key, _ in events:
            if key.data == "server":
                self.accept_client()
            elif key.data == "serial":
                self.forward_serial()
            elif key.data == "client":
                self.forward_client()

    def run(self) -> int:
        self.log("press Ctrl-C to stop")
        while not self.stop_requested:
            self.tick()
        return 0

    def close(self) -> None:
        self.close_client()
        self.close_serial()

        try:
            self.selector.unregister(self.server)
        except Exception:
            pass

        try:
            self.server.close()
        except OSError:
            pass

        self.selector.close()

        if self.capture_fp is not None:
            self.capture_fp.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Expose the A90 USB ACM shell over a local TCP port."
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="serial device path, or 'auto' to use the Samsung by-id symlink",
    )
    parser.add_argument(
        "--device-glob",
        default=DEFAULT_DEVICE_GLOB,
        help="glob used when --device=auto",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="listen host")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="listen TCP port",
    )
    parser.add_argument(
        "--baud",
        type=int,
        choices=sorted(BAUD_MAP),
        default=DEFAULT_BAUD,
        help="serial baud rate",
    )
    parser.add_argument(
        "--retry-interval",
        type=float,
        default=1.0,
        help="seconds between serial reconnect attempts",
    )
    parser.add_argument(
        "--capture",
        help="optional path to append raw bridge traffic",
    )
    parser.add_argument(
        "--allow-client-without-serial",
        action="store_true",
        help=(
            "accept a TCP client even when the serial device is absent; "
            "without this, clients are rejected so probe scripts can retry "
            "instead of sending commands into a missing serial device"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bridge = Bridge(args)

    def handle_signal(signum: int, _frame) -> None:
        bridge.log(f"signal {signum} received, stopping")
        bridge.stop_requested = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        return bridge.run()
    finally:
        bridge.close()


if __name__ == "__main__":
    raise SystemExit(main())
