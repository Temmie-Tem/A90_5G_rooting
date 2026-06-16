#!/usr/bin/env python3
"""V2594 host-only RE for send_audio_cal_v5 pre-first-GET geometry.

No device action. Reads the private stock libacdbloader.so, maps PLT calls in
acdb_loader_send_audio_cal_v5(), and pins the first dispatcher query reached
before per-device subcalls. The resulting report is metadata-only; proprietary
binary/disassembly output stays under workspace/private.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2594"
BUILD_TAG = "v2594-acdb-send-audio-cal-preget-geometry-re"
DEFAULT_LIB = ROOT / "workspace/private/inputs/audio/acdb-deps-v2506/vendor-lib/libacdbloader.so"
DEFAULT_OUT_DIR = ROOT / "workspace/private/runs/audio/v2594-send-audio-cal-preget-recon"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2594_AUDIO_ACDB_SEND_AUDIO_CAL_PREGET_GEOMETRY_RE_2026-06-16.md"
DEFAULT_LLVM_OBJDUMP = ROOT / "workspace/private/inputs/toolchains/llvm-arm-toolchain-ship-10.0/bin/llvm-objdump"
DEFAULT_LLVM_READELF = ROOT / "workspace/private/inputs/toolchains/llvm-arm-toolchain-ship-10.0/bin/llvm-readelf"
SEND_AUDIO_CAL_START = 0x9D30
SEND_AUDIO_CAL_STOP = 0xA010
FIRST_DISPATCH_CMD = 0x1122E
FIRST_DISPATCH_ADDR = 0x9E86
FIRST_DISPATCH_INBUF_STORE_ADDR = 0x9E42
FIRST_DISPATCH_INBUF_WORD = 0x11135
FIRST_DISPATCH_IN_LEN = 4
FIRST_DISPATCH_OUT_LEN = 4

CALL_RE = re.compile(r"^\s*([0-9a-fA-F]+):.*\b(blx?|b\.w)\s+#(-?\d+)")
RELOC_RE = re.compile(r"^([0-9a-fA-F]+)\s+\S+\s+R_ARM_JUMP_SLOT\s+\S+\s+(.+?)\s*$")
PLT_ADDR_RE = re.compile(r"^\s*([0-9a-fA-F]+):")
SYMBOL_RE = re.compile(r"^\s*\d+:\s+([0-9a-fA-F]+)\s+(\d+)\s+FUNC\s+\S+\s+\S+\s+(\S+)\s+(.+?)\s*$")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, env=env, timeout=60)
    return {"cmd": cmd, "rc": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "ok": proc.returncode == 0}


def parse_jump_slots(readelf_relocs: str) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for line in readelf_relocs.splitlines():
        match = RELOC_RE.match(line)
        if not match:
            continue
        name = match.group(2).split("@", 1)[0].strip()
        slots.append({"got_offset": int(match.group(1), 16), "symbol": name})
    return slots


def parse_plt_entries(plt_disasm: str) -> list[int]:
    instruction_addrs: list[int] = []
    for line in plt_disasm.splitlines():
        match = PLT_ADDR_RE.match(line)
        if not match:
            continue
        addr = int(match.group(1), 16)
        if addr >= 0x159F0:
            instruction_addrs.append(addr)
    if not instruction_addrs:
        return []
    first_entry = instruction_addrs[0]
    return [addr for addr in instruction_addrs if (addr - first_entry) % 0x10 == 0]


def map_plt(readelf_relocs: str, plt_disasm: str) -> dict[int, str]:
    slots = parse_jump_slots(readelf_relocs)
    entries = parse_plt_entries(plt_disasm)
    mapping: dict[int, str] = {}
    for index, slot in enumerate(slots):
        if index < len(entries):
            mapping[entries[index]] = slot["symbol"]
    return mapping


def parse_symbols(readelf_symbols: str) -> list[dict[str, Any]]:
    symbols: list[dict[str, Any]] = []
    for line in readelf_symbols.splitlines():
        match = SYMBOL_RE.match(line)
        if not match:
            continue
        ndx = match.group(3)
        if ndx == "UND":
            continue
        name = match.group(4).split("@", 1)[0].strip()
        symbols.append({"addr": int(match.group(1), 16), "size": int(match.group(2)), "name": name})
    return sorted(symbols, key=lambda item: item["addr"])


def nearest_symbol(addr: int, symbols: list[dict[str, Any]]) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for symbol in symbols:
        start = int(symbol["addr"])
        size = int(symbol["size"])
        end = start + max(size, 1)
        if start <= addr < end:
            return {**symbol, "offset": addr - start, "contains": True}
        if start <= addr:
            best = symbol
        else:
            break
    if best:
        return {**best, "offset": addr - int(best["addr"]), "contains": False}
    return None


def resolve_plt_target(dest: int, plt: dict[int, str]) -> tuple[int | None, str | None]:
    if not plt:
        return None, None
    best_addr = min(plt, key=lambda addr: abs(addr - dest))
    if abs(best_addr - dest) <= 4:
        return best_addr, plt[best_addr]
    return None, None


def parse_calls(function_disasm: str, plt: dict[int, str], symbols: list[dict[str, Any]]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for line in function_disasm.splitlines():
        match = CALL_RE.match(line)
        if not match:
            continue
        addr = int(match.group(1), 16)
        imm = int(match.group(3), 10)
        dest = addr + 4 + imm
        plt_addr, import_symbol = resolve_plt_target(dest, plt)
        symbol = None if import_symbol else nearest_symbol(dest, symbols)
        calls.append(
            {
                "call_addr": f"0x{addr:04x}",
                "instruction": match.group(2),
                "immediate": imm,
                "dest": f"0x{dest:04x}",
                "plt_addr": f"0x{plt_addr:04x}" if plt_addr is not None else None,
                "import_symbol": import_symbol,
                "local_symbol": None if symbol is None else symbol["name"],
                "local_offset": None if symbol is None else f"0x{int(symbol['offset']):x}",
                "local_contains": None if symbol is None else bool(symbol["contains"]),
                "before_first_dispatch": addr < FIRST_DISPATCH_ADDR,
            }
        )
    return calls


def make_payload(args: argparse.Namespace) -> dict[str, Any]:
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    env = None
    relib = ROOT / "tmp/relibs"
    if relib.exists():
        env = {**dict(__import__("os").environ), "LD_LIBRARY_PATH": str(relib)}

    if not args.lib.exists():
        return {"ok": False, "error": f"missing private lib: {rel(args.lib)}"}

    reloc = run([str(args.readelf), "-r", str(args.lib)], env=env)
    sym = run([str(args.readelf), "-Ws", str(args.lib)], env=env)
    plt_dis = run([str(args.objdump), "-d", "--section=.plt", str(args.lib)], env=env)
    func_dis = run(
        [
            str(args.objdump),
            "-d",
            "--triple=thumbv7-linux-android",
            f"--start-address=0x{SEND_AUDIO_CAL_START:x}",
            f"--stop-address=0x{SEND_AUDIO_CAL_STOP:x}",
            str(args.lib),
        ],
        env=env,
    )
    for name, result in {"relocations": reloc, "symbols": sym, "plt": plt_dis, "function": func_dis}.items():
        (out_dir / f"{name}.stdout.txt").write_text(result["stdout"], encoding="utf-8", errors="replace")
        (out_dir / f"{name}.stderr.txt").write_text(result["stderr"], encoding="utf-8", errors="replace")

    if not all(result["ok"] for result in (reloc, sym, plt_dis, func_dis)):
        return {
            "ok": False,
            "error": "tool failure",
            "tool_results": {"relocations": reloc["rc"], "symbols": sym["rc"], "plt": plt_dis["rc"], "function": func_dis["rc"]},
        }

    plt = map_plt(reloc["stdout"], plt_dis["stdout"])
    symbols = parse_symbols(sym["stdout"])
    calls = parse_calls(func_dis["stdout"], plt, symbols)
    before_dispatch = [call for call in calls if call["before_first_dispatch"]]
    first_dispatch_call = next((call for call in calls if call["call_addr"] == f"0x{FIRST_DISPATCH_ADDR:04x}"), None)
    imported_before = [call for call in before_dispatch if call.get("import_symbol")]
    local_before = [call for call in before_dispatch if not call.get("import_symbol")]
    direct_get = {
        "cmd": f"0x{FIRST_DISPATCH_CMD:05x}",
        "call_addr": f"0x{FIRST_DISPATCH_ADDR:04x}",
        "in_len": FIRST_DISPATCH_IN_LEN,
        "out_len": FIRST_DISPATCH_OUT_LEN,
        "inbuf_first_word": f"0x{FIRST_DISPATCH_INBUF_WORD:05x}",
        "inbuf_first_word_source": "r8 = send_audio_cal_v5 arg3 app_id; stored to [sp,#80] at 0x9e42",
        "safe_direct_probe": "post-init acdb_ioctl(0x1122e, &app_id, 4, &out_word, 4), no AUDIO_SET_CALIBRATION",
    }
    decision = "v2594-send-audio-cal-v5-first-dispatch-geometry-pinned"
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": decision,
        "host_only": True,
        "device_action": "none",
        "private_inputs": {"libacdbloader": rel(args.lib), "scratch": rel(out_dir)},
        "call_scan": {
            "function": "acdb_loader_send_audio_cal_v5",
            "range": [f"0x{SEND_AUDIO_CAL_START:x}", f"0x{SEND_AUDIO_CAL_STOP:x}"],
            "calls": calls,
            "before_first_dispatch": before_dispatch,
            "imported_before_first_dispatch": imported_before,
            "local_before_first_dispatch": local_before,
            "first_dispatch_call": first_dispatch_call,
        },
        "direct_get_geometry": direct_get,
        "next_unit": {
            "recommended": "V2595 build direct 0x1122e metadata probe before more send_audio_cal_v5 variants",
            "reason": "V2593 timed out before any real acdb_ioctl row; the first row is a pure-read metadata query with 4-byte in/out geometry now pinned from disassembly.",
            "fallback": "If 0x1122e returns valid metadata, derive subsequent per-device GET request structs; if it fails, build an armed import-call tracer around send_audio_cal_v5.",
        },
        "boundary": {
            "no_live": True,
            "no_set": True,
            "no_native_replay": True,
            "raw_payload_private_only": True,
        },
    }
    payload["ok"] = bool(
        first_dispatch_call
        and first_dispatch_call.get("import_symbol") == "acdb_ioctl"
        and direct_get["cmd"] == "0x1122e"
        and len(local_before) >= 1
    )
    (out_dir / "v2594-preget-recon.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def write_report(path: Path, payload: dict[str, Any]) -> None:
    calls = payload.get("call_scan", {})
    imported = calls.get("imported_before_first_dispatch", [])
    local = calls.get("local_before_first_dispatch", [])
    direct = payload.get("direct_get_geometry", {})
    lines = [
        "# NATIVE_INIT V2594 — ACDB send_audio_cal_v5 pre-GET geometry RE",
        "",
        "Date: 2026-06-16",
        "",
        "## Scope",
        "",
        "Host-only RE after V2593. No Android handoff, native replay `SET`, speaker write,",
        "ACDB command execution, or raw payload publication was performed. Proprietary disassembly",
        f"and JSON scratch stay private under `{payload.get('private_inputs', {}).get('scratch')}`.",
        "",
        "## Decision",
        "",
        f"- decision: `{payload.get('decision')}`",
        f"- ok: `{payload.get('ok')}`",
        "- V2593 closed corrected stack-arg order as insufficient: `send_audio_cal_v5` still timed out before any real armed `acdb_ioctl` row.",
        "- This unit pins the first dispatcher row geometry so the next unit can bypass the hanging local setup path with a pure-read metadata probe.",
        "",
        "## Pre-first-dispatch Calls",
        "",
        "Imported calls before the first `acdb_ioctl` dispatcher row:",
    ]
    for call in imported:
        lines.append(f"- `{call['call_addr']}` -> `{call['import_symbol']}` via PLT `{call['plt_addr']}`")
    lines.extend(["", "Local/internal calls before the first dispatcher row:"])
    for call in local:
        sym = call.get("local_symbol") or "unknown"
        off = call.get("local_offset") or "?"
        lines.append(f"- `{call['call_addr']}` -> `{call['dest']}` (`{sym}+{off}`, contains={call.get('local_contains')})")
    lines.extend(
        [
            "",
            "The first dispatcher call itself is the `acdb_ioctl` PLT call at `0x9e86`. V2593 saw zero real",
            "armed rows, so the live stall is before or at the local setup that precedes this call, not in later",
            "AFE/AUDPROC/VOL handlers.",
            "",
            "## Direct Metadata GET Geometry",
            "",
            f"- command: `{direct.get('cmd')}`",
            f"- call site: `{direct.get('call_addr')}`",
            f"- `in_len`: `{direct.get('in_len')}`",
            f"- `out_len`: `{direct.get('out_len')}`",
            f"- first input word: `{direct.get('inbuf_first_word')}`",
            f"- input source: {direct.get('inbuf_first_word_source')}",
            "- proposed pure-read probe: `acdb_ioctl(0x1122e, &app_id, 4, &out_word, 4)` after ACDB init and before any `send_audio_cal_v5` call.",
            "- boundary: no `AUDIO_SET_CALIBRATION`, no native replay SET, no speaker write.",
            "",
            "## Interpretation",
            "",
            "The corrected `send_audio_cal_v5(15, 1, 0x11135, 48000, 0, 48000, 1)` call still depends on local",
            "state/list setup before it can issue its first ACDB dispatcher row. The direct `0x1122e` metadata",
            "query is safer and higher-signal than another argument variant because it exercises the first pinned",
            "pure-read row without entering the hanging local setup path or the later SET path.",
            "",
            "## Next Unit",
            "",
            "Build V2595 as a host-only source/build unit for a post-init direct `0x1122e` metadata probe:",
            "",
            "1. reuse the own-process Android-good helper and fake-allocate preload;",
            "2. initialize ACDB normally and keep the zero-buffer discriminator;",
            "3. call only `acdb_ioctl(0x1122e, &app_id, 4, &out_word, 4)` with `app_id=0x11135`;",
            "4. record `{ret,out_word,sha/all-zero}` privately/metadata-only;",
            "5. do not issue `send_audio_cal_v5` or any `/dev/msm_audio_cal` SET in that unit.",
            "",
            "If V2595 returns valid metadata, use that value to derive the subsequent per-device pure-read request",
            "structs. If it fails, fall back to an armed import-call tracer around `send_audio_cal_v5` to identify",
            "which internal pre-`0x1122e` helper stalls.",
            "",
            "## Validation",
            "",
            "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_send_audio_cal_preget_recon_v2594.py tests/test_native_audio_acdb_send_audio_cal_preget_recon_v2594.py`",
            "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_native_audio_acdb_send_audio_cal_preget_recon_v2594`",
            "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/native_audio_acdb_send_audio_cal_preget_recon_v2594.py --write-report`",
            "- `git diff --check`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lib", type=Path, default=DEFAULT_LIB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--objdump", type=Path, default=DEFAULT_LLVM_OBJDUMP)
    parser.add_argument("--readelf", type=Path, default=DEFAULT_LLVM_READELF)
    parser.add_argument("--write-report", action="store_true")
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
