"""Single-writer device command client for A90 native-init validation."""

from __future__ import annotations

import threading
import time

from a90ctl import ProtocolResult, run_cmdv1_command

from a90harness.schema import CommandRecord


class DeviceClient:
    """Thread-safe wrapper around the serial bridge cmdv1 protocol."""

    def __init__(self, host: str = "127.0.0.1", port: int = 54321, timeout: float = 20.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._lock = threading.RLock()

    def run(self,
            name: str,
            command: list[str],
            *,
            timeout: float | None = None,
            retry_unsafe: bool = False,
            transcript: str = "") -> tuple[CommandRecord, str]:
        started = time.monotonic()
        with self._lock:
            try:
                result: ProtocolResult = run_cmdv1_command(
                    self.host,
                    self.port,
                    self.timeout if timeout is None else timeout,
                    command,
                    retry_unsafe=retry_unsafe,
                )
                duration = time.monotonic() - started
                ok = result.rc == 0 and result.status == "ok"
                record = CommandRecord(
                    name=name,
                    command=command,
                    ok=ok,
                    rc=result.rc,
                    status=result.status,
                    duration_sec=duration,
                    transcript=transcript,
                )
                return record, result.text
            except Exception as exc:  # noqa: BLE001 - harness records exact failure evidence
                duration = time.monotonic() - started
                record = CommandRecord(
                    name=name,
                    command=command,
                    ok=False,
                    rc=None,
                    status="exception",
                    duration_sec=duration,
                    transcript=transcript,
                    error=f"{type(exc).__name__}: {exc}",
                )
                return record, record.error + "\n"

