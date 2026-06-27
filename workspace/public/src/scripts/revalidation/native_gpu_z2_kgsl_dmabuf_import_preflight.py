#!/usr/bin/env python3
"""Run V3324 GPU Z2 KGSL dma-buf import preflight.

This is a no-flash, no-present probe. It creates the same scanout-capable
DRM msm GEM proven by V3323, exports it as a PRIME fd, imports that fd through
KGSL GPUOBJ_IMPORT, and checks KGSL GPUOBJ_INFO for a usable gpuaddr. It does
not submit GPU commands or change KMS CRTC state.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import native_kernel_timer_object_histogram_v2202 as live_base


REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT_DIR = REPO_ROOT / "workspace/public/src/scripts/revalidation"
HELPER_SOURCE = REPO_ROOT / "workspace/public/src/native-init/helpers/a90_kgsl_dmabuf_import_probe_z2.c"
GPU_SOURCE = REPO_ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"
PRIVATE_RUNS = REPO_ROOT / "workspace/private/runs/gpu"
REPORT_PATH = REPO_ROOT / "docs/reports/NATIVE_INIT_V3324_GPU_Z2_KGSL_DMABUF_IMPORT_PREFLIGHT_2026-06-27.md"
REMOTE_HELPER = "/cache/bin/a90_kgsl_dmabuf_import_probe_z2"
DEFAULT_TOYBOX = "/bin/busybox"
RUN_ID = "V3324"
DECISION_DRY_RUN = "v3324-gpu-z2-kgsl-dmabuf-import-preflight-dry-run"
DECISION_PASS = "v3324-z2-kgsl-dmabuf-import-preflight-pass"
DECISION_PARTIAL = "v3324-z2-kgsl-dmabuf-import-preflight-partial"
DECISION_FAILED = "v3324-z2-kgsl-dmabuf-import-preflight-failed"

KEY_VALUE_RE = re.compile(r"^(?P<key>[A-Za-z0-9_.]+)=(?P<value>.*)$", re.MULTILINE)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def now_label() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def parse_tokens(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for token in body.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        fields[key] = value
    return fields


def parse_int(value: str | None, default: int = 0) -> int:
    if value is None:
        return default
    stripped = value.strip()
    if not stripped:
        return default
    try:
        return int(stripped, 0)
    except ValueError:
        return default


def clean_resident_version(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("version: ") or line.startswith("A90 Linux init "):
            return line.strip()
    return text.strip().splitlines()[0] if text.strip() else ""


def parse_probe_stdout(text: str) -> dict[str, Any]:
    values = {match.group("key"): match.group("value") for match in KEY_VALUE_RE.finditer(text)}
    fields: dict[str, str] = {}

    for line in text.splitlines():
        if not line.startswith("probe."):
            continue
        if line.startswith("probe.drm.mmap.sample "):
            values["probe.drm.mmap.sample"] = line[len("probe.drm.mmap.sample "):]
            fields.update({
                f"probe.drm.mmap.sample.{key}": value
                for key, value in parse_tokens(line[len("probe.drm.mmap.sample "):]).items()
            })
            continue
        first, *rest = line.split()
        if "=" not in first:
            continue
        first_key, first_value = first.split("=", 1)
        values[first_key] = first_value
        if first_key.startswith("probe.cleanup."):
            prefix = "probe.cleanup"
        else:
            prefix = first_key.rsplit(".", 1)[0]
        fields.update({
            f"{prefix}.{key}": value
            for key, value in parse_tokens(" ".join(rest)).items()
        })

    result = values.get("probe.result", "")
    if result == "z2-kgsl-dmabuf-import-preflight-pass":
        decision = DECISION_PASS
    elif result:
        decision = DECISION_PARTIAL
    else:
        decision = DECISION_FAILED

    gpuaddr = parse_int(fields.get("probe.kgsl.gpuobj_info.gpuaddr"), 0)
    kgsl_size = parse_int(fields.get("probe.kgsl.gpuobj_info.size"), 0)
    return {
        "stdout": text,
        "values": values,
        "fields": fields,
        "result": result,
        "decision": decision,
        "drm_gem_ok": parse_int(values.get("probe.drm.msm_gem_new.rc"), -1) == 0,
        "drm_prime_export_ok": parse_int(values.get("probe.drm.prime.export.rc"), -1) == 0,
        "drm_addfb2_ok": parse_int(values.get("probe.drm.addfb2.rc"), -1) == 0,
        "kgsl_open_ok": parse_int(values.get("probe.kgsl.open.rc"), -1) == 0,
        "kgsl_import_ok": parse_int(values.get("probe.kgsl.gpuobj_import.rc"), -1) == 0,
        "kgsl_info_ok": parse_int(values.get("probe.kgsl.gpuobj_info.rc"), -1) == 0,
        "kgsl_gpuaddr": gpuaddr,
        "kgsl_size": kgsl_size,
        "kgsl_gpuaddr_ok": gpuaddr != 0,
        "kgsl_size_ok": kgsl_size >= 2764800,
        "cleanup_ok": (
            parse_int(values.get("probe.cleanup.kgsl_free.rc"), -1) == 0 and
            parse_int(fields.get("probe.cleanup.rmfb.rc"), -1) == 0 and
            parse_int(fields.get("probe.cleanup.close_drm_handle.rc"), -1) == 0
        ),
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def install_helper(args: argparse.Namespace,
                   out_dir: Path,
                   steps: list[live_base.StepResult],
                   local_binary: Path,
                   summary: dict[str, Any]) -> None:
    if not args.device_ip:
        raise RuntimeError("--device-ip or A90_NCM_DEVICE_IP is required for this no-flash helper install")
    live_base.install_helper(args, out_dir, steps, "gpu-z2-kgsl-dmabuf-import-probe", local_binary, REMOTE_HELPER)
    summary["install_path"] = "bridge-nc"


def render_report(summary: dict[str, Any]) -> str:
    probe = summary.get("probe") or {}
    values = probe.get("values") or {}
    fields = probe.get("fields") or {}
    build = summary.get("build") or {}
    decision = summary.get("decision", probe.get("decision", DECISION_DRY_RUN))

    lines = [
        "# Native Init V3324 GPU Z2 KGSL Dmabuf Import Preflight",
        "",
        "- Date: 2026-06-27",
        f"- Cycle: `{RUN_ID}`",
        "- Track: GPU rung ④ zero-copy KMS/dmabuf scanout.",
        f"- Decision: `{decision}`",
        "",
        "## Scope",
        "",
        "This was a no-flash Z2 preflight. The helper creates one DRM msm",
        "`MSM_BO_SCANOUT | MSM_BO_WC` GEM, exports it as a PRIME dma-buf fd,",
        "registers it as an `XBGR8888` KMS framebuffer object, then imports the",
        "same dma-buf fd into `/dev/kgsl-3d0` via `IOCTL_KGSL_GPUOBJ_IMPORT` and",
        "queries `IOCTL_KGSL_GPUOBJ_INFO`. It does not submit GPU commands, modeset,",
        "pageflip, present, or write power/panel controls.",
        "",
        "## Safety",
        "",
        "- Flash/reboot: `0`",
        "- Partition/firmware writes: `0`",
        "- Display mutation: `0` (FB object creation/removal only; no present/modeset/pageflip)",
        "- GPU submit: `0`",
        "- PMIC/GDSC/regulator/GPIO/backlight writes: `0`",
        "",
        "## Build",
        "",
        f"- Helper source: `{rel(HELPER_SOURCE)}`",
        f"- Helper SHA-256: `{build.get('helper_sha256', '')}`",
        f"- Helper size: `{build.get('helper_size', 0)}` bytes",
        f"- Install path: `{summary.get('install_path', '')}`",
        "",
        "## Live Result",
        "",
        f"- Resident version: `{clean_resident_version(summary.get('resident_version', ''))}`",
        f"- Pre selftest fail=0: `{summary.get('pre_selftest_fail0', False)}`",
        f"- Post selftest fail=0: `{summary.get('post_selftest_fail0', False)}`",
        f"- Target: `{values.get('probe.target.width', '')}`x`{fields.get('probe.target.height', '')}` "
        f"stride=`{fields.get('probe.target.stride', '')}` bytes=`{fields.get('probe.target.bytes', '')}` "
        f"format=`{fields.get('probe.target.format', '')}` flags=`{fields.get('probe.target.flags', '')}`",
        f"- DRM open: rc=`{values.get('probe.drm.open.rc', '')}` node=`{fields.get('probe.drm.open.node', '')}`",
        f"- DRM PRIME cap: `{values.get('probe.drm.cap.prime', '')}` "
        f"import=`{fields.get('probe.drm.cap.import', '')}` export=`{fields.get('probe.drm.cap.export', '')}`",
        f"- DRM GEM new: rc=`{values.get('probe.drm.msm_gem_new.rc', '')}` handle=`{fields.get('probe.drm.msm_gem_new.handle', '')}`",
        f"- DRM GEM offset: rc=`{values.get('probe.drm.msm_gem_info.offset.rc', '')}` value=`{fields.get('probe.drm.msm_gem_info.offset.value', '')}`",
        f"- DRM GEM IOVA: rc=`{values.get('probe.drm.msm_gem_info.iova.rc', '')}` value=`{fields.get('probe.drm.msm_gem_info.iova.value', '')}`",
        f"- DRM mmap: rc=`{values.get('probe.drm.mmap.rc', '')}` sample=`{values.get('probe.drm.mmap.sample', '')}`",
        f"- DRM PRIME export: rc=`{values.get('probe.drm.prime.export.rc', '')}` fd_valid=`{fields.get('probe.drm.prime.export.fd_valid', '')}`",
        f"- DRM ADDFB2: rc=`{values.get('probe.drm.addfb2.rc', '')}` fb_id=`{fields.get('probe.drm.addfb2.fb_id', '')}`",
        f"- KGSL open: rc=`{values.get('probe.kgsl.open.rc', '')}` node=`{fields.get('probe.kgsl.open.node', '')}`",
        f"- KGSL import: rc=`{values.get('probe.kgsl.gpuobj_import.rc', '')}` id=`{fields.get('probe.kgsl.gpuobj_import.id', '')}` "
        f"type=`{fields.get('probe.kgsl.gpuobj_import.type', '')}` flags=`{fields.get('probe.kgsl.gpuobj_import.flags', '')}`",
        f"- KGSL info: rc=`{values.get('probe.kgsl.gpuobj_info.rc', '')}` id=`{fields.get('probe.kgsl.gpuobj_info.id', '')}` "
        f"gpuaddr=`{fields.get('probe.kgsl.gpuobj_info.gpuaddr', '')}` size=`{fields.get('probe.kgsl.gpuobj_info.size', '')}` "
        f"flags=`{fields.get('probe.kgsl.gpuobj_info.flags', '')}` va_len=`{fields.get('probe.kgsl.gpuobj_info.va_len', '')}`",
        f"- Cleanup: kgsl_free=`{values.get('probe.cleanup.kgsl_free.rc', '')}` "
        f"rmfb=`{fields.get('probe.cleanup.rmfb.rc', '')}` close_drm_handle=`{fields.get('probe.cleanup.close_drm_handle.rc', '')}`",
        f"- Helper result: `{probe.get('result', '')}`",
        "",
        "## Interpretation",
        "",
    ]
    if decision == DECISION_PASS:
        lines.extend([
            "The zero-copy allocator bridge is proven through both sides: the same DRM",
            "msm scanout GEM can become a KMS framebuffer and a KGSL GPU object with a",
            "non-zero KGSL gpuaddr. Z2 can now be a bounded source/build unit that",
            "replaces the current `session->linear` KGSL allocation with the imported",
            "dma-buf object for the final render target, then keeps the existing CPU-copy",
            "path as fallback until a one-frame direct pageflip proof passes.",
        ])
    elif decision == DECISION_PARTIAL:
        lines.extend([
            "The import bridge was partial. Keep the CPU-copy present path. If KGSL",
            "import failed, pivot to DRM msm submit or stop zero-copy on the current",
            "KGSL path. If KGSL import passed but info/gpuaddr failed, inspect the",
            "import flags and KGSL source before using the object as a render target.",
        ])
    else:
        lines.extend([
            "No usable live import result was produced. Keep the existing CPU-copy KMS",
            "path and inspect the private run logs before changing the GPU source path.",
        ])
    lines.extend([
        "",
        "## Source Grounding",
        "",
        "- Samsung kernel UAPI exposes `KGSL_USER_MEM_TYPE_DMABUF=3` and",
        "  `IOCTL_KGSL_GPUOBJ_IMPORT` at ioctl number `0x48`.",
        "- Samsung KGSL source wires that ioctl to `kgsl_ioctl_gpuobj_import()`,",
        "  whose dma-buf path calls `dma_buf_get(fd)` and `kgsl_setup_dma_buf()`.",
        "- Mesa Turnip KGSL path imports dma-buf by filling `kgsl_gpuobj_import_dma_buf`",
        "  and then querying `IOCTL_KGSL_GPUOBJ_INFO` for the KGSL iova.",
        f"- Existing extracted KGSL present path: `{rel(GPU_SOURCE)}`.",
        "",
        "## Validation",
        "",
        f"- Runner: `{rel(REPO_ROOT / 'workspace/public/src/scripts/revalidation/native_gpu_z2_kgsl_dmabuf_import_preflight.py')}`",
        f"- Private summary: `{summary.get('out_dir', '')}/summary.json`",
        f"- Pass: `{summary.get('pass', False)}`",
        "",
    ])
    return "\n".join(lines)


def run_live(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = PRIVATE_RUNS / f"v3324-gpu-z2-kgsl-dmabuf-import-preflight-{now_label()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    steps: list[live_base.StepResult] = []
    summary: dict[str, Any] = {
        "run_id": RUN_ID,
        "out_dir": str(out_dir.relative_to(REPO_ROOT)),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "helper_source": rel(HELPER_SOURCE),
        "remote_helper": REMOTE_HELPER,
        "safety": {
            "flash_reboot": False,
            "partition_or_firmware_write": False,
            "display_mutation": False,
            "gpu_submit": False,
            "power_write": False,
            "no_present_or_modeset": True,
        },
    }
    try:
        os.environ.setdefault("A90CTL_INPUT_CHAR_DELAY_SEC", "0.25")
        live_base.run_host(out_dir, steps, "bridge-status", [
            sys.executable,
            str(SCRIPT_DIR / "a90_bridge.py"),
            "status",
            "--json",
        ], timeout=30, allow_error=True)
        version = live_base.a90ctl(args, out_dir, steps, "resident-version", ["version"], timeout=90, allow_error=True)
        live_base.a90ctl(args, out_dir, steps, "resident-status", ["status"], timeout=90, allow_error=True)
        pre_selftest = live_base.a90ctl(args, out_dir, steps, "resident-selftest", ["selftest"], timeout=90, allow_error=True)
        summary["resident_version"] = version.strip()
        summary["version_ok"] = "A90 Linux init" in version
        summary["pre_selftest_fail0"] = "fail=0" in pre_selftest

        build_dir = out_dir / "build"
        build_dir.mkdir(parents=True, exist_ok=True)
        helper_bin = live_base.build_helper(
            build_dir,
            steps,
            source=HELPER_SOURCE,
            output_name="a90_kgsl_dmabuf_import_probe_z2",
            cc=args.cc,
            strip=args.strip,
        )
        summary["build"] = {
            "helper_local": str(helper_bin.relative_to(REPO_ROOT)),
            "helper_sha256": live_base.sha256_file(helper_bin),
            "helper_size": helper_bin.stat().st_size,
        }
        if not args.skip_install:
            install_helper(args, out_dir, steps, helper_bin, summary)

        probe_stdout = live_base.tcpctl_run(
            args,
            out_dir,
            steps,
            "gpu-z2-kgsl-dmabuf-import-preflight",
            [REMOTE_HELPER],
            timeout=60,
            allow_error=True,
        )
        probe = parse_probe_stdout(probe_stdout)
        summary["probe"] = probe
        post_selftest = live_base.a90ctl(args, out_dir, steps, "post-selftest", ["selftest"], timeout=90, allow_error=True)
        summary["post_selftest_fail0"] = "fail=0" in post_selftest
        summary["decision"] = probe["decision"]
        summary["pass"] = bool(
            summary["post_selftest_fail0"] and
            probe.get("result") == "z2-kgsl-dmabuf-import-preflight-pass"
        )
    except Exception as exc:
        summary["decision"] = DECISION_FAILED
        summary["pass"] = False
        summary["error"] = str(exc)
    finally:
        summary["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        summary["steps"] = [
            {
                "name": step.name,
                "returncode": step.returncode,
                "ok": step.ok,
                "elapsed_sec": step.elapsed_sec,
                "stdout_path": step.stdout_path,
                "stderr_path": step.stderr_path,
            }
            for step in steps
        ]
        write_json(out_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--transfer-timeout", type=float, default=120.0)
    parser.add_argument("--transfer-port", type=int, default=18192)
    parser.add_argument("--transfer-delay", type=float, default=1.0)
    parser.add_argument("--connect-timeout", type=float, default=5.0)
    parser.add_argument("--device-ip", default=os.environ.get("A90_NCM_DEVICE_IP", ""))
    parser.add_argument("--toybox", default=DEFAULT_TOYBOX)
    parser.add_argument("--cc", default="aarch64-linux-gnu-gcc")
    parser.add_argument("--strip", default="aarch64-linux-gnu-strip")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    if args.run_live:
        summary = run_live(args)
    else:
        summary = {
            "run_id": RUN_ID,
            "decision": DECISION_DRY_RUN,
            "helper_source": rel(HELPER_SOURCE),
            "remote_helper": REMOTE_HELPER,
            "probe": {},
            "build": {},
            "pass": False,
        }

    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("pass") or not args.run_live else 1


if __name__ == "__main__":
    raise SystemExit(main())
