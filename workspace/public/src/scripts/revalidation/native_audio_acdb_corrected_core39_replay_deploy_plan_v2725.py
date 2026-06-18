#!/usr/bin/env python3
"""V2725 host-only deploy plan for corrected ACDB replay with V2724 ioctl logging helper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import native_audio_acdb_corrected_core39_replay_deploy_plan_v2721 as v2721

ROOT = v2721.ROOT
RUN_ID = "V2725"
BUILD_TAG = "v2725-audio-acdb-corrected-core39-ioctl-result-deploy-plan"
DEFAULT_HELPER = ROOT / "workspace/private/builds/audio/v2724-acdb-setcal-helper-ioctl-result/bin/a90_acdb_setcal_replay_execute_v2635"
EXPECTED_HELPER_SHA256 = "aa9160278a344b706ef644fb1b27b5af39e58553697bbfc4a39f2635282c7751"
DEFAULT_BUILD_ROOT = ROOT / "workspace/private/builds/audio" / BUILD_TAG
DEFAULT_PRIVATE_MANIFEST = DEFAULT_BUILD_ROOT / "deploy-plan.json"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2725_AUDIO_ACDB_CORRECTED_CORE39_IOCTL_RESULT_DEPLOY_PLAN_2026-06-18.md"
DEFAULT_REMOTE_DIR = "/cache/a90-acdb-setcal-replay-v2725"


def write_json(path: Path, payload: dict[str, Any], *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    upstream_args = argparse.Namespace(
        v2636_manifest=args.v2636_manifest,
        v2669_run=args.v2669_run,
        helper=args.helper,
        expected_helper_sha256=args.expected_helper_sha256,
        real_hal_run=args.real_hal_run,
        build_root=args.build_root,
        manifest_path=args.manifest_path,
        report_path=args.report_path,
        remote_dir=args.remote_dir,
        hold_sec=args.hold_sec,
        write_report=args.write_report,
    )
    manifest = v2721.build_manifest(upstream_args)
    ready = bool(manifest.get("ok"))
    manifest["run_id"] = RUN_ID
    manifest["build_tag"] = BUILD_TAG
    manifest["summary"]["decision"] = (
        "v2725-corrected-core39-ioctl-result-deploy-plan-ready"
        if ready else
        "v2725-corrected-core39-ioctl-result-deploy-plan-blocked"
    )
    manifest["v2725_delta"] = {
        "uses_v2724_ioctl_result_helper": True,
        "helper_sha256": manifest.get("helper_contract", {}).get("helper_sha256"),
        "expected_helper_sha256": args.expected_helper_sha256,
        "future_live_has_uniform_ioctl_markers": True,
        "future_live_has_post_set_pre_pcm_dmesg": True,
    }
    return manifest


def write_report(path: Path, manifest: dict[str, Any], private_manifest_path: Path) -> None:
    contract = manifest["corrected_manifest_contract"]
    helper = manifest["helper_contract"]
    lines = [
        "# NATIVE_INIT V2725 — corrected ACDB replay deploy plan with ioctl-result helper",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only deploy-plan refresh for the corrected ACDB SET replay path. This keeps the",
        "V2721 corrected replay set, but replaces the helper artifact with the V2724 private",
        "helper that emits uniform per-ioctl result markers and pairs with the V2639 pre-PCM",
        "dmesg capture. No device action, flash, calibration ioctl, or playback occurred.",
        "",
        "## Decision",
        "",
        f"- decision: `{manifest['summary']['decision']}`",
        f"- ok: `{manifest['ok']}`",
        f"- safe_to_run_native_replay: `{manifest['safe_to_run_native_replay']}`",
        f"- replay_blockers: `{manifest['replay_blockers']}`",
        f"- private_manifest: `{v2721.rel(private_manifest_path)}`",
        f"- remote_dir: `{manifest['remote_dir']}`",
        f"- helper_sha256: `{helper['helper_sha256']}`",
        f"- expected_helper_sha256: `{helper['expected_helper_sha256']}`",
        f"- declared_replay_entries: `{helper['declared_replay_entries']}`",
        f"- helper_entry_count_fits: `{helper['entry_count_fits']}`",
        f"- replay_order: `{contract['replay_order']}`",
        f"- expected_replay_order: `{contract['expected_replay_order']}`",
        f"- stale_cal_types_present: `{contract['stale_cal_types_present']}`",
        f"- no_basic_payload_argv: `{contract['no_basic_payload_argv']}`",
        "",
        "## Replay Entries",
        "",
        "| seq | cal_type | role | kind | payload | ok |",
        "| ---: | ---: | --- | --- | --- | --- |",
    ]
    for entry in manifest["replay_entries"]:
        lines.append(
            f"| {entry.get('sequence')} | {entry.get('cal_type')} | `{entry.get('role')}` | "
            f"`{entry.get('kind')}` | `{bool(entry.get('payload_remote'))}` | `{entry.get('ok')}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The deploy set remains the corrected V2721/V2722 set: cal39 + cal20 +",
            "  per-device records, with no stale 10/14/24 and no legacy `--basic-payload`.",
            "- The helper artifact is the V2724 private build, so the next live run can",
            "  classify every calibration ioctl by `A90_ACDB_SETCAL_IOCTL_RESULT`.",
            "- The paired V2639 runner now captures `post_set_dmesg` before PCM prepare, so",
            "  future live evidence can separate SET ioctl acceptance from DSP prepare failure.",
            "",
            "## Validation",
            "",
            "- Re-read `GOAL.md`, `AGENTS.md`, `CLAUDE.md`, and the ACDB operator spec.",
            "- Generated private V2725 deploy manifest with V2724 helper SHA validation.",
            "- Verified corrected replay order and stale cal_type exclusion through focused tests.",
            "- `py_compile`, focused unittest, dry-run/write-report, and `git diff --check` passed.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2636-manifest", type=Path, default=v2721.DEFAULT_V2636_MANIFEST)
    parser.add_argument("--v2669-run", type=Path, default=v2721.DEFAULT_V2669_RUN)
    parser.add_argument("--helper", type=Path, default=DEFAULT_HELPER)
    parser.add_argument("--expected-helper-sha256", default=EXPECTED_HELPER_SHA256)
    parser.add_argument("--real-hal-run", default=v2721.DEFAULT_REAL_HAL_RUN)
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_PRIVATE_MANIFEST)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--remote-dir", default=DEFAULT_REMOTE_DIR)
    parser.add_argument("--hold-sec", type=int, default=10)
    parser.add_argument("--write-report", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args)
    write_json(Path(args.manifest_path), manifest, mode=0o600)
    if args.write_report:
        write_report(Path(args.report_path), manifest, Path(args.manifest_path))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
