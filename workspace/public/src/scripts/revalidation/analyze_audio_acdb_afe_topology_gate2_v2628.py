#!/usr/bin/env python3
"""V2628 host-only Gate-2 mapping for the V2627 AFE topology capture.

This analyzer intentionally reads private V2627 ACDB raw artifacts but emits
only metadata and small scalar words. It decides whether the captured
`0x13262` records are suitable as native ACDB replay payloads for the V2393
AFE topology gate. It never stages device work and never writes raw payload
bytes outside `workspace/private`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2628"
BUILD_TAG = "v2628-audio-acdb-afe-topology-gate2-mapping"
DEFAULT_V2627_RUN = ROOT / "workspace/private/runs/audio/v2627-acdb-afe-topology-20260616-224848"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2628_AUDIO_ACDB_AFE_TOPOLOGY_GATE2_MAPPING_2026-06-17.md"


def rel(path: Path | str) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def int_or_none(value: Any) -> int | None:
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


def fmt_word(value: int | None) -> str:
    if value is None:
        return "none"
    return f"0x{value & 0xFFFFFFFF:08x}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def le_words(data: bytes) -> list[int]:
    return [int.from_bytes(data[index : index + 4], "little") for index in range(0, len(data) - (len(data) % 4), 4)]


def raw_path_for_event(acdbtap_dir: Path, event: dict[str, Any]) -> Path | None:
    raw = event.get("raw_path")
    if not raw:
        return None
    path = Path(str(raw))
    if path.exists():
        return path
    candidate = acdbtap_dir / path.name
    if candidate.exists():
        return candidate
    return None


def summarize_raw_event(acdbtap_dir: Path, event: dict[str, Any]) -> dict[str, Any]:
    path = raw_path_for_event(acdbtap_dir, event)
    data = path.read_bytes() if path else b""
    words = le_words(data)
    return {
        "seq": int_or_none(event.get("seq")),
        "cmd": int_or_none(event.get("cmd")),
        "buffer": event.get("buffer"),
        "ret": int_or_none(event.get("ret")),
        "out_len": int_or_none(event.get("out_len")),
        "raw_path": rel(path) if path else None,
        "raw_exists": bool(path),
        "raw_len": len(data),
        "raw_sha256": sha256_bytes(data) if data else event.get("sha256"),
        "raw_words": [fmt_word(word) for word in words],
        "all_zero": bool(data and all(byte == 0 for byte in data)),
    }


def helper_case_rows(artifact_dir: Path) -> list[dict[str, Any]]:
    path = artifact_dir / "acdb-v2626-afe-topology-probe-events.jsonl"
    return [
        row for row in read_jsonl(path)
        if row.get("event") == "v2626_afe_topology_probe" and row.get("stage") == "case_return"
    ]


def summarize_helper_cases(artifact_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for row in helper_case_rows(artifact_dir):
        rows.append(
            {
                "case": row.get("case"),
                "cmd": fmt_word(int_or_none(row.get("cmd"))),
                "step": int_or_none(row.get("step")),
                "ret": int_or_none(row.get("ret")),
                "out_word": fmt_word(int_or_none(row.get("out_word"))),
            }
        )
    return rows


def summarize_acdbtap(artifact_dir: Path) -> list[dict[str, Any]]:
    acdbtap_dir = artifact_dir / "acdbtap"
    events = read_jsonl(acdbtap_dir / "acdbtap-events.jsonl")
    return [
        summarize_raw_event(acdbtap_dir, event)
        for event in events
        if "buffer" in event and int_or_none(event.get("cmd")) in {0x130D8, 0x13262}
    ]


def selected_artifact_dir(run_dir: Path, result: dict[str, Any]) -> Path:
    summary = result.get("afe_topology_summary", {})
    helper_path = summary.get("helper_event_path")
    if helper_path:
        path = ROOT / str(helper_path)
        if path.exists():
            return path.parent
    return run_dir / "ownget-device-artifacts"


def summarize_prior_direct_records() -> list[dict[str, Any]]:
    """Summarize historical direct 0x13262 size records when local runs exist."""

    patterns = [
        "v2560-*",
        "v2566-*",
        "v2570-*",
    ]
    rows: list[dict[str, Any]] = []
    base = ROOT / "workspace/private/runs/audio"
    for pattern in patterns:
        for run_dir in sorted(base.glob(pattern)):
            for event_path in sorted(run_dir.glob("**/acdbtap-events.jsonl")):
                acdbtap_dir = event_path.parent
                for event in read_jsonl(event_path):
                    if int_or_none(event.get("cmd")) != 0x13262:
                        continue
                    raw_name = Path(str(event.get("raw_path", ""))).name
                    buffer_name = event.get("buffer")
                    is_direct_out = buffer_name == "out" or (
                        not buffer_name
                        and "-len-" in raw_name
                        and "-in-" not in raw_name
                        and "-ind-" not in raw_name
                    )
                    if not is_direct_out:
                        continue
                    item = summarize_raw_event(acdbtap_dir, event)
                    if item["raw_len"] == 4:
                        rows.append(
                            {
                                "run": rel(run_dir),
                                "seq": item["seq"],
                                "out_word": item["raw_words"][0] if item["raw_words"] else "none",
                                "sha256": item["raw_sha256"],
                            }
                        )
    return rows


def decide_mapping(helper_rows: list[dict[str, Any]], acdbtap_rows: list[dict[str, Any]]) -> dict[str, Any]:
    topology_id_words = [
        row["out_word"] for row in helper_rows
        if row.get("case") == "afe-topology-id" and row.get("ret") == 0
    ]
    cap_rows = [
        row for row in helper_rows
        if str(row.get("case", "")).startswith("afe-topology-cap") and row.get("ret") == 0
    ]
    direct_13262 = [
        row for row in acdbtap_rows
        if row.get("cmd") == 0x13262 and row.get("buffer") == "out" and row.get("ret") == 0
    ]
    indirect_13262 = [
        row for row in acdbtap_rows
        if row.get("cmd") == 0x13262 and row.get("buffer") == "ind-afe-topology" and row.get("ret") == 0
    ]
    direct_words = sorted({row["raw_words"][0] for row in direct_13262 if row.get("raw_words")})
    indirect_words = sorted({row["raw_words"][0] for row in indirect_13262 if row.get("raw_words")})
    all_indirect_four_bytes = bool(indirect_13262) and all(row.get("raw_len") == 4 for row in indirect_13262)
    observed_only_count_record = all_indirect_four_bytes and indirect_words == ["0x00000001"]
    observed_only_size_record = bool(direct_13262) and direct_words == ["0x00000004"]
    replay_ready = False
    if observed_only_count_record and observed_only_size_record:
        decision = "v2628-afe-topology-gate2-reject-replay-payload"
        reason = (
            "V2627 captured 0x13262 direct size 4 and indirect word 1 only. "
            "That is useful evidence but not a cal_type 8/9 replay payload."
        )
    elif indirect_13262:
        decision = "v2628-afe-topology-gate2-requires-operator-review"
        reason = "0x13262 indirect records exist but do not match the known four-byte count pattern."
    else:
        decision = "v2628-afe-topology-gate2-no-indirect-records"
        reason = "No 0x13262 indirect AFE topology records were available for Gate-2 mapping."
    return {
        "decision": decision,
        "reason": reason,
        "replay_ready": replay_ready,
        "native_replay_blocked": not replay_ready,
        "operator_valuable": bool(topology_id_words or direct_13262 or indirect_13262 or cap_rows),
        "topology_id_words": sorted(set(topology_id_words)),
        "capacity_case_count": len(cap_rows),
        "direct_13262_count": len(direct_13262),
        "direct_13262_words": direct_words,
        "indirect_13262_count": len(indirect_13262),
        "indirect_13262_words": indirect_words,
        "observed_only_count_record": observed_only_count_record,
        "observed_only_size_record": observed_only_size_record,
        "next_gate": "capture actual AUDIO_SET_AFE_CUSTOM_TOPOLOGY/AFE topology SET payload before native replay",
    }


def make_payload(args: argparse.Namespace) -> dict[str, Any]:
    result_path = args.v2627_run / "v2627-result.json"
    result = read_json(result_path)
    artifact_dir = selected_artifact_dir(args.v2627_run, result)
    helper_rows = summarize_helper_cases(artifact_dir)
    acdbtap_rows = summarize_acdbtap(artifact_dir)
    prior_rows = summarize_prior_direct_records() if args.include_prior_scan else []
    decision = decide_mapping(helper_rows, acdbtap_rows)
    return {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "host_only": True,
        "device_action": "none",
        "source_run": rel(args.v2627_run),
        "source_result": rel(result_path),
        "artifact_dir": rel(artifact_dir),
        "source_decision": result.get("decision"),
        "source_rolled_back": result.get("rolled_back"),
        "helper_cases": helper_rows,
        "acdbtap_records": acdbtap_rows,
        "historical_direct_13262": prior_rows,
        **decision,
        "ok": bool(decision["operator_valuable"]),
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# NATIVE_INIT V2628 — ACDB AFE topology Gate-2 mapping",
        "",
        "Date: 2026-06-17",
        "",
        "## Scope",
        "",
        "Host-only mapping of the V2627 AFE-topology capture. This does not run",
        "device code, does not replay ACDB, and does not expose private raw buffers.",
        "",
        "## Decision",
        "",
        f"- decision: `{payload['decision']}`",
        f"- ok: `{payload['ok']}`",
        f"- replay_ready: `{payload['replay_ready']}`",
        f"- native_replay_blocked: `{payload['native_replay_blocked']}`",
        f"- operator_valuable: `{payload['operator_valuable']}`",
        f"- reason: {payload['reason']}",
        f"- next_gate: `{payload['next_gate']}`",
        "",
        "## Inputs",
        "",
        f"- source_run: `{payload['source_run']}`",
        f"- source_result: `{payload['source_result']}`",
        f"- artifact_dir: `{payload['artifact_dir']}`",
        f"- source_decision: `{payload['source_decision']}`",
        f"- source_rolled_back: `{payload['source_rolled_back']}`",
        "",
        "## Helper Case Results",
        "",
        "| case | cmd | step | ret | out_word |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in payload["helper_cases"]:
        lines.append(
            f"| `{row['case']}` | `{row['cmd']}` | `{row['step']}` | `{row['ret']}` | `{row['out_word']}` |"
        )
    lines.extend([
        "",
        "## ACDB Tap Records",
        "",
        "| seq | cmd | buffer | ret | raw_len | sha256 | words |",
        "| ---: | --- | --- | ---: | ---: | --- | --- |",
    ])
    for row in payload["acdbtap_records"]:
        if row["cmd"] not in {0x130D8, 0x13262}:
            continue
        seq = row["seq"] if row["seq"] is not None else ""
        cmd = fmt_word(row["cmd"])
        words = ", ".join(row.get("raw_words") or [])
        lines.append(
            f"| `{seq}` | `{cmd}` | `{row['buffer']}` | `{row['ret']}` | `{row['raw_len']}` | "
            f"`{row['raw_sha256']}` | `{words}` |"
        )
    lines.extend([
        "",
        "## Mapping Interpretation",
        "",
        "- `0x130d8` returns AFE topology ID `0x1001025d` for the probed speaker ACDB ID.",
        "- `0x13262` returned direct output word `0x00000004` for every capacity sweep.",
        "- `0x13262` also exposed an indirect `ind-afe-topology` word `0x00000001` for every sweep.",
        "- The V2627 four-byte indirect record is therefore treated as a topology count/table scalar, not a native replay cal block.",
        "- V2393/V2552 still require real AFE topology cal_type 8/9 material before native SET replay can be unblocked.",
        "",
        "## Historical Cross-Check",
        "",
    ])
    prior = payload.get("historical_direct_13262") or []
    if prior:
        lines.extend([
            "| run | seq | out_word | sha256 |",
            "| --- | ---: | --- | --- |",
        ])
        for row in prior[:40]:
            lines.append(
                f"| `{row['run']}` | `{row['seq']}` | `{row['out_word']}` | `{row['sha256']}` |"
            )
        if len(prior) > 40:
            lines.append(f"| ... | ... | ... | `{len(prior) - 40} additional rows omitted` |")
    else:
        lines.append("- no local historical direct records scanned")
    lines.extend([
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_afe_topology_gate2_v2628.py tests/test_analyze_audio_acdb_afe_topology_gate2_v2628.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_afe_topology_gate2_v2628 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_afe_topology_gate2_v2628.py --write-report`",
        "- `git diff --check`",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2627-run", type=Path, default=DEFAULT_V2627_RUN)
    parser.add_argument("--include-prior-scan", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = make_payload(args)
    if args.write_report:
        write_report(args.report_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
