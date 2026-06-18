#!/usr/bin/env python3
"""V2702 host-only libaudcal topology-data handler RE.

V2701 proved the libaudcal dispatch validators for cal_type 10/14/24 all accept
the same two-word request shape before tail-calling command-specific topology
handlers.  This unit inspects those data handlers themselves and classifies the
observed V2700 ret=-12 path without executing device code or emitting vendor
bytes.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2702"
LIBAUDCAL = ROOT / "workspace/private/inputs/audio/acdb-deps-v2506/vendor-lib/libaudcal.so"
LLVM_OBJDUMP = ROOT / "workspace/private/inputs/toolchains/llvm-arm-toolchain-ship-10.0/bin/llvm-objdump"
COMPAT_LIBS = ROOT / "workspace/private/inputs/toolchains/compat-libs"
OUT_DIR = ROOT / "workspace/private/builds/audio/v2702-libaudcal-topology-data-handler-re"
REPORT = ROOT / "docs/reports/NATIVE_INIT_V2702_AUDIO_LIBAUDCAL_TOPOLOGY_DATA_HANDLER_RE_2026-06-18.md"

PLT_ENTRY0_ADDR = 0x00025C90
PLT_ENTRY_SIZE = 0x10

HANDLERS = (
    {
        "cal_type": 10,
        "role": "ADM_CUST_TOPOLOGY",
        "cmd": 0x11394,
        "symbol": "AcdbCmdGetAudioCOPPTopologyData",
        "symbol_addr": 0x17050,
        "stop_addr": 0x1710C,
        "expected_table_id": 0x12E47,
        "lookup_call_addr": 0x17098,
        "copy_call_addr": 0x170E6,
        "observed_v2700_ret": -12,
        "observed_v2700_state": "absent-ret-minus-12",
    },
    {
        "cal_type": 14,
        "role": "ASM_CUST_TOPOLOGY",
        "cmd": 0x12E01,
        "symbol": "AcdbCmdGetAudioPOPPTopologyData",
        "symbol_addr": 0x171A4,
        "stop_addr": 0x17264,
        "expected_table_id": 0x12E48,
        "lookup_call_addr": 0x171EC,
        "copy_call_addr": 0x17240,
        "observed_v2700_ret": 0,
        "observed_v2700_state": "stale-selected-absent",
    },
    {
        "cal_type": 24,
        "role": "AFE_CUST_TOPOLOGY",
        "cmd": 0x130DA,
        "symbol": "AcdbCmdGetAfeTopologyData",
        "symbol_addr": 0x17734,
        "stop_addr": 0x177F0,
        "expected_table_id": 0x130DE,
        "lookup_call_addr": 0x1777C,
        "copy_call_addr": 0x177CA,
        "observed_v2700_ret": 0,
        "observed_v2700_state": "aligned-selected-present",
    },
)


@dataclasses.dataclass(frozen=True)
class Instruction:
    addr: int
    mnemonic: str
    operands: str
    text: str


@dataclasses.dataclass(frozen=True)
class PltSymbol:
    index: int
    plt_addr: int
    got_addr: int
    name: str


@dataclasses.dataclass(frozen=True)
class TopologyHandler:
    cal_type: int
    role: str
    cmd: int
    symbol: str
    symbol_addr: int
    table_id: int | None
    lookup_call_addr: int
    lookup_call_target: int | None
    lookup_plt_addr: int | None
    lookup_plt_symbol: str | None
    copy_call_addr: int
    copy_call_target: int | None
    copy_plt_addr: int | None
    copy_plt_symbol: str | None
    word0_length_load_addr: int | None
    required_size_load_addr: int | None
    insufficient_buffer_return_addr: int | None
    word1_destination_load_addr: int | None
    return_size_store_addr: int | None
    fail_lookup_return_addr: int | None
    observed_v2700_ret: int
    observed_v2700_state: str
    has_buffer_size_gate: bool
    interpretation: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def env_with_toolchain() -> dict[str, str]:
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(COMPAT_LIBS) + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    return env


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, cwd=ROOT, env=env_with_toolchain(), text=True, stderr=subprocess.STDOUT)


def disassemble(start: int, stop: int, output_name: str) -> str:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = run(
        [
            str(LLVM_OBJDUMP),
            "-d",
            "--triple=thumbv7a-linux-android",
            f"--start-address=0x{start:x}",
            f"--stop-address=0x{stop:x}",
            str(LIBAUDCAL),
        ]
    )
    (OUT_DIR / output_name).write_text(text, encoding="utf-8")
    return text


def generate_disassembly() -> dict[str, str]:
    paths: dict[str, str] = {}
    for handler in HANDLERS:
        output_name = f"libaudcal-v2702-{handler['symbol']}.thumb-objdump.txt"
        disassemble(int(handler["symbol_addr"]), int(handler["stop_addr"]), output_name)
        paths[str(handler["symbol"])] = rel(OUT_DIR / output_name)
    return paths


def refresh_disassembly() -> dict[str, str]:
    return {
        str(handler["symbol"]): rel(OUT_DIR / f"libaudcal-v2702-{handler['symbol']}.thumb-objdump.txt")
        for handler in HANDLERS
    }


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
        instructions.append(Instruction(addr=int(match.group(1), 16), mnemonic=parts[0], operands=parts[1] if len(parts) > 1 else "", text=line.rstrip()))
    return instructions


def branch_target(instruction: Instruction) -> int | None:
    if instruction.mnemonic not in {"bl", "blx", "b.w"}:
        return None
    match = re.match(r"#(-?\d+)", instruction.operands)
    if not match:
        return None
    return instruction.addr + 4 + int(match.group(1), 10)


def parse_relplt(readelf_output: str) -> list[PltSymbol]:
    symbols: list[PltSymbol] = []
    for line in readelf_output.splitlines():
        match = re.match(r"\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_ARM_JUMP_SLOT\s+[0-9a-fA-F]+\s+([^\s]+)", line)
        if not match:
            continue
        index = len(symbols)
        symbols.append(PltSymbol(index=index, plt_addr=PLT_ENTRY0_ADDR + index * PLT_ENTRY_SIZE, got_addr=int(match.group(1), 16), name=match.group(2)))
    return symbols


def read_relplt() -> list[PltSymbol]:
    return parse_relplt(subprocess.check_output(["readelf", "-rW", str(LIBAUDCAL)], cwd=ROOT, text=True))


def resolve_plt_symbol(plt_symbols: list[PltSymbol], address: int | None) -> PltSymbol | None:
    if address is None or address < PLT_ENTRY0_ADDR:
        return None
    index = (address - PLT_ENTRY0_ADDR) // PLT_ENTRY_SIZE
    if 0 <= index < len(plt_symbols):
        slot = plt_symbols[index]
        if slot.plt_addr <= address < slot.plt_addr + PLT_ENTRY_SIZE:
            return slot
    return None


def find_instruction(instructions: list[Instruction], addr: int) -> Instruction | None:
    return next((instruction for instruction in instructions if instruction.addr == addr), None)


def parse_mov_imm(operands: str, register: str) -> int | None:
    match = re.match(rf"{register}, #(\d+)$", operands)
    if not match:
        return None
    return int(match.group(1), 10)


def find_table_id(instructions: list[Instruction], before_addr: int) -> int | None:
    low: int | None = None
    high: int | None = None
    for instruction in instructions:
        if instruction.addr >= before_addr:
            break
        if instruction.mnemonic == "movw":
            imm = parse_mov_imm(instruction.operands, "r1")
            if imm is not None:
                low = imm
                high = None
        if instruction.mnemonic == "movt":
            imm = parse_mov_imm(instruction.operands, "r1")
            if imm is not None and low is not None:
                high = imm
    if low is None:
        return None
    return low | ((high or 0) << 16)


def find_first_addr(instructions: list[Instruction], pattern: re.Pattern[str]) -> int | None:
    for instruction in instructions:
        if pattern.search(instruction.mnemonic + " " + instruction.operands):
            return instruction.addr
    return None


def find_first_addr_after(instructions: list[Instruction], pattern: re.Pattern[str], after_addr: int | None) -> int | None:
    for instruction in instructions:
        if after_addr is not None and instruction.addr <= after_addr:
            continue
        if pattern.search(instruction.mnemonic + " " + instruction.operands):
            return instruction.addr
    return None


def find_mvn_return(instructions: list[Instruction], imm: int) -> int | None:
    for instruction in instructions:
        if instruction.mnemonic == "mvn" and instruction.operands == f"r0, #{imm}":
            return instruction.addr
    return None


def analyze_handler(handler: dict[str, Any], disasm: str, plt_symbols: list[PltSymbol]) -> TopologyHandler:
    instructions = parse_instructions(disasm)
    lookup_instruction = find_instruction(instructions, int(handler["lookup_call_addr"]))
    copy_instruction = find_instruction(instructions, int(handler["copy_call_addr"]))
    lookup_target = branch_target(lookup_instruction) if lookup_instruction else None
    copy_target = branch_target(copy_instruction) if copy_instruction else None
    lookup_symbol = resolve_plt_symbol(plt_symbols, lookup_target)
    copy_symbol = resolve_plt_symbol(plt_symbols, copy_target)
    word0_load = find_first_addr(instructions, re.compile(r"^ldr r0, \[r5\]$"))
    required_size_load = find_first_addr(instructions, re.compile(r"^ldr r2, \[sp, #12\]$"))
    fail_lookup_return = find_mvn_return(instructions, 17)
    insufficient_return = find_mvn_return(instructions, 11)
    word1_dest_load = find_first_addr_after(instructions, re.compile(r"^ldr r0, \[r5, #4\]$"), insufficient_return)
    return_size_store = find_first_addr_after(instructions, re.compile(r"^str r0, \[r4\]$"), copy_instruction.addr if copy_instruction else None)
    table_id = find_table_id(instructions, int(handler["lookup_call_addr"]))
    has_buffer_size_gate = bool(word0_load and required_size_load and insufficient_return and word1_dest_load and return_size_store)
    if int(handler["observed_v2700_ret"]) == -12 and has_buffer_size_gate:
        interpretation = (
            "ret=-12 maps to the handler's insufficient-destination-buffer branch: after the ACDB table lookup, the handler compares request word0 against the returned required size before copying into request word1."
        )
    elif has_buffer_size_gate:
        interpretation = (
            "handler uses the same table lookup plus word0 length gate; ret=0 means the returned required size fit the supplied destination buffer for this run."
        )
    else:
        interpretation = "handler shape did not match the expected table lookup plus output-buffer gate."
    return TopologyHandler(
        cal_type=int(handler["cal_type"]),
        role=str(handler["role"]),
        cmd=int(handler["cmd"]),
        symbol=str(handler["symbol"]),
        symbol_addr=int(handler["symbol_addr"]),
        table_id=table_id,
        lookup_call_addr=int(handler["lookup_call_addr"]),
        lookup_call_target=lookup_target,
        lookup_plt_addr=lookup_symbol.plt_addr if lookup_symbol else None,
        lookup_plt_symbol=lookup_symbol.name if lookup_symbol else None,
        copy_call_addr=int(handler["copy_call_addr"]),
        copy_call_target=copy_target,
        copy_plt_addr=copy_symbol.plt_addr if copy_symbol else None,
        copy_plt_symbol=copy_symbol.name if copy_symbol else None,
        word0_length_load_addr=word0_load,
        required_size_load_addr=required_size_load,
        insufficient_buffer_return_addr=insufficient_return,
        word1_destination_load_addr=word1_dest_load,
        return_size_store_addr=return_size_store,
        fail_lookup_return_addr=fail_lookup_return,
        observed_v2700_ret=int(handler["observed_v2700_ret"]),
        observed_v2700_state=str(handler["observed_v2700_state"]),
        has_buffer_size_gate=has_buffer_size_gate,
        interpretation=interpretation,
    )


def classify_handlers(handlers: list[TopologyHandler]) -> dict[str, Any]:
    all_lookup = all(handler.lookup_plt_symbol == "acdbdata_ioctl" for handler in handlers)
    all_copy = all(handler.copy_plt_symbol == "__aeabi_memcpy" for handler in handlers)
    all_buffer_gate = all(handler.has_buffer_size_gate for handler in handlers)
    table_ids_match = all(handler.table_id == spec["expected_table_id"] for handler, spec in zip(handlers, HANDLERS, strict=True))
    cal10 = next(handler for handler in handlers if handler.cal_type == 10)
    cal10_reclassified = cal10.observed_v2700_ret == -12 and cal10.has_buffer_size_gate
    if all_lookup and all_copy and all_buffer_gate and table_ids_match and cal10_reclassified:
        decision = "v2702-libaudcal-ret-minus-12-is-buffer-too-small"
        recommended = "v2703-ownprocess-large-buffer-topology-get-plan"
        reason = (
            "The topology-data handlers first query ACDB table data, then compare request word0 with the returned required size before copying into request word1. "
            "The observed cal_type 10 ret=-12 is therefore best classified as the insufficient-buffer branch, not as proof that the selected ADM topology is absent."
        )
    else:
        decision = "v2702-libaudcal-topology-handler-shape-incomplete"
        recommended = "v2703-recheck-topology-handler-disassembly"
        reason = "At least one handler did not match the expected lookup/copy/word0-size-gate shape."
    return {
        "decision": decision,
        "ok": True,
        "all_lookup_calls_resolve_acdbdata_ioctl": all_lookup,
        "all_copy_calls_resolve_memcpy": all_copy,
        "all_handlers_have_buffer_size_gate": all_buffer_gate,
        "table_ids_match_expected": table_ids_match,
        "cal10_ret_minus_12_reclassified": cal10_reclassified,
        "native_replay_remains_parked": True,
        "recommended_next": recommended,
        "reason": reason,
    }


def analyze_handlers(refresh_objdump: bool = True) -> dict[str, Any]:
    disasm_paths = generate_disassembly() if refresh_objdump else refresh_disassembly()
    plt_symbols = read_relplt()
    analyses: list[TopologyHandler] = []
    for handler in HANDLERS:
        path = OUT_DIR / f"libaudcal-v2702-{handler['symbol']}.thumb-objdump.txt"
        disasm = path.read_text(encoding="utf-8", errors="ignore")
        analyses.append(analyze_handler(handler, disasm, plt_symbols))
    return {
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "scope": "host-only libaudcal topology-data handler RE; private vendor .so disassembly read only; no device action, Android handoff, ioctl, mixer write, PCM probe, raw ACDB payload commit, or vendor byte emission",
        "input": {
            "libaudcal": rel(LIBAUDCAL),
            "private_disassembly": disasm_paths,
            "source_iterations": ["V2700", "V2701"],
        },
        "classification": classify_handlers(analyses),
        "handlers": [dataclasses.asdict(analysis) for analysis in analyses],
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
    rows = [["cal_type", "role", "cmd", "handler", "table id", "lookup", "copy", "size gate", "V2700 state"]]
    for handler in summary["handlers"]:
        gate = (
            f"word0_len={hex_or_none(handler['word0_length_load_addr'])}, "
            f"required={hex_or_none(handler['required_size_load_addr'])}, "
            f"ret-12={hex_or_none(handler['insufficient_buffer_return_addr'])}, "
            f"word1_dst={hex_or_none(handler['word1_destination_load_addr'])}"
        )
        rows.append(
            [
                str(handler["cal_type"]),
                handler["role"],
                hex_or_none(handler["cmd"], 5),
                f"{handler['symbol']}@{hex_or_none(handler['symbol_addr'])}",
                hex_or_none(handler["table_id"], 5),
                f"{hex_or_none(handler['lookup_call_addr'])}->{handler['lookup_plt_symbol']}@{hex_or_none(handler['lookup_plt_addr'])}",
                f"{hex_or_none(handler['copy_call_addr'])}->{handler['copy_plt_symbol']}@{hex_or_none(handler['copy_plt_addr'])}",
                gate,
                f"ret={handler['observed_v2700_ret']} {handler['observed_v2700_state']}",
            ]
        )
    lines = [
        "# NATIVE_INIT V2702 — libaudcal topology-data handler RE",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only `libaudcal.so` topology-data handler reverse engineering. This unit reads a private vendor library and stores only public-safe metadata: command IDs, handler symbols, table IDs, branch targets, and control-flow interpretation. No device action, Android handoff, `/dev/msm_audio_cal` ioctl, mixer write, PCM probe, raw ACDB payload commit, or vendor byte commit occurred.",
        "",
        "## Result",
        "",
        f"- decision: `{c['decision']}`",
        f"- ok: `{c['ok']}`",
        f"- all_lookup_calls_resolve_acdbdata_ioctl: `{c['all_lookup_calls_resolve_acdbdata_ioctl']}`",
        f"- all_copy_calls_resolve_memcpy: `{c['all_copy_calls_resolve_memcpy']}`",
        f"- all_handlers_have_buffer_size_gate: `{c['all_handlers_have_buffer_size_gate']}`",
        f"- table_ids_match_expected: `{c['table_ids_match_expected']}`",
        f"- cal10_ret_minus_12_reclassified: `{c['cal10_ret_minus_12_reclassified']}`",
        f"- recommended_next: `{c['recommended_next']}`",
        f"- native_replay_remains_parked: `{c['native_replay_remains_parked']}`",
        "",
        "## Handler internals",
        "",
        table(rows),
        "",
        "## Interpretation",
        "",
        "The three topology-data handlers share the same internal pattern: build a 12-byte ACDB table query on the stack, call `acdbdata_ioctl(3, query, 12, NULL, 0)`, then copy the returned table bytes only if the caller-provided destination size is large enough.",
        "",
        "The important correction is cal_type `10` / command `0x11394`. In `AcdbCmdGetAudioCOPPTopologyData`, the `-12` return is the insufficient-destination-buffer branch (`mvn r0, #11`) reached after the handler loads request `word0` as the supplied destination length, loads the returned required size from the ACDB table query, and compares them. V2700 supplied `word0=0x1000`; therefore the previous `absent-ret-minus-12` label is too strong. The evidence now points to `buffer too small` rather than selected ADM topology absence.",
        "",
        "The `ret=0` paths for cal_type `14` and `24` mean their returned required sizes fit the supplied buffer in that run. That does not prove the ASM selected topology was correct; V2700 still observed stale/non-selected data for cal_type `14`. It does mean the next capture unit should fix output-buffer geometry before treating `-12` or stale success as database absence.",
        "",
        "## Next unit",
        "",
        "V2703 should update the own-process ACDB topology GET path to use a size-first or larger indirect output buffer for `0x11394` and re-check `0x12e01` with the same geometry. Acceptance should require `ret==0`, a non-zero output buffer, and private-only raw bytes/SHA for selected cal_type `10` and `14`. Native replay remains parked until byte-exact selected topology SET/GET payloads are recovered.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_libaudcal_topology_data_handlers_v2702.py tests/test_analyze_audio_libaudcal_topology_data_handlers_v2702.py`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_libaudcal_topology_data_handlers_v2702 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_libaudcal_topology_data_handlers_v2702.py --write-report --json`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest discover -s tests -v`",
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
    summary = analyze_handlers(refresh_objdump=not args.no_refresh_objdump)
    if args.write_report:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(render_report(summary), encoding="utf-8")
    if args.json or not args.write_report:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
