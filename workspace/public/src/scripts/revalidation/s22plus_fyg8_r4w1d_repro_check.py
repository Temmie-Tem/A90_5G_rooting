#!/usr/bin/env python3
"""Check two independent FYG8 R4W1-D Full-LTO reproductions host-only."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import s22plus_fyg8_r4w1b_repro_check as engine  # noqa: E402
import s22plus_fyg8_r4w1d_build as r4w1d_build  # noqa: E402
import s22plus_fyg8_r4w1d_static_audit as static_audit  # noqa: E402
import s22plus_fyg8_r4w1d_witness_contract as contract  # noqa: E402


SCHEMA = "s22plus_fyg8_r4w1d_repro_check_v1"
TARGET = contract.TARGET
VERDICT = "PASS_R4W1D_CLEAN_REPRODUCIBILITY"
BLOCKED_VERDICT = "BLOCKED_R4W1D_REPRODUCIBILITY"
EXPECTED_SOURCE_SYMLINK_COUNT = 5
CheckError = engine.CheckError
sha256_file = engine.sha256_file
load_json = engine.load_json
normalized_config = engine.normalized_config
identity_gate = engine.identity_gate
check_artifact_binding = engine.check_artifact_binding
check_distinct_artifact_paths = engine.check_distinct_artifact_paths


@contextmanager
def _bind_engine_contract() -> Iterator[None]:
    replacements = {
        "SCHEMA": SCHEMA,
        "TARGET": TARGET,
        "VERDICT": VERDICT,
        "BLOCKED_VERDICT": BLOCKED_VERDICT,
        "BUILD_SCHEMA": r4w1d_build.SCHEMA,
        "STATIC_SCHEMA": static_audit.SCHEMA,
        "PATCH_SHA256": contract.PATCH_SHA256,
        "MARKER": contract.PROOF.encode("ascii"),
        "MARKER_FAMILY": contract.PROOF_FAMILY.encode("ascii"),
        "HISTORICAL_MARKER_FAMILY": static_audit.HISTORICAL_MARKER_FAMILY,
        "WITNESS_CONFIG": contract.CONFIG,
        "BUILD_PASS_FIELD": "r4w1d_build_pass",
        "STATIC_PASS_FIELD": static_audit.STATIC_PASS_FIELD,
        "IMAGE_SIZE": r4w1d_build.engine.STOCK_IMAGE_SIZE,
        "ALIGNED_SIZE": r4w1d_build.engine.FIXED_KERNEL_SLOT_CAPACITY,
        "static_audit": static_audit,
    }
    previous = {name: getattr(engine, name) for name in replacements}
    try:
        for name, value in replacements.items():
            setattr(engine, name, value)
        yield
    finally:
        for name, value in previous.items():
            setattr(engine, name, value)


def check_build(path: Path) -> dict[str, Any]:
    with _bind_engine_contract():
        return engine.check_build(path)


def check_image(path: Path) -> dict[str, Any]:
    with _bind_engine_contract():
        return engine.check_image(path)


def check_static(
    path: Path, *, build_result: Path, expected_inputs: dict[str, Path]
) -> dict[str, Any]:
    with _bind_engine_contract():
        return engine.check_static(
            path, build_result=build_result, expected_inputs=expected_inputs
        )


def source_link_identity(control: dict[str, Any]) -> list[dict[str, str]] | None:
    links = control.get("links")
    if not isinstance(links, list):
        return None
    identity: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in links:
        if not isinstance(row, dict):
            return None
        relative_path = row.get("relative_path")
        expected_target = row.get("expected_target")
        if (
            not isinstance(relative_path, str)
            or not relative_path
            or relative_path in seen
            or not isinstance(expected_target, str)
            or not expected_target
        ):
            return None
        seen.add(relative_path)
        identity.append(
            {
                "relative_path": relative_path,
                "expected_target": expected_target,
            }
        )
    return sorted(identity, key=lambda row: row["relative_path"])


def source_restoration_gate(build_paths: tuple[Path, Path]) -> dict[str, Any]:
    rows = []
    for path in build_paths:
        value = load_json(path)
        work_tree_value = value.get("work_tree")
        overlay = value.get("provenance", {}).get("source_overlay", {})
        current = (
            r4w1d_build.inspect_source_symlink_control(
                Path(work_tree_value), overlay
            )
            if isinstance(work_tree_value, str) and work_tree_value
            else {"verified": False, "reason": "missing-work-tree"}
        )
        runtime = value.get("source_symlink_control_runtime")
        current_identity = source_link_identity(current)
        runtime_identity = (
            source_link_identity(runtime) if isinstance(runtime, dict) else None
        )
        identity_match = (
            current_identity is not None
            and runtime_identity is not None
            and len(current_identity) == EXPECTED_SOURCE_SYMLINK_COUNT
            and runtime_identity == current_identity
            and runtime.get("members_sha256") == current.get("members_sha256")
            and isinstance(current.get("members_sha256"), str)
            and len(current["members_sha256"]) == 64
        )
        runtime_verified = (
            isinstance(runtime, dict)
            and runtime.get("verified") is True
            and runtime.get("restored") is True
            and runtime.get("absolute_symlink_count")
            == current.get("absolute_symlink_count")
            == EXPECTED_SOURCE_SYMLINK_COUNT
            and runtime.get("mutation_count", 0) > 0
            and identity_match
            and all(
                row.get("verified") is True
                and row.get("restored_target") == row.get("expected_target")
                for row in runtime.get("links", [])
            )
            and all(
                row.get("verified") is True
                and row.get("actual_target") == row.get("expected_target")
                for row in current.get("links", [])
            )
        )
        rows.append(
            {
                "build_result": str(path),
                "current_control": current,
                "recorded_runtime_present": isinstance(runtime, dict),
                "recorded_runtime_identity": runtime_identity,
                "current_identity": current_identity,
                "recorded_runtime_identity_match": identity_match,
                "recorded_runtime_verified": runtime_verified,
            }
        )
    result = {
        "builds": rows,
        "current_controls_verified": all(
            row["current_control"].get("verified") is True for row in rows
        ),
        "recorded_successful_runtime_count": sum(
            row["recorded_runtime_verified"] for row in rows
        ),
        "final_hardening_full_build_claimed": False,
    }
    result["verified"] = (
        result["current_controls_verified"]
        and result["recorded_successful_runtime_count"] >= 1
    )
    return result


def run_check(**kwargs: Any) -> dict[str, Any]:
    with _bind_engine_contract():
        result = engine.run_check(**kwargs)
    restoration = source_restoration_gate(
        (kwargs["build_a"], kwargs["build_b"])
    )
    result["source_symlink_restoration"] = restoration
    if not restoration["verified"]:
        result["blockers"].append(
            "source symlink current-state or recorded restoration evidence failed"
        )
    result["reproducible"] = not result["blockers"]
    result["verdict"] = VERDICT if result["reproducible"] else BLOCKED_VERDICT
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "build-a",
        "build-b",
        "static-a",
        "static-b",
        "image-a",
        "image-b",
        "config-a",
        "config-b",
        "symvers-a",
        "symvers-b",
        "abi-a",
        "abi-b",
        "vmlinux-a",
        "vmlinux-b",
        "system-map-a",
        "system-map-b",
        "out",
    ):
        parser.add_argument(f"--{name}", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = engine.repo_root()
    result = run_check(
        **{
            name: engine.resolve(root, getattr(args, name))
            for name in (
                "build_a",
                "build_b",
                "static_a",
                "static_b",
                "image_a",
                "image_b",
                "config_a",
                "config_b",
                "symvers_a",
                "symvers_b",
                "abi_a",
                "abi_b",
                "vmlinux_a",
                "vmlinux_b",
                "system_map_a",
                "system_map_b",
            )
        }
    )
    out = engine.resolve(root, args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(
        json.dumps(
            {
                "result": "pass" if result["reproducible"] else "blocked",
                "image_sha256": result["images"][0]["sha256"],
                "blocker_count": len(result["blockers"]),
                "out": str(out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["reproducible"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CheckError, OSError, KeyError) as exc:
        raise SystemExit(str(exc)) from exc
