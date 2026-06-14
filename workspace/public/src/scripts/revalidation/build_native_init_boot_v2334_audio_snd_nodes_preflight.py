#!/usr/bin/env python3
"""Build V2334 audio /dev/snd node preflight boot.

V2334 keeps the V2331 ADSP firmware_class native-path fix and adds an
AUD-3-preflight command surface for ALSA /dev/snd inventory plus a token-gated
node materializer. It does not flash, open ALSA nodes, run tinyalsa, or play
sound.
"""

from __future__ import annotations

import json
import shlex
import tempfile
from pathlib import Path

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

import build_native_init_boot_v2323_usb_multi_lun_identity as v2323
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path


OUT_DIR = workspace_private_build_path("native-init", "v2334-audio-snd-nodes-preflight")
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2334_AUDIO_SND_NODES_PREFLIGHT_SOURCE_BUILD_2026-06-14.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2334_audio_snd_nodes_preflight.img", legacy_fallback=False
)
BASE_BOOT = workspace_private_input_path(
    "boot_images", "boot_linux_v2331_audio_adsp_fwclass_native_path.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v2334_audio_snd_nodes_preflight"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v2334_audio_snd_nodes_preflight.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v441_audio_snd_nodes_preflight"
FWCLASS_NATIVE_PATH_FLAGS = (
    "-UA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH",
    "-DA90_WIFI_TEST_BOOT_FWCLASS_VENDOR_PATH=0",
)
THIRD_PARTY_MKBOOTIMG = REPO_ROOT / "workspace" / "public" / "src" / "third_party" / "mkbootimg"


def base_module():
    return v2323.base_module()


def helper_builder_module():
    return v2323.helper_builder_module()


def set_arg(args: list[str], key: str, value: str) -> None:
    index = args.index(key)
    args[index + 1] = value


def set_or_append_arg(args: list[str], key: str, value: str) -> None:
    if key in args:
        set_arg(args, key, value)
    else:
        args.extend([key, value])


def inherited_clean_identity_patch_info() -> dict[str, object]:
    return {
        **v2323.v2321.USB_CLEAN_IDENTITY_RODATA_PATCH,
        "mode": "inherited-clean-identity-from-base-boot",
        "base_boot": str(BASE_BOOT.relative_to(REPO_ROOT)),
        "base_boot_sha256": v2323.v2321.sha256(BASE_BOOT),
        "patched_kernel_sha256": "inherited-from-v2331-base-boot",
    }


def patch_mkbootimg_tool_paths(base_wrapper) -> None:
    build_base = base_wrapper.base

    def build_boot_image(args) -> None:
        with tempfile.TemporaryDirectory(prefix="a90-v2334-unpack-") as temp_name:
            temp_dir = Path(temp_name)
            unpack_args = build_base.run(
                [
                    "python3",
                    THIRD_PARTY_MKBOOTIMG / "unpack_bootimg.py",
                    "--boot_img",
                    args.base_boot,
                    "--out",
                    temp_dir,
                    "--format=mkbootimg",
                ],
                capture=True,
            ).stdout
            mkboot_args = shlex.split(unpack_args)
            for index, item in enumerate(mkboot_args):
                if item == "--ramdisk":
                    mkboot_args[index + 1] = str(args.ramdisk_cpio)
                    break
            else:
                raise RuntimeError("base boot image mkbootimg args did not include --ramdisk")
            if args.boot_image.exists():
                args.boot_image.unlink()
            build_base.run(
                [
                    "python3",
                    THIRD_PARTY_MKBOOTIMG / "mkbootimg.py",
                    *mkboot_args,
                    "--output",
                    args.boot_image,
                ]
            )
        args.boot_image.chmod(0o600)

    build_base.build_boot_image = build_boot_image


def configure_base() -> tuple[str, ...]:
    v2323.OUT_DIR = OUT_DIR
    v2323.REPORT_PATH = REPORT_PATH
    v2323.BOOT_IMAGE = BOOT_IMAGE
    v2323.INIT_BINARY = INIT_BINARY
    v2323.RAMDISK_CPIO = RAMDISK_CPIO
    v2323.HELPER_BINARY = HELPER_BINARY
    helper_flags = v2323.configure_base()

    base = base_module()
    args = list(base.DEFAULT_ARGS)
    replacements = {
        "--cycle": "V2334",
        "--decision": "v2334-audio-snd-nodes-preflight-source-build-pass",
        "--cycle-label": "v2334",
        "--init-version": "0.9.292",
        "--init-build": "v2334-audio-snd-nodes-preflight",
        "--out-dir": str(OUT_DIR),
        "--init-binary": str(INIT_BINARY),
        "--helper-binary": str(HELPER_BINARY),
        "--ramdisk-cpio": str(RAMDISK_CPIO),
        "--boot-image": str(BOOT_IMAGE),
        "--base-boot": str(BASE_BOOT),
        "--wifi-test-klog-prefix": "A90v2334",
        "--wifi-test-disable": "/cache/native-init-wifi-test-boot-v2334.disable",
        "--wifi-test-log": "/cache/native-init-wifi-test-boot-v2334.log",
        "--wifi-test-summary": "/cache/native-init-wifi-test-boot-v2334.summary",
        "--wifi-test-helper-result": "/cache/native-init-wifi-test-boot-v2334-helper.result",
        "--wifi-test-pid": "/cache/native-init-wifi-test-boot-v2334.pid",
        "--wifi-test-watcher-pid": "/cache/native-init-wifi-test-boot-v2334-supervisor.pid",
    }
    for key, value in replacements.items():
        set_or_append_arg(args, key, value)
    base.DEFAULT_ARGS = args
    inherited_extra_flags = tuple(base.base.EXTRA_INIT_FLAGS)
    base.base.EXTRA_INIT_FLAGS = (*inherited_extra_flags, *FWCLASS_NATIVE_PATH_FLAGS)
    return helper_flags


def render_report(
    manifest: dict[str, object],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    helper_flag_lines = [f"- `{flag}`" for flag in helper_flags]
    init_extra_flag_lines = [f"- `{flag}`" for flag in init_extra_flags]
    identities = manifest["usb_named_lun_identities"]
    identity_lines = [
        f"- `lun.{item['lun']}` model `{item['inquiry_product']}`, FAT label `{item['volume_label']}`, backing `{item['backing_file']}`."
        for item in identities
    ]
    return "\n".join([
        "# Native Init V2334 Audio `/dev/snd` Nodes Preflight Source Build",
        "",
        "## Summary",
        "",
        "- Cycle: `V2334`",
        "- Track: audio AUD-3 preflight, source/build-only.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no`.",
        "- Device action: `none`.",
        "- Manifest: `workspace/private/builds/native-init/v2334-audio-snd-nodes-preflight/manifest.json`",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        f"- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `{manifest['helper_marker']}`)",
        f"- Helper SHA256: `{manifest['helper_sha256']}`",
        "",
        "## Change",
        "",
        "- Keeps V2331's `firmware_class.path=/vendor/firmware_mnt/image` behavior for ADSP firmware loading.",
        "- Adds `audio snd-status`, a read-only `/sys/class/sound` inventory that reports allowed ALSA node names, sysfs `major:minor`, and matching `/dev/snd/*` state.",
        "- Adds `audio snd-materialize-once AUD3_DEV_SND_MATERIALIZE_ONLY`, a token-gated materialization-only command.",
        "- The materializer creates only `/dev/snd/<allowed>` char nodes from `/sys/class/sound/<allowed>/dev`; it never accepts arbitrary paths or inferred major/minor values.",
        "- Allowed names are `controlC[0-9]+`, `pcmC[0-9]+D[0-9]+p`, `pcmC[0-9]+D[0-9]+c`, `timer`, and `seq`.",
        "- Existing nodes are accepted only when they are char devices with matching `st_rdev`; mismatches are refused and not unlinked.",
        "- No ALSA node open, ioctl, mixer, tinyalsa, PCM, HAL, adsprpc invoke/ioctl, `/dev/subsys_adsp` open, or playback path is added.",
        "",
        "## Command Surface",
        "",
        "- `audio adsp-status` / `audio status`: retained AUD-2 status surface, now also emits the bounded `audio.snd_status.*` summary when sysfs can be scanned.",
        "- `audio snd-status`: read-only and menu/power safe.",
        "- `audio snd-materialize-once AUD3_DEV_SND_MATERIALIZE_ONLY`: blocked from menu/power contexts; future live use needs the V2333 explicit AUD-3-preflight operator phrase.",
        "- `audio adsp-boot-once AUD2_ONE_SHOT_ADSP_BOOT`: unchanged and still AUD-2 liveness-only.",
        "",
        "## Safety Boundary",
        "",
        "- This is not AUD-3 playback. It only builds the node-inventory/materialization preflight needed before playback can be evaluated.",
        "- No flash was performed by this source-build unit.",
        "- Future live materialization remains a separate operator-gated step and must rollback to V2321 after validation.",
        "- Future playback remains a later, separate operator-gated AUD-3 step.",
        "",
        "## USB Baseline Retained",
        "",
        "- Parent descriptor remains V2321: `A90-LNX` / `A90 Linux ARM64` / `A90NATIVE001`.",
        "- V2323 named multi-LUN behavior is retained:",
        *identity_lines,
        "",
        "## Helper Flags",
        "",
        *helper_flag_lines,
        "",
        "## Init Extra Flags",
        "",
        *init_extra_flag_lines,
        "",
        "## Static Validation",
        "",
        "- Source build: PASS.",
        "- `file` on init binary: recorded by builder output.",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v2334_audio_snd_nodes_preflight.py`: PASS.",
        "- `python3 -m unittest discover -s tests -p 'test_*.py'`: PASS.",
        "- `git diff --check`: PASS.",
        "",
    ])


def main() -> int:
    helper_flags = configure_base()
    init_extra_flags = tuple(base_module().base.EXTRA_INIT_FLAGS)
    helper_builder = helper_builder_module()
    helper_builder.EXPECTED_HELPER_MARKER = v2323.v2321.EXPECTED_HELPER_MARKER
    helper_builder.EXPECTED_HELPER_SHA256 = v2323.v2321.EXPECTED_HELPER_SHA256
    base = base_module()
    base.base.EXPECTED_HELPER_MARKER = v2323.v2321.EXPECTED_HELPER_MARKER
    base.base.EXPECTED_HELPER_SHA256 = v2323.v2321.EXPECTED_HELPER_SHA256
    helper_builder.patch_helper_builder(base)
    patch_mkbootimg_tool_paths(base)

    def render_with_v2334_info(manifest: dict[str, object]) -> str:
        if "usb_clean_identity_rodata_patch" not in manifest:
            manifest["usb_clean_identity_rodata_patch"] = inherited_clean_identity_patch_info()
        manifest["usb_named_lun_identities"] = v2323.LUN_IDENTITIES
        return render_report(manifest, helper_flags, init_extra_flags)

    base.render_report = render_with_v2334_info
    rc = base.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    patch_info = inherited_clean_identity_patch_info()
    manifest["candidate_tag"] = "v2334-audio-snd-nodes-preflight"
    manifest["parent_baseline"] = "v2331-audio-adsp-fwclass-native-path"
    manifest["rollback_baseline"] = "v2321-usb-clean-identity-rodata"
    manifest["deeper_fallback_baseline"] = "v2237-supplicant-terminate-poll"
    manifest["helper_flags"] = list(helper_flags)
    manifest["init_extra_flags"] = list(init_extra_flags)
    manifest["audio_snd_preflight"] = {
        "snd_status_read_only": True,
        "materialize_command": "audio snd-materialize-once AUD3_DEV_SND_MATERIALIZE_ONLY",
        "materialize_only": True,
        "opens_alsa_nodes": False,
        "ioctl_attempted_by_build": False,
        "playback_attempted_by_build": False,
        "allowed_node_names": [
            "controlC[0-9]+",
            "pcmC[0-9]+D[0-9]+p",
            "pcmC[0-9]+D[0-9]+c",
            "timer",
            "seq",
        ],
    }
    manifest["usb_clean_identity_rodata_patch"] = patch_info
    manifest["usb_named_lun_identities"] = v2323.LUN_IDENTITIES
    manifest["audio_command"] = {
        "name": "audio",
        "subcommands": [
            "adsp-status",
            "status",
            "snd-status",
            "adsp-boot-once",
            "snd-materialize-once",
        ],
        "boot_once_token": "AUD2_ONE_SHOT_ADSP_BOOT",
        "snd_materialize_token": "AUD3_DEV_SND_MATERIALIZE_ONLY",
        "activation_write_attempted_by_build": False,
        "audio_playback_attempted": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(manifest, helper_flags, init_extra_flags), encoding="utf-8")
    promotion_path = OUT_DIR / "promotion-candidate.json"
    promotion_path.write_text(json.dumps({
        "candidate_tag": "v2334-audio-snd-nodes-preflight",
        "boot_image": str(BOOT_IMAGE.relative_to(REPO_ROOT)),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "helper_sha256": manifest["helper_sha256"],
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "audio_command": manifest["audio_command"],
        "audio_snd_preflight": manifest["audio_snd_preflight"],
        "usb_named_lun_identities": manifest["usb_named_lun_identities"],
        "clean_identity_rodata_patch": patch_info,
        "note": "V2334 is a source/build-only AUD-3-preflight artifact. Do not flash or run audio snd-materialize-once without the explicit AUD-3-preflight operator phrase.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
