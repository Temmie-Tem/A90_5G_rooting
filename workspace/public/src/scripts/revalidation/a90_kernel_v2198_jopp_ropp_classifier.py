#!/usr/bin/env python3
"""Classify A90 JOPP/ROPP slide evidence from existing kernel artifacts.

This is host-only analysis.  It combines:

* stock System.map recovered from embedded kallsyms,
* the bit-exact stock kernel image,
* V2195 stackmap IPs,
* V2196 timer:timer_start function pointers,
* OSRC source patterns for timer callback semantics.

The goal is not to force a slide answer.  The goal is to separate map authority,
JOPP magic matches, timer callback semantics, and ROPP stack-callsite evidence so
later WLAN stack/object-chain symbolization does not rely on a false "exact"
slide.
"""

from __future__ import annotations

import argparse
import bisect
import gzip
import json
import re
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


STACK_IP_RE = re.compile(r"stack_ip\s+index=(?P<index>\d+)\s+value=0x(?P<addr>[0-9a-fA-F]+)")
TIMER_VALUE_RE = re.compile(r"value=(?P<addr>\d+)\s+count=(?P<count>\d+)")
CONFIG_RE = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$")
CONFIG_NOT_SET_RE = re.compile(r"^# (CONFIG_[A-Za-z0-9_]+) is not set$")
JOPP_MAGIC = 0x00BE7BAD
JOPP_MAGIC_BYTES = struct.pack("<I", JOPP_MAGIC)
ROPP_EOR_X16_X30_X17 = 0xCA1103D0
DEFAULT_SLIDE_MIN = -0x200000
DEFAULT_SLIDE_MAX = 0x200000
DEFAULT_MAGIC_DELTAS = (4, 8)

HIGH_CONF_TIMER_PATTERNS = (
    re.compile(r"\bDEFINE_TIMER\s*\(\s*[A-Za-z_][A-Za-z0-9_]*\s*,\s*&?\s*([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\bsetup_timer\s*\(\s*[^,]+,\s*&?\s*([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\btimer_setup\s*\(\s*[^,]+,\s*&?\s*([A-Za-z_][A-Za-z0-9_]*)"),
)
LOW_CONF_TIMER_PATTERNS = (
    re.compile(r"(?:->|\.)function\s*=\s*&?\s*([A-Za-z_][A-Za-z0-9_]*)"),
)
SKIP_CALLBACK_NAMES = {
    "NULL",
    "null",
    "fn",
    "function",
    "timer",
    "hrtimer",
}


@dataclass(frozen=True)
class Symbol:
    address: int
    kind: str
    name: str


@dataclass(frozen=True)
class TimerValue:
    address: int
    count: int


def parse_int(value: str) -> int:
    value = value.strip()
    if value.lower().startswith("0x"):
        return int(value, 16)
    return int(value, 10)


def format_signed_hex(value: int) -> str:
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
    symbols.sort(key=lambda symbol: symbol.address)
    return symbols


def nearest_symbol(symbols: list[Symbol], addresses: list[int], address: int) -> dict[str, object] | None:
    index = bisect.bisect_right(addresses, address) - 1
    if index < 0:
        return None
    symbol = symbols[index]
    next_address = symbols[index + 1].address if index + 1 < len(symbols) else None
    return {
        "symbol_address": symbol.address,
        "symbol_address_hex": f"0x{symbol.address:016x}",
        "symbol": symbol.name,
        "kind": symbol.kind,
        "offset": address - symbol.address,
        "next_delta": None if next_address is None else next_address - address,
    }


def build_symbol_index(symbols: list[Symbol]) -> dict[str, int]:
    index: dict[str, int] = {}
    for symbol in symbols:
        index.setdefault(symbol.name, symbol.address)
    return index


