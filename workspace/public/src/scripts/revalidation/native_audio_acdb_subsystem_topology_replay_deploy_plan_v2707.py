#!/usr/bin/env python3
"""V2707 host-only deploy plan using the entry-cap ACDB SET replay helper.

V2706 proved the V2705 manifest still staged the older V2635 helper artifact,
which rejected the expanded 12-entry replay argv before any ACDB ioctl ran.
This unit converts the V2705 manifest to use the private V2679 entry-cap helper
artifact and validates that the declared replay entry count fits the helper
contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import native_audio_acdb_subsystem_topology_replay_deploy_plan_v2705 as v2705

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2707"
BUILD_TAG = "v2707-audio-acdb-subsystem-topology-entrycap-deploy-plan"
DEFAULT_V2705_MANIFEST = ROOT / "workspace/private/builds/audio/v2705-audio-acdb-subsystem-topology-replay-deploy-plan/deploy-plan.json"
DEFAULT_HELPER = ROOT / "workspace/private/builds/audio/v2679-acdb-setcal-helper-entry-cap/bin/a90_acdb_setcal_replay_execute_v2635"
DEFAULT_PRIVATE_MANIFEST = ROOT / "workspace/private/builds/audio" / BUILD_TAG / "deploy-plan.json"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2707_AUDIO_ACDB_SUBSYSTEM_TOPOLOGY_ENTRYCAP_DEPLOY_PLAN_2026-06-18.md"
DEFAULT_REMOTE_DIR = "/cache/a90-acdb-setcal-replay-v2707"
EXPECTED_HELPER_SHA256 = "5da19e3127255702f7ef2389d7252b4edf30c59185792f30057aa36a2ca33d18"
EXPECTED_HELPER_MAX_REPLAY_ENTRIES = 16
REQUIRED_HELPER_STRINGS = {
    "start_marker": "A90_ACDB_SETCAL_REPLAY_START",
    "set_marker": "A90_ACDB_SETCAL_SET_OK",
    "done_marker": "A90_ACDB_SETCAL_REPLAY_DONE",
    "basic_payload_option": "--basic-payload CAL_TYPE:BUFFER:PAYLOAD",
    "exact_set_option": "--exact-set ARG[:PAYLOAD]",
    "entry_count_guard": "entry count out of bounds: %zu",
}


def rel(path: Path | str) -> str:
    target = Path(path)
    try:
        return str(target.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strings_text(path: Path) -> str:
    completed = subprocess.run(
        ["strings", "-a", str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30.0,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout


def source_entry_cap_state() -> dict[str, Any]:
    source = ROOT / "workspace/public/src/native-init/helpers/a90_acdb_setcal_replay_scaffold_v2635.c"
    text = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    token = f"#define A90_MAX_REPLAY_ENTRIES {EXPECTED_HELPER_MAX_REPLAY_ENTRIES}"
    return {
        "source": rel(source),
        "exists": source.exists(),
        "expected_token": token,
        "entry_cap_source_ok": token in text,
    }


def helper_state(helper_path: Path, expected_sha256: str | None = EXPECTED_HELPER_SHA256) -> dict[str, Any]:
    state: dict[str, Any] = {
        "path_private": rel(helper_path),
        "exists": helper_path.exists(),
        "ok": False,
        "sha256": None,
        "size": None,
        "mode": None,
        "private_only": True,
        "expected_sha256": expected_sha256,
        "sha256_matches": False,
        "required_strings": {name: False for name in REQUIRED_HELPER_STRINGS},
    }
    if not helper_path.exists() or not helper_path.is_file():
        return state
    digest = sha256_file(helper_path)
    text = strings_text(helper_path)
    required = {name: marker in text for name, marker in REQUIRED_HELPER_STRINGS.items()}
    file_result = subprocess.run(["file", str(helper_path)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30.0)
    state.update(
        {
            "sha256": digest,
            "size": helper_path.stat().st_size,
            "mode": oct(helper_path.stat().st_mode & 0o777),
            "file": file_result.stdout.strip(),
            "sha256_matches": expected_sha256 is None or digest == expected_sha256,
            "required_strings": required,
        }
    )
    state["ok"] = bool(state["sha256_matches"] and all(required.values()))
    return state


def replace_remote_dir(value: Any, old_remote_dir: str, new_remote_dir: str) -> Any:
    if isinstance(value, str):
        return value.replace(old_remote_dir, new_remote_dir)
    if isinstance(value, list):
        return [replace_remote_dir(item, old_remote_dir, new_remote_dir) for item in value]
    if isinstance(value, dict):
        return {key: replace_remote_dir(item, old_remote_dir, new_remote_dir) for key, item in value.items()}
    return value


def file_state_for_helper(path: Path, helper: dict[str, Any], remote_path: str) -> dict[str, Any]:
    return {
        "kind": "helper",
        "local": {
            "local_path_private": rel(path),
            "exists": helper["exists"],
            "ok": helper["ok"],
            "size": helper.get("size"),
            "sha256": helper.get("sha256"),
            "nonzero": bool((helper.get("size") or 0) > 0),
            "size_matches": True,
            "sha256_matches": helper.get("sha256_matches"),
            "private_only": True,
            "mode": helper.get("mode"),
        },
        "ok": helper["ok"],
        "remote_path": remote_path,
        "remote_mode": "0700",
        "remote_sha256_command": f"sha256sum {remote_path}",
    }


def entry_count(manifest: dict[str, Any]) -> int:
    entries = manifest.get("replay_entries")
    if isinstance(entries, list):
        return len(entries)
    argv = manifest.get("remote_argv") or []
    return int(argv.count("--basic-payload") + argv.count("--exact-set"))


def build_manifest(v2705_manifest_path: Path,
                   helper_path: Path,
                   *,
                   remote_dir: str = DEFAULT_REMOTE_DIR,
                   expected_helper_sha256: str | None = EXPECTED_HELPER_SHA256) -> dict[str, Any]:
    base = read_json(v2705_manifest_path)
    if not base.get("ok") or not base.get("all_inputs_ok"):
        raise RuntimeError(f"V2705 manifest is not ready: {rel(v2705_manifest_path)}")
    old_remote_dir = str(base.get("remote_dir") or "")
    if not old_remote_dir:
        raise RuntimeError("V2705 manifest lacks remote_dir")

    helper = helper_state(helper_path, expected_helper_sha256)
    source_state = source_entry_cap_state()
    manifest = replace_remote_dir(base, old_remote_dir, remote_dir)
    manifest.update(
        {
            "run_id": RUN_ID,
            "build_tag": BUILD_TAG,
            "created_at": now_iso(),
            "source_v2705_manifest": rel(v2705_manifest_path),
            "remote_dir": remote_dir,
            "native_calibration_ioctls_run": False,
            "audio_playback_run": False,
            "device_action": "none",
            "flash_action": "none",
        }
    )

    files = list(manifest.get("files") or [])
    helper_indices = [index for index, item in enumerate(files) if item.get("kind") == "helper"]
    if len(helper_indices) != 1:
        raise RuntimeError(f"expected one helper file entry, found {len(helper_indices)}")
    remote_helper_path = f"{remote_dir}/{Path(str(files[helper_indices[0]].get('remote_path'))).name}"
    files[helper_indices[0]] = file_state_for_helper(helper_path, helper, remote_helper_path)
    manifest["files"] = files
    manifest["files_redacted"] = [v2705.redacted_file(entry) for entry in files]

    argv = list(manifest.get("remote_argv") or [])
    if not argv:
        raise RuntimeError("manifest lacks remote_argv")
    argv[0] = remote_helper_path
    manifest["remote_argv"] = argv

    replay_entry_count = entry_count(manifest)
    helper_contract = {
        "helper_source": source_state,
        "helper_path_private": helper["path_private"],
        "helper_sha256": helper.get("sha256"),
        "expected_helper_sha256": expected_helper_sha256,
        "helper_ok": helper.get("ok"),
        "helper_required_strings": helper.get("required_strings"),
        "max_replay_entries": EXPECTED_HELPER_MAX_REPLAY_ENTRIES,
        "declared_replay_entries": replay_entry_count,
        "entry_count_fits": replay_entry_count <= EXPECTED_HELPER_MAX_REPLAY_ENTRIES,
    }
    manifest["helper_upgrade"] = {
        "from_private_sha256": base.get("files", [{}])[helper_indices[0]].get("local", {}).get("sha256"),
        "to_private_sha256": helper.get("sha256"),
        "reason": "V2706 rejected the expanded 12-entry argv with the older helper artifact",
    }
    manifest["helper_contract"] = helper_contract
    all_inputs_ok = bool(all(entry.get("ok") for entry in files))
    gate_ok = bool(all_inputs_ok and helper.get("ok") and source_state.get("entry_cap_source_ok") and helper_contract["entry_count_fits"])
    manifest["all_inputs_ok"] = all_inputs_ok
    manifest["ok"] = gate_ok
    manifest["native_replay_ready"] = gate_ok
    manifest["safe_to_run_native_replay"] = gate_ok
    blockers: list[str] = []
    if not all_inputs_ok:
        blockers.append("one or more deployment inputs failed local validation")
    if not helper.get("ok"):
        blockers.append("entry-cap helper artifact validation failed")
    if not source_state.get("entry_cap_source_ok"):
        blockers.append("helper source does not expose expected entry cap")
    if not helper_contract["entry_count_fits"]:
        blockers.append("declared replay entry count exceeds helper max")
    manifest["replay_blockers"] = blockers
    summary = dict(manifest.get("summary") or {})
    summary.update(
        {
            "decision": "v2707-entrycap-deploy-plan-ready" if gate_ok else "v2707-entrycap-deploy-plan-blocked",
            "replay_entry_count": replay_entry_count,
            "helper_sha256": helper.get("sha256"),
            "helper_entry_cap": EXPECTED_HELPER_MAX_REPLAY_ENTRIES,
            "entry_count_fits": helper_contract["entry_count_fits"],
        }
    )
    manifest["summary"] = summary
    return manifest


def write_report(path: Path, manifest: dict[str, Any], private_manifest_path: Path) -> None:
    helper = manifest.get("helper_contract") or {}
    summary = manifest.get("summary") or {}
    lines = [
        "# NATIVE_INIT V2707 — subsystem topology replay entry-cap deploy plan",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only fix for the V2706 pre-ACDB block. V2706 proved the V2705",
        "manifest staged the old V2635 helper artifact and the helper rejected",
        "the expanded 12-entry replay argv before any ACDB ioctl ran.",
        "",
        "This unit rewrites the deploy manifest to stage the V2679 entry-cap helper",
        "artifact and validates that the declared replay entry count fits the helper",
        "contract. No device action, flash, audio playback, or calibration ioctl ran.",
        "",
        "## Result",
        "",
        f"- decision: `{summary.get('decision')}`",
        f"- ok: `{manifest.get('ok')}`",
        f"- native_replay_ready: `{manifest.get('native_replay_ready')}`",
        f"- safe_to_run_native_replay: `{manifest.get('safe_to_run_native_replay')}`",
        f"- private_manifest: `{rel(private_manifest_path)}`",
        f"- remote_dir: `{manifest.get('remote_dir')}`",
        "",
        "## Helper Contract",
        "",
        f"- helper_private_path: `{helper.get('helper_path_private')}`",
        f"- helper_sha256: `{helper.get('helper_sha256')}`",
        f"- expected_helper_sha256: `{helper.get('expected_helper_sha256')}`",
        f"- helper_ok: `{helper.get('helper_ok')}`",
        f"- max_replay_entries: `{helper.get('max_replay_entries')}`",
        f"- declared_replay_entries: `{helper.get('declared_replay_entries')}`",
        f"- entry_count_fits: `{helper.get('entry_count_fits')}`",
        "",
        "## Replay Shape",
        "",
        "- prepended basic payloads: cal_type 39 core, 24 AFE, 10 ADM, 14 ASM",
        "- existing exact SET records remain in the captured order after those topology payloads",
        "- final live replay remains delegated to the checked V2639 runner",
        "",
        "## Gate Blockers",
        "",
    ]
    blockers = manifest.get("replay_blockers") or []
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Unit",
            "",
            "V2708 may rerun the V2639 live replay with this V2707 manifest. The",
            "expected new frontier is the actual ACDB SET sequence and subsequent PCM",
            "probe; if it fails before the final SET marker again, that is no longer",
            "the V2706 helper artifact mismatch.",
            "",
            "## Validation",
            "",
            "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_subsystem_topology_replay_deploy_plan_v2707.py tests/test_native_audio_acdb_subsystem_topology_replay_deploy_plan_v2707.py`",
            "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_subsystem_topology_replay_deploy_plan_v2707 -v`",
            "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_subsystem_topology_replay_deploy_plan_v2707.py --write-report`",
            "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_setcal_replay_live_handoff_v2639.py --dry-run --v2636-manifest workspace/private/builds/audio/v2707-audio-acdb-subsystem-topology-entrycap-deploy-plan/deploy-plan.json --manifest-path /tmp/v2639-v2707-preflight-manifest.json`",
            "- `git diff --check`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2705-manifest", type=Path, default=DEFAULT_V2705_MANIFEST)
    parser.add_argument("--helper", type=Path, default=DEFAULT_HELPER)
    parser.add_argument("--remote-dir", default=DEFAULT_REMOTE_DIR)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_PRIVATE_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_manifest(args.v2705_manifest, args.helper, remote_dir=args.remote_dir)
    manifest["manifest_path"] = rel(args.manifest_path)
    write_json(args.manifest_path, manifest, mode=0o600)
    if args.write_report:
        write_report(args.report, manifest, args.manifest_path)
    print(json.dumps({
        "decision": manifest.get("summary", {}).get("decision"),
        "ok": manifest.get("ok"),
        "private_manifest": rel(args.manifest_path),
        "report": rel(args.report) if args.write_report else None,
        "helper_sha256": manifest.get("helper_contract", {}).get("helper_sha256"),
        "declared_replay_entries": manifest.get("helper_contract", {}).get("declared_replay_entries"),
        "max_replay_entries": manifest.get("helper_contract", {}).get("max_replay_entries"),
        "safe_to_run_native_replay": manifest.get("safe_to_run_native_replay"),
        "replay_blockers": manifest.get("replay_blockers"),
    }, indent=2, sort_keys=True))
    return 0 if manifest.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
