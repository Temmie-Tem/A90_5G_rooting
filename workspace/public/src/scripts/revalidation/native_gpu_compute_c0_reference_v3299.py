#!/usr/bin/env python3
"""Validate the staged A640 compute dispatch reference for the C0 rung."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root


CYCLE = "V3299"
SCOPE = "gpu-compute-c0-reference-envelope-recon"
REPO_ROOT = repo_root()
STAGED_ROOT = Path("/tmp/a90-mesa-gpu-src")
SPARSE_MESA_ROOT = Path("/tmp/a90-mesa-h3-sparse")
MESA_BUILD_ROOT = Path("/tmp/a90-mesa-h3-build-ir3")
DEFAULT_IR3_DISASM = Path("/tmp/a90-mesa-h3-build-ir3/src/freedreno/isa/ir3-disasm")

REFERENCE = STAGED_ROOT / "a6xx_compute_dispatch_reference.txt"
A6XX_XML = STAGED_ROOT / "a6xx.xml"
PM4_XML = SPARSE_MESA_ROOT / "src/freedreno/registers/adreno/adreno_pm4.xml"
COMPUTERATOR_A6XX = STAGED_ROOT / "comp_a6xx.cc"
FD6_COMPUTE = STAGED_ROOT / "comp_fd6_compute.cc"
KERNEL = STAGED_ROOT / "kern_invocationid.asm"

EXPECTED_REG_OFFSETS = {
    "SP_CS_CNTL_0": 0xA9B0,
    "SP_CS_CNTL_1": 0xA9B1,
    "SP_CS_BASE": 0xA9B4,
    "SP_CS_CONFIG": 0xA9BB,
    "SP_CS_INSTR_SIZE": 0xA9BC,
    "SP_CS_UAV_BASE": 0xA9F2,
    "SP_CS_USIZE": 0xAA00,
    "SP_CS_CONST_CONFIG": 0xB987,
    "SP_CS_NDRANGE_0": 0xB990,
    "SP_CS_NDRANGE_1": 0xB991,
    "SP_CS_NDRANGE_2": 0xB992,
    "SP_CS_NDRANGE_3": 0xB993,
    "SP_CS_NDRANGE_4": 0xB994,
    "SP_CS_NDRANGE_5": 0xB995,
    "SP_CS_NDRANGE_6": 0xB996,
    "SP_CS_CONST_CONFIG_0": 0xB997,
    "SP_CS_WGE_CNTL": 0xB998,
    "SP_CS_KERNEL_GROUP_X": 0xB999,
    "SP_CS_KERNEL_GROUP_Y": 0xB99A,
    "SP_CS_KERNEL_GROUP_Z": 0xB99B,
    "HLSQ_CS_CTRL_REG1": 0xB9D0,
    "SP_UPDATE_CNTL": 0xBB08,
}

EXPECTED_PM4_VALUES = {
    "CP_EXEC_CS": 0x33,
    "CP_SET_MARKER": 0x65,
    "SB6_CS_SHADER": 0x0D,
    "ST6_SHADER": 0x00,
    "ST6_CONSTANTS": 0x01,
    "ST6_UAV": 0x03,
    "SS6_DIRECT": 0x00,
    "SS6_INDIRECT": 0x02,
    "RM6_COMPUTE": 0x08,
}

EXPECTED_REFERENCE_MARKERS = [
    "cs_restore",
    "SP_CS_CONST_CONFIG",
    "SP_CS_CONFIG",
    "SP_CS_CNTL_0",
    "SP_CS_CNTL_1",
    "HLSQ_CS_CTRL_REG1",
    "SP_CS_WGE_CNTL",
    "SP_CS_BASE",
    "CP_LOAD_STATE6_FRAG  state_type=ST6_SHADER",
    "CP_LOAD_STATE6_FRAG  state_type=ST6_UAV",
    "SP_CS_UAV_BASE",
    "SP_CS_USIZE",
    "CP_SET_MARKER  mode=RM6_COMPUTE",
    "SP_CS_NDRANGE_0",
    "SP_CS_KERNEL_GROUP_X/Y/Z",
    "CP_EXEC_CS  (opcode 0x33)",
    "CP_WAIT_FOR_IDLE",
]

EXPECTED_COMPUTERATOR_MARKERS = [
    "crb.add(SP_CS_CONST_CONFIG",
    "crb.add(A6XX_SP_CS_CONFIG",
    "crb.add(A6XX_SP_CS_CNTL_0",
    "crb.add(A6XX_SP_CS_CNTL_1",
    "crb.add(SP_CS_WGE_CNTL",
    "crb.add(A6XX_SP_CS_BASE",
    ".state_type = ST6_SHADER",
    ".state_type = ST6_UAV",
    ".state_block = SB6_CS_SHADER",
    ".mode = RM6_COMPUTE",
    "crb.add(SP_CS_NDRANGE_0",
    "crb.add(SP_CS_KERNEL_GROUP_X",
    "fd_pkt7(cs, CP_EXEC_CS, 4)",
    "fd_pkt7(cs, CP_WAIT_FOR_IDLE, 0)",
]

ORDERED_ENVELOPE = [
    {
        "stage": "cs_restore",
        "source": "reuse G0-G3 KGSL context plus H3/H5 A640 restore/magic baseline",
    },
    {
        "stage": "cs_program_emit_regs",
        "registers": [
            "SP_UPDATE_CNTL",
            "SP_CS_CONST_CONFIG",
            "SP_CS_CONFIG",
            "SP_CS_INSTR_SIZE",
            "SP_CS_CNTL_0",
            "SP_CS_CNTL_1",
            "HLSQ_CS_CTRL_REG1",
            "SP_CS_CONST_CONFIG_0",
            "SP_CS_WGE_CNTL",
            "SP_CS_BASE",
        ],
    },
    {
        "stage": "cs_shader_preload",
        "packet": "CP_LOAD_STATE6_FRAG",
        "state_type": "ST6_SHADER",
        "state_src": "SS6_INDIRECT",
        "state_block": "SB6_CS_SHADER",
    },
    {
        "stage": "cs_const_emit",
        "packet": "CP_LOAD_STATE6_FRAG",
        "state_type": "ST6_CONSTANTS",
        "state_block": "SB6_CS_SHADER",
    },
    {
        "stage": "cs_uav_emit",
        "descriptor_dwords_per_buffer": 16,
        "format": "PIPE_FORMAT_R32_UINT",
        "packet": "CP_LOAD_STATE6_FRAG",
        "state_type": "ST6_UAV",
        "state_src": "SS6_INDIRECT",
        "state_block": "SB6_CS_SHADER",
        "registers": ["SP_CS_UAV_BASE", "SP_CS_USIZE"],
    },
    {
        "stage": "compute_marker",
        "packet": "CP_SET_MARKER",
        "mode": "RM6_COMPUTE",
    },
    {
        "stage": "ndrange",
        "registers": [
            "SP_CS_NDRANGE_0",
            "SP_CS_NDRANGE_1",
            "SP_CS_NDRANGE_2",
            "SP_CS_NDRANGE_3",
            "SP_CS_NDRANGE_4",
            "SP_CS_NDRANGE_5",
            "SP_CS_NDRANGE_6",
            "SP_CS_KERNEL_GROUP_X",
            "SP_CS_KERNEL_GROUP_Y",
            "SP_CS_KERNEL_GROUP_Z",
        ],
        "c1_grid": [1, 1, 1],
        "c1_local_size": [32, 1, 1],
        "c1_global_size": [32, 1, 1],
    },
    {
        "stage": "dispatch",
        "packet": "CP_EXEC_CS",
        "dwords": 4,
        "ngroups": [1, 1, 1],
    },
    {
        "stage": "idle_and_readback",
        "packet": "CP_WAIT_FOR_IDLE",
        "readback": "sync and verify UAV buffer on CPU",
    },
]


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_int(raw: str) -> int:
    return int(raw, 0)


def _variant_matches_a6xx(variants: str | None) -> bool:
    if variants is None:
        return True
    return variants in {"A6XX", "A6XX-", "A6XX-A7XX"}


def _local_tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _parse_a6xx_offsets(xml_path: Path = A6XX_XML) -> dict[str, int]:
    root = ET.parse(xml_path).getroot()
    offsets: dict[str, int] = {}
    for element in root.iter():
        if _local_tag(element) not in {"reg32", "reg64"}:
            continue
        name = element.attrib.get("name")
        if name not in EXPECTED_REG_OFFSETS:
            continue
        if not _variant_matches_a6xx(element.attrib.get("variants")):
            continue
        offsets.setdefault(name, _parse_int(element.attrib["offset"]))
    return offsets


def _parse_pm4_values(xml_path: Path = PM4_XML) -> dict[str, int]:
    root = ET.parse(xml_path).getroot()
    values: dict[str, int] = {}
    for element in root.iter():
        if _local_tag(element) != "value":
            continue
        name = element.attrib.get("name")
        if name in EXPECTED_PM4_VALUES:
            values.setdefault(name, _parse_int(element.attrib["value"]))
    return values


def _find_executable(candidates: list[str]) -> str | None:
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    search_roots = [Path("/tmp/a90-mesa-h3-build-ir3"), SPARSE_MESA_ROOT, STAGED_ROOT]
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or not os.access(path, os.X_OK):
                continue
            if path.name in candidates or any(token in path.name for token in candidates):
                return str(path)
    return None


def _find_ir3_disasm() -> str | None:
    if DEFAULT_IR3_DISASM.is_file() and os.access(DEFAULT_IR3_DISASM, os.X_OK):
        return str(DEFAULT_IR3_DISASM)
    return _find_executable(["ir3-disasm"])


def _ar_members(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        result = subprocess.run(
            ["ar", "t", str(path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _inspect_mesa_build(build_root: Path = MESA_BUILD_ROOT) -> dict[str, Any]:
    build_ninja = build_root / "build.ninja"
    libnir = build_root / "src/compiler/nir/libnir.a"
    members = _ar_members(libnir)
    computerator = build_root / "src/freedreno/computerator/computerator"
    ir3_disasm_target = build_root / "src/freedreno/ir3/ir3_disasm"
    build_text = build_ninja.read_text(encoding="utf-8") if build_ninja.is_file() else ""
    libnir_is_stub_only = members == [
        "/tmp/a90-mesa-h3-build-ir3/src/compiler/nir/libnir.a.p/nir_stub.c.o"
    ] or members == ["src/compiler/nir/libnir.a.p/nir_stub.c.o"]
    blockers: list[str] = []
    if libnir_is_stub_only:
        blockers.append("libnir.a contains only nir_stub.c.o, so ir3 assembler targets cannot resolve full NIR symbols")
    if "build src/freedreno/computerator/computerator" in build_text and not computerator.is_file():
        blockers.append("computerator target exists in build.ninja but no executable is present")
    return {
        "build_root": str(build_root),
        "build_ninja_present": build_ninja.is_file(),
        "computerator_target_present": "build src/freedreno/computerator/computerator" in build_text,
        "computerator_executable_present": computerator.is_file() and os.access(computerator, os.X_OK),
        "ir3_disasm_target_present": "build src/freedreno/ir3/ir3_disasm" in build_text,
        "ir3_disasm_executable_present": ir3_disasm_target.is_file() and os.access(ir3_disasm_target, os.X_OK),
        "libnir_archive": str(libnir),
        "libnir_sha256": _sha256(libnir),
        "libnir_members": members,
        "libnir_member_count": len(members),
        "libnir_is_stub_only": libnir_is_stub_only,
        "assembler_build_ready": (not libnir_is_stub_only) and computerator.is_file(),
        "blockers": blockers,
    }


def _parse_register_directive(text: str, directive: str) -> str | None:
    match = re.search(rf"@{directive}\(([^)]+)\)", text)
    return match.group(1).strip() if match else None


def _parse_kernel_contract(kernel_path: Path = KERNEL) -> dict[str, Any]:
    text = kernel_path.read_text(encoding="utf-8")
    localsize_match = re.search(r"@localsize\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", text)
    buf_match = re.search(r"@buf\s+(\d+)", text)
    localsize = [int(group) for group in localsize_match.groups()] if localsize_match else []
    buf_words = int(buf_match.group(1)) if buf_match else 0
    expected = list(range(buf_words)) if buf_words else []
    store = "stib.b.untyped.1d.u32.1.imm r0.x, r0.y, 0" in text
    move = "mov.u32u32 r0.y, r0.x" in text
    return {
        "path": str(kernel_path),
        "sha256": _sha256(kernel_path),
        "localsize": localsize,
        "buf_words": buf_words,
        "wgid_reg": _parse_register_directive(text, "wgid"),
        "invocationid_reg": _parse_register_directive(text, "invocationid"),
        "numwg_reg": _parse_register_directive(text, "numwg"),
        "moves_invocation_id_to_store_offset": move,
        "stores_invocation_id_to_uav": store,
        "ends": bool(re.search(r"^end$", text, re.M)),
        "expected_readback_words": buf_words,
        "expected_readback_prefix": expected[:16],
        "expected_readback": expected,
        "valid": (
            localsize == [32, 1, 1]
            and buf_words == 32
            and _parse_register_directive(text, "invocationid") == "r0.x"
            and _parse_register_directive(text, "wgid") == "r48.x"
            and _parse_register_directive(text, "numwg") == "c2.x"
            and move
            and store
        ),
    }


def _source_contains_all(path: Path, markers: list[str]) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8")
    return {marker: marker in text for marker in markers}


def run_recon(
    staged_root: Path = STAGED_ROOT,
    sparse_mesa_root: Path = SPARSE_MESA_ROOT,
) -> dict[str, Any]:
    reference = staged_root / "a6xx_compute_dispatch_reference.txt"
    a6xx_xml = staged_root / "a6xx.xml"
    pm4_xml = sparse_mesa_root / "src/freedreno/registers/adreno/adreno_pm4.xml"
    computerator_a6xx = staged_root / "comp_a6xx.cc"
    fd6_compute = staged_root / "comp_fd6_compute.cc"
    kernel = staged_root / "kern_invocationid.asm"

    files = {
        "reference": reference,
        "a6xx_xml": a6xx_xml,
        "pm4_xml": pm4_xml,
        "computerator_a6xx": computerator_a6xx,
        "fd6_compute": fd6_compute,
        "kernel": kernel,
    }
    missing = [name for name, path in files.items() if not path.is_file()]
    if missing:
        return {
            "cycle": CYCLE,
            "scope": SCOPE,
            "passed": False,
            "missing_files": missing,
            "files": {name: str(path) for name, path in files.items()},
        }

    offsets = _parse_a6xx_offsets(a6xx_xml)
    pm4_values = _parse_pm4_values(pm4_xml)
    kernel_contract = _parse_kernel_contract(kernel)
    reference_markers = _source_contains_all(reference, EXPECTED_REFERENCE_MARKERS)
    computerator_markers = _source_contains_all(computerator_a6xx, EXPECTED_COMPUTERATOR_MARKERS)
    fd6_markers = _source_contains_all(
        fd6_compute,
        ["fd6_set_render_mode<CHIP>(cs, {RM6_COMPUTE})", "fd_pkt7(cs, CP_EXEC_CS, 4)"],
    )

    offset_mismatches = {
        name: {"expected": expected, "actual": offsets.get(name)}
        for name, expected in EXPECTED_REG_OFFSETS.items()
        if offsets.get(name) != expected
    }
    pm4_mismatches = {
        name: {"expected": expected, "actual": pm4_values.get(name)}
        for name, expected in EXPECTED_PM4_VALUES.items()
        if pm4_values.get(name) != expected
    }
    assembler_binary = _find_executable(["computerator", "ir3-asm", "ir3_asm"])
    ir3_disasm = _find_ir3_disasm()
    mesa_build = _inspect_mesa_build()

    checks = {
        "reference_files_present": not missing,
        "reference_markers_present": all(reference_markers.values()),
        "computerator_source_confirms_envelope": all(computerator_markers.values()),
        "fd6_compute_crosscheck_present": all(fd6_markers.values()),
        "xml_offsets_match_expected": not offset_mismatches,
        "pm4_values_match_expected": not pm4_mismatches,
        "kernel_contract_valid": kernel_contract["valid"],
        "ir3_disasm_available": ir3_disasm is not None,
        "compute_assembler_binary_available": assembler_binary is not None,
        "mesa_build_has_full_nir": not mesa_build["libnir_is_stub_only"],
        "mesa_computerator_executable_available": mesa_build["computerator_executable_present"],
        "kernel_bytes_verified": False,
        "ready_for_c1_live": False,
    }
    checks["c0_reference_recon_passed"] = all(
        checks[name]
        for name in (
            "reference_files_present",
            "reference_markers_present",
            "computerator_source_confirms_envelope",
            "fd6_compute_crosscheck_present",
            "xml_offsets_match_expected",
            "pm4_values_match_expected",
            "kernel_contract_valid",
            "ir3_disasm_available",
        )
    )

    return {
        "cycle": CYCLE,
        "scope": SCOPE,
        "passed": checks["c0_reference_recon_passed"],
        "checks": checks,
        "files": {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in files.items()
        },
        "expected_reg_offsets": EXPECTED_REG_OFFSETS,
        "actual_reg_offsets": offsets,
        "offset_mismatches": offset_mismatches,
        "expected_pm4_values": EXPECTED_PM4_VALUES,
        "actual_pm4_values": pm4_values,
        "pm4_mismatches": pm4_mismatches,
        "ordered_envelope": ORDERED_ENVELOPE,
        "reference_markers": reference_markers,
        "computerator_markers": computerator_markers,
        "fd6_compute_markers": fd6_markers,
        "kernel_contract": kernel_contract,
        "tools": {
            "ir3_disasm": ir3_disasm,
            "compute_assembler_binary": assembler_binary,
            "mesa_build": mesa_build,
            "assembler_sources": [
                str(staged_root / "comp_ir3_asm.cc"),
                str(sparse_mesa_root / "src/freedreno/computerator/ir3_asm.cc"),
            ],
        },
        "next_required_before_c1_live": [
            "materialize kern_invocationid.asm into CS shader words with a real ir3 assembler/computerator path",
            "verify the generated words with ir3-disasm",
            "only then wire those bytes into the boot artifact and run C1 live dispatch",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print compact JSON")
    args = parser.parse_args()
    result = run_recon()
    print(json.dumps(result, indent=None if args.json else 2, sort_keys=True))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
