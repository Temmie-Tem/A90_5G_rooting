#!/usr/bin/env python3
"""Collect an A90 native-init diagnostics snapshot through the serial bridge."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
A90CTL = REPO_ROOT / "scripts" / "revalidation" / "a90ctl.py"
TCPCTL_HOST = REPO_ROOT / "scripts" / "revalidation" / "tcpctl_host.py"
RSHELL_HOST = REPO_ROOT / "scripts" / "revalidation" / "rshell_host.py"


def run_command(command: list[str],
                timeout: int,
                check: bool = False,
                cwd: Path = REPO_ROOT) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or f"command failed rc={result.returncode}: {command}")
    return result.returncode, result.stdout


def run_a90ctl(args: argparse.Namespace, device_args: list[str], timeout: int | None = None) -> tuple[int, str]:
    command = [
        sys.executable,
        str(A90CTL),
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--timeout",
        str(timeout if timeout is not None else args.timeout),
        "--allow-error",
        *device_args,
    ]
    return run_command(command, timeout=(timeout if timeout is not None else args.timeout) + 5)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def append_section(lines: list[str], title: str, body: str) -> None:
    lines.append(f"[{title}]")
    lines.append(body.rstrip() if body.strip() else "(empty)")
    lines.append("")


def collect_host_metadata(args: argparse.Namespace) -> str:
    lines: list[str] = []
    lines.append(f"repo={REPO_ROOT}")
    rc, text = run_command(["git", "rev-parse", "--short", "HEAD"], timeout=5)
    lines.append(f"git_head={text.strip() if rc == 0 else 'unknown'}")
    rc, text = run_command(["git", "status", "--short"], timeout=5)
    lines.append(f"git_dirty={'yes' if rc == 0 and text.strip() else 'no' if rc == 0 else 'unknown'}")
    if rc == 0 and text.strip():
        lines.append("git_status_short:")
        lines.extend(f"  {line}" for line in text.splitlines())
    if args.boot_image:
        image = Path(args.boot_image)
        if not image.is_absolute():
            image = REPO_ROOT / image
        if image.exists():
            lines.append(f"boot_image={image}")
            lines.append(f"boot_image_sha256={sha256_file(image)}")
        else:
            lines.append(f"boot_image_missing={image}")
    return "\n".join(lines)


def collect_optional_network(args: argparse.Namespace) -> str:
    lines: list[str] = []
    if args.ncm_ping:
        rc, text = run_command(["ping", "-c", "3", "-W", "2", args.ncm_ping], timeout=12)
        lines.append(f"$ ping -c 3 -W 2 {args.ncm_ping}")
        lines.append(text.rstrip())
        lines.append(f"rc={rc}")
    if args.tcpctl:
        for subcommand in ("ping", "status"):
            rc, text = run_command(
                [sys.executable, str(TCPCTL_HOST), "--tcp-timeout", str(args.tcp_timeout), subcommand],
                timeout=args.tcp_timeout + 10,
            )
            lines.append(f"$ tcpctl_host.py {subcommand}")
            lines.append(text.rstrip())
            lines.append(f"rc={rc}")
    if args.rshell_smoke:
        rc, text = run_command(
            [sys.executable, str(RSHELL_HOST), "--timeout", str(args.rshell_timeout), "smoke"],
            timeout=args.rshell_timeout + 30,
        )
        lines.append("$ rshell_host.py smoke")
        lines.append(text.rstrip())
        lines.append(f"rc={rc}")
    return "\n".join(lines)


def default_output_path() -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return REPO_ROOT / "tmp" / "diag" / f"a90-diag-{stamp}.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="serial bridge host")
    parser.add_argument("--port", type=int, default=54321, help="serial bridge TCP port")
    parser.add_argument("--timeout", type=int, default=20, help="a90ctl command timeout")
    parser.add_argument("--out", type=Path, default=default_output_path(), help="host-side output path")
    parser.add_argument("--device-bundle", action="store_true", help="also run device-side diag bundle")
    parser.add_argument("--boot-image", help="optional boot image path to hash")
    parser.add_argument("--ncm-ping", metavar="IP", help="optional ping target, usually 192.168.7.2")
    parser.add_argument("--tcpctl", action="store_true", help="optionally collect tcpctl ping/status")
    parser.add_argument("--tcp-timeout", type=int, default=10)
    parser.add_argument("--rshell-smoke", action="store_true", help="optionally run rshell smoke")
    parser.add_argument("--rshell-timeout", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lines: list[str] = []
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()

    lines.append("A90 HOST DIAG")
    lines.append(f"generated={stamp}")
    lines.append("")
    append_section(lines, "host", collect_host_metadata(args))

    rc, text = run_a90ctl(args, ["diag", "full"])
    append_section(lines, "device diag full", text + f"\nrc={rc}")

    if args.device_bundle:
        rc, text = run_a90ctl(args, ["diag", "bundle"], timeout=max(args.timeout, 30))
        append_section(lines, "device diag bundle", text + f"\nrc={rc}")

    optional_network = collect_optional_network(args)
    if optional_network:
        append_section(lines, "optional network", optional_network)

    output = args.out
    if not output.is_absolute():
        output = REPO_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
