"""NCM/TCP preflight module wrapper."""

from __future__ import annotations

import subprocess
import sys
import time

from a90harness.module import ModuleContext, StepResult, TestModule


class NcmTcpPreflightModule(TestModule):
    name = "ncm-tcp-preflight"
    description = "run tcpctl smoke when host USB NCM is already configured"
    cycle_label = "v174"
    read_only = False
    requires_ncm = True

    def __init__(self) -> None:
        self._skip_reason = ""

    def prepare(self, ctx: ModuleContext) -> StepResult:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", "192.168.7.2"],
            cwd=ctx.repo_root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
        )
        ctx.store.write_text(f"modules/{self.name}/preflight-ping.txt", result.stdout)
        if result.returncode != 0:
            self._skip_reason = "SKIP: host NCM path 192.168.7.2 is not reachable; not attempting sudo or USB rebind"
            return StepResult("prepare", True, self._skip_reason, 0.0, skipped=True)
        return StepResult("prepare", True, "host NCM ping ok", 0.0)

    def run(self, ctx: ModuleContext) -> StepResult:
        if self._skip_reason:
            return StepResult("run", True, self._skip_reason, 0.0, skipped=True)
        command = [
            sys.executable,
            str(ctx.repo_root / "scripts/revalidation/tcpctl_host.py"),
            "--bridge-host",
            ctx.host,
            "--bridge-port",
            str(ctx.port),
            "--device-binary",
            "/bin/a90_tcpctl",
            "--toybox",
            "/cache/bin/toybox",
            "smoke",
            "--ready-timeout",
            "15",
        ]
        result = subprocess.run(
            command,
            cwd=ctx.repo_root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=240,
        )
        ctx.store.write_text(f"modules/{self.name}/wrapper-output.txt", "$ " + " ".join(command) + "\n\n" + result.stdout)
        required_markers = (
            "--- ping ---",
            "--- version ---",
            "--- status ---",
            "--- shutdown ---",
            "--- serial-run ---",
            "--- bridge-version ---",
            "--- ncm-ping ---",
            "[done] run",
        )
        missing = [marker for marker in required_markers if marker not in result.stdout]
        ok = result.returncode == 0 and not missing
        return StepResult("run", ok, f"rc={result.returncode} missing={missing}", 0.0)

    def cleanup(self, ctx: ModuleContext) -> StepResult:
        if self._skip_reason:
            return StepResult("cleanup", True, self._skip_reason, 0.0, skipped=True)
        return StepResult("cleanup", True, "tcpctl smoke performs shutdown", 0.0)

    def verify(self, ctx: ModuleContext) -> StepResult:
        if self._skip_reason:
            return StepResult("verify", True, self._skip_reason, 0.0, skipped=True)
        output_path = ctx.module_dir / "wrapper-output.txt"
        text = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else ""
        markers = {
            "pong": "pong" in text,
            "authenticated": "OK authenticated" in text,
            "auth_required": "auth=required" in text,
            "shutdown": "shutdown" in text,
            "serial_done": "[done] run" in text,
        }
        ok = all(markers.values()) and "auth=none" not in text
        return StepResult("verify", ok, " ".join(f"{key}={value}" for key, value in markers.items()), 0.0)
