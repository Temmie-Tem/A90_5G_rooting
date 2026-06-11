#!/usr/bin/env python3
"""Rescore V2198 timer slide candidates with source-level timer xrefs.

This is host-only analysis.  It does not try to prove a KASLR slide from JOPP
magic alone.  It takes the V2198 timer-magic candidates and adds source-derived
evidence:

* the candidate symbol is wired to a timer API,
* the timer object that uses it is actually armed,
* the arm cadence is plausible for the observed timer_start frequency,
* stack/callsite evidence remains non-authoritative unless it cross-confirms.

The output is intentionally a ranking and not a forced exact-symbolization
claim.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SOURCE_SUFFIXES = {".c", ".h"}
SKIP_TOP_LEVEL_DIRS = {"Documentation", "samples", "tools", "usr"}
IDENT = r"[A-Za-z_][A-Za-z0-9_]*"

TIMER_API_PATTERNS = (
    ("define_timer", re.compile(r"\bDEFINE_TIMER\s*\(\s*(?P<timer>" + IDENT + r")\s*,\s*&?\s*(?P<callback>" + IDENT + r")", re.S)),
    ("setup_timer", re.compile(r"\bsetup_timer\s*\(\s*(?P<timer>[^,]+?)\s*,\s*&?\s*(?P<callback>" + IDENT + r")", re.S)),
    ("timer_setup", re.compile(r"\btimer_setup\s*\(\s*(?P<timer>[^,]+?)\s*,\s*&?\s*(?P<callback>" + IDENT + r")", re.S)),
)
FUNCTION_ASSIGN_RE = re.compile(r"(?P<timer>[A-Za-z_][A-Za-z0-9_]*(?:\s*(?:->|\.)\s*[A-Za-z_][A-Za-z0-9_]*)?)\s*(?:->|\.)\s*function\s*=\s*&?\s*(?P<callback>" + IDENT + r")", re.S)
FUNCTION_DEF_RE = re.compile(
    r"\b(?P<prefix>(?:static\s+)?(?:inline\s+)?(?:noinline\s+)?"
    r"(?:void|int|long|enum\s+" + IDENT + r"|struct\s+" + IDENT + r"\s*\*)"
    r"[\w\s\*]*)\b(?P<callback>" + IDENT + r")\s*\(",
    re.S,
)
ARM_RE = re.compile(r"\b(?P<api>mod_timer|add_timer|add_timer_on|del_timer|del_timer_sync|timer_pending)\s*\(\s*(?P<timer>[^,);\n]+)(?:\s*,\s*(?P<expires>[^;\n]+))?", re.S)
RKP_ADDR_TAKEN = "scripts/rkp_cfp/addr_taken_func"


@dataclass
class SourceRef:
    path: str
    line: int
    text: str


@dataclass
class TimerUse:
    api: str
    timer_expr: str
    timer_leaf: str
    callback: str
    path: str
    line: int
    context: str


@dataclass
class ArmRef:
    api: str
    timer_expr: str
    timer_leaf: str
    expires: str
    interval_class: str
    path: str
    line: int
    context: str


@dataclass
class CallbackXref:
    name: str
    timer_uses: list[TimerUse] = field(default_factory=list)
    arm_refs: list[ArmRef] = field(default_factory=list)
    definitions: list[SourceRef] = field(default_factory=list)
    rkp_addr_taken: bool = False


def format_signed_hex(value: int) -> str:
    if value < 0:
        return f"-0x{-value:x}"
    return f"0x{value:x}"


def iter_source_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            try:
                rel_parts = path.relative_to(root).parts
            except ValueError:
                rel_parts = path.parts
            if not rel_parts:
                continue
            if rel_parts[0] in SKIP_TOP_LEVEL_DIRS:
                continue
            if rel_parts[0] == "arch" and len(rel_parts) > 1 and rel_parts[1] != "arm64":
                continue
            if path.suffix in SOURCE_SUFFIXES and path.is_file():
                files.append(path)
    return files


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def line_text(text: str, offset: int) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end < 0:
        end = len(text)
    return " ".join(text[start:end].strip().split())


def clean_expr(expr: str) -> str:
    expr = " ".join(expr.replace("\n", " ").split())
    expr = expr.strip()
    if expr.startswith("&"):
        expr = expr[1:].strip()
    return expr


def timer_leaf(expr: str) -> str:
    expr = clean_expr(expr)
    matches = re.findall(IDENT, expr)
    return matches[-1] if matches else expr


def interval_class(expires: str) -> str:
    compact = re.sub(r"\s+", "", expires or "")
    if not compact:
        return "none"
    if "jiffies+1" in compact:
        return "jiffies_plus_1"
    if "POLL_SPURIOUS_IRQ_INTERVAL" in expires or "HZ/10" in compact or "HZ/ 10" in expires:
        return "short_poll"
    if "24*60*60*HZ" in compact:
        return "daily"
    if "300*HZ" in compact:
        return "five_minutes"
    if "t_expires" in expires:
        return "journal_transaction_expiry"
    if "gc_at-now" in compact or "key_gc" in compact:
        return "gc_seconds"
    if "HZ" in expires:
        return "hz_relative"
    if "jiffies" in expires:
        return "jiffies_relative"
    return "variable"


def extract_source_xrefs(source_roots: list[Path], target_callbacks: set[str]) -> dict[str, CallbackXref]:
    target_callbacks = {name for name in target_callbacks if len(name) >= 3}
    xrefs: dict[str, CallbackXref] = {name: CallbackXref(name=name) for name in sorted(target_callbacks)}
    source_files = iter_source_files(source_roots)
    seen_uses: set[tuple[str, str, str, int, str]] = set()
    seen_defs: set[tuple[str, str, int]] = set()

    for path in source_files:
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        text = "\n".join(lines)

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

            for callback in target_callbacks:
                if callback not in line:
                    continue
                if not re.search(r"\b" + re.escape(callback) + r"\s*\(", line):
                    continue
                if not re.search(r"\b(static|void|int|long|enum|struct|noinline|inline)\b", line):
                    continue
                key = (callback, str(path), index + 1)
                if key in seen_defs:
                    continue
                seen_defs.add(key)
                xrefs[callback].definitions.append(SourceRef(
                    path=str(path),
                    line=index + 1,
                    text=" ".join(line.strip().split()),
                ))

    wanted_timer_leaves = {
        use.timer_leaf
        for xref in xrefs.values()
        for use in xref.timer_uses
    }
    arm_refs_by_leaf: dict[str, list[ArmRef]] = defaultdict(list)
    seen_arms: set[tuple[str, int, str, str]] = set()
    if wanted_timer_leaves:
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
                    expires = " ".join((match.group("expires") or "").replace("\n", " ").split())
                    key = (str(path), index + 1, match.group("api"), timer_expr)
                    if key in seen_arms:
                        continue
                    seen_arms.add(key)
                    arm_refs_by_leaf[leaf].append(ArmRef(
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

    for root in source_roots:
        addr_taken = root / RKP_ADDR_TAKEN
        if not addr_taken.exists():
            continue
        names = set(addr_taken.read_text(errors="ignore").split())
        for name in names:
            if name in xrefs:
                xrefs[name].rkp_addr_taken = True

    return {name: xref for name, xref in xrefs.items() if xref.timer_uses or xref.definitions or xref.rkp_addr_taken}


def interval_score(interval: str) -> int:
    if interval == "jiffies_plus_1":
        return 140
    if interval == "short_poll":
        return 75
    if interval == "journal_transaction_expiry":
        return 45
    if interval == "jiffies_relative":
        return 35
    if interval == "hz_relative":
        return 25
    if interval == "gc_seconds":
        return -35
    if interval == "five_minutes":
        return -45
    if interval == "daily":
        return -80
    return 0


def score_xref(xref: CallbackXref | None) -> dict[str, Any]:
    if xref is None:
        return {
            "score": 0,
            "best_interval_class": "none",
            "api_kinds": [],
            "timer_leaves": [],
            "arm_count": 0,
            "definition_count": 0,
            "rkp_addr_taken": False,
            "notes": ["no source timer xref"],
            "uses": [],
            "arms": [],
        }

    api_kinds = sorted({use.api for use in xref.timer_uses})
    timer_leaves = sorted({use.timer_leaf for use in xref.timer_uses})
    intervals = [arm.interval_class for arm in xref.arm_refs]
    best_interval = max(intervals, key=interval_score) if intervals else "none"

    score = 0
    notes: list[str] = []
    if "setup_timer" in api_kinds or "timer_setup" in api_kinds:
        score += 85
        notes.append("explicit runtime timer setup")
    if "define_timer" in api_kinds:
        score += 65
        notes.append("static DEFINE_TIMER")
    if "function_assignment" in api_kinds:
        score += 25
        notes.append("direct function assignment")
    if any("->" in use.timer_expr or "." in use.timer_expr for use in xref.timer_uses):
        score += 30
        notes.append("struct-field timer object")
    if xref.arm_refs:
        score += min(40, len(xref.arm_refs) * 10)
        notes.append("timer object has arm/delete references")
    if intervals:
        interval_bonus = max(interval_score(name) for name in intervals)
        score += interval_bonus
        notes.append(f"best interval {best_interval} score {interval_bonus}")
    if xref.definitions:
        score += 10
    if xref.rkp_addr_taken:
        score += 5
    if len(timer_leaves) == 1 and timer_leaves[0] in {"s_err_report", "key_gc_timer"}:
        score -= 30
        notes.append("low-cadence known timer object")
    if len(timer_leaves) == 1 and timer_leaves[0] == "nocb_timer":
        score += 45
        notes.append("RCU no-CB per-cpu timer object")

    return {
        "score": score,
        "best_interval_class": best_interval,
        "api_kinds": api_kinds,
        "timer_leaves": timer_leaves,
        "arm_count": len(xref.arm_refs),
        "definition_count": len(xref.definitions),
        "rkp_addr_taken": xref.rkp_addr_taken,
        "notes": notes,
        "uses": [use.__dict__ for use in xref.timer_uses[:8]],
        "arms": [arm.__dict__ for arm in xref.arm_refs[:12]],
        "definitions": [ref.__dict__ for ref in xref.definitions[:4]],
    }


def score_candidate(candidate: dict[str, Any], xrefs: dict[str, CallbackXref]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    weighted_score = 0
    dominant_score = 0
    non_callback_magic_penalty = 0

    for row in candidate.get("timer_rows", []):
        if not row.get("magic_deltas"):
            continue
        symbol = row.get("symbol") or ""
        count = int(row.get("count") or 0)
        offset = int(row.get("symbol_offset") or 0)
        xref_score = score_xref(xrefs.get(symbol))
        offset_penalty = 0 if offset == 0 else 20
        row_score = max(0, int(xref_score["score"]) - offset_penalty)
        if xref_score["score"] == 0:
            non_callback_magic_penalty += count * 25
        weighted_score += count * row_score
        if int(row.get("index") or 0) == 0:
            dominant_score = row_score
        rows.append({
            "timer_index": row.get("index"),
            "runtime": row.get("runtime"),
            "count": count,
            "symbol": symbol,
            "symbol_offset": offset,
            "magic_deltas": row.get("magic_deltas", []),
            "xref_score": xref_score,
            "offset_penalty": offset_penalty,
            "row_score": row_score,
        })

    final_score = weighted_score - non_callback_magic_penalty
    return {
        "slide": candidate.get("slide"),
        "slide_hex": candidate.get("slide_hex"),
        "v2198_known_callback_weight": candidate.get("known_callback_weight"),
        "v2198_magic_weight": candidate.get("magic_weight"),
        "dominant_xref_score": dominant_score,
        "weighted_xref_score": weighted_score,
        "non_callback_magic_penalty": non_callback_magic_penalty,
        "final_score": final_score,
        "rows": rows,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# A90 V2199 Timer Xref Slide Scorer",
        "",
        "## Decision",
        "",
        f"- Decision: `{result['decision']}`",
        f"- Reason: {result['reason']}",
        "",
        "## Scope",
        "",
        f"- Candidate scope: `{result['candidate_scope']}`",
        f"- Source files scanned: `{result['source_files_scanned']}`",
        f"- Callback xrefs: `{result['callback_xref_count']}`",
        "",
        "## Top Xref Candidates",
        "",
    ]
    for candidate in result["top_candidates"][:10]:
        lines.append(
            f"- slide `{candidate['slide_hex']}`: final={candidate['final_score']}, "
            f"dominant={candidate['dominant_xref_score']}, weighted={candidate['weighted_xref_score']}, "
            f"penalty={candidate['non_callback_magic_penalty']}"
        )
        for row in candidate["rows"][:4]:
            xref = row["xref_score"]
            lines.append(
                f"  - timer{row['timer_index']} `{row['runtime']}` count={row['count']} -> "
                f"`{row['symbol']}`+0x{row['symbol_offset']:x}, row_score={row['row_score']}, "
                f"apis={xref['api_kinds']}, leaves={xref['timer_leaves']}, "
                f"interval={xref['best_interval_class']}"
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
    parser.add_argument("--v2198-json", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, action="append", default=[])
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()

    v2198 = json.loads(args.v2198_json.read_text())
    target_callbacks = {
        row.get("symbol", "")
        for candidate in v2198.get("top_timer_candidates", [])
        for row in candidate.get("timer_rows", [])
        if row.get("magic_deltas")
    }
    xrefs = extract_source_xrefs(args.source_root, target_callbacks)
    candidates = [
        score_candidate(candidate, xrefs)
        for candidate in v2198.get("top_timer_candidates", [])
    ]
    candidates.sort(
        key=lambda item: (
            int(item["final_score"]),
            int(item["dominant_xref_score"]),
            int(item["weighted_xref_score"]),
            -abs(int(item["slide"] or 0)),
        ),
        reverse=True,
    )

    best = candidates[0] if candidates else None
    second = candidates[1] if len(candidates) > 1 else None
    if not best:
        decision = "v2199-blocked-no-candidates"
        reason = "V2198 result contained no timer candidates"
        interpretation = "No host-only xref decision is possible without V2198 candidates."
    elif second and best["final_score"] <= second["final_score"]:
        decision = "v2199-provisional-xref-tie"
        reason = "source xref scoring did not separate the best candidate"
        interpretation = "The source xref scorer did not improve slide uniqueness."
    elif second and best["final_score"] < second["final_score"] * 1.25:
        decision = "v2199-provisional-xref-lead-not-authority"
        reason = "source xref scoring produced a lead, but not enough margin for exact symbolization"
        interpretation = (
            "The top candidate is more plausible than V2198's magic-only output, "
            "but the margin is not strong enough to set exact_symbolization=true."
        )
    else:
        decision = "v2199-xref-lead-provisional-slide"
        reason = "source xref scoring selects one dominant timer slide candidate"
        interpretation = (
            "The source xref scorer creates a strong timer-semantic lead. This is still "
            "a semantic lead, not an exact slide proof, until stack or same-boot timer_start "
            "caller evidence cross-confirms it."
        )

    source_files = len(iter_source_files(args.source_root))
    result = {
        "decision": decision,
        "reason": reason,
        "candidate_scope": "V2198 top_timer_candidates",
        "source_roots": [str(path) for path in args.source_root],
        "source_files_scanned": source_files,
        "callback_xref_count": len(xrefs),
        "top_candidates": candidates[:24],
        "interpretation": interpretation,
        "inputs": {
            "v2198_json": str(args.v2198_json),
        },
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(result) + "\n")
    print(json.dumps({
        "decision": decision,
        "reason": reason,
        "top_slide": None if best is None else best["slide_hex"],
        "top_score": None if best is None else best["final_score"],
        "second_slide": None if second is None else second["slide_hex"],
        "second_score": None if second is None else second["final_score"],
        "out_json": str(args.out_json),
        "out_md": str(args.out_md) if args.out_md else None,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
