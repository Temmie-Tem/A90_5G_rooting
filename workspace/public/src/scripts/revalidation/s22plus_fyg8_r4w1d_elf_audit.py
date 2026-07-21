#!/usr/bin/env python3
"""Audit the final R4W1-D contiguous PID1 witness ELF host-only."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
from typing import Any, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import s22plus_fyg8_r4w1b_elf_audit as engine


Elf64 = engine.Elf64
ElfAuditError = engine.ElfAuditError
sha256_file = engine.sha256_file

EXPECTED_KERNEL_INIT_SHA256 = (
    "be96fac2bcc31dda93f14ee702ecd03dcc3d1ab85060337cdcfa07819d4143bc"
)
EXPECTED_RUN_INIT_PROCESS_SHA256 = (
    "0fa953f7b4d36f3916df01206930e6fe81dbe598437396fb73d34d142f31ac12"
)
WITNESS_WORDS = (
    0xF94456C8, 0xD2A00409, 0xF2C00109, 0x5289E98A,
    0xCB080128, 0xB2596108, 0x91001109, 0x72A9A8EA,
    0x88DFFD29, 0x6B0A013F, 0x54000141, 0x529FFDEA,
    0x91002109, 0x72A003EA, 0x88DFFD29, 0x6B0A013F,
    0x540000E8, 0xB00038A0, 0x91344800, 0x1400001E,
    0xF0003E00, 0x91037C00, 0x1400001B, 0x5281002B,
    0x53047D2A, 0x72A2000B, 0x9BAB7D4A, 0x321C43EC,
    0xD36DFD4A, 0x529FF86D, 0x1B0CA549, 0x72A003ED,
    0xF0003BCE, 0xD100B52C, 0x7100B13F, 0x91171DCE,
    0x9A8D8189, 0xA9402DCA, 0xA94135CC, 0x8B090108,
    0xF84251C9, 0xF94011CE, 0xA9012D0A, 0xF900110C,
    0xF8035109, 0xA902B90D, 0xD5033ABF,
)


def find_contiguous_backfill_chains(
    *,
    instructions: list[tuple[int, int, int]],
    successors: dict[int, set[int]],
    witness_index: int,
    marker_reference: dict[str, int],
    memstart_reference: dict[str, int],
    memcpy_address: int,
    marker_size: int,
) -> list[dict[str, Any]]:
    if marker_size != 45 or witness_index + len(WITNESS_WORDS) > len(instructions):
        return []
    rows = instructions[witness_index : witness_index + len(WITNESS_WORDS)]
    words = tuple(row[2] for row in rows)
    if words != WITNESS_WORDS:
        return []

    magic_guard = engine.conditional_branch(words[10])
    saturation_guard = engine.conditional_branch(words[16])
    magic_failure = (
        engine.target_index(instructions, rows[10][1], magic_guard["target_delta"])
        if magic_guard is not None
        else None
    )
    saturation_success = (
        engine.target_index(
            instructions, rows[16][1], saturation_guard["target_delta"]
        )
        if saturation_guard is not None
        else None
    )
    marker_index = marker_reference["index"]
    branch_targets = {
        target
        for _, pc, word in rows
        if (target := engine.branch_target(pc, word)) is not None
    }
    idx_store_candidates = [
        {
            "index": index,
            "pc": pc,
            **decoded,
        }
        for index, pc, word in rows
        if (decoded := engine.store_w_unsigned(word)) is not None
        and decoded["base"] == 8
        and decoded["offset"] == 8
    ]
    gates = {
        "head_uses_memstart_addr": (
            memstart_reference["index"] == witness_index
            and memstart_reference["base_register"] == 22
            and memstart_reference["destination"] == 8
            and memstart_reference["width"] == 64
        ),
        "marker_reference_exact": (
            marker_reference["index"] == witness_index + 32
            and marker_reference["consumer_index"] == witness_index + 35
            and marker_reference["register"] == 14
        ),
        "magic_guard_exact": (
            magic_guard is not None
            and magic_guard["condition"] == 1
            and magic_failure == witness_index + 20
        ),
        "saturation_guard_exact": (
            saturation_guard is not None
            and saturation_guard["condition"] == 8
            and saturation_success == witness_index + 23
        ),
        "magic_match_reaches_proof": engine.is_reachable_within(
            successors,
            witness_index + 11,
            marker_index,
            minimum=witness_index,
            maximum=witness_index + 46,
        ),
        "magic_mismatch_cannot_reach_proof": (
            magic_failure is not None
            and not engine.is_reachable_within(
                successors,
                magic_failure,
                marker_index,
                minimum=witness_index,
                maximum=witness_index + 46,
            )
        ),
        "unsaturated_path_cannot_reach_proof": not engine.is_reachable_within(
            successors,
            witness_index + 17,
            marker_index,
            minimum=witness_index,
            maximum=witness_index + 46,
        ),
        "saturated_path_reaches_proof": (
            saturation_success is not None
            and engine.is_reachable_within(
                successors,
                saturation_success,
                marker_index,
                minimum=witness_index,
                maximum=witness_index + 46,
            )
        ),
        "proof_stores_reach_barrier": engine.is_reachable_within(
            successors,
            witness_index + 37,
            witness_index + 46,
            minimum=witness_index,
            maximum=witness_index + 46,
        ),
        "no_memcpy_call": memcpy_address not in branch_targets,
        "no_head_idx_store": not idx_store_candidates,
    }
    if not all(gates.values()):
        return []
    return [
        {
            "memstart_reference_pc": memstart_reference["producer_pc"],
            "head_load_pc": rows[0][1],
            "magic_guard_pc": rows[10][1],
            "idx_load_pc": rows[14][1],
            "saturation_guard_pc": rows[16][1],
            "marker_reference_pc": rows[32][1],
            "marker_materialize_pc": rows[35][1],
            "position_select_pc": rows[36][1],
            "first_store_pc": rows[42][1],
            "last_store_pc": rows[45][1],
            "dmb_ishst_pc": rows[46][1],
            "proof_size": marker_size,
            "payload_size": 0x1FFFF0,
            "idx_written": False,
            "idx_store_candidates": idx_store_candidates,
            "gates": gates,
        }
    ]


def expected_witness_ingress(
    instructions: list[tuple[int, int, int]],
    witness_index: int,
    branch: tuple[int, int, int],
) -> set[tuple[int, int]]:
    return {
        (branch[1], instructions[witness_index][1]),
        (
            instructions[witness_index + 10][1],
            instructions[witness_index + 20][1],
        ),
        (
            instructions[witness_index + 16][1],
            instructions[witness_index + 23][1],
        ),
    }


@contextmanager
def _bind_engine_contract() -> Iterator[None]:
    replacements = {
        "EXPECTED_KERNEL_INIT_SHA256": EXPECTED_KERNEL_INIT_SHA256,
        "EXPECTED_RUN_INIT_PROCESS_SHA256": EXPECTED_RUN_INIT_PROCESS_SHA256,
        "find_ring_publication_chains": find_contiguous_backfill_chains,
        "expected_witness_ingress": expected_witness_ingress,
    }
    previous = {name: getattr(engine, name) for name in replacements}
    try:
        for name, value in replacements.items():
            setattr(engine, name, value)
        yield
    finally:
        for name, value in previous.items():
            setattr(engine, name, value)


def inspect_final_vmlinux(path: Path, marker: bytes) -> dict[str, Any]:
    with _bind_engine_contract():
        result = engine.inspect_final_vmlinux(path, marker)
    result["witness_layout"] = "saturated-ring-pre-cursor-contiguous-backfill"
    return result
