#!/usr/bin/env python3
"""Validate the P2.44 12-gate E2 provider-chain implementation host-only."""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SCRIPT_DIR))

import s22plus_fyg8_p232_e1_latest_stage_design as model  # noqa: E402
import s22plus_fyg8_p233_e1_static_checker as p233  # noqa: E402
import s22plus_fyg8_p241_e2_static_checker as p241  # noqa: E402
import s22plus_fyg8_p243_rpmh_dependency_audit as p243  # noqa: E402
import s22plus_fyg8_p244_e2_provider_sources as sources  # noqa: E402
import s22plus_o2_module_plan as planner  # noqa: E402


SCHEMA = "s22plus_fyg8_p244_e2_static_checker_v1"
VERDICT = "PASS_P244_E2_PROVIDER_IMPLEMENTATION_HOST_ONLY"
TARGET = model.TARGET
PROFILE = "E2"
RUN_ID = hashlib.sha256(
    b"S22PLUS-FYG8-P244-E2-PROVIDER-SOURCE-CHECK-V1"
).digest()[:16]

E2_SEQUENCE = (
    model.E1_LOCAL_SEQUENCE
    + tuple(range(sources.MODULE_STAGE_FIRST, sources.MODULE_STAGE_LAST + 1))
    + tuple(range(sources.GATE_STAGE_FIRST, sources.GATE_STAGE_LAST + 1))
    + (sources.SUCCESS_STAGE,)
)
REACHABLE_VARIANTS = (len(E2_SEQUENCE) - 1) * 4096 + 1


class CheckError(ValueError):
    pass


def receipt(data: bytes) -> dict[str, Any]:
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def ascii_text(data: bytes, label: str) -> str:
    try:
        return data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise CheckError(f"{label} is not ASCII") from exc


def audit_dependency_contract() -> dict[str, Any]:
    result = p243.build_result()
    if result["verdict"] != p243.VERDICT:
        raise CheckError("P2.43 dependency audit no longer passes")
    discriminator = result["bounded_discriminator"]
    source_chain = [
        {"id": gate_id, "path": path}
        for gate_id, _kind, path, _basename in sources.GATES[3:9]
    ]
    if (
        discriminator["ordered_predicates"] != source_chain
        or discriminator["replaces_existing_gates"]
        != ["rpmh", "gcc-waipio"]
        or discriminator["resulting_gate_count"] != len(sources.GATES)
        or discriminator["resulting_stage_range"]
        != {"first": "0x7b", "last": "0x86", "success": "0x8f"}
        or discriminator["add_modules"]
        or discriminator["do_not_add"] != ["dispcc-waipio.ko"]
    ):
        raise CheckError("P2.44 gate chain differs from the P2.43 design")
    return {
        "p243_verdict": result["verdict"],
        "failure_classification": result["failure_explanation"][
            "classification"
        ],
        "p242_live_root_cause_proven": result["failure_explanation"][
            "p242_live_root_cause_proven"
        ],
        "provider_chain": discriminator["ordered_predicates"],
        "replaces_existing_gates": discriminator["replaces_existing_gates"],
        "verified": True,
    }


def _parse_plan_modules(text: str) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        match.groups()
        for match in re.finditer(
            r'^\s+\{"([^"]+\.ko)", "([^"]+)", "([^"]*)"\},$',
            text,
            re.MULTILINE,
        )
    )


def _parse_plan_gates(
    text: str,
) -> tuple[tuple[int, str, str, str], ...]:
    return tuple(
        (int(order), gate_id, kind, path)
        for order, gate_id, kind, path in re.findall(
            r'^\s+\{(\d+)U, "([^"]+)", "([^"]+)", "([^"]+)"\},$',
            text,
            re.MULTILINE,
        )
    )


def _parse_runtime_basenames(text: str) -> tuple[str, ...]:
    match = re.search(
        r"static const char \*const k_e2_gate_basenames\[\] = \{"
        r"(?P<body>.*?)\n\};",
        text,
        re.DOTALL,
    )
    if match is None:
        raise CheckError("P2.44 runtime basename table is absent")
    return tuple(
        re.findall(r'^\s+"([^"]+)",$', match.group("body"), re.MULTILINE)
    )