def load_kernel(path: Path) -> bytes:
    payload = path.read_bytes()
    if payload.startswith(b"UNCOMPRESSED_IMG"):
        if len(payload) < 20:
            raise ValueError("UNCOMPRESSED_IMG wrapper is too short")
        image_size = struct.unpack_from("<I", payload, 16)[0]
        raw = payload[20:20 + image_size]
        if len(raw) != image_size:
            raise ValueError(f"wrapper declares {image_size} bytes but only {len(raw)} are available")
        return raw
    return payload


def extract_ikconfig(raw: bytes) -> dict[str, str]:
    start = raw.find(b"IKCFG_ST")
    if start < 0:
        return {}
    end = raw.find(b"IKCFG_ED", start + len(b"IKCFG_ST"))
    if end < 0:
        return {}
    block = raw[start + len(b"IKCFG_ST"):end]
    gzip_offset = block.find(b"\x1f\x8b")
    if gzip_offset < 0:
        return {}
    text = gzip.decompress(block[gzip_offset:]).decode("utf-8", "replace")
    config: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = CONFIG_RE.match(line)
        if match:
            config[match.group(1)] = match.group(2).strip('"')
            continue
        match = CONFIG_NOT_SET_RE.match(line)
        if match:
            config[match.group(1)] = "n"
    return config


def config_state(config: dict[str, str], name: str) -> str:
    return config.get(name, "unset")


def find_magic_addresses(raw: bytes, synthetic_base: int) -> list[int]:
    addresses: list[int] = []
    cursor = 0
    while True:
        offset = raw.find(JOPP_MAGIC_BYTES, cursor)
        if offset < 0:
            break
        addresses.append(synthetic_base + offset)
        cursor = offset + 1
    return addresses


def read_u32(raw: bytes, synthetic_base: int, address: int) -> int | None:
    offset = address - synthetic_base
    if offset < 0 or offset + 4 > len(raw):
        return None
    return struct.unpack_from("<I", raw, offset)[0]


def is_bl(insn: int | None) -> bool:
    return insn is not None and (insn & 0xFC000000) == 0x94000000


def is_blr(insn: int | None) -> bool:
    return insn is not None and (insn & 0xFFFFFC1F) == 0xD63F0000


def decode_bl_target(insn: int, pc: int) -> int:
    imm26 = insn & 0x03FFFFFF
    if imm26 & 0x02000000:
        imm26 -= 0x04000000
    return pc + (imm26 << 2)


def classify_function_entry(raw: bytes, synthetic_base: int, address: int) -> dict[str, object]:
    magic_before = read_u32(raw, synthetic_base, address - 4) == JOPP_MAGIC
    ropp_offsets: list[int] = []
    for offset in range(0, 32, 4):
        if read_u32(raw, synthetic_base, address + offset) == ROPP_EOR_X16_X30_X17:
            ropp_offsets.append(offset)
    return {
        "jopp_magic_before_entry": magic_before,
        "ropp_prologue_offsets": ropp_offsets,
        "ropp_prologue_present": bool(ropp_offsets),
    }


def parse_stack_logs(paths: list[Path]) -> list[int]:
    stack_ips: list[int] = []
    for path in paths:
        for line in path.read_text(errors="replace").splitlines():
            match = STACK_IP_RE.search(line)
            if match:
                stack_ips.append(int(match.group("addr"), 16))
    return stack_ips


def parse_timer_logs(paths: list[Path]) -> list[TimerValue]:
    counters: Counter[int] = Counter()
    for path in paths:
        for line in path.read_text(errors="replace").splitlines():
            match = TIMER_VALUE_RE.search(line)
            if match:
                counters[int(match.group("addr"), 10) & ((1 << 64) - 1)] += int(match.group("count"), 10)
    return [TimerValue(address, count) for address, count in counters.most_common()]


