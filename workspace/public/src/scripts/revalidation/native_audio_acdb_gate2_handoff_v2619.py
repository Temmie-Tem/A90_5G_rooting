#!/usr/bin/env python3
"""Build a Gate-2 handoff manifest from the V2618 ACDB capture.

Host-only. Reads the private V2618 direct-matrix run, verifies captured raw
payload hashes, writes a private raw-path manifest for operator Gate-2 review,
and writes a redacted public report. It never promotes the payloads into replay
and never copies raw bytes into tracked paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2619"
BUILD_TAG = "v2619-audio-acdb-gate2-handoff"
DEFAULT_RUN_GLOB = "v2618-acdb-direct-matrix-*"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2619_AUDIO_ACDB_GATE2_HANDOFF_2026-06-16.md"
DEFAULT_PRIVATE_NAME = "v2619-acdb-gate2-handoff-manifest.json"


def rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: dict[str, Any], mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def parse_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text, 0)
    except ValueError:
        return None


def cmd_text(value: Any) -> str:
    parsed = parse_int(value)
    if parsed is None:
        return str(value or "")
    return f"0x{parsed:08x}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def all_zero(path: Path) -> bool:
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            if any(chunk):
                return False
    return True


def latest_v2618_run(base: Path) -> Path:
    candidates = sorted(
        path for path in base.glob(DEFAULT_RUN_GLOB)
        if path.is_dir() and (path / "v2618-result.json").exists()
    )
    if not candidates:
        raise FileNotFoundError(f"no V2618 runs with v2618-result.json under {rel(base)}")
    return candidates[-1]


def local_raw_from_state(run_dir: Path, state: dict[str, Any]) -> Path | None:
    local = state.get("local_raw_path")
    if local:
        return ROOT / str(local)
    raw_path = state.get("raw_path")
    if raw_path:
        return run_dir / "ownget-device-artifacts" / str(raw_path).split("/a90-acdb-tap/", 1)[-1]
    return None


def payload_category(buffer_name: str, cmd: str) -> str:
    if buffer_name == "ind-ap-common":
        return "AUDPROC_COMMON_CANDIDATE"
    if buffer_name == "ind-ap-stream":
        return "AUDPROC_STREAM_CANDIDATE"
    if buffer_name == "ind-afe-common":
        return "AFE_COMMON_CANDIDATE"
    if "vol" in buffer_name or cmd in {"0x0001326d", "0x0001326e"}:
        return "VOL_CANDIDATE"
    if cmd in {"0x000130da", "0x000130dc", "0x00013296"}:
        return "TOPOLOGY_CANDIDATE"
    return "UNMAPPED_CANDIDATE"


def collect_payload_candidates(run_dir: Path, result: dict[str, Any]) -> list[dict[str, Any]]:
    summary = result.get("direct_matrix_summary", {})
    base_summary = summary.get("base_summary", {})
    records = summary.get("ordered_records") or []
    candidates: list[dict[str, Any]] = []
    for index, state in enumerate(records, 1):
        buffer_name = str(state.get("buffer") or "")
        out_len = parse_int(state.get("out_len"))
        ret = parse_int(state.get("ret"))
        cmd = cmd_text(state.get("cmd"))
        local_raw = local_raw_from_state(run_dir, state)
        if not buffer_name.startswith("ind-"):
            continue
        if ret != 0 or out_len is None or out_len <= 4:
            continue
        if local_raw is None or not local_raw.exists():
            continue
        raw_size = local_raw.stat().st_size
        raw_sha = sha256_file(local_raw)
        zero = all_zero(local_raw)
        expected_sha = state.get("sha256") or state.get("raw_sha256")
        if raw_size != out_len or zero:
            verified = False
        else:
            verified = expected_sha in (None, raw_sha)
        candidates.append({
            "order": len(candidates) + 1,
            "record_index": index,
            "category": payload_category(buffer_name, cmd),
            "cmd": cmd,
            "seq": str(state.get("seq") or ""),
            "buffer": buffer_name,
            "in_len": parse_int(state.get("in_len")),
            "out_len": out_len,
            "ret": ret,
            "sha256": raw_sha,
            "raw_size": raw_size,
            "nonzero": not zero,
            "hash_matches_event": expected_sha in (None, raw_sha),
            "verified_for_gate2": bool(verified),
            "raw_path_private": rel(local_raw),
            "source_device_raw_path": state.get("raw_path"),
        })
    return candidates


def collect_case_returns(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "ownget-device-artifacts/acdb-v2617-direct-matrix-events.jsonl"
    rows: list[dict[str, Any]] = []
    for event in read_jsonl(path):
        if event.get("event") != "v2617_direct_matrix" or event.get("stage") != "case_return":
            continue
        rows.append({
            "case": event.get("case"),
            "cmd": cmd_text(event.get("cmd")),
            "step": parse_int(event.get("step")),
            "ret": parse_int(event.get("ret")),
            "out_word": cmd_text(event.get("out_word")),
        })
    return rows


def redacted_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        key: candidate[key]
        for key in [
            "order", "category", "cmd", "seq", "buffer", "in_len", "out_len", "ret",
            "sha256", "raw_size", "nonzero", "hash_matches_event", "verified_for_gate2",
        ]
    }


def build_manifest(run_dir: Path) -> dict[str, Any]:
    result_path = run_dir / "v2618-result.json"
    if not result_path.exists():
        raise FileNotFoundError(f"missing {rel(result_path)}")
    result = read_json(result_path)
    summary = result.get("direct_matrix_summary", {})
    candidates = collect_payload_candidates(run_dir, result)
    case_returns = collect_case_returns(run_dir)
    categories = [item["category"] for item in candidates]
    vol_cases = [row for row in case_returns if str(row.get("case") or "").startswith("vol-")]
    payload = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_run_id": "V2618",
        "source_run_dir": rel(run_dir),
        "source_result": rel(result_path),
        "source_decision": result.get("decision"),
        "source_rolled_back": result.get("rolled_back"),
        "source_operator_valuable": result.get("operator_valuable"),
        "gate": "operator-gate2-pending",
        "native_replay_ready": False,
        "replay_blockers": [
            "operator must map size/order/cmd to ACDB cal_type before replay",
            "VOL payload absent in V2618 direct matrix capture",
        ],
        "summary": {
            "payload_candidate_count": len(candidates),
            "payload_verified_count": sum(1 for item in candidates if item.get("verified_for_gate2")),
            "audproc_candidate_count": sum(1 for item in candidates if str(item.get("category", "")).startswith("AUDPROC")),
            "afe_candidate_count": sum(1 for item in candidates if str(item.get("category", "")).startswith("AFE")),
            "vol_candidate_count": sum(1 for item in candidates if str(item.get("category", "")).startswith("VOL")),
            "topology_candidate_count": sum(1 for item in candidates if str(item.get("category", "")).startswith("TOPOLOGY")),
            "case_return_count": len(case_returns),
            "vol_case_return_count": len(vol_cases),
            "matrix_complete": summary.get("matrix_complete"),
            "v2618_classification": summary.get("classification"),
            "real_audio_set_pass_through_count": summary.get("real_audio_set_pass_through_count"),
        },
        "payload_candidates": candidates,
        "payload_candidates_redacted": [redacted_payload(item) for item in candidates],
        "case_returns": case_returns,
        "category_order": categories,
        "operator_note": (
            "Use raw_path_private only from workspace/private. Public report contains SHA/length only. "
            "Do not enter replay until Gate-2 mapping verifies cal_type/order and the missing VOL path is resolved."
        ),
    }
    payload["ok"] = bool(
        candidates
        and payload["summary"]["payload_candidate_count"] == payload["summary"]["payload_verified_count"]
        and payload["summary"].get("real_audio_set_pass_through_count") == 0
    )
    return payload


def write_report(path: Path, manifest: dict[str, Any], private_manifest_path: Path) -> None:
    summary = manifest.get("summary", {})
    lines = [
        "# NATIVE_INIT V2619 — ACDB Gate-2 handoff manifest",
        "",
        "Date: 2026-06-16",
        "",
        "## Scope",
        "",
        "Host-only handoff of the V2618 ACDB direct-matrix capture. This unit does not",
        "run the device, does not replay calibration, and does not copy raw payload bytes",
        "into tracked paths. It writes a private raw-path manifest for operator Gate-2",
        "mapping and a public redacted report with command/order/length/SHA metadata.",
        "",
        "## Result",
        "",
        f"- decision: `v2619-gate2-handoff-{'ready' if manifest.get('ok') else 'needs-review'}`",
        f"- ok: `{manifest.get('ok')}`",
        f"- source_decision: `{manifest.get('source_decision')}`",
        f"- source_rolled_back: `{manifest.get('source_rolled_back')}`",
        f"- source_run_dir: `{manifest.get('source_run_dir')}`",
        f"- private_manifest: `{rel(private_manifest_path)}`",
        f"- native_replay_ready: `{manifest.get('native_replay_ready')}`",
        f"- payload_candidate_count: `{summary.get('payload_candidate_count')}`",
        f"- payload_verified_count: `{summary.get('payload_verified_count')}`",
        f"- audproc_candidate_count: `{summary.get('audproc_candidate_count')}`",
        f"- afe_candidate_count: `{summary.get('afe_candidate_count')}`",
        f"- vol_candidate_count: `{summary.get('vol_candidate_count')}`",
        f"- topology_candidate_count: `{summary.get('topology_candidate_count')}`",
        f"- case_return_count: `{summary.get('case_return_count')}`",
        f"- vol_case_return_count: `{summary.get('vol_case_return_count')}`",
        f"- real_audio_set_pass_through_count: `{summary.get('real_audio_set_pass_through_count')}`",
        "",
        "## Payload Candidates",
        "",
        "| order | category | cmd | seq | buffer | bytes | sha256 |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for item in manifest.get("payload_candidates_redacted", []):
        lines.append(
            f"| {item.get('order')} | `{item.get('category')}` | `{item.get('cmd')}` | "
            f"`{item.get('seq')}` | `{item.get('buffer')}` | {item.get('out_len')} | "
            f"`{item.get('sha256')}` |"
        )
    lines.extend([
        "",
        "## Gate-2 Boundary",
        "",
        "- These rows are **not** a replay manifest yet.",
        "- Operator must verify size/order to cal_type mapping before any V2552 replay extension.",
        "- VOL is still absent in V2618; replay remains blocked for the VOL cal_type path.",
        "- Raw payload paths exist only in the private manifest and must not be committed.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_gate2_handoff_v2619.py tests/test_native_audio_acdb_gate2_handoff_v2619.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_gate2_handoff_v2619 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_gate2_handoff_v2619.py --write-report`",
        "- `git diff --check`",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--run-base", type=Path, default=ROOT / "workspace/private/runs/audio")
    parser.add_argument("--private-manifest")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir or latest_v2618_run(args.run_base)
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    manifest = build_manifest(run_dir)
    private_manifest = Path(args.private_manifest) if args.private_manifest else run_dir / DEFAULT_PRIVATE_NAME
    if not private_manifest.is_absolute():
        private_manifest = ROOT / private_manifest
    write_json(private_manifest, manifest, mode=0o600)
    if args.write_report:
        write_report(args.report, manifest, private_manifest)
    if args.json:
        redacted = dict(manifest)
        redacted["payload_candidates"] = manifest.get("payload_candidates_redacted", [])
        redacted.pop("payload_candidates_redacted", None)
        redacted["private_manifest"] = rel(private_manifest)
        print(json.dumps(redacted, indent=2, sort_keys=True))
    else:
        print(json.dumps({
            "decision": f"v2619-gate2-handoff-{'ready' if manifest.get('ok') else 'needs-review'}",
            "ok": manifest.get("ok"),
            "private_manifest": rel(private_manifest),
            "payload_candidate_count": manifest.get("summary", {}).get("payload_candidate_count"),
            "vol_candidate_count": manifest.get("summary", {}).get("vol_candidate_count"),
            "native_replay_ready": manifest.get("native_replay_ready"),
        }, indent=2, sort_keys=True))
    return 0 if manifest.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
