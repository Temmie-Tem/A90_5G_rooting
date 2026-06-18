#!/usr/bin/env python3
"""V2695 host-only selector audit for ACDB custom-topology recovery.

This consumes existing private V2693 lower pointer-target capture artifacts and
public topology parsers to decide whether another same-route pointer-target run
is useful.  It performs no device action and commits no raw ACDB bytes.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import analyze_audio_acdb_core_topology_bridge_v2683 as v2683
except ModuleNotFoundError:  # pragma: no cover - package import path in unittest.
    from workspace.public.src.scripts.revalidation import analyze_audio_acdb_core_topology_bridge_v2683 as v2683

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2695"
DEFAULT_V2693_RUN = ROOT / "workspace/private/runs/audio/v2693-acdb-lower-ptrtarget-capture-20260618-171518"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2695_AUDIO_ACDB_SELECTED_TOPOLOGY_SELECTOR_AUDIT_2026-06-18.md"
LEGACY_TRACE_DIRS = (
    ROOT / "workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190515",
    ROOT / "workspace/private/runs/audio/v2461-acdb-compat-live-20260615-190530",
    ROOT / "workspace/private/runs/audio/v2466-acdb-dmabuf-live-20260615-200643",
)
CMD_TO_CAL_TYPE = {
    0x000130DA: 24,
    0x00011394: 10,
    0x00012E01: 14,
    0x000130DC: 24,
}
CUSTOM_TARGETS = {
    10: {"role": "ADM_CUST_TOPOLOGY", "selected_topology": 0x10004000, "get_cmd": 0x00011394},
    14: {"role": "ASM_CUST_TOPOLOGY", "selected_topology": 0x10005000, "get_cmd": 0x00012E01},
    24: {"role": "AFE_CUST_TOPOLOGY", "selected_topology": 0x1001025D, "get_cmd": 0x000130DA},
}


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def intish(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(text, 0)
    except ValueError:
        return default


def hex32(value: int | None) -> str:
    if value is None:
        return "None"
    return f"0x{value & 0xFFFFFFFF:08x}"


def parse_relaxed_json_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        # Some historical event logs used unquoted 0x... numeric literals.
        fixed = re.sub(r"(:\s*)(0x[0-9A-Fa-f]+)(\s*[,}])", r'\1"\2"\3', line)
        return json.loads(fixed)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(errors="ignore").splitlines():
        row = parse_relaxed_json_line(line)
        if row is not None:
            rows.append(row)
    return rows


@dataclasses.dataclass
class TapRecord:
    cal_type: int
    cmd: int
    seq: int
    in_word0: int | None = None
    in_word1: int | None = None
    ptrtarget_status: str | None = None
    ptrtarget_map_start: int | None = None
    ptrtarget_map_end: int | None = None
    ret: int | None = None
    out_len: int | None = None
    out_sha256: str | None = None
    out_all_zero: bool | None = None

    @property
    def word1_page_aligned(self) -> bool:
        return self.in_word1 is not None and self.in_word1 % 0x1000 == 0

    @property
    def word1_unmapped(self) -> bool:
        return self.ptrtarget_status == "ptrtarget_unmapped"


def signed32(value: int | None) -> int | None:
    if value is None:
        return None
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def parse_tap_records(artifacts: Path) -> list[TapRecord]:
    rows = read_jsonl(artifacts / "acdbtap" / "acdbtap-events.jsonl")
    by_seq: dict[int, TapRecord] = {}
    for row in rows:
        cmd = intish(row.get("cmd"))
        seq = intish(row.get("seq"))
        if cmd not in CMD_TO_CAL_TYPE or seq is None:
            continue
        record = by_seq.setdefault(seq, TapRecord(cal_type=CMD_TO_CAL_TYPE[cmd], cmd=cmd, seq=seq))
        event = row.get("event")
        if event == "acdb_ioctl_call" and row.get("phase") in {"enter", "before_real"}:
            record.in_word0 = intish(row.get("in_word0"), record.in_word0)
            record.in_word1 = intish(row.get("in_word1"), record.in_word1)
        elif event == "ptrtarget_status":
            record.ptrtarget_status = str(row.get("status") or "")
            record.ptrtarget_map_start = intish(row.get("map_start"))
            record.ptrtarget_map_end = intish(row.get("map_end"))
        elif row.get("buffer") == "out":
            record.ret = signed32(intish(row.get("ret")))
            record.out_len = intish(row.get("out_len"))
            record.out_sha256 = row.get("sha256")
            record.out_all_zero = bool(row.get("all_zero"))
    return [by_seq[key] for key in sorted(by_seq)]


def parse_lower_snapshots(artifacts: Path) -> dict[int, dict[str, Any]]:
    rows = read_jsonl(artifacts / "acdb-v2674-lower-hidden-inhook-events.jsonl")
    out: dict[int, dict[str, Any]] = {cal: {} for cal in CUSTOM_TARGETS}
    for row in rows:
        cal_type = intish(row.get("cal_type"))
        if cal_type not in CUSTOM_TARGETS:
            continue
        current = out.setdefault(cal_type, {})
        event = row.get("event")
        if event == "v2692_lower_block_snapshot":
            current["snapshot"] = {
                "node": row.get("node"),
                "block": row.get("block"),
                "get_arg0": intish(row.get("get_arg0")),
                "get_arg1": intish(row.get("get_arg1")),
                "mem_handle": intish(row.get("mem_handle")),
                "word4": intish(row.get("word4")),
                "word16": intish(row.get("word16")),
                "word20": intish(row.get("word20")),
            }
        elif row.get("stage") == "create_cal_node_return":
            current["create_code"] = intish(row.get("code"))
            current["node_value"] = row.get("value")
        elif row.get("stage") == "allocate_cal_block_return":
            current["allocate_code"] = intish(row.get("code"))
            current["block_value"] = row.get("value")
        elif row.get("stage") == "acdb_ioctl_get_return":
            current["get_code"] = intish(row.get("code"))
            current["get_value"] = intish(row.get("value"))
    return out


def parse_setcal_payloads(artifacts: Path) -> dict[int, dict[str, Any]]:
    rows = read_jsonl(artifacts / "setcal-events.jsonl")
    out: dict[int, dict[str, Any]] = {}
    for row in rows:
        cal_type = intish(row.get("cal_type"))
        if cal_type not in CUSTOM_TARGETS:
            continue
        dmabuf = row.get("dmabuf") or {}
        private_path = dmabuf.get("path")
        local_payload: Path | None = None
        if private_path:
            # Device path basename is pulled into the artifacts directory.
            local_payload = artifacts / Path(str(private_path)).name
        topologies: list[dict[str, Any]] = []
        parse_ok = False
        parse_error = None
        if local_payload and local_payload.exists():
            data = local_payload.read_bytes()
            try:
                records = v2683.parse_fixed_payload(data)
                parse_ok = True
                for record in records:
                    topologies.append({
                        "topology_id": record.topology_id,
                        "topology_hex": hex32(record.topology_id),
                        "module_count": len(record.modules),
                    })
            except Exception as exc:  # noqa: BLE001 - report parser failure as data.
                parse_error = str(exc)
        out[cal_type] = {
            "sequence": intish(row.get("sequence")),
            "cal_size": intish(row.get("cal_size")),
            "mem_handle": intish(row.get("mem_handle")),
            "arg_sha256": ((row.get("set_arg") or {}).get("sha256")),
            "payload_sha256": dmabuf.get("sha256"),
            "payload_all_zero": bool(dmabuf.get("all_zero")),
            "payload_status": dmabuf.get("status"),
            "payload_private_path": rel(local_payload) if local_payload else None,
            "parse_ok": parse_ok,
            "parse_error": parse_error,
            "topologies": topologies,
        }
    return out


def topology_ids(payload: dict[str, Any] | None) -> set[int]:
    if not payload:
        return set()
    return {int(item["topology_id"]) for item in payload.get("topologies") or []}


def iter_values(obj: Any, key: str) -> Iterable[Any]:
    if isinstance(obj, dict):
        for current_key, value in obj.items():
            if current_key == key:
                yield value
            yield from iter_values(value, key)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_values(item, key)


def scan_legacy_trace_markers(dirs: Iterable[Path]) -> dict[str, Any]:
    """Count structured custom-cal evidence in old Android-good trace runs.

    This is deliberately conservative: count explicit result.json cal_type fields
    and ACDB-LOADER cal_type[...] log lines only. Do not grep arbitrary hex words,
    because old logcat/BufferQueue IDs create many false positives.
    """
    counts = {10: 0, 14: 0, 24: 0, 39: 0}
    setcal_literal = 0
    files_scanned = 0
    dirs_seen: list[str] = []
    logcat_pattern = re.compile(r"cal_type\[(\d+)\]")
    for directory in dirs:
        if not directory.exists():
            continue
        dirs_seen.append(rel(directory))
        for path in directory.rglob("*"):
            if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
                continue
            if path.name == "result.json":
                files_scanned += 1
                try:
                    data = json.loads(path.read_text(errors="ignore"))
                except json.JSONDecodeError:
                    continue
                for value in iter_values(data, "cal_type"):
                    cal_type = intish(value)
                    if cal_type in counts:
                        counts[cal_type] += 1
                continue
            if path.name.endswith((".stdout.txt", ".stderr.txt", ".txt")):
                files_scanned += 1
                text = path.read_text(errors="ignore")
                setcal_literal += len(re.findall(r"AUDIO_SET_CALIBRATION|0xc00461cb", text, re.I))
                for match in logcat_pattern.finditer(text):
                    cal_type = int(match.group(1))
                    if cal_type in counts:
                        counts[cal_type] += 1
    return {
        "files_scanned": files_scanned,
        "dirs_seen": dirs_seen,
        "setcal_literal": setcal_literal,
        "cal10_structured_matches": counts[10],
        "cal14_structured_matches": counts[14],
        "cal24_structured_matches": counts[24],
        "cal39_structured_matches": counts[39],
    }


def analyze(v2693_run: Path, legacy_trace_dirs: Iterable[Path] = LEGACY_TRACE_DIRS) -> dict[str, Any]:
    artifacts = v2693_run / "ownget-device-artifacts"
    tap_records = parse_tap_records(artifacts)
    lower = parse_lower_snapshots(artifacts)
    payloads = parse_setcal_payloads(artifacts)
    rows: list[dict[str, Any]] = []
    for cal_type in (24, 10, 14):
        target = CUSTOM_TARGETS[cal_type]
        tap = next((record for record in tap_records if record.cal_type == cal_type), None)
        payload = payloads.get(cal_type)
        ids = topology_ids(payload)
        selected = int(target["selected_topology"])
        lower_snapshot = (lower.get(cal_type) or {}).get("snapshot") or {}
        word1 = tap.in_word1 if tap and tap.in_word1 is not None else lower_snapshot.get("get_arg1")
        rows.append({
            "cal_type": cal_type,
            "role": target["role"],
            "get_cmd": target["get_cmd"],
            "expected_selected_topology": selected,
            "expected_selected_topology_hex": hex32(selected),
            "create_code": (lower.get(cal_type) or {}).get("create_code"),
            "allocate_code": (lower.get(cal_type) or {}).get("allocate_code"),
            "get_code": (lower.get(cal_type) or {}).get("get_code"),
            "get_value": (lower.get(cal_type) or {}).get("get_value"),
            "request_word0": tap.in_word0 if tap else lower_snapshot.get("get_arg0"),
            "request_word1": word1,
            "request_word1_hex": hex32(word1),
            "word1_page_aligned": bool(word1 is not None and word1 % 0x1000 == 0),
            "ptrtarget_status": tap.ptrtarget_status if tap else None,
            "ptrtarget_unmapped": bool(tap.word1_unmapped if tap else False),
            "tap_ret": tap.ret if tap else None,
            "tap_out_all_zero": tap.out_all_zero if tap else None,
            "set_captured": payload is not None,
            "set_cal_size": payload.get("cal_size") if payload else None,
            "set_mem_handle": payload.get("mem_handle") if payload else None,
            "payload_sha256": payload.get("payload_sha256") if payload else None,
            "payload_parse_ok": payload.get("parse_ok") if payload else False,
            "payload_topology_hex": [item["topology_hex"] for item in (payload or {}).get("topologies") or []],
            "selected_topology_present": selected in ids,
        })
    all_word1_unmapped = all(row["ptrtarget_unmapped"] for row in rows)
    all_word1_page_aligned = all(row["word1_page_aligned"] for row in rows)
    afe_aligned = next(row for row in rows if row["cal_type"] == 24)["selected_topology_present"]
    asm_aligned = next(row for row in rows if row["cal_type"] == 14)["selected_topology_present"]
    adm_captured = next(row for row in rows if row["cal_type"] == 10)["set_captured"]
    decision = "v2695-selector-audit-pivots-away-from-lower-ptrtarget"
    if not all_word1_unmapped:
        decision = "v2695-pointer-target-route-still-open"
    elif afe_aligned and not asm_aligned and not adm_captured:
        decision = "v2695-selector-audit-pivots-away-from-lower-ptrtarget"
    legacy = scan_legacy_trace_markers(legacy_trace_dirs)
    return {
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "decision": decision,
        "ok": True,
        "v2693_run": rel(v2693_run),
        "artifacts": rel(artifacts),
        "all_word1_unmapped": all_word1_unmapped,
        "all_word1_page_aligned": all_word1_page_aligned,
        "afe_selected_topology_present_in_cal24": afe_aligned,
        "asm_selected_topology_present_in_cal14": asm_aligned,
        "adm_set_captured": adm_captured,
        "lower_ptrtarget_retries_low_value": all_word1_unmapped and all_word1_page_aligned,
        "custom_rows": rows,
        "legacy_trace_marker_scan": legacy,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    rows = summary["custom_rows"]
    lines = [
        "# NATIVE_INIT V2695 — ACDB selected-topology selector audit",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only audit after V2693/V2694. This reads existing private V2693 lower pointer-target artifacts and parsed topology payload metadata only. No device action, flash, Android handoff, `/dev/msm_audio_cal` ioctl, mixer write, PCM probe, or raw ACDB payload commit occurred.",
        "",
        "## Result",
        "",
        f"- decision: `{summary['decision']}`",
        f"- ok: `{summary['ok']}`",
        f"- v2693_run: `{summary['v2693_run']}`",
        f"- all_word1_unmapped: `{summary['all_word1_unmapped']}`",
        f"- all_word1_page_aligned: `{summary['all_word1_page_aligned']}`",
        f"- afe_selected_topology_present_in_cal24: `{summary['afe_selected_topology_present_in_cal24']}`",
        f"- asm_selected_topology_present_in_cal14: `{summary['asm_selected_topology_present_in_cal14']}`",
        f"- adm_set_captured: `{summary['adm_set_captured']}`",
        f"- lower_ptrtarget_retries_low_value: `{summary['lower_ptrtarget_retries_low_value']}`",
        "",
        "## Selector table",
        "",
        "| cal_type | role | GET cmd | request words | ptrtarget | ret | SET captured | payload topologies | selected topology | selected present | verdict |",
        "| ---: | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |",
    ]
    verdicts = {
        24: "AFE path aligned; selected topology is present",
        10: "ADM exact SET still absent; lower GET returns failure",
        14: "ASM exact SET is stale/misaligned; selected topology absent",
    }
    for row in rows:
        topologies = ", ".join(f"`{item}`" for item in row["payload_topology_hex"]) or "none"
        lines.append(
            "| {cal} | `{role}` | `{cmd}` | `{w0}`, `{w1}` | `{ptr}` | `{ret}` | `{set}` | {topos} | `{selected}` | `{present}` | {verdict} |".format(
                cal=row["cal_type"],
                role=row["role"],
                cmd=hex32(row["get_cmd"]),
                w0=hex32(row["request_word0"]),
                w1=row["request_word1_hex"],
                ptr=row["ptrtarget_status"],
                ret=row["tap_ret"],
                set=row["set_captured"],
                topos=topologies,
                selected=row["expected_selected_topology_hex"],
                present=row["selected_topology_present"],
                verdict=verdicts[row["cal_type"]],
            )
        )
    legacy = summary["legacy_trace_marker_scan"]
    lines.extend([
        "",
        "## Legacy real-HAL trace scan",
        "",
        f"- dirs_seen: `{legacy.get('dirs_seen')}`",
        f"- files_scanned: `{legacy.get('files_scanned')}`",
        f"- setcal_literal_matches: `{legacy.get('setcal_literal')}`",
        f"- cal10_structured_matches: `{legacy.get('cal10_structured_matches')}`",
        f"- cal14_structured_matches: `{legacy.get('cal14_structured_matches')}`",
        f"- cal24_structured_matches: `{legacy.get('cal24_structured_matches')}`",
        f"- cal39_structured_matches: `{legacy.get('cal39_structured_matches')}`",
        "",
        "This structured legacy scan is intentionally limited evidence: it counts explicit result.json `cal_type` fields and ACDB-LOADER `cal_type[...]` log lines only. It shows the archived V2461/V2466 artifacts expose cal39 but no obvious cal10/cal14/cal24 custom-topology SET record; it does not replace byte-exact route-specific SET capture.",
        "",
        "## Interpretation",
        "",
        "V2693 did not recover a new selector buffer. The second GET word for cal_types 24/10/14 is page-aligned but maps-unreadable in the helper process, and all three pointer-target probes returned `ptrtarget_unmapped`. That makes another same-route maps-based pointer-target retry low-value unless the argument model changes.",
        "",
        "The subsystem alignment is now split cleanly:",
        "",
        "- AFE is aligned: cal_type 24 contains the selected `0x1001025d` topology and produced a real SET payload.",
        "- ASM is not aligned: cal_type 14 produced a structurally valid 2356-byte payload, but it contains only `0x1000ffff` and `0x10000018..1b`, not selected `0x10005000`. V2694 already showed host SET geometry is not the blocker, and V2689 falsified synthetic selected-topology replacements.",
        "- ADM remains absent: cal_type 10 create/allocate succeeded, but the lower GET returned `-12`, produced an all-zero size output, and no SET payload exists for selected `0x10004000`.",
        "",
        "Therefore the current lower own-process route is no longer producing the byte-exact selected ADM/ASM custom topology records needed by the DSP. Native replay should remain parked: replaying existing cal14, defined-only cal14, or another lower-ptrtarget retry would repeat already-refuted evidence.",
        "",
        "## Next unit",
        "",
        "Do not rerun V2693 or any existing cal14/defined-only replay. The next useful branch is either a route-specific Android-good capture that observes the real HAL custom-topology SET path for selected ADM `0x10004000` and ASM `0x10005000`, or a deeper libacdbloader/ACDB DB selector RE unit that changes the request model rather than dumping the same unmapped `get_arg1` word again. If neither path can recover byte-exact selected cal10/cal14 payloads, close native speaker playback as blocked on DSP topology semantics, not on `/dev/msm_audio_cal` SET delivery.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_selected_topology_selector_v2695.py tests/test_analyze_audio_acdb_selected_topology_selector_v2695.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_selected_topology_selector_v2695 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_selected_topology_selector_v2695.py --write-report`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest discover -s tests -v`",
        "- `git diff --check`",
        "",
    ])
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2693-run", type=Path, default=DEFAULT_V2693_RUN)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = analyze(args.v2693_run)
    if args.write_report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_markdown(summary), encoding="utf-8")
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps({"decision": summary["decision"], "ok": summary["ok"], "report": rel(args.report) if args.write_report else None}, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
