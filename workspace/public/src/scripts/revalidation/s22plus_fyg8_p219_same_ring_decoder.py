#!/usr/bin/env python3
"""Fixed raw-byte decoder for the FYG8 P2.19 same-ring records."""

from __future__ import annotations

import hashlib
from typing import Any


TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
ENTRY_FAMILY = b"[[S22P1U|"
UNSAT_FAMILY = b"S22UNS1|"
ENTRY_SIZE = 45
UNSAT_SIZE = 24
TAG_SIZE = 16
CONTRACT_PREIMAGE = (
    "S22PLUS_FYG8_P219_SAME_RING_CANDIDATE_CONTRACT_V1|"
    "target=SM-S906N/g0q/S906NKSS7FYG8|"
    "base-main=7d281c86ca63646083b9f489eed28281c7d2518f397f34ceccf34c223eaa663a|"
    "base-kconfig=8273d233a441c21df2fcb1d5d17a590321d758205fd5babd8b8dcb4e6a334019|"
    "base-defconfig=12661b7d249fb8f80135c3fdcd331733b86d5215f2f4e88e356d1516831ab493|"
    "config=CONFIG_S22PLUS_FYG8_PID1_SAME_RING_DISCRIMINATOR=y|"
    "init=c3fd6cc88d8de494421ff2bf0f082d278745fdf9c2a74a2b5edba9fb8ca93627|"
    "request=53323251010110000000000064554e8469385878c5bf8d57c44edeeafd118a62|"
    "model=Samsung G0Q PROJECT (board-id,12)|"
    "log=0x800200000+0x200000;magic=0x4d474f4c|"
    "states=ENTRY45,USERSPACE45,UNSAT24,ZERO|"
    "semantics=post-kernel_execve-/init-pid1;stable-header;no-index-mutation|"
    "format=s22plus-fyg8-p218-record-v1"
)
CONTRACT_BYTES = CONTRACT_PREIMAGE.encode("ascii")
CONTRACT_SHA256 = hashlib.sha256(CONTRACT_BYTES).hexdigest()
CONTRACT_ID = bytes.fromhex(CONTRACT_SHA256[:32])
ENTRY_PROOF = b"\n[[S22P1U|b1e3af3bab0296cb70085d40026663cf]]\n"
USERSPACE_PROOF = b"\n[[S22P1U|df36273d5465a9763ce7b0df8eb75c84]]\n"
UNSAT_PROOF = bytes.fromhex(
    "533232554e53317c7a8c535f3154ebbeb185f9fb45126cae"
)


class DecodeError(ValueError):
    pass


def _edge_partial(payload: bytes) -> bool:
    for record in (ENTRY_PROOF, USERSPACE_PROOF, UNSAT_PROOF):
        for length in range(4, len(record)):
            if (
                not payload.startswith(record)
                and payload.startswith(record[-length:])
            ) or (
                not payload.endswith(record)
                and payload.endswith(record[:length])
            ):
                return True
    return False


def classify_observation(payload: bytes) -> dict[str, Any]:
    if not isinstance(payload, bytes):
        raise DecodeError("same-ring observation must be raw bytes")
    entry_count = payload.count(ENTRY_PROOF)
    userspace_count = payload.count(USERSPACE_PROOF)
    unsat_count = payload.count(UNSAT_PROOF)
    long_family_count = payload.count(ENTRY_FAMILY)
    unsat_family_count = payload.count(UNSAT_FAMILY)
    partial = _edge_partial(payload)
    exact_total = entry_count + userspace_count + unsat_count
    integrity_issue = (
        partial
        or exact_total > 1
        or long_family_count != entry_count + userspace_count
        or unsat_family_count != unsat_count
    )
    if integrity_issue:
        classification = "AMBIGUOUS_INTEGRITY_FAILURE"
        accepted = False
    elif userspace_count == 1:
        classification = "USERSPACE_CALLBACK_REACHED"
        accepted = True
    elif entry_count == 1:
        classification = "ENTRY_ONLY"
        accepted = False
    elif unsat_count == 1:
        classification = "UNSAT_VALID_MAGIC_ENTRY_DID_NOT_FIT"
        accepted = False
    else:
        classification = "ZERO_AMBIGUOUS"
        accepted = False
    return {
        "classification": classification,
        "accepted": accepted,
        "integrity_issue": integrity_issue,
        "entry_count": entry_count,
        "userspace_count": userspace_count,
        "unsat_count": unsat_count,
        "long_family_count": long_family_count,
        "unsat_family_count": unsat_family_count,
        "partial_at_snapshot_edge": partial,
        "residual_zero_meanings": (
            [
                "candidate or post-exec hook not reached",
                "path or PID guard rejected",
                "retained magic invalid",
                "valid magic with idx below 24",
                "store, readback, or header-stability failure",
                "later overwrite, loss, or observer failure",
            ]
            if classification == "ZERO_AMBIGUOUS"
            else []
        ),
    }


if (
    CONTRACT_SHA256
    != "a01800f437cf129e693f32b7199ea6a613dd2366fff82ca45083f2098fd13bae"
    or len(ENTRY_PROOF) != ENTRY_SIZE
    or len(USERSPACE_PROOF) != ENTRY_SIZE
    or len(UNSAT_PROOF) != UNSAT_SIZE
):
    raise RuntimeError("fixed P2.19 same-ring decoder identity changed")