def _expected_gates_from_p241(
    base_text: str, dependency: dict[str, Any]
) -> tuple[tuple[int, str, str, str], ...]:
    base_gates = _parse_plan_gates(base_text)
    replace_ids = tuple(dependency["replaces_existing_gates"])
    base_ids = tuple(row[1] for row in base_gates)
    if (
        len(base_gates) != 8
        or tuple(row[0] for row in base_gates) != tuple(range(1, 9))
        or len(set(row[3] for row in base_gates)) != len(base_gates)
        or base_gates[-1][1:] != (
            "udc",
            "class-device",
            "/sys/class/udc/a600000.dwc3",
        )
        or any(row[2] != "driver-bind-symlink" for row in base_gates[:-1])
    ):
        raise CheckError("P2.41 base gate contract changed")
    try:
        replace_at = base_ids.index(replace_ids[0])
    except (IndexError, ValueError) as exc:
        raise CheckError("P2.41 replacement gates are absent") from exc
    if base_ids[replace_at : replace_at + len(replace_ids)] != replace_ids:
        raise CheckError("P2.41 replacement gates are not one ordered span")

    provider_rows = tuple(
        (row["id"], "driver-bind-symlink", row["path"])
        for row in dependency["provider_chain"]
    )
    preserved_prefix = tuple(row[1:] for row in base_gates[:replace_at])
    preserved_suffix = tuple(
        row[1:] for row in base_gates[replace_at + len(replace_ids) :]
    )
    rows = preserved_prefix + provider_rows + preserved_suffix
    expected = tuple(
        (order, gate_id, kind, path)
        for order, (gate_id, kind, path) in enumerate(rows, 1)
    )
    if (
        len(expected) != 12
        or len(set(row[1] for row in expected)) != len(expected)
        or len(set(row[3] for row in expected)) != len(expected)
        or expected[-1][1:] != base_gates[-1][1:]
        or any(row[2] != "driver-bind-symlink" for row in expected[:-1])
    ):
        raise CheckError("P2.44 independently derived gate contract is invalid")
    return expected


def audit_plan(
    root: Path, data: bytes, dependency: dict[str, Any]
) -> tuple[planner.ModulePlan, dict[str, Any]]:
    text = ascii_text(data, "P2.44 plan")
    base_header = p243.stable_read(
        root / sources.BASE_PATHS["plan"],
        "P2.41 base plan",
        sources.BASE_SHA256["plan"],
        1024 * 1024,
    )
    metadata, plan, base_audit = p241.audit_plan(
        root / planner.DEFAULT_METADATA_DIR, base_header
    )
    modules = _parse_plan_modules(text)
    expected_modules = tuple(
        (
            name,
            planner.normalize_module_name(name),
            metadata.options.get(name, ""),
        )
        for name in plan.modules
    )
    expected_gates = _expected_gates_from_p241(
        ascii_text(base_header, "P2.41 base plan"),
        dependency,
    )
    gates = _parse_plan_gates(text)
    if (
        modules != expected_modules
        or gates != expected_gates
        or len(set(name for name, _runtime, _params in modules))
        != len(modules)
        or "dispcc-waipio.ko" in {row[0] for row in modules}
    ):
        raise CheckError("P2.44 generated plan contract mismatch")
    return plan, {
        **receipt(data),
        "module_count": len(modules),
        "constraint_count": base_audit["constraint_count"],
        "gate_count": len(gates),
        "module_order_unchanged": True,
        "display_module_absent": True,
        "preserved_from_p241": [
            row[1] for row in expected_gates[:3] + expected_gates[-3:]
        ],
        "gate_ids_unique": True,
        "gate_paths_unique": True,
        "last_gate_udc_class": True,
        "gates": [
            {"order": order, "id": gate_id, "kind": kind, "path": path}
            for order, gate_id, kind, path in gates
        ],
        "verified": True,
    }


def audit_sources(
    plan_data: bytes,
    runtime_data: bytes,
    checkpoint_data: bytes,
    plan_audit: dict[str, Any],
) -> dict[str, Any]:
    plan = ascii_text(plan_data, "P2.44 plan")
    runtime = ascii_text(runtime_data, "P2.44 runtime")
    checkpoint = ascii_text(checkpoint_data, "P2.44 checkpoint")
    required_runtime = (
        '#include "s22plus_fyg8_p244_e2_plan.h"',
        "S22PLUS_O2_BIND_GATE_COUNT == 12U",
        "== 0x86U,\n    \"E2 gate stage range\"",
        "S22PLUS_O2_BIND_GATE_COUNT - 1U",
        "if (index + 1U < S22PLUS_O2_BIND_GATE_COUNT)",
        "p241_check_driver_symlink(index)",
        "p241_check_udc()",
        "s22_r4w1e_checkpoint_success(&g_checkpoint)",
    )
    required_checkpoint = (
        "#define S22_P244_STAGE_E2_GATE_11 0x86U",
        "stage < S22_P244_STAGE_E2_GATE_11",
        "stage == S22_P244_STAGE_E2_GATE_11",
        "stage <= S22_P244_STAGE_E2_GATE_11",
    )
    missing = [token for token in required_runtime if token not in runtime]
    missing.extend(
        token for token in required_checkpoint if token not in checkpoint
    )
    if missing:
        raise CheckError(f"P2.44 generated source contract missing: {missing}")
    forbidden = (
        "af20000.rsc",
        "dispcc-waipio.ko",
        "/config/usb_gadget",
        "/dev/block",
        "kernel_restart",
        "emergency_restart",
        "SYS_reboot",
    )
    present = [token for token in forbidden if token in runtime + checkpoint]
    if present:
        raise CheckError(f"P2.44 generated source widens authority: {present}")
    if any(plan.count(row["path"]) != 1 for row in plan_audit["gates"]):
        raise CheckError("P2.44 plan gate path cardinality changed")
    expected_basenames = tuple(
        row["path"].rsplit("/", 1)[-1]
        for row in plan_audit["gates"]
        if row["kind"] == "driver-bind-symlink"
    )
    basenames = _parse_runtime_basenames(runtime)
    if (
        basenames != expected_basenames
        or len(basenames) != 11
        or len(set(basenames)) != len(basenames)
    ):
        raise CheckError("P2.44 runtime driver basenames differ from gate paths")
    return {
        "runtime": receipt(runtime_data),
        "checkpoint": receipt(checkpoint_data),
        "driver_gate_count": len(expected_basenames),
        "udc_gate_count": 1,
        "driver_basenames": list(basenames),
        "basenames_derived_from_gate_paths": True,
        "read_only_gate_phase": True,
        "verified": True,
    }


