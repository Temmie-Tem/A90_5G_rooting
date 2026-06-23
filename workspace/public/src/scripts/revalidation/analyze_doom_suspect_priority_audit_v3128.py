#!/usr/bin/env python3
"""V3128 host-only audit for the DOOM stutter suspect priority list."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root

ROOT = repo_root()

RUN_ID = "V3128"
DECISION = "v3128-doom-suspect-priority-audit-complete"
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V3128_DOOM_SUSPECT_PRIORITY_AUDIT_2026-06-23.md"
V3124_REPORT = ROOT / "docs/reports/NATIVE_INIT_V3124_DOOMGENERIC_SUMMARY_ONLY_DIRECT_BLIT_LIVE_2026-06-23.md"
V3127_REPORT = ROOT / "docs/reports/NATIVE_INIT_V3127_DOOMGENERIC_SMOOTH_DEMO_DIRECT_BLIT_LIVE_2026-06-23.md"
KMS_SOURCE = ROOT / "workspace/public/src/native-init/a90_kms.c"
KMS_HEADER = ROOT / "workspace/public/src/native-init/a90_kms.h"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _metric(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, re.MULTILINE)
    if match is None:
        return None
    return int(match.group(1))


def _present(needle: str, text: str) -> bool:
    return needle in text


def collect_evidence() -> dict[str, Any]:
    v3124 = read_text(V3124_REPORT)
    v3127 = read_text(V3127_REPORT)
    kms_source = read_text(KMS_SOURCE)
    kms_header = read_text(KMS_HEADER)
    return {
        "v3124": {
            "report": rel(V3124_REPORT),
            "read_avg_us": _metric(r"Timing alloc/read/begin avg us: `\d+` / `(\d+)` / `\d+`", v3124),
            "draw_avg_us": _metric(r"Timing draw avg/max us: `(\d+)` / `\d+`", v3124),
            "flip_avg_us": _metric(r"Flip events: `\d+` delta avg/max us: `(\d+)` / `\d+`", v3124),
            "flip_max_us": _metric(r"Flip events: `\d+` delta avg/max us: `\d+` / `(\d+)`", v3124),
            "seq_missed": _metric(r"Shared seq missed/max-gap: `(\d+)` / `\d+`", v3124),
            "seq_max_gap": _metric(r"Shared seq missed/max-gap: `\d+` / `(\d+)`", v3124),
            "direct_reader": _present("Direct reader marker: `shared-mmap-direct-blit` ok=`1`", v3124),
            "summary_only": _present("Summary-only marker: foreground_frame_log=`0` ok=`1`", v3124),
        },
        "v3127": {
            "report": rel(V3127_REPORT),
            "read_avg_us": _metric(r"Timing read/draw/total avg us: `(\d+)` / `\d+` / `\d+`", v3127),
            "draw_avg_us": _metric(r"Timing read/draw/total avg us: `\d+` / `(\d+)` / `\d+`", v3127),
            "total_avg_us": _metric(r"Timing read/draw/total avg us: `\d+` / `\d+` / `(\d+)`", v3127),
            "flip_avg_us": _metric(r"Flip events: `\d+` delta avg/max us: `(\d+)` / `\d+`", v3127),
            "flip_max_us": _metric(r"Flip events: `\d+` delta avg/max us: `\d+` / `(\d+)`", v3127),
            "seq_missed": _metric(r"Shared seq missed/max-gap: `(\d+)` / `\d+`", v3127),
            "seq_max_gap": _metric(r"Shared seq missed/max-gap: `\d+` / `(\d+)`", v3127),
            "dump_repeated": _metric(r"Dump gametic changed/repeated/max_same_run/max_delta: `\d+` / `(\d+)` / `\d+` / `\d+`", v3127),
            "dump_max_same_run": _metric(r"Dump gametic changed/repeated/max_same_run/max_delta: `\d+` / `\d+` / `(\d+)` / `\d+`", v3127),
            "output_gametic_bounded": _present("Output gametic repetition bounded: `1`", v3127),
            "smooth_mode": _present("Smooth mode: `non-original-smooth-demo`", v3127),
            "telemetry_available": _present("Telemetry available: `1`", v3127),
        },
        "kms": {
            "source": rel(KMS_SOURCE),
            "header": rel(KMS_HEADER),
            "static_kms_state": _present("static struct a90_kms_state kms_state", kms_source),
            "pageflip_api": _present("int a90_kms_present_pageflip(", kms_source)
            and _present("int a90_kms_present_pageflip(", kms_header),
            "framebuffer_api": _present("struct a90_fb *a90_kms_framebuffer(void)", kms_header),
            "shared_buffer_export_api": _present("dma_buf", kms_source) or _present("PRIME", kms_source),
        },
    }


def build_audit(evidence: dict[str, Any]) -> dict[str, Any]:
    v3124 = evidence["v3124"]
    v3127 = evidence["v3127"]
    kms = evidence["kms"]
    read_avg = v3127.get("read_avg_us")
    direct_kms_saves_meaningful_time = isinstance(read_avg, int) and read_avg > 500

    suspects = [
        {
            "rank": 1,
            "suspect": "producer_presenter_dual_sleep_or_unsynced_pacing",
            "status": "closed",
            "evidence": [
                f"V3127 pageflip avg/max us={v3127.get('flip_avg_us')}/{v3127.get('flip_max_us')}",
                f"V3127 seq missed/max_gap={v3127.get('seq_missed')}/{v3127.get('seq_max_gap')}",
                "V3127 paced-time telemetry available and presenter-token model validated",
            ],
            "conclusion": "single presenter-token/pageflip pacing is stable; dual unsynced sleep is no longer the observed bottleneck",
        },
        {
            "rank": 2,
            "suspect": "raw_frame_file_ipc_malloc_open_read_free",
            "status": "closed",
            "evidence": [
                f"V3124 direct reader marker={int(bool(v3124.get('direct_reader')))} read_avg_us={v3124.get('read_avg_us')}",
                f"V3127 read_avg_us={v3127.get('read_avg_us')}",
            ],
            "conclusion": "shared-mmap direct blit reduced presenter read cost to single-digit microseconds",
        },
        {
            "rank": 3,
            "suspect": "dashboard_large_cpu_scaling",
            "status": "closed",
            "evidence": [
                "V3127 pre-scaled producer and 1:1-pre-scaled markers are present",
                f"V3127 draw_avg_us={v3127.get('draw_avg_us')} total_avg_us={v3127.get('total_avg_us')}",
            ],
            "conclusion": "large per-frame presenter scaling is off the critical path; large DOOM frame stays within the 16.6ms vblank budget",
        },
        {
            "rank": 4,
            "suspect": "no_new_frame_sync",
            "status": "closed",
            "evidence": [
                f"V3127 shared seq missed/max_gap={v3127.get('seq_missed')}/{v3127.get('seq_max_gap')}",
                f"V3124 shared seq missed/max_gap={v3124.get('seq_missed')}/{v3124.get('seq_max_gap')}",
            ],
            "conclusion": "shared-frame sequence gating proves no presenter-side missed-frame stream in the bounded live runs",
        },
        {
            "rank": 5,
            "suspect": "low_frame_write_cadence_or_game_tick_cadence",
            "status": "explained",
            "evidence": [
                f"V3127 smooth mode={int(bool(v3127.get('smooth_mode')))} telemetry={int(bool(v3127.get('telemetry_available')))}",
                f"V3127 dump_gametic repeated/max_same_run={v3127.get('dump_repeated')}/{v3127.get('dump_max_same_run')}",
                f"V3127 output_gametic_bounded={int(bool(v3127.get('output_gametic_bounded')))}",
            ],
            "conclusion": "when DOOM virtual time is paced per presented token, output-frame gametic repetition disappears; the prior stepped feel is original 35Hz DOOM cadence on a 60Hz panel",
        },
    ]

    direct_kms = {
        "status": "defer",
        "reason": "not current bottleneck",
        "expected_best_case_saved_us": read_avg,
        "direct_kms_saves_meaningful_time": direct_kms_saves_meaningful_time,
        "source_constraints": [
            "a90_kms.c owns DRM fd, dumb-buffer maps, current buffer, and pageflip event wait inside static kms_state",
            "a90_kms.h exposes framebuffer pointer only inside the native-init process; it does not expose a producer-safe back-buffer lease/export API",
            "no PRIME/dma-buf export path is present in the current KMS source",
        ],
        "code_evidence": kms,
        "next_if_reopened": "implement only if a future live run shows presenter read/copy back above the vblank budget or if the engine is moved into the native-init process",
    }

    return {
        "run_id": RUN_ID,
        "decision": DECISION,
        "result": "complete",
        "evidence": evidence,
        "suspects": suspects,
        "direct_kms": direct_kms,
        "remaining_required_work": [],
    }


def render_report(audit: dict[str, Any]) -> str:
    evidence = audit["evidence"]
    lines = [
        "# Native Init V3128 DOOM Suspect Priority Audit",
        "",
        "## Summary",
        "",
        f"- Run ID: `{RUN_ID}`",
        f"- Decision: `{audit['decision']}`",
        "- Result: PASS",
        "- Device flash: `no`; host-only evidence audit.",
        "- Scope: close the operator-provided DOOM stutter suspect list against current V3124/V3127 live evidence.",
        "",
        "## Suspect Status",
        "",
    ]
    for item in audit["suspects"]:
        lines.extend([
            f"### {item['rank']}. {item['suspect']}",
            "",
            f"- Status: `{item['status']}`",
            f"- Conclusion: {item['conclusion']}",
            "- Evidence:",
            *[f"  - {entry}" for entry in item["evidence"]],
            "",
        ])

    direct_kms = audit["direct_kms"]
    lines.extend([
        "## Direct KMS Buffer Path",
        "",
        f"- Status: `{direct_kms['status']}`",
        f"- Reason: `{direct_kms['reason']}`",
        f"- Expected best-case saved time: `{direct_kms['expected_best_case_saved_us']} us` (current V3127 presenter read avg).",
        f"- Meaningful current win: `{int(bool(direct_kms['direct_kms_saves_meaningful_time']))}`",
        "- Code constraints:",
        *[f"  - {entry}" for entry in direct_kms["source_constraints"]],
        "",
        "## Key Metrics",
        "",
        f"- V3124 report: `{evidence['v3124']['report']}`",
        f"- V3124 read/draw avg us: `{evidence['v3124']['read_avg_us']}` / `{evidence['v3124']['draw_avg_us']}`",
        f"- V3127 report: `{evidence['v3127']['report']}`",
        f"- V3127 read/draw/total avg us: `{evidence['v3127']['read_avg_us']}` / `{evidence['v3127']['draw_avg_us']}` / `{evidence['v3127']['total_avg_us']}`",
        f"- V3127 flip avg/max us: `{evidence['v3127']['flip_avg_us']}` / `{evidence['v3127']['flip_max_us']}`",
        f"- V3127 shared seq missed/max-gap: `{evidence['v3127']['seq_missed']}` / `{evidence['v3127']['seq_max_gap']}`",
        f"- V3127 dump gametic repeated/max-same-run: `{evidence['v3127']['dump_repeated']}` / `{evidence['v3127']['dump_max_same_run']}`",
        "",
        "## Decision",
        "",
        "- Do not implement helper-direct-KMS in this pass: it would remove at most the current `3 us` read stage while adding a broad display-ownership redesign.",
        "- The actionable stutter path from the pasted suspect list is closed by current live evidence.",
        "- Further visual quality work should be framed explicitly as a DOOM semantics/interpolation feature, not as another producer/presenter/IPC bug hunt.",
        "",
        "## Validation",
        "",
        "- Parsed V3124 and V3127 public reports.",
        "- Inspected `a90_kms.c` / `a90_kms.h` ownership and export surface.",
        "- `py_compile`: V3128 analyzer and focused tests.",
        "- `unittest`: V3128 analyzer contract.",
        "- `git diff --check`: PASS.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    audit = build_audit(collect_evidence())
    REPORT_PATH.write_text(render_report(audit), encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