def extract_timer_callback_candidates(source_roots: list[Path]) -> dict[str, object]:
    high: dict[str, list[str]] = defaultdict(list)
    low: dict[str, list[str]] = defaultdict(list)
    scanned_files = 0
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix not in {".c", ".h"}:
                continue
            scanned_files += 1
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            for pattern in HIGH_CONF_TIMER_PATTERNS:
                for match in pattern.finditer(text):
                    name = match.group(1)
                    if name not in SKIP_CALLBACK_NAMES:
                        high[name].append(str(path))
            for pattern in LOW_CONF_TIMER_PATTERNS:
                for match in pattern.finditer(text):
                    name = match.group(1)
                    if name not in SKIP_CALLBACK_NAMES:
                        low[name].append(str(path))
    return {
        "scanned_files": scanned_files,
        "high_confidence": {name: paths[:5] for name, paths in sorted(high.items())},
        "low_confidence": {name: paths[:5] for name, paths in sorted(low.items())},
    }


def callback_confidence(name: str, callbacks: dict[str, object]) -> str:
    if name in callbacks["high_confidence"]:
        return "high"
    if name in callbacks["low_confidence"]:
        return "low"
    return "none"


def timer_magic_candidate_slides(timers: list[TimerValue],
                                 magic_addresses: list[int],
                                 deltas: list[int],
                                 slide_min: int,
                                 slide_max: int) -> dict[int, list[dict[str, int]]]:
    candidates: dict[int, list[dict[str, int]]] = defaultdict(list)
    for timer_index, timer in enumerate(timers):
        for magic_address in magic_addresses:
            for delta in deltas:
                slide = timer.address - (magic_address + delta)
                if slide_min <= slide <= slide_max and len(candidates[slide]) < 16:
                    candidates[slide].append({
                        "timer_index": timer_index,
                        "timer_runtime": timer.address,
                        "timer_count": timer.count,
                        "magic_address": magic_address,
                        "delta": delta,
                    })
    return candidates


def score_timer_slide(slide: int,
                      timers: list[TimerValue],
                      raw: bytes,
                      synthetic_base: int,
                      symbols: list[Symbol],
                      addresses: list[int],
                      callbacks: dict[str, object],
                      deltas: list[int]) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    magic_weight = 0
    magic_distinct = 0
    high_weight = 0
    low_weight = 0
    high_distinct = 0
    low_distinct = 0
    dominant_magic = False
    for index, timer in enumerate(timers):
        static_address = timer.address - slide
        magic_deltas: list[int] = []
        for delta in deltas:
            if read_u32(raw, synthetic_base, static_address - delta) == JOPP_MAGIC:
                magic_deltas.append(delta)
        mapping = nearest_symbol(symbols, addresses, static_address)
        symbol_name = "" if mapping is None else str(mapping["symbol"])
        confidence = callback_confidence(symbol_name, callbacks) if symbol_name else "none"
        if magic_deltas:
            magic_distinct += 1
            magic_weight += timer.count
            if index == 0:
                dominant_magic = True
        if confidence == "high" and magic_deltas:
            high_distinct += 1
            high_weight += timer.count
        if confidence in {"high", "low"} and magic_deltas:
            low_distinct += 1
            low_weight += timer.count
        entry = classify_function_entry(raw, synthetic_base, static_address)
        rows.append({
            "index": index,
            "runtime": f"0x{timer.address:016x}",
            "static": f"0x{static_address:016x}",
            "count": timer.count,
            "magic_deltas": magic_deltas,
            "symbol": symbol_name,
            "symbol_offset": None if mapping is None else mapping["offset"],
            "callback_confidence": confidence,
            "entry": entry,
        })
    return {
        "slide": slide,
        "slide_hex": format_signed_hex(slide),
        "magic_distinct": magic_distinct,
        "magic_weight": magic_weight,
        "high_callback_distinct": high_distinct,
        "high_callback_weight": high_weight,
        "known_callback_distinct": low_distinct,
        "known_callback_weight": low_weight,
        "dominant_timer_magic": dominant_magic,
        "timer_rows": rows,
    }


