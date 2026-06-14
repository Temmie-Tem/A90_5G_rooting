#!/usr/bin/env python3
"""V2399 host-only analyzer for V2397 Android/Magisk ACDB captures.

This script does not touch the device.  It consumes a private V2397
Android/Magisk ACDB measurement run directory and classifies whether the stock
Android-good evidence points to a bounded native ACDB/App Type bootstrap, an
opaque HAL dependency, an incomplete capture, or a complete-but-negative capture.

Raw Android logs and pulled artifacts remain under workspace/private; the JSON
output reports only marker counts, selected lines, and metadata needed for the
next engineering decision.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

RUN_ID = "V2399"
BUILD_TAG = "v2399-audio-acdb-capture-analyzer"
ROOT = Path(__file__).resolve().parents[5]
DEFAULT_RUNS_ROOT = ROOT / "workspace/private/runs/audio"
RUN_GLOB = "v2397-android-acdb-measurement-*"

STIMULUS_MARKERS = (
    "A90_AUDIO_STIMULUS_BEGIN",
    "A90_AUDIO_STIMULUS_END",
    "A90_AUDIO_STIMULUS_FINISH",
)
ERROR_MARKERS = (
    "A90_AUDIO_STIMULUS_ERROR",
    "REVIEW_PERMISSIONS",
    "PermissionController",
)
CALIBRATION_PATTERNS: dict[str, str] = {
    "ACDB": r"\bACDB\b|\bacdb\b|acdb_loader|libacdbloader",
    "msm_audio_cal": r"msm_audio_cal|/dev/msm_audio_cal",
    "send_afe_cal": r"send_afe_cal|send_afe_cal_type|afe_get_cal_topology_id",
    "q6asm_send_cal": r"q6asm_send_cal|q6asm",
    "adm_open": r"adm_open|ADM_CMD|adm_",
    "app_type": r"app[_ -]?type|App Type|Audio Stream 0 App Type Cfg",
}
HAL_PATTERNS: dict[str, str] = {
    "audio_primary": r"audio\.primary\.msmnile\.so|audio\.primary",
    "libacdbloader": r"libacdbloader\.so|acdbloader",
    "libtinyalsa": r"libtinyalsa\.so|tinyalsa",
    "hwbinder": r"hwbinder|android\.hardware\.audio",
}
PHASES = ("baseline", "active", "post")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - analyzer reports malformed private artifacts.
        return {"_parse_error": str(exc)}


def latest_run_dir(runs_root: Path = DEFAULT_RUNS_ROOT) -> Path | None:
    candidates = [path for path in runs_root.glob(RUN_GLOB) if path.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def find_first(root: Path, names: Iterable[str]) -> Path | None:
    for name in names:
        direct = root / name
        if direct.exists():
            return direct
    for name in names:
        matches = sorted(root.rglob(name))
        if matches:
            return matches[0]
    return None


def find_all(root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in root.rglob(pattern) if path.is_file())


def collect_artifacts(run_dir: Path) -> dict[str, Any]:
    result_path = find_first(run_dir, ["result.json"])
    logcat_path = find_first(run_dir, ["stimulus-logcat.stdout.txt", "acdb-logcat.stdout.txt"])
    if logcat_path is None:
        logcat_matches = [path for path in find_all(run_dir, "*logcat*.stdout.txt") if path.is_file()]
        logcat_path = logcat_matches[0] if logcat_matches else None

    phase_files: dict[str, dict[str, list[Path]]] = {}
    for phase in PHASES:
        phase_files[phase] = {
            "meta": find_all(run_dir, f"{phase}-meta.txt"),
            "tinymix": find_all(run_dir, f"{phase}-tinymix-all-values.txt"),
            "dmesg": find_all(run_dir, f"{phase}-dmesg-tail.txt"),
            "devnodes": find_all(run_dir, f"{phase}-devnodes.txt"),
            "proc_asound": find_all(run_dir, f"{phase}-proc-asound.txt"),
            "hal_pids": find_all(run_dir, f"{phase}-audio-hal-pids.txt"),
            "hal_maps": find_all(run_dir, f"{phase}-audio-hal-*-maps.txt"),
            "hal_fd": find_all(run_dir, f"{phase}-audio-hal-*-fd.txt"),
            "getprop": find_all(run_dir, f"{phase}-getprop-audio.txt"),
            "ps": find_all(run_dir, f"{phase}-ps.txt"),
        }

    return {
        "run_dir": run_dir,
        "result_path": result_path,
        "logcat_path": logcat_path,
        "phase_files": phase_files,
    }


def path_list(paths: list[Path]) -> list[str]:
    return [rel(path) for path in paths]


def artifact_manifest(artifacts: dict[str, Any]) -> dict[str, Any]:
    phase_manifest: dict[str, dict[str, list[str]]] = {}
    for phase, groups in artifacts["phase_files"].items():
        phase_manifest[phase] = {name: path_list(paths) for name, paths in groups.items()}
    return {
        "result": rel(artifacts["result_path"]) if artifacts["result_path"] else None,
        "logcat": rel(artifacts["logcat_path"]) if artifacts["logcat_path"] else None,
        "phases": phase_manifest,
    }


def missing_requirements(artifacts: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if artifacts["result_path"] is None:
        missing.append("result.json")
    if artifacts["logcat_path"] is None:
        missing.append("stimulus-logcat.stdout.txt")
    for phase, groups in artifacts["phase_files"].items():
        for group in ("tinymix", "dmesg", "devnodes", "proc_asound"):
            if not groups[group]:
                missing.append(f"{phase}-{group}")
    return missing


def concat_files(paths: list[Path]) -> str:
    return "\n".join(read_text(path) for path in paths)


def all_phase_text(artifacts: dict[str, Any], groups: Iterable[str]) -> str:
    paths: list[Path] = []
    for phase in PHASES:
        for group in groups:
            paths.extend(artifacts["phase_files"][phase][group])
    return concat_files(paths)


def count_patterns(text: str, patterns: dict[str, str]) -> dict[str, int]:
    return {
        name: len(re.findall(pattern, text, flags=re.IGNORECASE))
        for name, pattern in patterns.items()
    }


def selected_lines(text: str, pattern: str, *, limit: int = 20) -> list[str]:
    regex = re.compile(pattern, flags=re.IGNORECASE)
    lines: list[str] = []
    for line in text.splitlines():
        if regex.search(line):
            stripped = line.strip()
            if stripped and stripped not in lines:
                lines.append(stripped[:500])
        if len(lines) >= limit:
            break
    return lines


def stimulus_state(logcat: str) -> dict[str, Any]:
    counts = {marker: logcat.count(marker) for marker in (*STIMULUS_MARKERS, *ERROR_MARKERS)}
    return {
        "counts": counts,
        "ok": all(counts[marker] > 0 for marker in STIMULUS_MARKERS) and all(counts[marker] == 0 for marker in ERROR_MARKERS),
    }


def phase_app_type_lines(artifacts: dict[str, Any]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for phase in PHASES:
        text = concat_files(artifacts["phase_files"][phase]["tinymix"])
        output[phase] = selected_lines(text, r"Audio Stream \d+ App Type Cfg|App Type|app[_ -]?type", limit=12)
    return output


def result_state(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "ok": bool(result.get("ok")),
        "rolled_back": bool(result.get("rolled_back")),
        "rollback_fallback": result.get("rollback_fallback"),
        "approval_ok": bool(result.get("approval_ok")),
        "run_id": result.get("run_id"),
        "build_tag": result.get("build_tag"),
    }


def classify(payload: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if payload["missing_requirements"]:
        return "capture-incomplete", ["missing required artifacts"] + payload["missing_requirements"]

    result = payload["result"]
    if not result["ok"] or not result["rolled_back"]:
        reasons.append("result.json does not prove capture ok plus rollback")
    if not payload["stimulus"]["ok"]:
        reasons.append("AudioTrack stimulus markers incomplete or error markers present")

    calibration_counts = payload["marker_counts"]["calibration"]
    has_app_type = any(payload["app_type_lines"].values()) or calibration_counts["app_type"] > 0
    has_acdb = calibration_counts["ACDB"] > 0 or calibration_counts["msm_audio_cal"] > 0
    has_dsp_cal_edge = any(calibration_counts[name] > 0 for name in ("send_afe_cal", "q6asm_send_cal", "adm_open"))
    has_hal_symbols = any(payload["marker_counts"]["hal"].values())

    if result["ok"] and result["rolled_back"] and payload["stimulus"]["ok"] and has_app_type and has_acdb and has_dsp_cal_edge:
        reasons.append("capture has stimulus, App Type, ACDB/msm_audio_cal, and AFE/ASM/ADM calibration edges")
        return "bounded-native-acdb-candidate", reasons

    no_sequence_markers = not has_app_type and calibration_counts["ACDB"] == 0 and not has_dsp_cal_edge
    if no_sequence_markers:
        reasons.append("capture complete but no App Type or calibration sequence markers were found")
        return "negative-no-calibration", reasons

    if has_hal_symbols and not (has_app_type and has_acdb and has_dsp_cal_edge):
        reasons.append("evidence points at Android HAL/vendor libs but lacks a bounded ACDB edge sequence")
        return "hal-dependent-or-opaque", reasons

    reasons.append("capture complete but marker set is insufficient for bounded native bootstrap")
    return "negative-no-calibration", reasons


def analyze_run(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    artifacts = collect_artifacts(run_dir)
    missing = missing_requirements(artifacts)
    result = load_json(artifacts["result_path"]) if artifacts["result_path"] else {}
    logcat = read_text(artifacts["logcat_path"]) if artifacts["logcat_path"] else ""
    calibration_text = "\n".join([
        logcat,
        all_phase_text(artifacts, ("dmesg", "tinymix", "devnodes", "getprop")),
    ])
    hal_text = all_phase_text(artifacts, ("hal_maps", "hal_fd", "ps", "getprop"))
    app_lines = phase_app_type_lines(artifacts)
    calibration_lines = selected_lines(
        calibration_text,
        r"ACDB|acdb|msm_audio_cal|send_afe_cal|q6asm_send_cal|adm_open|App Type|app[_ -]?type",
        limit=30,
    )
    hal_lines = selected_lines(
        hal_text,
        r"audio\.primary|libacdbloader|libtinyalsa|android\.hardware\.audio|hwbinder",
        limit=20,
    )
    devnode_lines = selected_lines(
        all_phase_text(artifacts, ("devnodes",)),
        r"/dev/msm_audio_cal|/dev/snd|/dev/ion",
        limit=20,
    )

    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "generated_at": now_iso(),
        "host_only": True,
        "device_action": "none",
        "raw_logs_private": True,
        "run_dir": rel(run_dir),
        "artifact_manifest": artifact_manifest(artifacts),
        "missing_requirements": missing,
        "result": result_state(result),
        "stimulus": stimulus_state(logcat),
        "marker_counts": {
            "calibration": count_patterns(calibration_text, CALIBRATION_PATTERNS),
            "hal": count_patterns(hal_text, HAL_PATTERNS),
        },
        "app_type_lines": app_lines,
        "selected_evidence_lines": {
            "calibration": calibration_lines,
            "hal": hal_lines,
            "devnodes": devnode_lines,
        },
    }
    decision, reasons = classify(payload)
    payload["decision"] = decision
    payload["ok"] = decision in {"bounded-native-acdb-candidate", "hal-dependent-or-opaque", "negative-no-calibration"}
    payload["reasons"] = reasons
    payload["next_action"] = next_action(decision)
    return payload


def next_action(decision: str) -> str:
    if decision == "bounded-native-acdb-candidate":
        return "design a bounded native ACDB/App Type bootstrap using only the observed minimal sequence"
    if decision == "hal-dependent-or-opaque":
        return "close or narrow the audio epic unless a specific M1/M2 Magisk measurement gap is proven"
    if decision == "capture-incomplete":
        return "fix measurement capture or consider a separately gated M1 early-boot Magisk sampler only if timing was missed"
    return "do not design native ACDB yet; inspect capture gaps or rerun AUD-5A if evidence is too thin"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, help="private V2397 run directory to analyze")
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT, help="root used to locate latest V2397 run when --run-dir is omitted")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir or latest_run_dir(args.runs_root)
    if run_dir is None:
        payload = {
            "run_id": RUN_ID,
            "build_tag": BUILD_TAG,
            "generated_at": now_iso(),
            "host_only": True,
            "device_action": "none",
            "decision": "capture-incomplete",
            "ok": False,
            "reason": f"no {RUN_GLOB} run directory found under {args.runs_root}",
            "next_action": next_action("capture-incomplete"),
        }
    else:
        payload = analyze_run(run_dir)
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True) + "\n", end="")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