def audit_patch(root: Path, data: bytes, path: Path) -> dict[str, Any]:
    text = ascii_text(data, "P2.44 kernel patch")
    path.write_bytes(data)
    p233.run_checked(
        ["git", "apply", "--check", "--unsafe-paths", str(path)],
        cwd=root / p241.DEFAULT_SOURCE,
        label="P2.44 clean-apply check",
    )
    match = re.search(
        r"s22_fyg8_e2_sequence\[\]\s*=\s*\{(?P<body>.*?)\};",
        text,
        re.DOTALL,
    )
    if match is None:
        raise CheckError("P2.44 kernel E2 sequence is absent")
    values = tuple(
        int(value, 16)
        for value in re.findall(r"0x([0-9a-fA-F]+)", match.group("body"))
    )
    if values != E2_SEQUENCE:
        raise CheckError("P2.44 kernel E2 sequence differs from the contract")
    if text.count("0x83, 0x84, 0x85, 0x86") != 1:
        raise CheckError("P2.44 provider stage tail cardinality changed")
    return {
        **receipt(data),
        "clean_apply": True,
        "sequence_count": len(values),
        "gate_stage_count": len(sources.GATES),
        "terminal": values[-1],
        "verified": True,
    }


@contextlib.contextmanager
def p244_model_contract() -> Iterator[None]:
    old_gate = model.STAGES["E2_GATE_7"]
    old_sequence = model.PROFILE_STAGE_SEQUENCES["E2"]
    try:
        model.STAGES["E2_GATE_7"] = sources.GATE_STAGE_LAST
        model.PROFILE_STAGE_SEQUENCES["E2"] = E2_SEQUENCE
        yield
    finally:
        model.STAGES["E2_GATE_7"] = old_gate
        model.PROFILE_STAGE_SEQUENCES["E2"] = old_sequence


def audit_reachable_records() -> tuple[dict[str, Any], dict[str, Any]]:
    with p244_model_contract():
        reachable = p233.validate_reachable_records({PROFILE: RUN_ID})
    if reachable["reachable_slot_variants"] != REACHABLE_VARIANTS:
        raise CheckError("P2.44 reachable record count mismatch")
    if model.STAGES["E2_GATE_7"] != 0x82:
        raise CheckError("historical E2 model was not restored")
    regression = p233.validate_reachable_records(p233.SOURCE_CHECK_RUN_IDS)
    if regression["reachable_slot_variants"] != 90_114:
        raise CheckError("E1A/E1B reachable identity regression")
    return reachable, regression


