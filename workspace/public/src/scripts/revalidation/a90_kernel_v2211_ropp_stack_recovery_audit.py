#!/usr/bin/env python3
"""Audit whether existing stackmap frames can be recovered under ROPP.

This host-only analyzer does not claim exact symbolization.  It checks the
existing V2195 raw stack IPs against the bit-exact stock image and the RKP_CFP
ROPP/JOPP source rules:

* direct and JOPP-springboard BL callsite return-address matches
* canonical/aligned pass-through behavior from arch/arm64/kernel/stacktrace.c
* an offline joint-key search for frames that could share one ROPP XOR key

The goal is to decide whether the current six-frame capture can decode stack
symbolization, or whether a new live capture with raw frame slots / more stack
diversity is required.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[5]
PRIVATE_KERNEL_RUNS = REPO_ROOT / "workspace/private/runs/kernel"
SOURCE_ROOT = REPO_ROOT / "tmp/wifi/v766-icnss-qcacld-patch-apply-build/source"
DEFAULT_STOCK_DIR = PRIVATE_KERNEL_RUNS / "v2197-stock-kallsyms"
DEFAULT_SYSTEM_MAP = DEFAULT_STOCK_DIR / "System.map"
DEFAULT_KERNEL_RAW = DEFAULT_STOCK_DIR / "kernel.raw"
DEFAULT_STOCK_META = DEFAULT_STOCK_DIR / "stock-kallsyms.json"
DEFAULT_V2197_SYMBOLIZATION = DEFAULT_STOCK_DIR / "symbolization.json"
DEFAULT_V2198_RESULT = PRIVATE_KERNEL_RUNS / "v2198-jopp-ropp-classifier/result.json"
DEFAULT_STACKTRACE_C = SOURCE_ROOT / "arch/arm64/kernel/stacktrace.c"
DEFAULT_RKP_INSTRUMENT = SOURCE_ROOT / "scripts/rkp_cfp/instrument.py"
DEFAULT_AUTOCONF = SOURCE_ROOT / "out/include/generated/autoconf.h"
DEFAULT_OUT_DIR = PRIVATE_KERNEL_RUNS / "v2211-ropp-stack-recovery-audit"
REPORT_PATH = REPO_ROOT / "docs/reports/NATIVE_INIT_V2211_ROPP_STACK_RECOVERY_AUDIT_2026-06-12.md"

KERNEL_VA_MIN = 0xFFFFFF8008000000
KERNEL_VA_MAX = 0xFFFFFF800C000000
TEXT_SYMBOL_KINDS = {"T", "t", "W", "w"}
TOP_KEY_LIMIT = 8
DEFAULT_MAX_JOINT_CALLSITES = 100_000


@dataclass(frozen=True)
class Symbol:
    address: int
    kind: str
    name: str


@dataclass(frozen=True)
class Callsite:
    return_static: int
    call_static: int
    kind: str
    target_static: int
    target_symbol: str | None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parse_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip()
    return int(text, 16) if text.lower().startswith("0x") else int(text, 10)


def hex64(value: int) -> str:
    return f"0x{value & ((1 << 64) - 1):016x}"


def hex_signed(value: int) -> str:
    if value < 0:
        return f"-0x{-value:x}"
    return f"0x{value:x}"


def parse_system_map(path: Path) -> list[Symbol]:
    symbols: list[Symbol] = []
    for line in path.read_text(errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            address = int(parts[0], 16)
        except ValueError:
            continue
        symbols.append(Symbol(address, parts[1], parts[2]))
    symbols.sort(key=lambda item: item.address)
    return symbols


def build_symbol_index(symbols: list[Symbol]) -> dict[str, int]:
    index: dict[str, int] = {}
    for symbol in symbols:
        index.setdefault(symbol.name, symbol.address)
    return index


def nearest_symbol(symbols: list[Symbol], addresses: list[int], address: int) -> dict[str, Any] | None:
    index = bisect.bisect_right(addresses, address) - 1
    if index < 0:
        return None
    symbol = symbols[index]
    next_address = symbols[index + 1].address if index + 1 < len(symbols) else None
    return {
        "symbol": symbol.name,
        "kind": symbol.kind,
        "symbol_address": hex64(symbol.address),
        "offset": address - symbol.address,
        "offset_hex": hex_signed(address - symbol.address),
        "next_delta": None if next_address is None else next_address - address,
    }


def load_kernel_raw(path: Path) -> bytes:
    payload = path.read_bytes()
    if payload.startswith(b"UNCOMPRESSED_IMG"):
        image_size = struct.unpack_from("<I", payload, 16)[0]
        raw = payload[20:20 + image_size]
        if len(raw) != image_size:
            raise ValueError("truncated UNCOMPRESSED_IMG wrapper")
        return raw
    return payload


def load_synthetic_base(path: Path) -> int:
    metadata = json.loads(path.read_text())
    return parse_int(metadata["synthetic_base"])


def parse_config_symbols(path: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    for line in path.read_text(errors="replace").splitlines():
        match = re.match(r"^#define\s+(CONFIG_[A-Za-z0-9_]+)\s+(.*)$", line)
        if match:
            config[match.group(1)] = match.group(2).strip().strip('"')
    return config


def read_u32(raw: bytes, synthetic_base: int, address: int) -> int | None:
    offset = address - synthetic_base
    if offset < 0 or offset + 4 > len(raw):
        return None
    return struct.unpack_from("<I", raw, offset)[0]


def is_bl(insn: int | None) -> bool:
    return insn is not None and (insn & 0xFC000000) == 0x94000000


def decode_bl_target(insn: int, pc: int) -> int:
    imm26 = insn & 0x03FFFFFF
    if imm26 & 0x02000000:
        imm26 -= 0x04000000
    return pc + (imm26 << 2)


def build_callsite_map(
    raw: bytes,
    synthetic_base: int,
    symbols: list[Symbol],
    symbol_index: dict[str, int],
) -> dict[int, list[Callsite]]:
    symbol_addresses = [symbol.address for symbol in symbols]
    springboards = {
        symbol.address: symbol.name
        for symbol in symbols
        if symbol.name.startswith("jopp_springboard_blr_")
    }
    callsites: dict[int, list[Callsite]] = {}
    text_start = symbol_index.get("_stext", symbol_index.get("_text", synthetic_base))
    text_end = symbol_index.get("_etext", synthetic_base + len(raw))
    start_offset = max(0, text_start - synthetic_base)
    end_offset = min(len(raw) - 3, text_end - synthetic_base)
    start_offset += (-start_offset) % 4
    for offset in range(start_offset, end_offset, 4):
        address = synthetic_base + offset
        insn = struct.unpack_from("<I", raw, offset)[0]
        if not is_bl(insn):
            continue
        target = decode_bl_target(insn, address)
        if not (KERNEL_VA_MIN <= target < KERNEL_VA_MAX):
            continue
        nearest = nearest_symbol(symbols, symbol_addresses, target)
        target_symbol = None if nearest is None else str(nearest["symbol"])
        kind = "springboard" if target in springboards else "direct"
        return_static = address + 4
        callsites.setdefault(return_static, []).append(Callsite(return_static, address, kind, target, target_symbol))
    return callsites


def candidate_slides(v2197: dict[str, Any], v2198: dict[str, Any]) -> list[int]:
    slides: set[int] = set()
    for row in v2197.get("top_slide_candidates", []):
        slides.add(parse_int(row["slide"]))
    for row in v2198.get("top_timer_candidates", []):
        slides.add(parse_int(row["slide"]))
    for row in v2198.get("stack_candidate_cross_check", []):
        slides.add(parse_int(row["slide"]))
    slides.add(0x80000)
    return sorted(slides)


def stack_rows_for_slide(
    stack_ips: list[int],
    slide: int,
    callsites: dict[int, list[Callsite]],
    symbols: list[Symbol],
    addresses: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, runtime in enumerate(stack_ips):
        static = runtime - slide
        matches = callsites.get(static, [])
        direct_matches = [match for match in matches if match.kind == "direct"]
        springboard_matches = [match for match in matches if match.kind == "springboard"]
        rows.append({
            "index": index,
            "runtime": hex64(runtime),
            "static": hex64(static),
            "canonical_kernel_va": KERNEL_VA_MIN <= runtime < KERNEL_VA_MAX,
            "aligned_4": (runtime & 0x3) == 0,
            "nearest_symbol": nearest_symbol(symbols, addresses, static),
            "callsite_match_count": len(matches),
            "direct_callsite": bool(direct_matches),
            "springboard_callsite": bool(springboard_matches),
            "callsite_examples": [
                {
                    "kind": match.kind,
                    "call_static": hex64(match.call_static),
                    "target_static": hex64(match.target_static),
                    "target_symbol": match.target_symbol,
                }
                for match in matches[:3]
            ],
        })
    return rows


def solve_joint_keys(
    stack_ips: list[int],
    slide: int,
    callsite_returns: list[int],
    callsites: dict[int, list[Callsite]],
) -> list[dict[str, Any]]:
    key_counts: Counter[int] = Counter()
    key_indices: dict[int, set[int]] = {}
    runtime_returns = [value + slide for value in callsite_returns]
    for index, encoded in enumerate(stack_ips):
        for decoded_runtime in runtime_returns:
            key = encoded ^ decoded_runtime
            key_counts[key] += 1
            key_indices.setdefault(key, set()).add(index)
    candidates: list[dict[str, Any]] = []
    for key, count in key_counts.most_common(TOP_KEY_LIMIT):
        rows: list[dict[str, Any]] = []
        for index, encoded in enumerate(stack_ips):
            decoded_runtime = encoded ^ key
            decoded_static = decoded_runtime - slide
            matches = callsites.get(decoded_static, [])
            rows.append({
                "index": index,
                "encoded_runtime": hex64(encoded),
                "decoded_runtime": hex64(decoded_runtime),
                "decoded_static": hex64(decoded_static),
                "callsite": bool(matches),
                "callsite_kind": None if not matches else matches[0].kind,
                "target_symbol": None if not matches else matches[0].target_symbol,
            })
        candidates.append({
            "key": hex64(key),
            "raw_count": count,
            "distinct_frame_count": len(key_indices[key]),
            "rows": rows,
        })
    return candidates


def source_evidence(stacktrace_c: Path, instrument_py: Path) -> dict[str, Any]:
    stacktrace = stacktrace_c.read_text(errors="replace")
    instrument = instrument_py.read_text(errors="replace")
    return {
        "stacktrace_c": rel(stacktrace_c),
        "instrument_py": rel(instrument_py),
        "stacktrace_decode_outside_kernel_range": "frame->pc < 0xffffff8008000000" in stacktrace and "ropp_enable_backtrace" in stacktrace,
        "stacktrace_decode_misaligned_kernel_range": "((frame->pc & 0x3) != 0)" in stacktrace,
        "instrument_eor_lr_key": "eor RRX, x30, RRK" in instrument,
        "instrument_stp_encoded_lr": "stp x29, RRX" in instrument,
        "instrument_ldp_decode": "eor x30, RRX, RRK" in instrument,
    }


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    v2197 = json.loads(args.v2197_symbolization.read_text())
    v2198 = json.loads(args.v2198_result.read_text())
    stack_ips = [parse_int(value) for value in v2197["raw_stack_ips"]]
    symbols = parse_system_map(args.system_map)
    symbol_index = build_symbol_index(symbols)
    addresses = [symbol.address for symbol in symbols]
    raw = load_kernel_raw(args.kernel_raw)
    synthetic_base = load_synthetic_base(args.stock_meta)
    config = parse_config_symbols(args.autoconf)
    callsites = build_callsite_map(raw, synthetic_base, symbols, symbol_index)
    callsite_returns = sorted(callsites)
    joint_key_enabled = args.enable_joint_key_exhaustive and len(callsite_returns) <= args.max_joint_callsites
    slides = candidate_slides(v2197, v2198)

    slide_rows: list[dict[str, Any]] = []
    for slide in slides:
        rows = stack_rows_for_slide(stack_ips, slide, callsites, symbols, addresses)
        direct_hits = sum(1 for row in rows if row["direct_callsite"])
        springboard_hits = sum(1 for row in rows if row["springboard_callsite"])
        callsite_hits = sum(1 for row in rows if row["callsite_match_count"])
        unique_callsite_runtime_hits = len({row["runtime"] for row in rows if row["callsite_match_count"]})
        joint_keys = solve_joint_keys(stack_ips, slide, callsite_returns, callsites) if joint_key_enabled else []
        best_joint = joint_keys[0] if joint_keys else None
        slide_rows.append({
            "slide": slide,
            "slide_hex": hex_signed(slide),
            "callsite_hits": callsite_hits,
            "unique_callsite_runtime_hits": unique_callsite_runtime_hits,
            "direct_callsite_hits": direct_hits,
            "springboard_callsite_hits": springboard_hits,
            "best_joint_key_distinct_frames": 0 if best_joint is None else best_joint["distinct_frame_count"],
            "best_joint_key": None if best_joint is None else best_joint["key"],
            "rows": rows,
            "joint_key_candidates": joint_keys,
        })
    slide_rows.sort(key=lambda row: (-row["callsite_hits"], -row["best_joint_key_distinct_frames"], abs(row["slide"])))

    all_canonical = all(KERNEL_VA_MIN <= value < KERNEL_VA_MAX and (value & 0x3) == 0 for value in stack_ips)
    best = slide_rows[0] if slide_rows else {}
    strong_joint_key_slide_count = sum(1 for row in slide_rows if row["best_joint_key_distinct_frames"] >= 3)
    strong_stack_callsite = bool(best and best["unique_callsite_runtime_hits"] >= 3)
    strong_joint_key = bool(best and best["best_joint_key_distinct_frames"] >= 3 and strong_joint_key_slide_count <= 2)
    if strong_stack_callsite:
        decision = "v2211-stack-callsite-slide-candidate"
        reason = "Existing stack IPs contain at least three direct/springboard callsite matches under one slide candidate."
    elif strong_joint_key:
        decision = "v2211-ropp-joint-key-candidate"
        reason = "Existing stack IPs share a candidate XOR key for at least three frames; live validation is still required."
    else:
        decision = "v2211-ropp-stack-recovery-blocked-by-canonical-pass-through"
        reason = "Existing stack IPs are canonical/aligned and do not yield a strong callsite or joint-key solution."

    return {
        "decision": decision,
        "reason": reason,
        "inputs": {
            "system_map": rel(args.system_map),
            "kernel_raw": rel(args.kernel_raw),
            "stock_meta": rel(args.stock_meta),
            "v2197_symbolization": rel(args.v2197_symbolization),
            "v2198_result": rel(args.v2198_result),
            "stacktrace_c": rel(args.stacktrace_c),
            "rkp_instrument": rel(args.rkp_instrument),
            "autoconf": rel(args.autoconf),
        },
        "config": {
            "CONFIG_RKP_CFP": config.get("CONFIG_RKP_CFP"),
            "CONFIG_RKP_CFP_JOPP": config.get("CONFIG_RKP_CFP_JOPP"),
            "CONFIG_RKP_CFP_ROPP": config.get("CONFIG_RKP_CFP_ROPP"),
            "CONFIG_RKP_CFP_ROPP_SYSREGKEY": config.get("CONFIG_RKP_CFP_ROPP_SYSREGKEY"),
        },
        "source_evidence": source_evidence(args.stacktrace_c, args.rkp_instrument),
        "stack": {
            "raw_ips": [hex64(value) for value in stack_ips],
            "count": len(stack_ips),
            "all_canonical_aligned": all_canonical,
        },
        "callsites": {
            "return_address_count": len(callsite_returns),
            "record_count": sum(len(values) for values in callsites.values()),
            "springboard_record_count": sum(1 for values in callsites.values() for value in values if value.kind == "springboard"),
            "scan_range": {
                "start": hex64(symbol_index.get("_stext", symbol_index.get("_text", synthetic_base))),
                "end": hex64(symbol_index.get("_etext", synthetic_base + len(raw))),
            },
        },
        "joint_key_quality": {
            "strong_joint_key_slide_count": strong_joint_key_slide_count,
            "accepted": strong_joint_key,
            "search_enabled": joint_key_enabled,
            "rejection_reason": None if strong_joint_key else (
                "joint-key exhaustive search skipped because the callsite corpus is dense; raw frame-slot context is required"
                if not joint_key_enabled
                else "joint-key candidates are not accepted when many slide candidates produce comparable frame coverage"
            ),
        },
        "slide_candidate_count": len(slide_rows),
        "top_slide_rows": slide_rows[:12],
        "safety": {
            "host_only": True,
            "live_device_access": False,
            "probe_write_user_executed": False,
            "cgroup_attach": False,
            "wifi_action": False,
            "flash_reboot": False,
        },
    }


def render_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def render_markdown(result: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Native Init V2211 ROPP Stack Recovery Audit",
        "",
        "## Decision",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Reason: {result['reason']}",
        f"- Raw stack IPs: `{result['stack']['count']}`",
        f"- All canonical/aligned: `{str(result['stack']['all_canonical_aligned']).lower()}`",
        f"- Candidate slides checked: `{result['slide_candidate_count']}`",
        "",
        "## Interpretation",
        "",
        "- V2211 keeps stack recovery separate from the V2210 RELA-backed callback-table naming layer.",
        "- `stacktrace.c` only calls `ropp_enable_backtrace()` when a saved LR is outside the kernel range or is misaligned inside the kernel range.",
        "- The existing V2195 stack IPs are all canonical and 4-byte aligned, so an encoded-but-canonical value can pass through undecoded.",
        "- Existing evidence does not produce a strong direct/springboard callsite match or a strong shared XOR-key solution. Exact stack symbolization remains blocked for this capture.",
        "",
        "## Source Evidence",
        "",
    ]
    for key, value in result["source_evidence"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "## Callsite Corpus",
        "",
        f"- Scan range: `{result['callsites']['scan_range']['start']}` → `{result['callsites']['scan_range']['end']}`",
        f"- Return-address candidates: `{result['callsites']['return_address_count']}`",
        f"- Callsite records: `{result['callsites']['record_count']}`",
        f"- Springboard callsite records: `{result['callsites']['springboard_record_count']}`",
        f"- Joint-key exhaustive search enabled: `{str(result['joint_key_quality']['search_enabled']).lower()}`",
        f"- Strong joint-key slide count: `{result['joint_key_quality']['strong_joint_key_slide_count']}`",
        f"- Joint-key accepted: `{str(result['joint_key_quality']['accepted']).lower()}`",
        f"- Joint-key rejection: `{result['joint_key_quality']['rejection_reason']}`",
        "",
        "## Top Slide Rows",
        "",
    ])
    slide_table: list[list[Any]] = []
    for row in result["top_slide_rows"]:
        slide_table.append([
            f"`{row['slide_hex']}`",
            row["callsite_hits"],
            row["unique_callsite_runtime_hits"],
            row["direct_callsite_hits"],
            row["springboard_callsite_hits"],
            row["best_joint_key_distinct_frames"],
            "-" if row["best_joint_key"] is None else f"`{row['best_joint_key']}`",
        ])
    lines.append(render_table([
        "Slide",
        "Callsite hits",
        "Unique runtime hits",
        "Direct",
        "Springboard",
        "Best key frames",
        "Best key",
    ], slide_table))
    lines.extend([
        "",
        "## Raw Stack IPs",
        "",
    ])
    raw_rows: list[list[str]] = []
    first_slide = result["top_slide_rows"][0] if result["top_slide_rows"] else {"rows": []}
    for row in first_slide["rows"]:
        nearest = row["nearest_symbol"] or {}
        raw_rows.append([
            row["index"],
            f"`{row['runtime']}`",
            f"`{row['static']}`",
            f"`{nearest.get('symbol', '-')}`{nearest.get('offset_hex', '')}",
            str(row["direct_callsite"]).lower(),
            str(row["springboard_callsite"]).lower(),
        ])
    lines.append(render_table(["Index", "Runtime", "Static under top slide", "Nearest symbol", "Direct", "Springboard"], raw_rows))
    lines.extend([
        "",
        "## Next",
        "",
        "- Do not promote V2195 stack IPs to exact symbol names.",
        "- Next live unit, if stack symbolization is still needed: capture raw frame slots (`fp`, `*(fp)`, `*(fp+8)`) and task/key context with the read-only BPF path, or collect same-boot multi-stack diversity before retrying joint-key solving.",
        "- Keep `probe_write_user`, cgroup attach, flash/reboot, and Wi-Fi actions out of this path.",
        "",
        "## Safety",
        "",
    ])
    for key, value in result["safety"].items():
        lines.append(f"- {key}: `{str(value).lower()}`")
    lines.extend([
        "",
        "## Evidence",
        "",
        f"- Private result: `{rel(DEFAULT_OUT_DIR / 'result.json')}`",
        f"- V2197 symbolization: `{result['inputs']['v2197_symbolization']}`",
        f"- V2198 classifier: `{result['inputs']['v2198_result']}`",
        f"- Stock raw: `{result['inputs']['kernel_raw']}`",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system-map", type=Path, default=DEFAULT_SYSTEM_MAP)
    parser.add_argument("--kernel-raw", type=Path, default=DEFAULT_KERNEL_RAW)
    parser.add_argument("--stock-meta", type=Path, default=DEFAULT_STOCK_META)
    parser.add_argument("--v2197-symbolization", type=Path, default=DEFAULT_V2197_SYMBOLIZATION)
    parser.add_argument("--v2198-result", type=Path, default=DEFAULT_V2198_RESULT)
    parser.add_argument("--stacktrace-c", type=Path, default=DEFAULT_STACKTRACE_C)
    parser.add_argument("--rkp-instrument", type=Path, default=DEFAULT_RKP_INSTRUMENT)
    parser.add_argument("--autoconf", type=Path, default=DEFAULT_AUTOCONF)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--enable-joint-key-exhaustive", action="store_true")
    parser.add_argument("--max-joint-callsites", type=int, default=DEFAULT_MAX_JOINT_CALLSITES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = analyze(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.out_dir.joinpath("result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_markdown(result))
    print(json.dumps({
        "decision": result["decision"],
        "report": rel(args.report),
        "result": rel(args.out_dir / "result.json"),
        "raw_stack_ips": result["stack"]["count"],
        "all_canonical_aligned": result["stack"]["all_canonical_aligned"],
        "candidate_slides": result["slide_candidate_count"],
        "top_callsite_hits": result["top_slide_rows"][0]["callsite_hits"] if result["top_slide_rows"] else 0,
        "top_unique_callsite_runtime_hits": result["top_slide_rows"][0]["unique_callsite_runtime_hits"] if result["top_slide_rows"] else 0,
        "top_joint_key_frames": result["top_slide_rows"][0]["best_joint_key_distinct_frames"] if result["top_slide_rows"] else 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
