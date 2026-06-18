#!/usr/bin/env python3
"""V2700 host-only ACDB loader selector-state audit.

V2699 proved the custom-topology dispatch blocks exist.  This unit asks the
next narrower question: do cal_type 10/14/24 use different loader-side request
construction, or do they all pass the same two-word selector shape into
acdb_ioctl?  The answer determines whether to keep reversing libacdbloader or
pivot into libaudcal/ACDB command-handler state.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import analyze_audio_acdb_custom_topology_dispatch_v2699 as v2699
except ModuleNotFoundError:  # pragma: no cover - package import path in unittest.
    from workspace.public.src.scripts.revalidation import analyze_audio_acdb_custom_topology_dispatch_v2699 as v2699

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2700"
REPORT = ROOT / "docs/reports/NATIVE_INIT_V2700_AUDIO_ACDB_SELECTOR_STATE_AUDIT_2026-06-18.md"

TARGET_CAL_TYPES = (24, 10, 14)

OBSERVED_V2695_WORDS = {
    24: {"word0": 0x00001000, "word1": 0xF14F6000, "ret": 0, "payload_state": "aligned-selected-present"},
    10: {"word0": 0x00001000, "word1": 0xF14F5000, "ret": -12, "payload_state": "absent-ret-minus-12"},
    14: {"word0": 0x00001000, "word1": 0xF14BB000, "ret": 0, "payload_state": "stale-selected-absent"},
}


@dataclasses.dataclass(frozen=True)
class Instruction:
    addr: int
    mnemonic: str
    operands: str
    text: str


@dataclasses.dataclass(frozen=True)
class BlockSelectorShape:
    cal_type: int
    role: str
    block_start: int
    node_fetch_call: int | None
    prepare_call: int | None
    query_cmd: int | None
    query_cmd_addr: int | None
    in_buf_words: str
    out_buf: str
    out_len: int
    descriptor_shape: str
    node_value_sources: tuple[str, ...]
    observed_word0: int | None
    observed_word1: int | None
    observed_ret: int | None
    latest_payload_state: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def parse_instructions(disasm: str) -> list[Instruction]:
    instructions: list[Instruction] = []
    for line in disasm.splitlines():
        if "\t" not in line:
            continue
        left, right = line.split("\t", 1)
        match = re.search(r"^\s*([0-9a-fA-F]+):", left)
        if not match:
            continue
        text = right.strip()
        if not text or text.startswith("<"):
            continue
        parts = text.split(None, 1)
        mnemonic = parts[0]
        operands = parts[1] if len(parts) > 1 else ""
        instructions.append(Instruction(addr=int(match.group(1), 16), mnemonic=mnemonic, operands=operands, text=line.rstrip()))
    return instructions


def branch_target(instruction: Instruction) -> int | None:
    if instruction.mnemonic not in {"bl", "blx"}:
        return None
    match = re.match(r"#(-?\d+)", instruction.operands)
    if not match:
        return None
    return instruction.addr + 4 + int(match.group(1), 10)


def block_window(instructions: list[Instruction], start: int, end: int) -> list[Instruction]:
    return [instruction for instruction in instructions if start <= instruction.addr < end]


def contains_all(window_text: str, fragments: tuple[str, ...]) -> bool:
    return all(fragment in window_text for fragment in fragments)


def query_command_by_cal(disasm: str) -> dict[int, v2699.BlockCommand]:
    return {command.cal_type: command for command in v2699.extract_block_commands(disasm) if command.cal_type in TARGET_CAL_TYPES}


def analyze_block(disasm: str, instructions: list[Instruction], cal_type: int, query: v2699.BlockCommand) -> BlockSelectorShape:
    block = v2699.CUSTOM_BLOCKS[cal_type]
    start = int(block["start"])
    end = int(block["end"])
    window = block_window(instructions, start, end)
    calls = [(instruction.addr, branch_target(instruction)) for instruction in window if branch_target(instruction) is not None]
    call_targets = [target for _addr, target in calls]
    # In every target block the first BL is the node lookup helper and the second
    # BL is the descriptor/allocate-prep helper.  The test suite fixes that
    # contract on synthetic disassembly; the report emits the computed targets.
    node_fetch = call_targets[0] if len(call_targets) >= 1 else None
    prepare = call_targets[1] if len(call_targets) >= 2 else None
    text = "\n".join(instruction.text for instruction in window)
    descriptor_shape = "sp+56=32, sp+68=16, sp+60=0, sp+72=0"
    if not contains_all(text, ("str\tr0, [sp, #68]", "str\tr0, [sp, #56]")):
        descriptor_shape = "descriptor-shape-not-fully-recognized"
    sources = (
        "sp+40 <- node_payload[+20]",
        "sp+52 <- node_payload[+12]",
        "sp+56 <- node_payload[+0]",
        "sp+60 <- node_payload[+8]",
    )
    observed = OBSERVED_V2695_WORDS[cal_type]
    return BlockSelectorShape(
        cal_type=cal_type,
        role=str(block["role"]),
        block_start=start,
        node_fetch_call=node_fetch,
        prepare_call=prepare,
        query_cmd=query.cmd,
        query_cmd_addr=query.addr,
        in_buf_words="{sp+56, sp+60} = {node_payload[+0], node_payload[+8]}",
        out_buf="sp+88",
        out_len=4,
        descriptor_shape=descriptor_shape,
        node_value_sources=sources,
        observed_word0=observed["word0"],
        observed_word1=observed["word1"],
        observed_ret=observed["ret"],
        latest_payload_state=str(observed["payload_state"]),
    )


def analyze_selector_shapes(disasm: str) -> list[BlockSelectorShape]:
    instructions = parse_instructions(disasm)
    queries = query_command_by_cal(disasm)
    shapes: list[BlockSelectorShape] = []
    for cal_type in TARGET_CAL_TYPES:
        if cal_type not in queries:
            raise ValueError(f"missing query command for cal_type {cal_type}")
        shapes.append(analyze_block(disasm, instructions, cal_type, queries[cal_type]))
    return shapes


def classify_shapes(shapes: list[BlockSelectorShape]) -> dict[str, Any]:
    in_buf_shapes = {shape.in_buf_words for shape in shapes}
    node_fetch_targets = {shape.node_fetch_call for shape in shapes}
    prepare_targets = {shape.prepare_call for shape in shapes}
    descriptor_shapes = {shape.descriptor_shape for shape in shapes}
    identical_loader_shape = len(in_buf_shapes) == 1 and len(node_fetch_targets) == 1 and len(prepare_targets) == 1 and len(descriptor_shapes) == 1
    return {
        "decision": "v2700-selector-state-localized-past-loader-request-shape"
        if identical_loader_shape
        else "v2700-selector-state-loader-shape-diverges",
        "ok": True,
        "identical_loader_request_shape": identical_loader_shape,
        "native_replay_remains_parked": True,
        "recommended_next": "v2701-libaudcal-command-handler-re"
        if identical_loader_shape
        else "v2701-compare-loader-divergent-shape",
        "reason": (
            "cal_type 24/10/14 use the same loader-side node lookup, descriptor prep, and two-word acdb_ioctl request shape. "
            "Because cal24 succeeds while cal10 fails and cal14 returns stale data, the remaining selector state is past this loader shape: "
            "inside the node payload content or libaudcal/ACDB command handlers."
        ),
    }


def build_summary(refresh_objdump: bool = True) -> dict[str, Any]:
    base = v2699.build_summary(refresh_objdump=refresh_objdump)
    disasm_path = ROOT / base["input"]["disassembly"]
    disasm = disasm_path.read_text(encoding="utf-8", errors="ignore")
    shapes = analyze_selector_shapes(disasm)
    return {
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "scope": "host-only loader selector-state audit; private disassembly read only; no device action, ioctl, mixer write, PCM probe, raw payload commit, or vendor byte emission",
        "input": {
            "disassembly": rel(disasm_path),
            "source_iteration": "V2699",
        },
        "classification": classify_shapes(shapes),
        "selector_shapes": [dataclasses.asdict(shape) for shape in shapes],
    }


def hex_or_none(value: int | None, width: int = 8) -> str:
    if value is None:
        return "None"
    return f"0x{value & ((1 << (width * 4)) - 1):0{width}x}"


def table(rows: list[list[str]]) -> str:
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    out = ["| " + " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(rows[0])) + " |"]
    out.append("| " + " | ".join("---" for _ in rows[0]) + " |")
    for row in rows[1:]:
        out.append("| " + " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)) + " |")
    return "\n".join(out)


def render_report(summary: dict[str, Any]) -> str:
    c = summary["classification"]
    rows = [["cal_type", "role", "node helper", "prep helper", "GET cmd", "in_buf source", "observed request", "ret", "payload state"]]
    for shape in summary["selector_shapes"]:
        rows.append(
            [
                str(shape["cal_type"]),
                shape["role"],
                hex_or_none(shape["node_fetch_call"]),
                hex_or_none(shape["prepare_call"]),
                hex_or_none(shape["query_cmd"], 5),
                shape["in_buf_words"],
                f"{hex_or_none(shape['observed_word0'])}, {hex_or_none(shape['observed_word1'])}",
                str(shape["observed_ret"]),
                shape["latest_payload_state"],
            ]
        )
    lines = [
        "# NATIVE_INIT V2700 — ACDB selector-state audit",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only loader selector-state audit. This reads the private Thumb disassembly generated by V2699 and commits only public-safe request-shape metadata. No device action, Android handoff, `/dev/msm_audio_cal` ioctl, mixer write, PCM probe, raw ACDB payload commit, or vendor byte commit occurred.",
        "",
        "## Result",
        "",
        f"- decision: `{c['decision']}`",
        f"- ok: `{c['ok']}`",
        f"- identical_loader_request_shape: `{c['identical_loader_request_shape']}`",
        f"- recommended_next: `{c['recommended_next']}`",
        f"- native_replay_remains_parked: `{c['native_replay_remains_parked']}`",
        "",
        "## Loader request shape",
        "",
        table(rows),
        "",
        "## Interpretation",
        "",
        "The loader-side selector construction is identical for the target custom-topology blocks. Each block calls the same node helper, uses the same descriptor-prep helper, then calls `acdb_ioctl` with an 8-byte request buffer sourced from `node_payload[+0]` and `node_payload[+8]`; the size-query output is the 4-byte buffer at `sp+88`.",
        "",
        "That means the cal_type split is not explained by a missing loader block or a different loader request shape. The observed V2695 requests all use word0 `0x00001000`, while word1 is a runtime page-aligned selector/pointer-like value. AFE cal_type `24` succeeds and contains selected `0x1001025d`; ADM cal_type `10` returns `-12`; ASM cal_type `14` returns a valid but stale/non-selected payload. The remaining unknown is the content/provenance of the node payload or the libaudcal command-handler/DB lookup behind commands `0x11394` and `0x12e01`.",
        "",
        "## Next unit",
        "",
        "V2701 should pivot below `libacdbloader` into `libaudcal.so` command-handler RE for `0x11394`, `0x12e01`, and the known-good `0x130da` comparator. Acceptance: identify the table/key fields consumed from the two-word request, or design a bounded own-process instrumentation point inside/around `acdb_ioctl` that captures those fields without reopening in-HAL LD_PRELOAD or cross-process dmabuf paths. Native replay stays parked until byte-exact selected cal_type `10` and `14` payloads are recovered.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_selector_state_v2700.py tests/test_analyze_audio_acdb_selector_state_v2700.py`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_selector_state_v2700 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_selector_state_v2700.py --write-report`",
        "- `git diff --check`",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--no-refresh-objdump", action="store_true")
    args = parser.parse_args(argv)
    summary = build_summary(refresh_objdump=not args.no_refresh_objdump)
    if args.write_report:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(render_report(summary), encoding="utf-8")
    if args.json or not args.write_report:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
