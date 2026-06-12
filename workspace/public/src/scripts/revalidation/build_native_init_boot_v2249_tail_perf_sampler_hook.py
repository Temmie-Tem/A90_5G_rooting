#!/usr/bin/env python3
"""Build V2249 post-FWREADY tail perf sampler hook test boot.

This source/build wrapper keeps the V2237 Wi-Fi route and adds only a
compile-gated helper-side launch of the V2216 perf regs/codeword sampler before
the post-FWREADY boot_wlan write.  The sampler binary is packaged in the
ramdisk so the target window can be captured without a late host-side install.
"""

from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
from pathlib import Path

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2237_supplicant_terminate_poll as v2237
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2249-tail-perf-sampler-hook")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2249_TAIL_PERF_SAMPLER_HOOK_SOURCE_BUILD_2026-06-12.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2249_tail_perf_sampler_hook.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2249_tail_perf_sampler_hook"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2249_tail_perf_sampler_hook.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v428_tail_perf_sampler_hook"
BPF_HELPER_BINARY = OUT_DIR / "a90_bpf_perf_regs_codeword_sample_ring"
BPF_HELPER_SOURCE = REPO_ROOT / "workspace/public/src/native-init/helpers/a90_bpf_perf_regs_codeword_sample_ring.c"
BPF_HELPER_RAMDISK_PATH = "bin/a90_bpf_perf_regs_codeword_sample_ring"
BPF_HELPER_RUNTIME_PATH = "/bin/a90_bpf_perf_regs_codeword_sample_ring"
REMOTE_PROPERTY_ROOT = v2237.REMOTE_PROPERTY_ROOT
EXPECTED_HELPER_MARKER = "a90_android_execns_probe v428"
EXPECTED_HELPER_SHA256 = "fa9718619f905dd0d5d5a54b3fb608e9a966c3ce82547a2e97c55af35f0cc70e"
EXPECTED_BPF_HELPER_SHA256 = "3a16efc217eafeacbcc95a5e6005d0abce02e89ab52ed537df1fc2b193ca3dd7"
EXTRA_INIT_FLAGS = v2237.EXTRA_INIT_FLAGS
HELPER_MODE = v2237.HELPER_MODE
HELPER_RUNTIME_MODE = v2237.HELPER_RUNTIME_MODE
TAIL_SAMPLER_FLAGS = (
    "-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_SAMPLER=1",
    '-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_HELPER_PATH="/bin/a90_bpf_perf_regs_codeword_sample_ring"',
)


def base_module():
    return v2237.base_module()


def helper_chain():
    return v2237.helper_chain()


def helper_builder_module():
    return v2237.helper_builder_module()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str | Path]) -> subprocess.CompletedProcess[str]:
    print("+ " + shlex.join(str(item) for item in command), flush=True)
    return subprocess.run([str(item) for item in command], check=True, text=True)


def with_tail_flags(flags: tuple[str, ...]) -> tuple[str, ...]:
    merged = v2237.with_bridge_flag(flags)
    for flag in TAIL_SAMPLER_FLAGS:
        merged = (*tuple(item for item in merged if item != flag), flag)
    return merged


def configure_helper_flags() -> tuple[str, ...]:
    prev2137 = helper_chain()
    helper_flags = with_tail_flags(prev2137.HELPER_FLAGS)
    prev2137.HELPER_FLAGS = helper_flags
    prev2137.prev2135.HELPER_FLAGS = helper_flags
    prev2137.prev2135.prev2133.prev2131.HELPER_FLAGS = helper_flags
    helper_builder_module().HELPER_FLAGS = helper_flags
    return helper_flags


def configure_base() -> tuple[str, ...]:
    v2237.OUT_DIR = OUT_DIR
    v2237.REPORT_PATH = REPORT_PATH
    v2237.BOOT_IMAGE = BOOT_IMAGE
    v2237.INIT_BINARY = INIT_BINARY
    v2237.RAMDISK_CPIO = RAMDISK_CPIO
    v2237.REMOTE_PROPERTY_ROOT = REMOTE_PROPERTY_ROOT
    v2237.configure_base()
    helper_flags = configure_helper_flags()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2249",
        "--decision": "v2249-tail-perf-sampler-hook-source-build-pass",
        "--cycle-label": "v2249",
        "--init-version": "0.9.269",
        "--init-build": "v2249-tail-perf-sampler-hook",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(HELPER_BINARY),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--wifi-test-klog-prefix": "A90v2249",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2249.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2249.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2249.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2249-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2249.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2249-supervisor.pid",
        "--wifi-test-property-root": REMOTE_PROPERTY_ROOT,
        "--wifi-test-helper-mode": HELPER_MODE,
        "--wifi-test-watch-sec": "190",
        "--wifi-test-supervisor-timeout-sec": "245",
    }
    for key, value in replacements.items():
        v2237.v2230.v2189.v2188.v2187.v2182.v2178.v2176.v2174.v2169.v726.set_arg(args, key, value)
    base.DEFAULT_ARGS = args
    base.base.EXTRA_INIT_FLAGS = EXTRA_INIT_FLAGS
    return helper_flags


def build_bpf_helper() -> None:
    BPF_HELPER_BINARY.parent.mkdir(parents=True, exist_ok=True)
    run([
        "aarch64-linux-gnu-gcc",
        "-static",
        "-Os",
        "-Wall",
        "-Wextra",
        "-o",
        BPF_HELPER_BINARY,
        BPF_HELPER_SOURCE,
    ])
    run(["aarch64-linux-gnu-strip", BPF_HELPER_BINARY])
    helper_sha = sha256(BPF_HELPER_BINARY)
    if helper_sha != EXPECTED_BPF_HELPER_SHA256:
        raise RuntimeError(f"BPF helper sha mismatch: got {helper_sha}, expected {EXPECTED_BPF_HELPER_SHA256}")