def score_stack_slide(slide: int,
                      stack_ips: list[int],
                      raw: bytes,
                      synthetic_base: int,
                      symbols: list[Symbol],
                      addresses: list[int],
                      jopp_springboards: set[int]) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    direct_hits = 0
    springboard_hits = 0
    mapped = 0
    for index, runtime_ip in enumerate(stack_ips):
        static_address = runtime_ip - slide
        mapping = nearest_symbol(symbols, addresses, static_address)
        if mapping is not None:
            mapped += 1
        prev_pc = static_address - 4
        prev_insn = read_u32(raw, synthetic_base, prev_pc)
        direct_call = is_bl(prev_insn) or is_blr(prev_insn)
        springboard_call = False
        target = None
        target_symbol = None
        if is_bl(prev_insn):
            target = decode_bl_target(int(prev_insn), prev_pc)
            springboard_call = target in jopp_springboards
            target_mapping = nearest_symbol(symbols, addresses, target)
            target_symbol = None if target_mapping is None else target_mapping["symbol"]
        if direct_call:
            direct_hits += 1
        if springboard_call:
            springboard_hits += 1
        rows.append({
            "index": index,
            "runtime": f"0x{runtime_ip:016x}",
            "static": f"0x{static_address:016x}",
            "symbol": None if mapping is None else mapping["symbol"],
            "symbol_offset": None if mapping is None else mapping["offset"],
            "prev_insn": None if prev_insn is None else f"0x{prev_insn:08x}",
            "direct_callsite": direct_call,
            "springboard_callsite": springboard_call,
            "bl_target": None if target is None else f"0x{target:016x}",
            "bl_target_symbol": target_symbol,
        })
    return {
        "mapped": mapped,
        "direct_callsite_hits": direct_hits,
        "springboard_callsite_hits": springboard_hits,
        "rows": rows,
    }


