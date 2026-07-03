#!/usr/bin/env python3
"""Prepare the D-public test without opening a public tunnel.

This is the no-exposure preflight for the first external server-distro test.  It
verifies the already-approved D4 foundation and the host-side cloudflared
artifact, records what is still required for a live publish, and optionally runs
read-only device health checks.  It never starts cloudflared, never publishes a
URL, and never writes the device.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[5]
REVAL_DIR = REPO_ROOT / "workspace" / "public" / "src" / "scripts" / "revalidation"
if str(REVAL_DIR) not in sys.path:
    sys.path.insert(0, str(REVAL_DIR))

import a90ctl  # noqa: E402


DEFAULT_RUN_BASE = REPO_ROOT / "workspace" / "private" / "runs" / "server-distro"
DEFAULT_CLOUDFLARED = (
    REPO_ROOT / "workspace/private/builds/server-distro/tunnel/cloudflared-linux-arm64"
)
DEFAULT_TOKEN_FILE = REPO_ROOT / "workspace/private/secrets/server-distro/cloudflared_tunnel_token"
DEFAULT_HOSTNAME_FILE = REPO_ROOT / "workspace/private/secrets/server-distro/cloudflared_hostname"
DEFAULT_SERVICE_URL = "http://127.0.0.1:8080"
EXPECTED_CLOUDFLARED_SHA256 = "59816ce9b16db71f5bc2a86d59b3632a96c8c3ee934bde2bc8641ee83a6070eb"
EXPECTED_CLOUDFLARED_SIZE = 36_980_327
DPUBLIC_LIVE_OPERATOR_TOKEN = "D-PUBLIC-LIVE-PUBLISH"
REQUIRED_PUBLIC_DOCS = (
    "docs/plans/NATIVE_INIT_SERVER_DISTRO_ENDGAME_DESIGN_2026-06-30.md",
    "docs/reports/SERVER_DISTRO_D0_HOST_STAGING_2026-07-01.md",
    "docs/reports/SERVER_DISTRO_D4D_USERDATA_APPLIANCE_HANDOFF_2026-07-03.md",
)


def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp_slug() -> str:
    return utc_now().replace(":", "").replace("-", "")


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
        json.dump(payload, fp, indent=2, sort_keys=True, ensure_ascii=True)
        fp.write("\n")
        fp.flush()
        os.fsync(fp.fileno())
    tmp.replace(path)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def normalize_run_dir(path: Path) -> Path:
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def run_host(command: list[object], *, timeout: float, cwd: Path = REPO_ROOT) -> dict[str, Any]:
    result = subprocess.run(
        [str(item) for item in command],
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "command": [str(item) for item in command],
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def verify_required_docs(paths: tuple[str, ...] = REQUIRED_PUBLIC_DOCS) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for doc in paths:
        path = REPO_ROOT / doc
        exists = path.is_file()
        records.append({"path": doc, "exists": exists, "size_bytes": path.stat().st_size if exists else None})
        if not exists:
            raise FileNotFoundError(path)
    return records


def verify_cloudflared(path: Path, expected_sha256: str, expected_size: int) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_sha256 = sha256_file(path)
    actual_size = path.stat().st_size
    if actual_sha256 != expected_sha256:
        raise RuntimeError(f"cloudflared sha mismatch: {actual_sha256} != {expected_sha256}")
    if actual_size != expected_size:
        raise RuntimeError(f"cloudflared size mismatch: {actual_size} != {expected_size}")
    file_record = run_host(["file", path], timeout=10.0)
    return {
        "path": rel(path),
        "sha256": actual_sha256,
        "size_bytes": actual_size,
        "mode_octal": oct(path.stat().st_mode & 0o777),
        "host_executable_bit": os.access(path, os.X_OK),
        "file_command": file_record,
        "target_device_mode_octal": "0755",
    }


def live_inputs(token_file: Path, hostname_file: Path, service_url: str) -> dict[str, Any]:
    token_present = token_file.is_file() and token_file.stat().st_size > 0
    hostname_present = hostname_file.is_file() and hostname_file.stat().st_size > 0
    return {
        "service_url": service_url,
        "token_file": rel(token_file),
        "token_present": token_present,
        "hostname_file": rel(hostname_file),
        "hostname_present": hostname_present,
        "quick_tunnel_possible_but_live_exposure": True,
        "live_operator_token_required": DPUBLIC_LIVE_OPERATOR_TOKEN,
        "live_publish_ready": token_present or hostname_present,
        "note": (
            "A named-tunnel token/hostname or an explicitly approved quick tunnel is required "
            "for the first public exposure gate."
        ),
    }


def run_device_cmd(host: str,
                   port: int,
                   timeout: float,
                   command: list[str],
                   *,
                   allow_error: bool = False) -> dict[str, Any]:
    result = a90ctl.run_cmdv1_command(
        host,
        port,
        timeout,
        command,
        retry_unsafe=False,
        require_prompt_after_end=True,
    )
    payload = {
        "command": command,
        "rc": result.rc,
        "status": result.status,
        "begin": result.begin,
        "end": result.end,
        "text": result.text,
    }
    if not allow_error and result.rc != 0:
        raise RuntimeError(f"device command failed rc={result.rc}: {command}\n{result.text}")
    return payload


def device_readonly_check(host: str, port: int, timeout: float) -> dict[str, Any]:
    find_script = (
        "for d in /mnt/sdext/a90/runtime /mnt/sdext/a90; do "
        "[ -d \"$d\" ] && /bin/busybox find \"$d\" -maxdepth 4 "
        "\\( -name '*cloudflared*' -o -name '*tunnel*' \\); "
        "done"
    )
    version = run_device_cmd(host, port, timeout, ["version"])
    selftest = run_device_cmd(host, port, timeout, ["selftest"])
    status = run_device_cmd(host, port, timeout, ["status"])
    find_record = run_device_cmd(
        host,
        port,
        timeout,
        ["run", "/bin/busybox", "sh", "-c", find_script],
        allow_error=True,
    )
    final_v2321 = "v2321-usb-clean-identity-rodata" in version["text"]
    final_selftest_fail0 = "fail=0" in selftest["text"]
    discovered = [
        line.strip()
        for line in find_record["text"].splitlines()
        if line.strip().startswith("/mnt/")
    ]
    return {
        "version": version,
        "selftest": selftest,
        "status": status,
        "sd_tunnel_scan": find_record,
        "final_v2321": final_v2321,
        "final_selftest_fail0": final_selftest_fail0,
        "sd_tunnel_artifact_paths": discovered,
        "device_write_performed": False,
        "public_exposure_performed": False,
    }


def build_next_steps(inputs: dict[str, Any], device: dict[str, Any] | None) -> list[str]:
    steps = [
        "Choose the live exposure mode: named Cloudflare Tunnel token/hostname, or operator-approved quick tunnel.",
        "Stage cloudflared into the userdata Debian appliance with mode 0755, without starting it.",
        "Stage a minimal local HTTP smoke service bound to loopback/LAN inside the appliance.",
        "Boot a D4-capable appliance image and confirm outbound internet before starting cloudflared.",
        f"Only then run the live publish command after the operator says {DPUBLIC_LIVE_OPERATOR_TOKEN}.",
    ]
    if not inputs["token_present"] and not inputs["hostname_present"]:
        steps.insert(1, "Provide tunnel credentials under workspace/private/secrets/ or explicitly select quick-tunnel mode.")
    if device is not None and device["sd_tunnel_artifact_paths"]:
        steps = [step for step in steps if not step.startswith("Stage cloudflared")]
    return steps


def collect(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    run_id = args.run_id or "dpublic-preflight-" + timestamp_slug()
    run_dir = normalize_run_dir(args.run_dir or (args.run_base / run_id))
    run_dir.mkdir(parents=True, exist_ok=False)

    steps: dict[str, Any] = {
        "run_id": run_id,
        "timestamp_utc": utc_now(),
        "run_dir": rel(run_dir),
        "public_exposure_performed": False,
        "device_write_performed": False,
    }

    def save_step(name: str, payload: Any) -> None:
        steps[name] = payload
        write_json(run_dir / f"{name}.json", payload)
        write_json(run_dir / "summary.json", steps)

    save_step("required_docs", verify_required_docs())
    tunnel = verify_cloudflared(args.cloudflared, args.expected_cloudflared_sha256, args.expected_cloudflared_size)
    save_step("cloudflared", tunnel)
    inputs = live_inputs(args.token_file, args.hostname_file, args.service_url)
    save_step("live_inputs", inputs)
    device = device_readonly_check(args.host, args.port, args.timeout) if args.device_check else None
    if device is not None:
        save_step("device_readonly_check", device)

    result = {
        "decision": "dpublic-preflight-complete-no-public-exposure",
        "ok": True,
        "run_dir": rel(run_dir),
        "d4_foundation_docs_present": True,
        "host_cloudflared_ready": True,
        "host_cloudflared_sha256": tunnel["sha256"],
        "live_publish_ready": inputs["live_publish_ready"],
        "live_publish_performed": False,
        "public_exposure_performed": False,
        "device_write_performed": False,
        "device_check_performed": device is not None,
        "device_final_v2321": None if device is None else device["final_v2321"],
        "device_final_selftest_fail0": None if device is None else device["final_selftest_fail0"],
        "device_tunnel_artifacts_present": None if device is None else bool(device["sd_tunnel_artifact_paths"]),
        "operator_gate": DPUBLIC_LIVE_OPERATOR_TOKEN,
        "next_steps": build_next_steps(inputs, device),
    }
    save_step("result", result)
    return steps, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-base", type=Path, default=DEFAULT_RUN_BASE)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--cloudflared", type=Path, default=DEFAULT_CLOUDFLARED)
    parser.add_argument("--expected-cloudflared-sha256", default=EXPECTED_CLOUDFLARED_SHA256)
    parser.add_argument("--expected-cloudflared-size", type=int, default=EXPECTED_CLOUDFLARED_SIZE)
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE)
    parser.add_argument("--hostname-file", type=Path, default=DEFAULT_HOSTNAME_FILE)
    parser.add_argument("--service-url", default=DEFAULT_SERVICE_URL)
    parser.add_argument("--device-check", action="store_true")
    parser.add_argument("--host", default=a90ctl.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=a90ctl.DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)

    _steps, result = collect(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
