#!/usr/bin/env python3
"""Build a private Codex Security console disposition plan from exported CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_CSV = Path(
    "workspace/private/raw-logs/security/codex/2026-06-10/"
    "codex-security-findings-2026-06-10T02-46-26.267Z.csv"
)
DEFAULT_ANALYSIS = Path(
    "workspace/private/raw-logs/security/codex/2026-06-10/analysis/"
    "codex_security_reclassified_ssvc_context_v2.json"
)
DEFAULT_OUTPUT_DIR = Path("workspace/private/outputs/security/codex/2026-06-10")

AUTO_WONT_FIX_REACHABILITY = {
    "archive_only",
    "docs_only",
    "existing_non_current",
    "missing_unmapped",
}

ACTIVE_FIXED_PRIORITIES = {"P0", "P1"}

FIXED_REASON = (
    "Fixed by repository hardening commits f16efca0 and e6f58aed; "
    "V2189 local security scan and live device validation passed with FAIL=0."
)

ARCHIVED_REASON = (
    "Archived, removed, or non-current after the 2026-06-07 workspace reorg; "
    "not part of the active native-init build or runtime path."
)

ACCEPTED_RISK_REASON = (
    "Trusted local lab boundary or context-dependent finding; keep manual review "
    "instead of automatic console closure."
)

CONSOLE_LABELS_KO = {
    "fixed": "이미 수정함",
    "wont_fix": "수정하지 않았음",
    "accepted_risk": "수정하지 않았음",
    "manual_review": "수동 검토",
}


def console_context(disposition: dict[str, object], priority: str, reachability: str, remediation_class: str) -> str:
    return (
        f"{disposition['disposition_reason']} "
        f"Local triage: priority={priority}, reachability={reachability}, remediation={remediation_class}. "
        f"Evidence: {evidence_refs(priority, reachability, remediation_class)}"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file_handle:
        reader = csv.DictReader(file_handle)
        rows = []
        for row_index, row in enumerate(reader, start=2):
            row["_csv_row"] = str(row_index)
            rows.append(row)
        return rows


def read_analysis_items(path: Path) -> tuple[dict[int, dict], dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = {}
    for item in payload.get("items", []):
        row_number = item.get("row")
        if isinstance(row_number, int):
            items[row_number] = item
    return items, payload


def finding_id(finding_url: str) -> str:
    parsed = urlparse(finding_url)
    return parsed.path.rstrip("/").rsplit("/", 1)[-1]


def resolved_zones(item: dict) -> str:
    zones = []
    for resolved in item.get("resolved") or []:
        zone = resolved.get("zone")
        if zone and zone not in zones:
            zones.append(zone)
    return ",".join(zones)


def evidence_refs(priority: str, reachability: str, remediation_class: str) -> str:
    refs = [
        "docs/reports/SECURITY_CODEX_FINDINGS_TRIAGE_2026-06-10.md",
        "docs/security/scans/SECURITY_FRESH_SCAN_V2189_2026-06-10.md",
        "docs/reports/NATIVE_INIT_V2189_SECURITY_TRIAGE_REFRESH_FLASH_VALIDATION_2026-06-10.md",
    ]
    if priority == "Deferred" or reachability in AUTO_WONT_FIX_REACHABILITY:
        refs.insert(1, "docs/reports/NATIVE_INIT_ARTIFACT_LAYOUT_CLEANUP_POLICY_2026-06-07.md")
    if remediation_class == "manual_review":
        refs.append("docs/reports/NATIVE_INIT_ARCHITECTURE_REVIEW_2026-06-10.md")
    return " | ".join(refs)


def classify_disposition(item: dict, include_p2: bool) -> dict[str, object]:
    priority = str(item.get("priority") or "")
    reachability = str(item.get("reachability") or "")
    priority_reason = str(item.get("priority_reason") or "")
    remediation_class = str(item.get("remediation_class") or "")

    if priority == "Deferred" or reachability in AUTO_WONT_FIX_REACHABILITY:
        return {
            "disposition": "wont_fix",
            "disposition_bucket": "archived_or_non_current",
            "console_reason_label": "Won't fix",
            "apply_eligible": True,
            "disposition_reason": ARCHIVED_REASON,
        }

    if priority in ACTIVE_FIXED_PRIORITIES:
        return {
            "disposition": "fixed",
            "disposition_bucket": "fixed_active_security_hardening",
            "console_reason_label": "Fixed",
            "apply_eligible": True,
            "disposition_reason": FIXED_REASON,
        }

    if priority == "P2" and include_p2:
        return {
            "disposition": "accepted_risk",
            "disposition_bucket": "accepted_trusted_lab_boundary",
            "console_reason_label": "Accepted risk",
            "apply_eligible": True,
            "disposition_reason": ACCEPTED_RISK_REASON,
        }

    if priority == "P2":
        bucket = "manual_review_context_dependent"
        if "lab" in priority_reason or remediation_class == "lab_server_limits_token_bind_scope":
            bucket = "manual_review_trusted_lab_boundary"
        return {
            "disposition": "manual_review",
            "disposition_bucket": bucket,
            "console_reason_label": "Manual review",
            "apply_eligible": False,
            "disposition_reason": ACCEPTED_RISK_REASON,
        }

    return {
        "disposition": "manual_review",
        "disposition_bucket": "unclassified_manual_review",
        "console_reason_label": "Manual review",
        "apply_eligible": False,
        "disposition_reason": "Unclassified by local triage; do not close automatically.",
    }


def build_plan(rows: list[dict[str, str]], analysis_items: dict[int, dict], include_p2: bool) -> list[dict[str, object]]:
    plan = []
    for csv_row in rows:
        row_number = int(csv_row["_csv_row"])
        item = analysis_items.get(row_number, {})
        disposition = classify_disposition(item, include_p2)
        priority = str(item.get("priority") or "missing_analysis")
        reachability = str(item.get("reachability") or "missing_analysis")
        remediation_class = str(item.get("remediation_class") or "missing_analysis")
        reason = str(item.get("priority_reason") or "missing_analysis")
        url = csv_row.get("finding_url", "")
        record = {
            "row": row_number,
            "finding_id": finding_id(url),
            "finding_url": url,
            "repository": csv_row.get("repository", ""),
            "severity": csv_row.get("severity", ""),
            "current_status": csv_row.get("status", ""),
            "title": csv_row.get("title", ""),
            "priority": priority,
            "reachability": reachability,
            "priority_reason": reason,
            "remediation_class": remediation_class,
            "relevant_paths": csv_row.get("relevant_paths", ""),
            "resolved_zones": resolved_zones(item),
            "disposition": disposition["disposition"],
            "disposition_bucket": disposition["disposition_bucket"],
            "console_reason_label": disposition["console_reason_label"],
            "console_reason_label_ko": CONSOLE_LABELS_KO.get(str(disposition["disposition"]), "수동 검토"),
            "apply_eligible": bool(disposition["apply_eligible"]),
            "disposition_reason": disposition["disposition_reason"],
            "console_context": console_context(disposition, priority, reachability, remediation_class),
            "evidence_refs": evidence_refs(priority, reachability, remediation_class),
        }
        plan.append(record)
    return plan


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(plan: list[dict[str, object]], csv_path: Path, analysis_path: Path, analysis_payload: dict) -> dict[str, object]:
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_csv": str(csv_path),
        "source_csv_sha256": sha256_file(csv_path),
        "source_analysis": str(analysis_path),
        "source_analysis_sha256": sha256_file(analysis_path),
        "analysis_method_version": analysis_payload.get("method_version"),
        "total": len(plan),
        "apply_eligible": sum(1 for item in plan if item["apply_eligible"]),
        "manual_review": sum(1 for item in plan if not item["apply_eligible"]),
        "by_disposition": Counter(str(item["disposition"]) for item in plan),
        "by_bucket": Counter(str(item["disposition_bucket"]) for item in plan),
        "by_priority": Counter(str(item["priority"]) for item in plan),
        "by_reachability": Counter(str(item["reachability"]) for item in plan),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Codex Security CSV export path")
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS, help="Local triage analysis JSON path")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Private output directory")
    parser.add_argument(
        "--include-p2",
        action="store_true",
        help="Mark P2 context-dependent items as apply-eligible accepted-risk entries",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_csv_rows(args.csv)
    analysis_items, analysis_payload = read_analysis_items(args.analysis)
    plan = build_plan(rows, analysis_items, args.include_p2)
    eligible = [item for item in plan if item["apply_eligible"]]
    summary = summarize(plan, args.csv, args.analysis, analysis_payload)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    plan_json = args.out_dir / "codex_security_disposition_plan.json"
    eligible_json = args.out_dir / "codex_security_apply_plan_eligible.json"
    plan_csv = args.out_dir / "codex_security_disposition_plan.csv"
    summary_json = args.out_dir / "codex_security_disposition_plan_summary.json"

    plan_json.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    eligible_json.write_text(json.dumps(eligible, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(plan_csv, plan)
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=dict) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, default=dict))
    print(f"plan_json={plan_json}")
    print(f"eligible_json={eligible_json}")
    print(f"plan_csv={plan_csv}")
    print(f"summary_json={summary_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