def audit_linked_userspace(
    root: Path,
    generated: dict[str, bytes],
    directory: Path,
) -> dict[str, Any]:
    plan = directory / "s22plus_fyg8_p244_e2_plan.h"
    runtime = directory / "s22plus_fyg8_p244_e2_runtime.c"
    checkpoint = directory / "s22plus_fyg8_p244_checkpoint.c"
    plan.write_bytes(generated["plan"])
    runtime.write_bytes(generated["runtime"])
    checkpoint.write_bytes(generated["checkpoint"])
    linked = p241.compile_runtime(
        root, runtime, checkpoint, root / p241.DEFAULT_CHILD
    )

    define = p233._run_id_define(RUN_ID)
    outputs: list[Path] = []
    for suffix in ("a", "b"):
        output = directory / f"init-{suffix}"
        p233.run_checked(
            [
                "aarch64-linux-gnu-gcc",
                *p233.legacy_e1.COMPILE_FLAGS,
                "-DS22PLUS_FYG8_P233_PROFILE=3",
                f"-DS22PLUS_FYG8_P233_RUN_ID_BYTES={define}",
                "-I",
                str(directory),
                "-I",
                str(root / "workspace/public/src/native-init"),
                str(runtime),
                str(checkpoint),
                "-o",
                str(output),
            ],
            cwd=root,
            label=f"P2.44 deterministic E2 cross-link {suffix}",
        )
        outputs.append(output)
    data = outputs[0].read_bytes()
    if data != outputs[1].read_bytes():
        raise CheckError("P2.44 repeated userspace link differs")
    file_text = p233.run_checked(
        ["file", "-b", str(outputs[0])],
        cwd=root,
        label="P2.44 file inspection",
    ).stdout.decode("ascii", "replace")
    readelf = p233.run_checked(
        ["aarch64-linux-gnu-readelf", "-W", "-h", "-l", str(outputs[0])],
        cwd=root,
        label="P2.44 readelf inspection",
    ).stdout.decode("ascii", "replace")
    undefined = p233.run_checked(
        ["aarch64-linux-gnu-nm", "-u", str(outputs[0])],
        cwd=root,
        label="P2.44 undefined-symbol inspection",
    ).stdout
    if (
        "ELF 64-bit LSB executable, ARM aarch64" not in file_text
        or "statically linked" not in file_text
        or "INTERP" in readelf
        or "DYNAMIC" in readelf
        or undefined.strip()
        or data.count(RUN_ID) != 1
    ):
        raise CheckError("P2.44 linked ELF contract mismatch")
    if any(
        data.count(path.encode("ascii")) != 1
        for _id, _kind, path, _basename in sources.GATES
    ):
        raise CheckError("P2.44 linked gate strings are not exact")
    if b"af20000.rsc" in data or b"dispcc-waipio.ko" in data:
        raise CheckError("P2.44 linked runtime contains retired display scope")
    return {
        "init": {
            **receipt(data),
            "static_aarch64": True,
            "undefined_symbols": 0,
            "run_id_count": 1,
        },
        "child": linked["child"],
        "p241_reference_contract": linked["init"],
        "all_12_gate_paths_exact": True,
        "retired_display_scope_absent": True,
        "two_link_reproducible": True,
    }


def build_result() -> dict[str, Any]:
    root = p243.repo_root()
    generation = sources.build_result()
    generated = sources.generate(root)
    dependency = audit_dependency_contract()
    plan, plan_audit = audit_plan(root, generated["plan"], dependency)
    reachable, regression = audit_reachable_records()
    with tempfile.TemporaryDirectory(prefix="s22-p244-e2-") as name:
        directory = Path(name)
        patch = audit_patch(
            root, generated["patch"], directory / "p244.patch"
        )
        linked = audit_linked_userspace(root, generated, directory)
    vendor = p241.audit_vendor_modules(
        root,
        root / p241.DEFAULT_VENDOR_RAMDISK,
        root / p241.DEFAULT_LZ4,
        plan,
    )
    return {
        "schema": SCHEMA,
        "verdict": VERDICT,
        "target": TARGET,
        "profile": PROFILE,
        "profile_number": 3,
        "run_id": RUN_ID.hex(),
        "generation": generation,
        "dependency_contract": dependency,
        "plan": plan_audit,
        "sources": audit_sources(
            generated["plan"],
            generated["runtime"],
            generated["checkpoint"],
            plan_audit,
        ),
        "patch": patch,
        "linked_userspace": linked,
        "vendor_rootfs": {
            "module_count": vendor["module_count"],
            "vendor_ramdisk": vendor["vendor_ramdisk"],
            "sec_log_buf_absent": vendor["sec_log_buf_absent"],
            "verified": vendor["verified"],
        },
        "reachable_record_contract": reachable,
        "e1a_e1b_regression": regression,
        "safety": {
            "host_only": True,
            "kernel_built": False,
            "image_built": False,
            "candidate_created": False,
            "manifest_created": False,
            "device_contact": False,
            "device_write": False,
            "odin_invoked": False,
            "live_authorized": False,
            "sysfs_write": False,
            "configfs_write": False,
        },
        "next": "separate P2.45 reproducible candidate construction",
    }


def main() -> int:
    try:
        result = build_result()
    except (
        CheckError,
        sources.SourceError,
        p243.AuditError,
        p241.CheckError,
        p233.CheckError,
        planner.PlanError,
        model.DesignError,
        p243.boot_verify.BootVerifyError,
        p243.dtbo_contract.ContractError,
        subprocess.TimeoutExpired,
        OSError,
    ) as exc:
        print(json.dumps({"verdict": "FAIL_CLOSED", "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
