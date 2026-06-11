#!/usr/bin/env python3
"""Match V2202 timer object rows against stock symbols and source timer xrefs.

This is host-only analysis. It consumes the V2202 timer object histogram rows and
V2198 slide candidates, then asks whether any slide maps the live rows to source
patterns consistent with their object invariants. It does not set exact
symbolization; it ranks and explains.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from a90_kernel_v2198_jopp_ropp_classifier import nearest_symbol, parse_system_map  # noqa: E402
from a90_kernel_v2199_timer_xref_scorer import (  # noqa: E402
    ARM_RE,
    FUNCTION_ASSIGN_RE,
    TIMER_API_PATTERNS,
    ArmRef,
    CallbackXref,
    TimerUse,
    clean_expr,
    interval_class,
    iter_source_files,
    score_xref,
    timer_leaf,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_V2198 = REPO_ROOT / "workspace/private/runs/kernel/v2198-jopp-ropp-classifier/result.json"
DEFAULT_SYSTEM_MAP = REPO_ROOT / "workspace/private/runs/kernel/v2197-stock-kallsyms/System.map"
DEFAULT_V2202 = REPO_ROOT / "workspace/private/runs/kernel/v2202-timer-object-histogram-20260612-010308/summary.json"
DEFAULT_OUT_DIR = REPO_ROOT / "workspace/private/runs/kernel/v2203-timer-row-source-matcher"



def fast_extract_timer_xrefs(source_roots: list[Path], target_callbacks: set[str]) -> dict[str, CallbackXref]:
    xrefs: dict[str, CallbackXref] = {name: CallbackXref(name=name) for name in target_callbacks}
    source_files = iter_source_files(source_roots)
    seen_uses: set[tuple[str, str, str, str]] = set()

    for path in source_files:
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines):
            window = " ".join(lines[index:index + 5])
            if any(token in line for token in ("DEFINE_TIMER", "setup_timer", "timer_setup")):
                for api, pattern in TIMER_API_PATTERNS:
                    for match in pattern.finditer(window):
                        callback = match.group("callback")
                        if callback not in target_callbacks:
                            continue
                        timer_expr = clean_expr(match.group("timer"))
                        key = (callback, api, str(path), timer_expr)
                        if key in seen_uses:
                            continue
                        seen_uses.add(key)
                        xrefs[callback].timer_uses.append(TimerUse(
                            api=api,
                            timer_expr=timer_expr,
                            timer_leaf=timer_leaf(timer_expr),
                            callback=callback,
                            path=str(path),
                            line=index + 1,
                            context=" ".join(line.strip().split()),
                        ))
            if ".function" in line or "->function" in line:
                for match in FUNCTION_ASSIGN_RE.finditer(window):
                    callback = match.group("callback")
                    if callback not in target_callbacks:
                        continue
                    timer_expr = clean_expr(match.group("timer"))
                    key = (callback, "function_assignment", str(path), timer_expr)
                    if key in seen_uses:
                        continue
                    seen_uses.add(key)
                    xrefs[callback].timer_uses.append(TimerUse(
                        api="function_assignment",
                        timer_expr=timer_expr,
                        timer_leaf=timer_leaf(timer_expr),
                        callback=callback,
                        path=str(path),
                        line=index + 1,
                        context=" ".join(line.strip().split()),
                    ))

    wanted_timer_leaves = {
        use.timer_leaf
        for xref in xrefs.values()
        for use in xref.timer_uses
    }
    if wanted_timer_leaves:
        seen_arms: set[tuple[str, int, str, str]] = set()
        arm_refs_by_leaf: dict[str, list[ArmRef]] = {}
        for path in source_files:
            try:
                lines = path.read_text(errors="ignore").splitlines()
            except OSError:
                continue
            for index, line in enumerate(lines):
                if not any(api in line for api in ("mod_timer", "add_timer", "add_timer_on", "del_timer", "timer_pending")):
                    continue
                window = " ".join(lines[index:index + 4])
                for match in ARM_RE.finditer(window):
                    timer_expr = clean_expr(match.group("timer"))
                    leaf = timer_leaf(timer_expr)
                    if leaf not in wanted_timer_leaves:
                        continue
                    key = (str(path), index + 1, match.group("api"), timer_expr)
                    if key in seen_arms:
                        continue
                    seen_arms.add(key)
                    expires = " ".join((match.group("expires") or "").replace("\n", " ").split())
                    arm_refs_by_leaf.setdefault(leaf, []).append(ArmRef(
                        api=match.group("api"),
                        timer_expr=timer_expr,
                        timer_leaf=leaf,
                        expires=expires,
                        interval_class=interval_class(expires),
                        path=str(path),
                        line=index + 1,
                        context=" ".join(line.strip().split()),
                    ))
        for xref in xrefs.values():
            seen: set[tuple[str, int, str]] = set()
            for use in xref.timer_uses:
                for arm_ref in arm_refs_by_leaf.get(use.timer_leaf, []):
                    key = (arm_ref.path, arm_ref.line, arm_ref.api)
                    if key in seen:
                        continue
                    seen.add(key)
                    xref.arm_refs.append(arm_ref)

    return {name: xref for name, xref in xrefs.items() if xref.timer_uses or xref.arm_refs}

def parse_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value)
    if text.startswith(("0x", "0X")):
        return int(text, 16)
    return int(text, 10)


def row_signature(row: dict[str, Any]) -> dict[str, Any]:
    timeout_min = int(row.get("timeout_min", 0))
    timeout_max = int(row.get("timeout_max", 0))
    timeout_avg = int(row.get("timeout_avg", 0))
    data_delta = int(row.get("obj_data_delta", 0))
    comm = str(row.get("comm", ""))
    signature = []
    if comm.startswith("rcu"):
        signature.append("rcu_comm")
    if timeout_min <= 1 <= timeout_max:
        signature.append("has_jiffies_1")
    if timeout_avg >= 10000:
        signature.append("long_timeout")
    if data_delta < 0 and abs(data_delta) <= 4096:
        signature.append("embedded_timer_data_delta")
    if int(row.get("obj_expires_match", 0)) == int(row.get("count", 0)):
        signature.append("expires_stable")
    if int(row.get("obj_function_match", 0)) == int(row.get("count", 0)):
        signature.append("function_stable")
    return {
        "comm": comm,
        "count": int(row.get("count", 0)),
        "timeout_min": timeout_min,
        "timeout_max": timeout_max,
        "timeout_avg": timeout_avg,
        "obj_data_delta": data_delta,
        "signature": signature,
    }


def score_row_mapping(row: dict[str, Any], symbol: dict[str, Any] | None, xref_score: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    notes: list[str] = []
    if symbol is None:
        return -200, ["no symbol mapping"]

    offset = int(symbol["offset"])
    if offset == 0:
        score += 35
        notes.append("entry offset")
    elif abs(offset) <= 8:
        score += 10
        notes.append("near-entry offset")
    else:
        score -= min(80, abs(offset) // 16)
        notes.append(f"non-entry offset {offset}")

    xscore = int(xref_score.get("score", 0))
    score += min(120, xscore)
    if xscore > 0:
        notes.append(f"source xref score {xscore}")
    else:
        notes.append("no timer xref")

    sig = row_signature(row)
    name = str(symbol.get("symbol", ""))
    timer_leaves = set(xref_score.get("timer_leaves", []))
    intervals = str(xref_score.get("best_interval_class", ""))

    if "rcu_comm" in sig["signature"]:
        if "nocb_timer" in timer_leaves or "rcu" in name or "nocb" in name:
            score += 90
            notes.append("rcu row matches rcu/nocb source pattern")
        else:
            score -= 90
            notes.append("rcu row maps to non-rcu source pattern")
    if "has_jiffies_1" in sig["signature"]:
        if intervals == "jiffies_plus_1":
            score += 70
            notes.append("jiffies+1 cadence match")
        elif xscore > 0:
            score -= 20
            notes.append("jiffies+1 row lacks matching source cadence")
    if "long_timeout" in sig["signature"]:
        if intervals in {"daily", "five_minutes", "gc_seconds"}:
            score += 25
            notes.append("long-timeout row maps to long-cadence timer")
        elif intervals == "jiffies_plus_1":
            score -= 80
            notes.append("long-timeout row conflicts with jiffies+1 source")
    if "embedded_timer_data_delta" in sig["signature"]:
        if any("struct-field timer object" in note for note in xref_score.get("notes", [])):
            score += 30
            notes.append("embedded data delta matches struct-field timer")
        elif xscore > 0 and "define_timer" in xref_score.get("api_kinds", []):
            score -= 25
            notes.append("embedded data delta conflicts with simple static timer")

    if int(row.get("obj_function_match", 0)) == int(row.get("count", 0)):
        score += 10
    if int(row.get("obj_read_errors", 0)) == 0:
        score += 5
    return score, notes


def candidate_source_roots(v2198: dict[str, Any], explicit: list[Path]) -> list[Path]:
    if explicit:
        return explicit
    roots = []
    for value in v2198.get("inputs", {}).get("source_roots", []):
        path = Path(value)
        if not path.is_absolute():
            path = REPO_ROOT / path
        roots.append(path)
    return roots


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    v2198 = json.loads(args.v2198_json.read_text())
    v2202 = json.loads(args.v2202_summary.read_text())
    rows = v2202.get("histogram", {}).get("rows", [])[:args.row_limit]

    symbols = parse_system_map(args.system_map)
    addresses = [symbol.address for symbol in symbols]
    source_roots = candidate_source_roots(v2198, args.source_root)

    mapped_names: set[str] = set()
    candidate_rows: list[dict[str, Any]] = []
    for candidate in v2198.get("top_timer_candidates", []):
        slide = int(candidate.get("slide") or 0)
        for row in rows:
            runtime = parse_int(row["function"])
            static_addr = runtime - slide
            symbol = nearest_symbol(symbols, addresses, static_addr)
            if symbol:
                mapped_names.add(str(symbol["symbol"]))
            candidate_rows.append({"candidate": candidate, "row": row, "symbol": symbol, "static_addr": static_addr})

    xrefs = fast_extract_timer_xrefs(source_roots, mapped_names)

    scored_candidates: list[dict[str, Any]] = []
    for candidate in v2198.get("top_timer_candidates", []):
        slide = int(candidate.get("slide") or 0)
        row_scores = []
        weighted = 0
        hard_conflicts = 0
        rcu_row_score = None
        top_row_score = None
        for row in rows:
            runtime = parse_int(row["function"])
            static_addr = runtime - slide
            symbol = nearest_symbol(symbols, addresses, static_addr)
            xscore = score_xref(xrefs.get(str(symbol["symbol"])) if symbol else None)
            row_score, notes = score_row_mapping(row, symbol, xscore)
            count = int(row.get("count", 0))
            weighted += row_score * max(1, min(count, args.count_cap))
            if row_score < -40:
                hard_conflicts += 1
            if int(row.get("rank", -1)) == 0:
                top_row_score = row_score
            if str(row.get("comm", "")).startswith("rcu"):
                rcu_row_score = row_score
            row_scores.append({
                "rank": row.get("rank"),
                "runtime_function": row.get("function"),
                "count": count,
                "comm": row.get("comm"),
                "signature": row_signature(row),
                "static_addr": f"0x{static_addr:016x}",
                "symbol": None if symbol is None else symbol["symbol"],
                "symbol_offset": None if symbol is None else symbol["offset"],
                "xref_score": xscore,
                "row_score": row_score,
                "notes": notes,
            })
        scored_candidates.append({
            "slide": slide,
            "slide_hex": candidate.get("slide_hex"),
            "weighted_score": weighted,
            "hard_conflicts": hard_conflicts,
            "top_row_score": top_row_score,
            "rcu_row_score": rcu_row_score,
            "rows": row_scores,
        })

    scored_candidates.sort(
        key=lambda item: (item["weighted_score"], -item["hard_conflicts"], item["rcu_row_score"] or -9999),
        reverse=True,
    )
    best = scored_candidates[0] if scored_candidates else None
    second = scored_candidates[1] if len(scored_candidates) > 1 else None

    if not best:
        decision = "v2203-blocked-no-candidates"
        reason = "no V2198 candidates available"
    elif best["hard_conflicts"] > 0:
        decision = "v2203-row-matcher-no-exact-slide"
        reason = "best candidate still has hard row/object conflicts"
    elif second and best["weighted_score"] < second["weighted_score"] * 1.25:
        decision = "v2203-row-matcher-provisional-not-unique"
        reason = "row matcher did not create enough margin"
    else:
        decision = "v2203-row-matcher-provisional-lead"
        reason = "row matcher produced a source-backed lead, still not exact symbolization"

    return {
        "decision": decision,
        "reason": reason,
        "inputs": {
            "v2198_json": str(args.v2198_json),
            "v2202_summary": str(args.v2202_summary),
            "system_map": str(args.system_map),
            "source_roots": [str(path) for path in source_roots],
        },
        "source_files_scanned": len(iter_source_files(source_roots)),
        "mapped_symbol_count": len(mapped_names),
        "xref_count": len(xrefs),
        "row_count": len(rows),
        "top_candidates": scored_candidates[:args.top_candidates],
        "interpretation": (
            "This is a row/object pattern matcher. It ranks slide candidates against V2202 raw rows, "
            "but it does not authorize exact symbol labels unless object invariants and source xrefs agree."
        ),
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# A90 V2203 Timer Row Source Matcher",
        "",
        "## Decision",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Reason: {result['reason']}",
        f"- Rows analyzed: `{result['row_count']}`",
        f"- Source files scanned: `{result['source_files_scanned']}`",
        f"- Xrefs found: `{result['xref_count']}`",
        "",
        "## Top Candidates",
        "",
    ]
    for candidate in result["top_candidates"][:8]:
        lines.append(
            f"- slide `{candidate['slide_hex']}`: weighted={candidate['weighted_score']}, "
            f"conflicts={candidate['hard_conflicts']}, top_row={candidate['top_row_score']}, "
            f"rcu_row={candidate['rcu_row_score']}"
        )
        for row in candidate["rows"][:4]:
            lines.append(
                f"  - row{row['rank']} `{row['runtime_function']}` comm={row['comm']} count={row['count']} -> "
                f"`{row['symbol']}`+{row['symbol_offset']}, score={row['row_score']}, "
                f"notes={'; '.join(row['notes'][:3])}"
            )
    lines.extend([
        "",
        "## Interpretation",
        "",
        result["interpretation"],
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2198-json", type=Path, default=DEFAULT_V2198)
    parser.add_argument("--v2202-summary", type=Path, default=DEFAULT_V2202)
    parser.add_argument("--system-map", type=Path, default=DEFAULT_SYSTEM_MAP)
    parser.add_argument("--source-root", type=Path, action="append", default=[])
    parser.add_argument("--row-limit", type=int, default=8)
    parser.add_argument("--count-cap", type=int, default=200)
    parser.add_argument("--top-candidates", type=int, default=16)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_DIR / "result.json")
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_DIR / "result.md")
    args = parser.parse_args()

    result = analyze(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_markdown(result) + "\n")
    best = result["top_candidates"][0] if result["top_candidates"] else {}
    print(json.dumps({
        "decision": result["decision"],
        "reason": result["reason"],
        "top_slide": best.get("slide_hex"),
        "top_score": best.get("weighted_score"),
        "top_conflicts": best.get("hard_conflicts"),
        "out_json": str(args.out_json),
        "out_md": str(args.out_md),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
