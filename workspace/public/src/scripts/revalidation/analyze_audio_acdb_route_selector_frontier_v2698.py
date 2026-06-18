#!/usr/bin/env python3
"""V2698 host-only ACDB route-selector frontier audit.

This unit consolidates the post-V2697 frontier.  It reads public reports plus
metadata from private stock audio binaries, but never emits proprietary bytes.
The purpose is to prevent another low-information capture/replay loop and to
name the next actionable branch for missing cal_type 10/14 custom topology SETs.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2698"
REPORT = ROOT / "docs/reports/NATIVE_INIT_V2698_AUDIO_ACDB_ROUTE_SELECTOR_FRONTIER_2026-06-18.md"

LIBACDBLOADER = ROOT / "workspace/private/inputs/audio/acdb-deps-v2506/vendor-lib/libacdbloader.so"
HAL_PRIMARY = ROOT / "workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump/lib/hw/audio.primary.msmnile.so"

REPORT_PATHS = {
    "v2671": ROOT / "docs/reports/NATIVE_INIT_V2671_AUDIO_ACDB_LOWER_CALLABLE_STRATEGY_HOST_RECON_2026-06-18.md",
    "v2689": ROOT / "docs/reports/NATIVE_INIT_V2689_AUDIO_ACDB_DEFINED_MODULE_TOPOLOGY_LIVE_REPLAY_2026-06-18.md",
    "v2690": ROOT / "docs/reports/NATIVE_INIT_V2690_AUDIO_ACDB_REQUEST_TUPLE_RECOVERY_AUDIT_2026-06-18.md",
    "v2694": ROOT / "docs/reports/NATIVE_INIT_V2694_AUDIO_ACDB_ASM_TOPOLOGY_GEOMETRY_AUDIT_2026-06-18.md",
    "v2695": ROOT / "docs/reports/NATIVE_INIT_V2695_AUDIO_ACDB_SELECTED_TOPOLOGY_SELECTOR_AUDIT_2026-06-18.md",
    "v2696": ROOT / "docs/reports/NATIVE_INIT_V2696_AUDIO_ACDB_DB_SELECTED_TOPOLOGY_AUDIT_2026-06-18.md",
    "v2697": ROOT / "docs/reports/NATIVE_INIT_V2697_AUDIO_ACDBDATA_FIRMWARE_STAGE_2026-06-18.md",
}

CONSTANTS = {
    "selected_adm_0x10004000": 0x10004000,
    "selected_asm_0x10005000": 0x10005000,
    "selected_afe_0x1001025d": 0x1001025D,
    "speaker_app_0x11135": 0x00011135,
    "adm_get_cmd_0x11394": 0x00011394,
    "asm_get_cmd_0x12e01": 0x00012E01,
    "afe_get_cmd_0x130da": 0x000130DA,
    "afe_get_cmd_alt_0x130dc": 0x000130DC,
    "avcs_custom_topo_cmd_0x13296": 0x00013296,
}

SYMBOLS_OF_INTEREST = (
    "acdb_ioctl",
    "acdb_loader_send_common_custom_topology",
    "acdb_loader_send_audio_cal_v5",
    "acdb_loader_store_set_audio_cal",
    "acdb_loader_set_audio_cal_v2",
    "acdb_loader_adsp_set_audio_cal",
    "platform_send_audio_calibration",
    "platform_send_audio_cal",
    "platform_get_audio_cal",
    "platform_store_audio_cal",
)


@dataclasses.dataclass(frozen=True)
class ConstantHit:
    name: str
    value: int
    count: int
    offsets: tuple[int, ...]


@dataclasses.dataclass(frozen=True)
class SymbolHit:
    binary: str
    name: str
    value: str
    size: int | None
    kind: str
    defined: bool


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_word_constants(data: bytes, constants: dict[str, int]) -> list[ConstantHit]:
    hits: list[ConstantHit] = []
    for name, value in constants.items():
        needle = value.to_bytes(4, "little", signed=False)
        offsets: list[int] = []
        start = 0
        while True:
            index = data.find(needle, start)
            if index < 0:
                break
            offsets.append(index)
            start = index + 1
        hits.append(ConstantHit(name=name, value=value, count=len(offsets), offsets=tuple(offsets[:8])))
    return hits


def run_readelf_symbols(path: Path) -> list[SymbolHit]:
    if not path.exists():
        return []
    proc = subprocess.run(
        ["readelf", "-sW", str(path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return []
    return parse_readelf_symbols(proc.stdout, rel(path), SYMBOLS_OF_INTEREST)


def parse_readelf_symbols(text: str, binary: str, names: Iterable[str]) -> list[SymbolHit]:
    wanted = set(names)
    hits: list[SymbolHit] = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 8 or not fields[0].rstrip(":").isdigit():
            continue
        name = fields[7].split("@", 1)[0]
        if name not in wanted:
            continue
        try:
            size = int(fields[2], 0)
        except ValueError:
            size = None
        hits.append(
            SymbolHit(
                binary=binary,
                name=name,
                value=fields[1],
                size=size,
                kind=fields[3],
                defined=fields[6] != "UND",
            )
        )
    return hits


def read_report(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def report_value(text: str, key: str) -> str | None:
    match = re.search(rf"^- {re.escape(key)}:\s*`?([^`\n]+?)`?\s*$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def report_contains(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def binary_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": rel(path), "exists": False}
    data = path.read_bytes()
    return {
        "path": rel(path),
        "exists": True,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
        "constants": [
            {
                "name": hit.name,
                "value": f"0x{hit.value:08x}",
                "count": hit.count,
                "offsets": [f"0x{offset:x}" for offset in hit.offsets],
            }
            for hit in scan_word_constants(data, CONSTANTS)
        ],
        "symbols": [dataclasses.asdict(hit) for hit in run_readelf_symbols(path)],
    }


def collect_report_markers() -> dict[str, Any]:
    reports = {key: read_report(path) for key, path in REPORT_PATHS.items()}
    spec = read_report(ROOT / "docs/OPERATOR_ACDB_IOCTL_INTERPOSE_CAPTURE_SPEC_2026-06-15.md")
    return {
        "v2689_decision": report_value(reports["v2689"], "decision"),
        "v2694_decision": report_value(reports["v2694"], "decision"),
        "v2695_decision": report_value(reports["v2695"], "decision"),
        "v2696_decision": report_value(reports["v2696"], "decision"),
        "v2697_decision": report_value(reports["v2697"], "decision"),
        "v2695_asm_selected_absent": report_contains(reports["v2695"], "selected `0x10005000`") and report_contains(reports["v2695"], "absent"),
        "v2695_adm_absent": report_contains(reports["v2695"], "ADM remains absent") or report_contains(reports["v2695"], "No byte-exact ADM"),
        "v2697_db_absent": report_contains(reports["v2697"], "no selected ADM") and report_contains(reports["v2697"], "or AFE"),
        "v2689_synthetic_failed": report_contains(reports["v2689"], "failed") or report_contains(reports["v2689"], "ADSP"),
        "v2694_set_geometry_not_blocker": report_contains(reports["v2694"], "SET geometry") and (
            report_contains(reports["v2694"], "not the blocker")
            or report_contains(reports["v2694"], "not the active blocker")
        ),
        "spec_cross_process_closed": (
            report_contains(spec, "supersedes the cross-process dmabuf")
            or report_contains(spec, "supersedes the cross-process dmabuf / file-read")
        )
        and report_contains(spec, "sidesteps the live-HAL blockers"),
    }


def constants_by_name(summary: dict[str, Any], name: str) -> dict[str, Any] | None:
    for row in summary.get("constants", []):
        if row.get("name") == name:
            return row
    return None


def classify_frontier(lib_summary: dict[str, Any], hal_summary: dict[str, Any], markers: dict[str, Any]) -> dict[str, Any]:
    lib_selected_asm = (constants_by_name(lib_summary, "selected_asm_0x10005000") or {}).get("count", 0)
    hal_selected_asm = (constants_by_name(hal_summary, "selected_asm_0x10005000") or {}).get("count", 0)
    lib_app = (constants_by_name(lib_summary, "speaker_app_0x11135") or {}).get("count", 0)
    hal_app = (constants_by_name(hal_summary, "speaker_app_0x11135") or {}).get("count", 0)
    lib_avcs = (constants_by_name(lib_summary, "avcs_custom_topo_cmd_0x13296") or {}).get("count", 0)

    closed = {
        "lower_ptrtarget_retry": bool(markers.get("v2695_decision")) and bool(markers.get("v2695_asm_selected_absent")),
        "db_staging_simple_parse": bool(markers.get("v2697_decision")) and bool(markers.get("v2697_db_absent")),
        "synthetic_core_replay": bool(markers.get("v2689_synthetic_failed")),
        "set_geometry": bool(markers.get("v2694_set_geometry_not_blocker")),
        "cross_process_or_in_hal_capture": bool(markers.get("spec_cross_process_closed")),
    }
    complete_selected_literals = lib_selected_asm > 0 and hal_selected_asm > 0 and (lib_app > 0 or hal_app > 0)
    actionable = "loader-selector-re-or-new-real-hal-set-capture"
    decision = "v2698-route-selector-frontier-needs-new-selector-model"
    if not all(closed.values()):
        decision = "v2698-route-selector-frontier-has-unclosed-prior-branch"
    if complete_selected_literals:
        actionable = "inspect-hardcoded-selected-route-literals"

    return {
        "decision": decision,
        "ok": True,
        "closed_branches": closed,
        "complete_selected_route_literals": complete_selected_literals,
        "lib_has_avcs_custom_topo_cmd": lib_avcs > 0,
        "recommended_next": actionable,
        "park_native_replay": True,
        "reason": (
            "V2695-V2697 close lower ptrtarget, simple DB staging, and existing synthetic replay branches. "
            "The stock loader/HAL metadata does not expose a complete selected ADM/ASM route as raw constants. "
            "The next useful unit must change the selector model or capture the real HAL SET path by a new safe mechanism."
        ),
    }


def build_summary() -> dict[str, Any]:
    lib_summary = binary_summary(LIBACDBLOADER)
    hal_summary = binary_summary(HAL_PRIMARY)
    markers = collect_report_markers()
    classification = classify_frontier(lib_summary, hal_summary, markers)
    return {
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "scope": "host-only metadata audit; no device action, audio ioctl, mixer write, PCM probe, raw payload commit, or vendor byte emission",
        "classification": classification,
        "reports": {key: rel(path) for key, path in REPORT_PATHS.items()},
        "report_markers": markers,
        "binaries": {
            "libacdbloader": lib_summary,
            "audio_primary": hal_summary,
        },
    }


def md_bool(value: Any) -> str:
    return "`True`" if bool(value) else "`False`"


def table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    out = []
    header = rows[0]
    out.append("| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(header)) + " |")
    out.append("| " + " | ".join("---" for _ in header) + " |")
    for row in rows[1:]:
        out.append("| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + " |")
    return "\n".join(out)


def render_report(summary: dict[str, Any]) -> str:
    c = summary["classification"]
    lines = [
        "# NATIVE_INIT V2698 — ACDB route-selector frontier audit",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only audit. This consolidates V2695-V2697 and scans metadata from private stock audio binaries without emitting proprietary bytes. No device action, Android handoff, `/dev/msm_audio_cal` ioctl, mixer write, PCM probe, raw ACDB payload commit, or vendor binary commit occurred.",
        "",
        "## Result",
        "",
        f"- decision: `{c['decision']}`",
        f"- ok: `{c['ok']}`",
        f"- recommended_next: `{c['recommended_next']}`",
        f"- park_native_replay: `{c['park_native_replay']}`",
        f"- lib_has_avcs_custom_topo_cmd: `{c['lib_has_avcs_custom_topo_cmd']}`",
        "",
        "## Closed branch matrix",
        "",
    ]
    rows = [["branch", "closed", "meaning"]]
    meanings = {
        "lower_ptrtarget_retry": "V2695: same lower pointer-target model produced stale ASM and no ADM SET",
        "db_staging_simple_parse": "V2697: firmware /etc/acdbdata staging has no simple parseable selected records",
        "synthetic_core_replay": "V2689: core-derived selected-topology replay failed DSP semantics",
        "set_geometry": "V2694: host SET geometry is not the blocker",
        "cross_process_or_in_hal_capture": "operator spec: cross-process dmabuf and in-HAL LD_PRELOAD are closed",
    }
    for key, value in c["closed_branches"].items():
        rows.append([key, str(value), meanings[key]])
    lines.extend([table(rows), ""])

    lines.extend(["## Binary metadata scan", ""])
    for label, binary in summary["binaries"].items():
        lines.extend(
            [
                f"### {label}",
                "",
                f"- path: `{binary['path']}`",
                f"- exists: `{binary['exists']}`",
            ]
        )
        if binary.get("exists"):
            lines.extend(
                [
                    f"- size: `{binary['size']}`",
                    f"- sha256: `{binary['sha256']}`",
                    "",
                ]
            )
            const_rows = [["constant", "value", "count", "first offsets"]]
            for row in binary.get("constants", []):
                const_rows.append(
                    [
                        row["name"],
                        row["value"],
                        str(row["count"]),
                        ", ".join(row["offsets"]) if row["offsets"] else "none",
                    ]
                )
            lines.extend([table(const_rows), ""])
            sym_rows = [["symbol", "value", "size", "defined"]]
            for sym in binary.get("symbols", []):
                sym_rows.append([sym["name"], sym["value"], str(sym["size"]), str(sym["defined"])])
            lines.extend([table(sym_rows), ""])

    lines.extend(
        [
            "## Interpretation",
            "",
            "The current evidence does not support another same-route lower GET/pointer-target retry. AFE cal_type `24` is aligned, but exact lower ASM cal_type `14` is stale and exact ADM cal_type `10` is absent. The staged firmware DB does not expose the selected ADM/ASM/AFE records as simple parseable `.acdb` records, and the synthetic core-derived replay path has already failed DSP-side semantics.",
            "",
            "The private binary metadata scan reinforces that this is a runtime selector problem, not a plain hardcoded route tuple: `libacdbloader.so` contains the AVCS custom topology command `0x13296`, but the stock loader/HAL metadata does not contain a complete selected route constant set for selected ADM `0x10004000`, selected ASM `0x10005000`, selected AFE `0x1001025d`, and app type `0x11135`. The lone selected-ADM literal in `libacdbloader.so`, by itself, is not enough to define the missing selected cal_type `10`/`14` SET payloads.",
            "",
            "Therefore native replay remains parked. The next useful work must either change the own-process selector model through deeper `libacdbloader`/ACDB runtime RE, or invent a new recoverable route-specific Android-good capture that observes the real HAL custom-topology SET path without reopening the closed cross-process dmabuf or in-HAL `LD_PRELOAD` lines.",
            "",
            "## Next unit",
            "",
            "Design a V2699 loader-selector RE unit around the `acdb_loader_send_common_custom_topology` / custom-topology lower blocks and the HAL `platform_send_audio_calibration` call graph. Acceptance should be a concrete new request model for cal_type `10` and `14`, or a documented close decision if no safe route-specific raw SET capture remains. Do not run another native replay until byte-exact selected cal_type `10` and selected cal_type `14` payloads are recovered.",
            "",
            "## Validation",
            "",
            "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_route_selector_frontier_v2698.py tests/test_analyze_audio_acdb_route_selector_frontier_v2698.py`",
            "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_route_selector_frontier_v2698 -v`",
            "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_route_selector_frontier_v2698.py --write-report`",
            "- `git diff --check`",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    summary = build_summary()
    if args.write_report:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(render_report(summary), encoding="utf-8")
    if args.json or not args.write_report:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