def patch_ramdisk_helpers(base_wrapper) -> None:
    original_ramdisk_helpers = base_wrapper.base.ramdisk_helpers

    def ramdisk_helpers_with_tail_sampler(args):
        helpers = dict(original_ramdisk_helpers(args))
        helpers[BPF_HELPER_RAMDISK_PATH] = BPF_HELPER_BINARY
        return helpers

    base_wrapper.base.ramdisk_helpers = ramdisk_helpers_with_tail_sampler


def render_report(manifest: dict[str, object], helper_flags: tuple[str, ...]) -> str:
    wifi = manifest["wifi_test"]
    helper_flag_lines = [f"- `{flag}`" for flag in helper_flags]
    return "\n".join([
        "# Native Init V2249 Tail Perf Sampler Hook Source Build",
        "",
        "## Summary",
        "",
        "- Cycle: `V2249`",
        "- Type: source/build-only rollbackable post-FWREADY tail exact-slide sampler test boot.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Reason: V2248 proved a host-side post-boot V2216 sampler can miss the qcacld/HDD tail; this build packages the V2216 sampler in ramdisk and starts it from the helper before `boot_wlan`.",
        "- Manifest: `workspace/private/builds/native-init/v2249-tail-perf-sampler-hook/manifest.json`",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Helper marker: `a90_android_execns_probe v428` (binary marker string: `{manifest['helper_marker']}`)",
        f"- Helper SHA256: `{manifest['helper_sha256']}`",
        f"- Tail sampler ramdisk path: `{BPF_HELPER_RUNTIME_PATH}`",
        f"- Tail sampler SHA256: `{EXPECTED_BPF_HELPER_SHA256}`",
        "",
        "## Route",
        "",
        f"- Helper runtime mode: `{wifi['helper_runtime_mode']}`",
        f"- Helper timeout: `{wifi['helper_timeout_sec']}`",
        f"- Property root: `{REMOTE_PROPERTY_ROOT}`",
        "- Kept from V2237: service-object-visible route, post-FWREADY `boot_wlan`, firmware_class feeder, and strict supplicant terminate polling.",
        "- Added for this build only: `A90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_SAMPLER=1` and ramdisk-local `/bin/a90_bpf_perf_regs_codeword_sample_ring`.",
        "- Capture contract: start before `append_post_fw_ready_boot_wlan_trigger`, run for 45 s with 1 ms CPU-clock period, print up to 512 samples, write `/cache/native-init-v2249-tail-perf-regs-codeword.log`, then score with `a90_kernel_v2247_tail_pc_lr_scorer.py` after the live handoff.",
        "",
        "## Helper Flags",
        "",
        *helper_flag_lines,
        "",
        "## Safety Scope",
        "",
        "This build script performed host-side source/build work only. The eventual live run remains rollbackable and observes kernel PC/LR with read-only BPF perf events. It does not scan/connect Wi-Fi beyond the existing bounded validation route, does not use credentials, does not configure DHCP/routes, does not ping externally, does not execute `probe_write_user`, and does not touch eSoC/PCIe/GDSC/PMIC/GPIO or device partitions.",
        "",
    ])


def main() -> int:
    helper_flags = configure_base()
    build_bpf_helper()
    helper_builder = helper_builder_module()
    helper_builder.EXPECTED_HELPER_MARKER = EXPECTED_HELPER_MARKER
    helper_builder.EXPECTED_HELPER_SHA256 = EXPECTED_HELPER_SHA256
    base = base_module()
    base.base.EXPECTED_HELPER_MARKER = EXPECTED_HELPER_MARKER
    base.base.EXPECTED_HELPER_SHA256 = EXPECTED_HELPER_SHA256
    helper_builder.patch_helper_builder(base)
    patch_ramdisk_helpers(base)
    v2237.patch_mkbootimg_tools(base)
    base.render_report = lambda manifest: render_report(manifest, helper_flags)
    rc = base.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_tag"] = "v2249-tail-perf-sampler-hook"
    manifest["parent_baseline"] = "v2237-supplicant-terminate-poll"
    manifest["rollback_baseline"] = "v2237-supplicant-terminate-poll"
    manifest["promoted_baseline"] = False
    manifest["helper_flags"] = list(helper_flags)
    manifest["tail_sampler"] = {
        "source": str(BPF_HELPER_SOURCE.relative_to(REPO_ROOT)),
        "ramdisk_path": BPF_HELPER_RUNTIME_PATH,
        "sha256": EXPECTED_BPF_HELPER_SHA256,
        "output_path": "/cache/native-init-v2249-tail-perf-regs-codeword.log",
        "duration_ms": 45000,
        "period_ns": 1000000,
        "print_limit": 512,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    promotion_path = OUT_DIR / "promotion-candidate.json"
    promotion_path.write_text(json.dumps({
        "candidate_tag": "v2249-tail-perf-sampler-hook",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest["helper_sha256"],
        "tail_sampler_sha256": EXPECTED_BPF_HELPER_SHA256,
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "note": "V2249 keeps V2237 Wi-Fi behavior and adds a helper-started read-only perf regs/codeword sampler for the post-FWREADY qcacld/HDD tail.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
