#!/usr/bin/env python3
"""Decode repeated FYG8 same-ring records across candidate boots."""

from __future__ import annotations

import hashlib
from typing import Any

import s22plus_fyg8_p219_same_ring_decoder as base


POLICY_PREIMAGE = (
    "S22PLUS_FYG8_P230_SAME_RING_MULTIBOOT_POLICY_V1|"
    "base=a01800f437cf129e693f32b7199ea6a613dd2366fff82ca45083f2098fd13bae|"
    "baseline=both-families-absent|"
    "accept=one-or-more-exact-userspace-only|"
    "reject=mixed,foreign,partial|"
    "zero=ambiguous|"
    "scope=bounded-post-rollback-snapshot"
)
POLICY_SHA256 = hashlib.sha256(POLICY_PREIMAGE.encode("ascii")).hexdigest()
POLICY_ID = bytes.fromhex(POLICY_SHA256[:32])


class DecodeError(ValueError):
    pass


def _edge_partial(payload: bytes) -> bool:
    records = (base.ENTRY_PROOF, base.USERSPACE_PROOF, base.UNSAT_PROOF)
    for record in records:
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
        raise DecodeError("same-ring multiboot observation must be raw bytes")

    entry_count = payload.count(base.ENTRY_PROOF)
    userspace_count = payload.count(base.USERSPACE_PROOF)
    unsat_count = payload.count(base.UNSAT_PROOF)
    long_family_count = payload.count(base.ENTRY_FAMILY)
    unsat_family_count = payload.count(base.UNSAT_FAMILY)
    partial = _edge_partial(payload)
    exact_total = entry_count + userspace_count + unsat_count
    populated_states = sum(
        count > 0 for count in (entry_count, userspace_count, unsat_count)
    )
    integrity_issue = (
        partial
        or populated_states > 1
        or long_family_count != entry_count + userspace_count
        or unsat_family_count != unsat_count
    )

    if integrity_issue:
        classification = "AMBIGUOUS_INTEGRITY_FAILURE"
        accepted = False
    elif userspace_count >= 1:
        classification = "USERSPACE_CALLBACK_REACHED_ONE_OR_MORE_BOOTS"
        accepted = True
    elif entry_count >= 1:
        classification = "ENTRY_ONLY_ONE_OR_MORE_BOOTS"
        accepted = False
    elif unsat_count >= 1:
        classification = "UNSAT_VALID_MAGIC_ONE_OR_MORE_BOOTS"
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
        "exact_record_count": exact_total,
        "long_family_count": long_family_count,
        "unsat_family_count": unsat_family_count,
        "partial_at_snapshot_edge": partial,
        "minimum_candidate_boots": exact_total if not integrity_issue else 0,
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
    POLICY_SHA256
    != "4a2a4f5740565b22e533e23a23d32ff6c380735224adc165192a57d9defa3f1f"
    or base.CONTRACT_SHA256
    != "a01800f437cf129e693f32b7199ea6a613dd2366fff82ca45083f2098fd13bae"
):
    raise RuntimeError("fixed P2.30 multiboot decoder identity changed")