def render_markdown(result: dict[str, object]) -> str:
    lines = [
        "# A90 V2198 JOPP/ROPP Slide Classifier",
        "",
        "## Decision",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Reason: {result['reason']}",
        "",
        "## Config",
        "",
    ]
    config = result["config"]
    for key in (
        "CONFIG_RKP_CFP",
        "CONFIG_RKP_CFP_JOPP",
        "CONFIG_RKP_CFP_JOPP_MAGIC",
        "CONFIG_RKP_CFP_ROPP",
        "CONFIG_RKP_CFP_ROPP_SYSREGKEY",
        "CONFIG_GCC_PLUGINS",
    ):
        lines.append(f"- {key}: `{config.get(key, 'unset')}`")
    lines.extend([
        "",
        "## Summary",
        "",
        f"- JOPP magic occurrences: `{result['jopp_magic_occurrences']}`",
        f"- JOPP springboards: `{result['jopp_springboard_count']}`",
        f"- Timer values: `{result['timer_count']}`",
        f"- Stack IPs: `{result['stack_ip_count']}`",
        f"- High-confidence callback names: `{result['callback_summary']['high_confidence_count']}`",
        f"- Low-confidence callback names: `{result['callback_summary']['low_confidence_count']}`",
        "",
        "## Top Timer-Magic Semantic Candidates",
        "",
    ])
    for candidate in result["top_timer_candidates"][:10]:
        lines.append(
            f"- slide `{candidate['slide_hex']}`: magic "
            f"{candidate['magic_distinct']}/{result['timer_count']} weight "
            f"{candidate['magic_weight']}/{result['timer_weight_total']}, known-callback "
            f"{candidate['known_callback_distinct']}/{result['timer_count']} weight "
            f"{candidate['known_callback_weight']}/{result['timer_weight_total']}, high-callback "
            f"{candidate['high_callback_distinct']}/{result['timer_count']} weight "
            f"{candidate['high_callback_weight']}/{result['timer_weight_total']}"
        )
        for row in candidate["timer_rows"][:8]:
            if not row["magic_deltas"]:
                continue
            lines.append(
                f"  - timer{row['index']} `{row['runtime']}` count={row['count']} -> "
                f"`{row['symbol']}`+0x{int(row['symbol_offset'] or 0):x}, "
                f"magic_delta={row['magic_deltas']}, callback={row['callback_confidence']}"
            )
    lines.extend(["", "## Existing Stack Candidate Cross-Check", ""])
    for candidate in result["stack_candidate_cross_check"]:
        stack = candidate["stack"]
        lines.append(
            f"- slide `{candidate['slide_hex']}`: mapped {stack['mapped']}/{result['stack_ip_count']}, "
            f"direct_callsite={stack['direct_callsite_hits']}, "
            f"springboard_callsite={stack['springboard_callsite_hits']}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system-map", type=Path, required=True)
    parser.add_argument("--stock-json", type=Path, required=True)
    parser.add_argument("--kernel", type=Path, required=True, help="raw Image or UNCOMPRESSED_IMG wrapper")
    parser.add_argument("--timer-log", type=Path, action="append", default=[])
    parser.add_argument("--stack-log", type=Path, action="append", default=[])
    parser.add_argument("--source-root", type=Path, action="append", default=[])
    parser.add_argument("--slide-min", type=lambda value: int(value, 0), default=DEFAULT_SLIDE_MIN)
    parser.add_argument("--slide-max", type=lambda value: int(value, 0), default=DEFAULT_SLIDE_MAX)
    parser.add_argument("--magic-delta", type=lambda value: int(value, 0), action="append", default=[])
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()

    stock = json.loads(args.stock_json.read_text())
    synthetic_base = int(stock["synthetic_base"], 16)
    raw = load_kernel(args.kernel)
    config = extract_ikconfig(raw)
    symbols = parse_system_map(args.system_map)
    addresses = [symbol.address for symbol in symbols]
    symbol_index = build_symbol_index(symbols)
    jopp_springboards = {
        symbol.address for symbol in symbols
        if symbol.name.startswith("jopp_springboard_blr_")
    }
    magic_addresses = find_magic_addresses(raw, synthetic_base)
    timers = parse_timer_logs(args.timer_log)
    stack_ips = parse_stack_logs(args.stack_log)
    callbacks = extract_timer_callback_candidates(args.source_root)
    deltas = args.magic_delta or list(DEFAULT_MAGIC_DELTAS)

    slide_sources = timer_magic_candidate_slides(
        timers,
        magic_addresses,
        deltas,
        args.slide_min,
        args.slide_max,
    )
    timer_candidates = [
        score_timer_slide(slide, timers, raw, synthetic_base, symbols, addresses, callbacks, deltas)
        for slide in slide_sources
    ]
    timer_candidates.sort(
        key=lambda item: (
            int(item["high_callback_weight"]),
            int(item["known_callback_weight"]),
            int(item["magic_distinct"]),
            int(item["magic_weight"]),
            bool(item["dominant_timer_magic"]),
            -abs(int(item["slide"])),
        ),
        reverse=True,
    )

    stack_candidate_slides: list[int] = []
    for name in ("__schedule", "schedule", "trace_event_raw_event_sched_switch", "perf_trace_sched_switch"):
        symbol_address = symbol_index.get(name)
        if symbol_address is None:
            continue
        for runtime_ip in stack_ips:
            slide = runtime_ip - symbol_address
            if args.slide_min <= slide <= args.slide_max:
                stack_candidate_slides.append(slide)
    for candidate in timer_candidates[:16]:
        stack_candidate_slides.append(int(candidate["slide"]))
    unique_stack_slides = sorted(set(stack_candidate_slides))
    stack_cross_check = [
        {
            "slide": slide,
            "slide_hex": format_signed_hex(slide),
            "stack": score_stack_slide(slide, stack_ips, raw, synthetic_base, symbols, addresses, jopp_springboards),
        }
        for slide in unique_stack_slides
    ]
    stack_cross_check.sort(
        key=lambda item: (
            item["stack"]["springboard_callsite_hits"],
            item["stack"]["direct_callsite_hits"],
            item["stack"]["mapped"],
        ),
        reverse=True,
    )

    best = timer_candidates[0] if timer_candidates else None
    cfp_ok = config_state(config, "CONFIG_RKP_CFP") == "y"
    jopp_ok = config_state(config, "CONFIG_RKP_CFP_JOPP") == "y"
    ropp_ok = config_state(config, "CONFIG_RKP_CFP_ROPP") == "y"
    if not (cfp_ok and jopp_ok and ropp_ok):
        decision = "v2198-classifier-blocked-config-mismatch"
        reason = "kernel config does not match expected RKP_CFP/JOPP/ROPP enabled state"
    elif not best:
        decision = "v2198-classifier-blocked-no-timer-magic-candidates"
        reason = "no timer pointer mapped to a JOPP magic target in the configured slide window"
    elif best["known_callback_weight"] == 0:
        decision = "v2198-classifier-pass-magic-only-not-authoritative"
        reason = "JOPP magic candidates exist, but none map to source-derived timer callback candidates"
    elif len([item for item in timer_candidates if item["known_callback_weight"] == best["known_callback_weight"]]) > 1:
        decision = "v2198-classifier-provisional-multiple-semantic-timer-slides"
        reason = "timer semantic candidates exist but do not uniquely select one slide"
    else:
        decision = "v2198-classifier-pass-timer-semantic-slide"
        reason = "one timer semantic slide candidate outranks all other timer-magic candidates"

    result = {
        "decision": decision,
        "reason": reason,
        "config": {
            "CONFIG_RKP_CFP": config_state(config, "CONFIG_RKP_CFP"),
            "CONFIG_RKP_CFP_JOPP": config_state(config, "CONFIG_RKP_CFP_JOPP"),
            "CONFIG_RKP_CFP_JOPP_MAGIC": config_state(config, "CONFIG_RKP_CFP_JOPP_MAGIC"),
            "CONFIG_RKP_CFP_ROPP": config_state(config, "CONFIG_RKP_CFP_ROPP"),
            "CONFIG_RKP_CFP_ROPP_SYSREGKEY": config_state(config, "CONFIG_RKP_CFP_ROPP_SYSREGKEY"),
            "CONFIG_GCC_PLUGINS": config_state(config, "CONFIG_GCC_PLUGINS"),
        },
        "inputs": {
            "system_map": str(args.system_map),
            "stock_json": str(args.stock_json),
            "kernel": str(args.kernel),
            "timer_logs": [str(path) for path in args.timer_log],
            "stack_logs": [str(path) for path in args.stack_log],
            "source_roots": [str(path) for path in args.source_root],
            "slide_min": format_signed_hex(args.slide_min),
            "slide_max": format_signed_hex(args.slide_max),
            "magic_deltas": deltas,
        },
        "jopp_magic": f"0x{JOPP_MAGIC:08x}",
        "jopp_magic_occurrences": len(magic_addresses),
        "jopp_springboard_count": len(jopp_springboards),
        "timer_count": len(timers),
        "timer_weight_total": sum(timer.count for timer in timers),
        "stack_ip_count": len(stack_ips),
        "callback_summary": {
            "scanned_files": callbacks["scanned_files"],
            "high_confidence_count": len(callbacks["high_confidence"]),
            "low_confidence_count": len(callbacks["low_confidence"]),
        },
        "top_timer_candidates": timer_candidates[:24],
        "stack_candidate_cross_check": stack_cross_check[:24],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(result))
    print(json.dumps({
        "decision": decision,
        "reason": reason,
        "jopp_magic_occurrences": len(magic_addresses),
        "top_timer_slide": None if best is None else best["slide_hex"],
        "top_known_callback_weight": None if best is None else best["known_callback_weight"],
        "top_magic_weight": None if best is None else best["magic_weight"],
        "out_json": str(args.out_json),
        "out_md": str(args.out_md) if args.out_md else None,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
