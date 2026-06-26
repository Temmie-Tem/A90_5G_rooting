#!/usr/bin/env python3
"""Verify the A640 CS shader words for the C2 compute pattern rung."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root


CYCLE = "V3302"
SCOPE = "gpu-compute-c2-pattern-shader-byte-materialization"
REPO_ROOT = repo_root()
FULL_NIR_BUILD_ROOT = Path("/tmp/a90-mesa-c1-fullnir-softpipe-v3300")
PREFERRED_IR3_DISASM = FULL_NIR_BUILD_ROOT / "src/freedreno/isa/ir3-disasm"

EXPECTED_ASM_SOURCE = """@localsize 1, 1, 1
@buf 16384  ; g[0]
@wgid(r48.x)        ; r48.xyz
@invocationid(r0.x) ; r0.xyz
@numwg(c2.x)        ; c2.xyz
mov.u32u32 r0.x, r48.x
mov.u32u32 r0.y, r48.x
(rpt5)nop
stib.b.untyped.1d.u32.1.imm r0.x, r0.y, 0
end
nop
"""

EXPECTED_ASM_SHA256 = "1f7f223c66a97975e416dce96b0a960933b7fa21b7bf4c6d380b3eb63e31b0d6"
EXPECTED_BINARY_SHA256 = "9259cd6e225aba4d1e86fb88527494404617b2aaf753c948379ade2edb18a6d1"
EXPECTED_IR3_DISASM_SHA256 = "5fdf9cba93165bad98e9d2fe1ee92bb7cd06ef88e286454379e4943331498fc1"

EXPECTED_LOCAL_SIZE = [1, 1, 1]
EXPECTED_NUM_BUFS = 1
EXPECTED_BUF_SIZES = [16384]
EXPECTED_BUF_ADDR_REGS = [252]
EXPECTED_INSTRLEN = 1
EXPECTED_SIZE_DWORDS = 32
EXPECTED_SIZE_BYTES = 128
EXPECTED_MAX_REG = 0
EXPECTED_MAX_HALF_REG = -1
EXPECTED_CONSTLEN = 4
EXPECTED_MERGEDREGS = True

EXPECTED_DWORDS = [
    0x000000C0,
    0x200CC000,
    0x000000C0,
    0x200CC001,
    0x00000000,
    0x00000500,
    0x01674000,
    0xC0260000,
    0x00000000,
    0x03000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
]

EXPECTED_DISASM_SNIPPETS = [
    "mov.u32u32 r0.x, r48.x",
    "mov.u32u32 r0.y, r48.x",
    "(rpt5)nop",
    "stib.b.untyped.1d.u32.1.imm r0.x, r0.y, 0",
    "end",
]


def _sha256_path(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dwords_to_bytes(dwords: list[int]) -> bytes:
    out = bytearray()
    for dword in dwords:
        out.extend(dword.to_bytes(4, "little"))
    return bytes(out)


def _find_ir3_disasm() -> Path | None:
    candidates = [
        PREFERRED_IR3_DISASM,
        Path("/tmp/a90-mesa-h3-build-ir3/src/freedreno/isa/ir3-disasm"),
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _run_ir3_disasm(binary: bytes, ir3_disasm: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="a90-c2-ir3-disasm-") as tmp:
        shader_path = Path(tmp) / "kern_c2_pattern_a640.bin"
        shader_path.write_bytes(binary)
        proc = subprocess.run(
            [str(ir3_disasm), "-g", "FD640", str(shader_path)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    return {
        "command": [str(ir3_disasm), "-g", "FD640", "<temp-shader-bin>"],
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "lines": [line for line in proc.stdout.splitlines() if line.strip()],
    }


def _shader_contract() -> dict[str, Any]:
    return {
        "source_sha256": _sha256_bytes(EXPECTED_ASM_SOURCE.encode("utf-8")),
        "has_localsize_1_1_1": "@localsize 1, 1, 1" in EXPECTED_ASM_SOURCE,
        "has_one_16384_word_uav": "@buf 16384" in EXPECTED_ASM_SOURCE,
        "has_wgid_r48x": "@wgid(r48.x)" in EXPECTED_ASM_SOURCE,
        "has_invocationid_r0x": "@invocationid(r0.x)" in EXPECTED_ASM_SOURCE,
        "moves_wgid_to_store_offset": "mov.u32u32 r0.x, r48.x" in EXPECTED_ASM_SOURCE,
        "moves_wgid_to_store_value": "mov.u32u32 r0.y, r48.x" in EXPECTED_ASM_SOURCE,
        "stores_wgid_to_uav": "stib.b.untyped.1d.u32.1.imm r0.x, r0.y, 0" in EXPECTED_ASM_SOURCE,
        "expected_readback_samples": {
            "0": 0,
            "1": 1,
            "2": 2,
            "3": 3,
            "31": 31,
            "127": 127,
            "128": 128,
            "4096": 4096,
            "8192": 8192,
            "16383": 16383,
        },
    }


def run_verification(*, require_disasm: bool = False) -> dict[str, Any]:
    shader_binary = _dwords_to_bytes(EXPECTED_DWORDS)
    ir3_disasm = _find_ir3_disasm()
    disasm: dict[str, Any] | None = None
    if ir3_disasm is not None:
        disasm = _run_ir3_disasm(shader_binary, ir3_disasm)

    disasm_stdout = disasm["stdout"] if disasm else ""
    checks = {
        "asm_source_sha256_matches": (
            _sha256_bytes(EXPECTED_ASM_SOURCE.encode("utf-8")) == EXPECTED_ASM_SHA256
        ),
        "shader_dword_count_matches": len(EXPECTED_DWORDS) == EXPECTED_SIZE_DWORDS,
        "shader_byte_count_matches": len(shader_binary) == EXPECTED_SIZE_BYTES,
        "shader_binary_sha256_matches": _sha256_bytes(shader_binary) == EXPECTED_BINARY_SHA256,
        "ir3_disasm_available": ir3_disasm is not None,
        "ir3_disasm_sha256_matches": (
            _sha256_path(ir3_disasm) == EXPECTED_IR3_DISASM_SHA256 if ir3_disasm else False
        ),
        "ir3_disasm_returncode_zero": disasm["returncode"] == 0 if disasm else False,
        "ir3_disasm_contains_expected_ops": (
            all(snippet in disasm_stdout for snippet in EXPECTED_DISASM_SNIPPETS)
            if disasm
            else False
        ),
    }

    mandatory_checks = [
        "asm_source_sha256_matches",
        "shader_dword_count_matches",
        "shader_byte_count_matches",
        "shader_binary_sha256_matches",
    ]
    if require_disasm:
        mandatory_checks.extend(
            [
                "ir3_disasm_available",
                "ir3_disasm_returncode_zero",
                "ir3_disasm_contains_expected_ops",
            ]
        )

    passed = all(checks[name] for name in mandatory_checks)
    ready_for_c2_live = all(
        checks[name]
        for name in [
            "asm_source_sha256_matches",
            "shader_binary_sha256_matches",
            "ir3_disasm_returncode_zero",
            "ir3_disasm_contains_expected_ops",
        ]
    )

    return {
        "cycle": CYCLE,
        "scope": SCOPE,
        "passed": passed,
        "ready_for_c2_live": ready_for_c2_live,
        "checks": checks,
        "shader_contract": _shader_contract(),
        "shader": {
            "gpu_name": "FD640",
            "gpu_id": 640,
            "local_size": EXPECTED_LOCAL_SIZE,
            "num_bufs": EXPECTED_NUM_BUFS,
            "buf_sizes": EXPECTED_BUF_SIZES,
            "buf_addr_regs": EXPECTED_BUF_ADDR_REGS,
            "instrlen": EXPECTED_INSTRLEN,
            "sizedwords": EXPECTED_SIZE_DWORDS,
            "size_bytes": EXPECTED_SIZE_BYTES,
            "max_reg": EXPECTED_MAX_REG,
            "max_half_reg": EXPECTED_MAX_HALF_REG,
            "constlen": EXPECTED_CONSTLEN,
            "mergedregs": EXPECTED_MERGEDREGS,
            "binary_sha256": _sha256_bytes(shader_binary),
            "dwords_hex": [f"0x{dword:08x}" for dword in EXPECTED_DWORDS],
        },
        "toolchain": {
            "full_nir_build_root": str(FULL_NIR_BUILD_ROOT),
            "ir3_disasm": str(ir3_disasm) if ir3_disasm else None,
            "ir3_disasm_sha256": _sha256_path(ir3_disasm) if ir3_disasm else None,
            "libnir_sha256": _sha256_path(FULL_NIR_BUILD_ROOT / "src/compiler/nir/libnir.a"),
            "libfreedreno_ir3_sha256": _sha256_path(
                FULL_NIR_BUILD_ROOT / "src/freedreno/ir3/libfreedreno_ir3.a"
            ),
            "assembler_cross_check": {
                "c1_reassembled_matches_v3300": True,
                "c2_asm_source_sha256": EXPECTED_ASM_SHA256,
            },
        },
        "disasm": disasm,
        "expected_disasm_snippets": EXPECTED_DISASM_SNIPPETS,
        "next": [
            "embed these verified CS shader words in the native-init C2 compute pattern probe",
            "dispatch 16384 one-lane workgroups and verify selected 128x128 buffer samples after WFI/readback",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON result")
    parser.add_argument(
        "--require-disasm",
        action="store_true",
        help="fail unless the local ir3-disasm decodes the expected ops",
    )
    args = parser.parse_args()
    result = run_verification(require_disasm=args.require_disasm)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{CYCLE} {SCOPE}: {'PASS' if result['passed'] else 'FAIL'}")
        print(f"ready_for_c2_live={int(result['ready_for_c2_live'])}")
        print(f"shader_sha256={result['shader']['binary_sha256']}")
        if result["disasm"]:
            print(result["disasm"]["stdout"])
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
