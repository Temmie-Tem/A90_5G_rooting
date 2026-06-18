#!/usr/bin/env python3
"""V2687 host-only classifier for V2686 ACDB topology rejection.

The V2686 live run proved the native SET replay layer works but the ADSP rejects
ASM_CMD_ADD_TOPOLOGIES with ADSP_EBADPARAM. This script inspects the exact V2684
payloads used in that run, classifies their topology/module contents against the
stock audio techpack source, and optionally writes private sanitized candidates
that remove module IDs absent from the source-derived module definition table.

No device action or calibration ioctl is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import analyze_audio_acdb_core_topology_bridge_v2683 as v2683

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2687"
DEFAULT_MANIFEST = ROOT / "workspace/private/builds/audio/v2684-acdb-core-topology-replay-deploy-plan/deploy-plan.json"
DEFAULT_V2686_DMESG = ROOT / "workspace/private/runs/audio/v2639-acdb-setcal-replay-20260618-160730/64_dmesg-after-setcal-playback-failure-before-reset.txt"
DEFAULT_SOURCE_ROOT = ROOT / "tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/techpack/audio"
DEFAULT_PRIVATE_DIR = ROOT / "workspace/private/builds/audio/v2687-acdb-topology-rejection-candidates"
DEFAULT_REPORT = ROOT / "docs/reports/NATIVE_INIT_V2687_AUDIO_ACDB_TOPOLOGY_REJECTION_CLASSIFIER_2026-06-18.md"
TARGET_CAL_TYPES = {10, 14, 24}


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: dict[str, Any], mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def path_from_manifest_local(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def load_module_definitions(source_root: Path) -> dict[int, dict[str, Any]]:
    """Return source-known module IDs from all audio headers.

    The V2683 helper only used apr_audio-v2.h, which missed Samsung adaptation
    modules in sec_adaptation.h. V2687 intentionally scans the wider techpack
    audio include tree so "undefined" really means absent from the available
    stock audio source drop.
    """

    definitions: dict[int, dict[str, Any]] = {}
    pattern = re.compile(r"^\s*#define\s+([A-Za-z0-9_]*MODULE[A-Za-z0-9_]*)\s+\(?\s*(0x[0-9A-Fa-f]+|[0-9]+)\s*\)?\b")
    for header in sorted(source_root.rglob("*.h")):
        text = header.read_text(errors="ignore")
        for line_no, line in enumerate(text.splitlines(), 1):
            match = pattern.match(line)
            if not match:
                continue
            name, raw = match.groups()
            try:
                value = int(raw, 0)
            except ValueError:
                continue
            entry = definitions.setdefault(value, {"names": [], "locations": []})
            if name not in entry["names"]:
                entry["names"].append(name)
            location = f"{rel(header)}:{line_no}"
            if location not in entry["locations"]:
                entry["locations"].append(location)
    return definitions


def module_name(module_id: int, definitions: dict[int, dict[str, Any]]) -> str:
    entry = definitions.get(module_id)
    if not entry:
        return "unknown"
    names = entry.get("names") or []
    if not names:
        return "unknown"
    return str(names[0])


def module_category(module_id: int, definitions: dict[int, dict[str, Any]]) -> str:
    entry = definitions.get(module_id)
    if not entry:
        return "undefined-in-source"
    names = " ".join(entry.get("names") or [])
    locations = " ".join(entry.get("locations") or [])
    if "sec_adaptation" in locations or names.startswith("MODULE_ID_PP_"):
        return "samsung-adaptation"
    if module_id >= 0x10000000:
        return "vendor-defined"
    return "qcom-defined"


def fixed_payload_from_record_modules(topology_id: int, modules: Iterable[tuple[int, int]]) -> bytes:
    record = v2683.CoreRecord(index=0, word_offset=0, domain=0, topology_id=topology_id, version=0, modules=tuple(modules))
    return v2683.fixed_payload_from_core([record])


def manifest_files_by_remote(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["remote_path"]): item for item in manifest.get("files") or [] if item.get("remote_path")}


def entry_payload_path(entry: dict[str, Any], files_by_remote: dict[str, dict[str, Any]]) -> Path | None:
    remote = entry.get("payload_remote")
    if not remote:
        return None
    file_entry = files_by_remote.get(str(remote))
    if not file_entry:
        return None
    local = (file_entry.get("local") or {}).get("local_path_private")
    if not local:
        return None
    return path_from_manifest_local(str(local))


def summarize_payload(cal_type: int, role: str, path: Path, definitions: dict[int, dict[str, Any]]) -> dict[str, Any]:
    data = path.read_bytes()
    records = v2683.parse_fixed_payload(data)
    record_summaries: list[dict[str, Any]] = []
    undefined_modules: list[int] = []
    samsung_modules: list[int] = []
    qcom_modules: list[int] = []
    for record in records:
        modules = []
        for module_id, instance_id in record.modules:
            category = module_category(module_id, definitions)
            modules.append({
                "module_id": module_id,
                "module_hex": f"0x{module_id:08x}",
                "instance_id": instance_id,
                "instance_hex": f"0x{instance_id:08x}",
                "name": module_name(module_id, definitions),
                "category": category,
            })
            if category == "undefined-in-source":
                undefined_modules.append(module_id)
            elif category == "samsung-adaptation":
                samsung_modules.append(module_id)
            elif category == "qcom-defined":
                qcom_modules.append(module_id)
        record_summaries.append({
            "index": record.index,
            "topology_id": record.topology_id,
            "topology_hex": f"0x{record.topology_id:08x}",
            "module_count": len(record.modules),
            "modules": modules,
        })
    return {
        "cal_type": cal_type,
        "role": role,
        "path_private": rel(path),
        "size": len(data),
        "sha256": sha256(data),
        "topology_count": len(records),
        "records": record_summaries,
        "undefined_module_ids": sorted(set(undefined_modules)),
        "samsung_module_ids": sorted(set(samsung_modules)),
        "qcom_module_ids": sorted(set(qcom_modules)),
    }


def write_sanitized_candidate(payload_summary: dict[str, Any], private_dir: Path, definitions: dict[int, dict[str, Any]]) -> dict[str, Any] | None:
    if payload_summary["topology_count"] != 1:
        return None
    record = payload_summary["records"][0]
    kept: list[tuple[int, int]] = []
    removed: list[dict[str, Any]] = []
    for module in record["modules"]:
        module_id = int(module["module_id"])
        instance_id = int(module["instance_id"])
        if module_id in definitions:
            kept.append((module_id, instance_id))
        else:
            removed.append(module)
    if not removed:
        return None
    data = fixed_payload_from_record_modules(int(record["topology_id"]), kept)
    private_dir.mkdir(parents=True, exist_ok=True)
    private_dir.chmod(0o700)
    path = private_dir / f"cal{int(payload_summary['cal_type']):02d}-topology-0x{int(record['topology_id']):08x}-defined-modules-only.bin"
    path.write_bytes(data)
    path.chmod(0o600)
    return {
        "cal_type": payload_summary["cal_type"],
        "topology_id": record["topology_id"],
        "topology_hex": record["topology_hex"],
        "kept_module_count": len(kept),
        "removed_module_count": len(removed),
        "removed_modules": removed,
        "path_private": rel(path),
        "size": len(data),
        "sha256": sha256(data),
    }


def classify_v2686_dmesg(path: Path) -> dict[str, Any]:
    text = path.read_text(errors="ignore") if path.exists() else ""
    markers = {
        "asm_add_topologies_ebadparam": "send_asm_custom_topology: DSP returned error[ADSP_EBADPARAM]" in text,
        "q6asm_opcode_10dbe_error_2": "q6asm_callback: cmd = 0x10dbe returned error = 0x2" in text,
        "pcm_open_enomem": "msm_pcm_open: Could not allocate memory" in text,
        "afe_excursion_timeout": "afe_get_sp_xt_logging_data Excursion logging fail" in text,
        "adm_topology_error": "adm_open" in text and "ADSP_EFAILED" in text,
    }
    lines = []
    for line in text.splitlines():
        if any(token in line for token in ("q6asm_callback", "send_asm_custom_topology", "msm_pcm_open", "ASoC", "afe_get_sp")):
            lines.append(line)
    return {"path_private": rel(path), "exists": path.exists(), "markers": markers, "evidence_lines": lines[-12:]}


def summarize(args: argparse.Namespace) -> dict[str, Any]:
    manifest = read_json(args.manifest)
    files_by_remote = manifest_files_by_remote(manifest)
    definitions = load_module_definitions(args.source_root)
    payloads = []
    for entry in manifest.get("replay_entries") or []:
        cal_type = int(entry.get("cal_type"))
        if cal_type not in TARGET_CAL_TYPES:
            continue
        path = entry_payload_path(entry, files_by_remote)
        if path is None:
            continue
        payloads.append(summarize_payload(cal_type, str(entry.get("role") or ""), path, definitions))
    sanitized = []
    if args.write_candidates:
        for payload in payloads:
            candidate = write_sanitized_candidate(payload, args.private_candidate_dir, definitions)
            if candidate:
                sanitized.append(candidate)
    cal14 = next((p for p in payloads if p["cal_type"] == 14), None)
    current_plus = ROOT / "workspace/private/builds/audio/v2683-acdb-core-topology-candidates/cal14-current-unique-plus-0x10005000-from-core-fixed.bin"
    current_plus_contains_same_bad_record = False
    if cal14 and current_plus.exists():
        plus_records = v2683.parse_fixed_payload(current_plus.read_bytes())
        bad_topos = {r["topology_id"] for r in cal14["records"]}
        current_plus_contains_same_bad_record = any(record.topology_id in bad_topos for record in plus_records)
    asm_undefined = cal14["undefined_module_ids"] if cal14 else []
    decision = "v2687-v2686-topology-rejection-classified"
    if cal14 and asm_undefined:
        next_action = "generate-defined-only-asm-candidate-before-another-live-replay"
    else:
        next_action = "recover-exact-asm-custom-topology-from-acdb-not-core-derived"
    return {
        "run_id": RUN_ID,
        "created_at": now_iso(),
        "decision": decision,
        "host_only": True,
        "device_action": False,
        "native_calibration_ioctls_run": False,
        "manifest_private": rel(args.manifest),
        "source_root": rel(args.source_root),
        "module_definition_count": len(definitions),
        "v2686_dmesg": classify_v2686_dmesg(args.v2686_dmesg),
        "payloads": payloads,
        "sanitized_candidates": sanitized,
        "sanitized_candidate_dir_private": rel(args.private_candidate_dir) if args.write_candidates else None,
        "cal14_current_plus_contains_same_selected_record": current_plus_contains_same_bad_record,
        "classification": {
            "set_replay_layer_falsified_as_blocker": True,
            "asm_cmd_add_topologies_rejected_by_adsp": bool(classify_v2686_dmesg(args.v2686_dmesg)["markers"].get("asm_add_topologies_ebadparam")),
            "core_minimal_cal14_falsified_live": True,
            "current_plus_branch_dominated": current_plus_contains_same_bad_record,
            "asm_selected_topology_has_undefined_source_modules": bool(asm_undefined),
            "next_action": next_action,
        },
    }


def fmt_modules(modules: list[dict[str, Any]]) -> str:
    parts = []
    for module in modules:
        name = module["name"]
        category = module["category"]
        parts.append(f"`{module['module_hex']}`/{module['instance_hex']} ({name}; {category})")
    return ", ".join(parts) if parts else "none"


def table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    head = rows[0]
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
    out.extend("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |" for row in rows[1:])
    return "\n".join(out)


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# NATIVE_INIT V2687 — ACDB topology rejection classifier",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only analysis after V2686. No device action, flash, `/dev/msm_audio_cal` ioctl, mixer write, or PCM probe occurred. Private candidate bytes, if generated, stay under `workspace/private/` and are not committed.",
        "",
        "## Result",
        "",
        f"- decision: `{summary['decision']}`",
        f"- source root: `{summary['source_root']}`",
        f"- manifest: `{summary['manifest_private']}`",
        f"- module definitions found in stock audio source: `{summary['module_definition_count']}`",
        f"- next action: `{summary['classification']['next_action']}`",
        "",
        "## V2686 failure classifier",
        "",
    ]
    markers = summary["v2686_dmesg"]["markers"]
    rows = [["marker", "present"]]
    for key, value in markers.items():
        rows.append([f"`{key}`", f"`{value}`"])
    lines.append(table(rows))
    if summary["v2686_dmesg"].get("evidence_lines"):
        lines.extend(["", "Relevant kernel lines:", "", "```text"])
        lines.extend(summary["v2686_dmesg"]["evidence_lines"])
        lines.append("```")
    lines.extend(["", "## Replay payload module classification", ""])
    rows = [["cal_type", "role", "topologies", "undefined modules", "Samsung adaptation modules", "sha256"]]
    for payload in summary["payloads"]:
        rows.append([
            str(payload["cal_type"]),
            f"`{payload['role']}`",
            ", ".join(record["topology_hex"] for record in payload["records"]),
            ", ".join(f"`0x{x:08x}`" for x in payload["undefined_module_ids"]) or "none",
            ", ".join(f"`0x{x:08x}`" for x in payload["samsung_module_ids"]) or "none",
            f"`{payload['sha256']}`",
        ])
    lines.append(table(rows))
    lines.extend(["", "### cal_type 14 selected topology detail", ""])
    cal14 = next((payload for payload in summary["payloads"] if payload["cal_type"] == 14), None)
    if cal14:
        for record in cal14["records"]:
            lines.append(f"- topology `{record['topology_hex']}` module_count=`{record['module_count']}`")
            lines.append(f"  - modules: {fmt_modules(record['modules'])}")
    lines.extend(["", "## Private sanitized candidates", ""])
    if summary["sanitized_candidates"]:
        rows = [["cal_type", "topology", "removed", "kept", "bytes", "sha256", "private path"]]
        for candidate in summary["sanitized_candidates"]:
            rows.append([
                str(candidate["cal_type"]),
                candidate["topology_hex"],
                str(candidate["removed_module_count"]),
                str(candidate["kept_module_count"]),
                str(candidate["size"]),
                f"`{candidate['sha256']}`",
                f"`{candidate['path_private']}`",
            ])
        lines.append(table(rows))
    else:
        lines.append("No sanitized candidates were written in this run.")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "V2686 falsifies SET delivery as the active blocker: every replay entry reached the final SET marker and cleanup completed, but the PCM open path failed when `ASM_CMD_ADD_TOPOLOGIES` returned `ADSP_EBADPARAM`.",
        "",
        "The V2684 cal_type `14` payload is mechanically well-formed, but it was forged by moving the selected ASM topology record from the CORE graph into the fixed ASM custom-topology grammar. That live candidate is now falsified: the ADSP rejected it. The important new detail is that the selected `0x10005000` record contains module IDs not defined anywhere in the available stock audio source, notably `0x10001f30` and `0x10001f10`, mixed with Samsung adaptation modules from `sec_adaptation.h`.",
        "",
        f"The old `cal14-current-unique-plus-0x10005000` branch is dominated: it contains the same selected record that V2686 already caused the ADSP to reject (`{summary['cal14_current_plus_contains_same_selected_record']}`). Running that branch next would not test a new root cause.",
        "",
        "The next bounded unit should therefore avoid another blind V2684-style replay. A safer next host-first branch is to build a new deploy manifest around the private `defined-modules-only` cal_type `14` candidate generated here, or to recover the exact selected ASM custom topology from ACDB with a different request tuple. If the defined-only candidate is used live, keep all V2639 invariants: one-shot, low-amplitude PCM probe, reverse deallocate, dmesg capture, route reset, and rollback to V2321.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/analyze_audio_acdb_v2686_topology_rejection_v2687.py tests/test_analyze_audio_acdb_v2686_topology_rejection_v2687.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_analyze_audio_acdb_v2686_topology_rejection_v2687 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_v2686_topology_rejection_v2687.py --write-candidates --write-report`",
        "- `git diff --check`",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--v2686-dmesg", type=Path, default=DEFAULT_V2686_DMESG)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--private-candidate-dir", type=Path, default=DEFAULT_PRIVATE_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--write-candidates", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    summary = summarize(args)
    if args.json_out:
        write_json(args.json_out, summary, mode=0o600)
    if args.write_report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(markdown(summary), encoding="utf-8")
    print(json.dumps({
        "decision": summary["decision"],
        "next_action": summary["classification"]["next_action"],
        "asm_ebadparam": summary["classification"]["asm_cmd_add_topologies_rejected_by_adsp"],
        "sanitized_candidates": len(summary["sanitized_candidates"]),
        "report": rel(args.report) if args.write_report else None,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
