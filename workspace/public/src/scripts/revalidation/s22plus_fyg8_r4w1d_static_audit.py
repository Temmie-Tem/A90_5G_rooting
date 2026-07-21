#!/usr/bin/env python3
"""Run the fail-closed R4W1-D static compatibility audit host-only."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import s22plus_fyg8_kernel_r2_audit as r2  # noqa: E402
import s22plus_fyg8_r4w1b_static_audit as engine  # noqa: E402
import s22plus_fyg8_r4w1d_build as r4w1d_build  # noqa: E402
import s22plus_fyg8_r4w1d_elf_audit as elf_audit  # noqa: E402
import s22plus_fyg8_r4w1d_witness_contract as contract  # noqa: E402


SCHEMA = "s22plus_fyg8_r4w1d_static_audit_v1"
TARGET = r2.TARGET
VERDICT = "PASS_R4W1D_STATIC_COMPATIBILITY"
BLOCKED_VERDICT = "BLOCKED_R4W1D_STATIC_COMPATIBILITY"
STATIC_PASS_FIELD = "r4w1d_static_pass"
DEFAULT_OUT = Path(
    "workspace/private/outputs/s22plus_fyg8_r4w1d_static_audit/result.json"
)
HISTORICAL_MARKER_FAMILY = b"[[S22R4W1"
PATCH_ADAPTER = SimpleNamespace(
    MARKER=contract.PROOF,
    MARKER_ID=contract.MARKER_ID,
    PATCH_SHA256=contract.PATCH_SHA256,
    VERDICT=contract.VERDICT,
)


class _BuildAdapter:
    def __getattr__(self, name: str) -> Any:
        if hasattr(r4w1d_build, name):
            return getattr(r4w1d_build, name)
        return getattr(r4w1d_build.engine, name)


BUILD_ADAPTER = _BuildAdapter()

AuditError = engine.AuditError
ARM64_IMAGE_HEADER = engine.ARM64_IMAGE_HEADER
CRITICAL_SECURITY_CONFIGS = engine.CRITICAL_SECURITY_CONFIGS
PINNED_BASELINE_INPUTS = engine.PINNED_BASELINE_INPUTS
FIPS_SOURCE_INPUTS = engine.FIPS_SOURCE_INPUTS
FIPS_RUNTIME_SCRIPT_NAMES = engine.FIPS_RUNTIME_SCRIPT_NAMES
FIPS_CRYPTO_OBJECTS = engine.FIPS_CRYPTO_OBJECTS
FIPS_ARM64_CRYPTO_OBJECTS = engine.FIPS_ARM64_CRYPTO_OBJECTS
file_identity = engine.file_identity
check_pinned_identity = engine.check_pinned_identity
check_arm64_image_header = engine.check_arm64_image_header
count_file_occurrences = engine.count_file_occurrences
compare_full_symvers = engine.compare_full_symvers
compare_abi_definition = engine.compare_abi_definition
check_sec_log_buf_module = engine.check_sec_log_buf_module


@contextmanager
def _bind_engine_contract() -> Iterator[None]:
    replacements = {
        "SCHEMA": SCHEMA,
        "VERDICT": VERDICT,
        "WITNESS_CONFIG": contract.CONFIG,
        "BUILD_PASS_FIELD": "r4w1d_build_pass",
        "PATCH_CONTRACT_FIELD": "r4w1d_witness_contract",
        "STATIC_PASS_FIELD": STATIC_PASS_FIELD,
        "BLOCKED_VERDICT": BLOCKED_VERDICT,
        "AUDIT_LABEL": "R4W1-D",
        "MARKER_FAMILY": contract.PROOF_FAMILY.encode("ascii"),
        "HISTORICAL_MARKER_FAMILY": HISTORICAL_MARKER_FAMILY,
        "r4w1b_build": BUILD_ADAPTER,
        "patch_check": PATCH_ADAPTER,
        "elf_audit": elf_audit,
    }
    previous = {name: getattr(engine, name) for name in replacements}
    try:
        for name, value in replacements.items():
            setattr(engine, name, value)
        yield
    finally:
        for name, value in previous.items():
            setattr(engine, name, value)


def compare_r4w1d_configs(stock_path: Path, generated_path: Path) -> dict[str, Any]:
    with _bind_engine_contract():
        return engine.compare_r4w1b_configs(stock_path, generated_path)


def audit_build_result(path: Path, **kwargs: Any) -> dict[str, Any]:
    with _bind_engine_contract():
        return engine.audit_build_result(path, **kwargs)


def check_final_binary_contract(**kwargs: Any) -> dict[str, Any]:
    with _bind_engine_contract():
        return engine.check_final_binary_contract(**kwargs)


def run_audit(root: Path, **kwargs: Any) -> dict[str, Any]:
    with _bind_engine_contract():
        return engine.run_audit(root, **kwargs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-tree", type=Path, required=True)
    parser.add_argument("--build-result", type=Path, required=True)
    parser.add_argument(
        "--baseline-symvers", type=Path, default=engine.DEFAULT_BASELINE_SYMVERS
    )
    parser.add_argument("--baseline-abi", type=Path, default=engine.DEFAULT_BASELINE_ABI)
    parser.add_argument("--symvers", type=Path, action="append")
    parser.add_argument("--stock-baseline", type=Path, default=r2.DEFAULT_STOCK_BASELINE)
    parser.add_argument("--stock-config", type=Path, default=r2.DEFAULT_STOCK_CONFIG)
    parser.add_argument("--requirements", type=Path, action="append")
    parser.add_argument("--module-map", type=Path, default=r2.DEFAULT_MODULE_MAP)
    parser.add_argument("--corpus-layout", type=Path, default=r2.DEFAULT_CORPUS_LAYOUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = r2.repo_root()
    requirements = args.requirements or [
        r2.DEFAULT_REQUIREMENTS,
        r2.DEFAULT_EXTRA_REQUIREMENTS,
    ]
    path_arguments = [
        args.work_tree,
        args.build_result,
        args.baseline_symvers,
        args.baseline_abi,
        args.stock_baseline,
        args.stock_config,
        args.module_map,
        args.corpus_layout,
        args.out,
        *(args.symvers or []),
        *requirements,
    ]
    if any(path.is_absolute() for path in path_arguments):
        raise AuditError("R4W1-D isolated audit requires repo-relative paths")
    reexecuted = r4w1d_build.engine.reexec_in_private_repo_namespace(
        root,
        script=Path(__file__),
        arguments=sys.argv[1:],
        compatibility_work_tree=args.work_tree,
    )
    if reexecuted is not None:
        return reexecuted
    private_namespace = r4w1d_build.engine.inspect_private_namespace(root)
    if not private_namespace["verified"]:
        raise AuditError("R4W1-D private repository namespace is not verified")
    recorded_root = Path(private_namespace["recorded_repo"])
    result = run_audit(
        root,
        recorded_root=recorded_root,
        work_tree=r2.resolve(root, args.work_tree),
        build_result=r2.resolve(root, args.build_result),
        baseline_symvers=r2.resolve(root, args.baseline_symvers),
        baseline_abi=r2.resolve(root, args.baseline_abi),
        symvers_paths=(
            [r2.resolve(root, path) for path in args.symvers]
            if args.symvers
            else None
        ),
        stock_baseline=r2.resolve(root, args.stock_baseline),
        stock_config=r2.resolve(root, args.stock_config),
        requirements=[r2.resolve(root, path) for path in requirements],
        module_map=r2.resolve(root, args.module_map),
        corpus_layout=r2.resolve(root, args.corpus_layout),
    )
    result["private_namespace"] = private_namespace
    out = r2.resolve(root, args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    recorded_result = r4w1d_build.engine.rebase_recorded_paths(
        result,
        observed_root=root,
        recorded_root=recorded_root,
        embedded=True,
    )
    out.write_text(
        json.dumps(recorded_result, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    print(
        json.dumps(
            {
                "result": "pass" if result[STATIC_PASS_FIELD] else "blocked",
                "out": r2.display_path(root, out),
                "blocker_count": len(result["blockers"]),
                "fixed_layout_remaining": result["gates"]["fixed_layout"][
                    "remaining"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result[STATIC_PASS_FIELD] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AuditError, OSError, KeyError) as exc:
        raise SystemExit(str(exc)) from exc
