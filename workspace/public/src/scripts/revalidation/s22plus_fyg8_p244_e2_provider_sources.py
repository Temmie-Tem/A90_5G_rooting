#!/usr/bin/env python3
"""Generate the P2.44 E2 provider-gate sources from pinned P2.41 inputs.

Host-only. The historical P2.41/P2.42 sources remain byte-identical; this
adapter applies a bounded, fail-closed transformation for the P2.44 contract.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SCRIPT_DIR))

import s22plus_fyg8_p243_rpmh_dependency_audit as p243  # noqa: E402


SCHEMA = "s22plus_fyg8_p244_e2_provider_sources_v1"
VERDICT = "PASS_P244_E2_PROVIDER_SOURCES_HOST_ONLY"

BASE_PATHS = {
    "plan": Path(
        "workspace/public/src/native-init/s22plus_fyg8_p241_e2_plan.h"
    ),
    "runtime": Path(
        "workspace/public/src/native-init/s22plus_fyg8_p241_e2_runtime.c"
    ),
    "checkpoint": Path(
        "workspace/public/src/native-init/s22plus_fyg8_p241_checkpoint.c"
    ),
    "patch": Path(
        "workspace/public/src/patches/"
        "s22plus_fyg8_p241_e2_latest_stage.patch"
    ),
}
BASE_SHA256 = {
    "plan": "2223ed333d6288e25b6ce7b7ae3aaa8dc31108dcc8536b9c582a7576953e7647",
    "runtime": "b70527307ff63713976371afddbdc13fa4b1bb009b527a74ab9997952e17aba6",
    "checkpoint": "de7ad8fdf83e7933ced221926a1b1c21568161ba796ea7a72a55fd5efc45edf9",
    "patch": "4148d981fd41832615d87eb15e8ca22eb9d73174d05b3e26f5063fd9799b3538",
}
GENERATED_SHA256 = {
    "plan": "874525283fe7d47ddbbddfa99b789eba73e283599a349af22c395014dec5f415",
    "runtime": "ffe325955dc62ce6684e95c54ae5895fd693cc918ff5fd3ef102581ad17f03f2",
    "checkpoint": "ed4c0395b90c6471959647f3b38dd2e9ee0787075538cfe1199ece4dc73df0c8",
    "patch": "1c9dc15b6bc19575cdd413487b610f1f2b4152a7c3bdb504dc90cbb95ab88be2",
}

GATES = (
    (
        "hwspinlock",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/qcom_hwspinlock/soc:hwlock",
        "soc:hwlock",
    ),
    (
        "smem",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/qcom-smem/soc:qcom,smem",
        "soc:qcom,smem",
    ),
    (
        "cmd-db",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/cmd-db/80860000.aop_cmd_db_region",
        "80860000.aop_cmd_db_region",
    ),
    (
        "psci-domain",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/psci-cpuidle-domain/soc:psci",
        "soc:psci",
    ),
    (
        "apps-rsc",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/rpmh/17a00000.rsc",
        "17a00000.rsc",
    ),
    (
        "apps-rpmh-clock",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/clk-rpmh/"
        "17a00000.rsc:qcom,rpmhclk",
        "17a00000.rsc:qcom,rpmhclk",
    ),
    (
        "apps-rpmh-cxlvl",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/qcom,rpmh-regulator/"
        "17a00000.rsc:rpmh-regulator-cxlvl",
        "17a00000.rsc:rpmh-regulator-cxlvl",
    ),
    (
        "apps-rpmh-mxlvl",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/qcom,rpmh-regulator/"
        "17a00000.rsc:rpmh-regulator-mxlvl",
        "17a00000.rsc:rpmh-regulator-mxlvl",
    ),
    (
        "gcc-waipio",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/gcc-waipio/"
        "100000.clock-controller",
        "100000.clock-controller",
    ),
    (
        "ssusb",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/msm-dwc3/a600000.ssusb",
        "a600000.ssusb",
    ),
    (
        "dwc3-core",
        "driver-bind-symlink",
        "/sys/bus/platform/drivers/dwc3/a600000.dwc3",
        "a600000.dwc3",
    ),
    (
        "udc",
        "class-device",
        "/sys/class/udc/a600000.dwc3",
        None,
    ),
)

MODULE_STAGE_FIRST = 0x40
MODULE_STAGE_LAST = 0x7A
GATE_STAGE_FIRST = 0x7B
GATE_STAGE_LAST = 0x86
SUCCESS_STAGE = 0x8F


class SourceError(ValueError):
    pass


def receipt(data: bytes) -> dict[str, Any]:
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _replace_exact(
    data: bytes,
    old: bytes,
    new: bytes,
    *,
    count: int,
    label: str,
) -> bytes:
    actual = data.count(old)
    if actual != count:
        raise SourceError(f"{label} replacement count {actual}, expected {count}")
    return data.replace(old, new)


def _replace_block(
    data: bytes,
    start: bytes,
    replacement: bytes,
    *,
    label: str,
) -> bytes:
    if data.count(start) != 1:
        raise SourceError(f"{label} start marker is not unique")
    begin = data.index(start)
    end = data.find(b"\n};", begin)
    if end < 0:
        raise SourceError(f"{label} end marker is absent")
    end += len(b"\n};")
    return data[:begin] + replacement + data[end:]


def _render_gate_table() -> bytes:
    lines = [
        "static const struct s22plus_o2_bind_gate_entry "
        "s22plus_o2_bind_gates[] = {"
    ]
    for order, (gate_id, kind, path, _basename) in enumerate(GATES, 1):
        lines.append(
            f'    {{{order}U, "{gate_id}", "{kind}", "{path}"}},'
        )
    lines.append("};")
    return ("\n".join(lines)).encode("ascii")


def _render_basenames() -> bytes:
    lines = ["static const char *const k_e2_gate_basenames[] = {"]
    lines.extend(
        f'    "{basename}",'
        for _gate_id, _kind, _path, basename in GATES
        if basename is not None
    )
    lines.extend(
        (
            "};",
            "",
            "_Static_assert(",
            "    sizeof(k_e2_gate_basenames) / "
            "sizeof(k_e2_gate_basenames[0]) ==",
            "        S22PLUS_O2_BIND_GATE_COUNT - 1U,",
            '    "E2 driver gate basename count");',
        )
    )
    return ("\n".join(lines)).encode("ascii")


def transform_plan(data: bytes) -> bytes:
    value = _replace_exact(
        data,
        b"S22PLUS_FYG8_P241_E2_PLAN_H",
        b"S22PLUS_FYG8_P244_E2_PLAN_H",
        count=2,
        label="plan include guard",
    )
    return _replace_block(
        value,
        b"static const struct s22plus_o2_bind_gate_entry "
        b"s22plus_o2_bind_gates[] = {",
        _render_gate_table(),
        label="plan gate table",
    )


def transform_runtime(data: bytes) -> bytes:
    replacements = (
        (
            b"/* P2.41 E2 exact-module and read-only bind/UDC runtime. */",
            b"/* P2.44 E2 provider-chain bind/UDC runtime. */",
            "runtime banner",
        ),
        (
            b'#error "P2.41 E2 runtime requires checkpoint profile 3"',
            b'#error "P2.44 E2 runtime requires checkpoint profile 3"',
            "runtime profile error",
        ),
        (
            b'#include "s22plus_fyg8_p241_e2_plan.h"',
            b'#include "s22plus_fyg8_p244_e2_plan.h"',
            "runtime plan include",
        ),
        (
            b"S22PLUS_O2_BIND_GATE_COUNT == 8U",
            b"S22PLUS_O2_BIND_GATE_COUNT == 12U",
            "runtime gate count",
        ),
        (
            b"== 0x82U,\n    \"E2 gate stage range\"",
            b"== 0x86U,\n    \"E2 gate stage range\"",
            "runtime gate stage range",
        ),
        (
            b"if (index < 7U) {",
            b"if (index + 1U < S22PLUS_O2_BIND_GATE_COUNT) {",
            "runtime UDC split",
        ),
    )
    value = data
    for old, new, label in replacements:
        value = _replace_exact(
            value, old, new, count=1, label=label
        )
    return _replace_block(
        value,
        b"static const char *const k_e2_gate_basenames[] = {",
        _render_basenames(),
        label="runtime gate basenames",
    )


def transform_checkpoint(data: bytes) -> bytes:
    value = _replace_exact(
        data,
        b"#define S22_P241_STAGE_E2_GATE_7 0x82U",
        b"#define S22_P244_STAGE_E2_GATE_11 0x86U",
        count=1,
        label="checkpoint last gate definition",
    )
    return _replace_exact(
        value,
        b"S22_P241_STAGE_E2_GATE_7",
        b"S22_P244_STAGE_E2_GATE_11",
        count=3,
        label="checkpoint last gate references",
    )


def transform_patch(data: bytes) -> bytes:
    return _replace_exact(
        data,
        b"+\t0x80, 0x81, 0x82, 0x8f,\n",
        b"+\t0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x8f,\n",
        count=1,
        label="kernel E2 sequence tail",
    )


def generate(root: Path | None = None) -> dict[str, bytes]:
    repository = p243.repo_root() if root is None else root
    base = {
        name: p243.stable_read(
            repository / path,
            f"P2.44 base {name}",
            BASE_SHA256[name],
            2 * 1024 * 1024,
        )
        for name, path in BASE_PATHS.items()
    }
    return {
        "plan": transform_plan(base["plan"]),
        "runtime": transform_runtime(base["runtime"]),
        "checkpoint": transform_checkpoint(base["checkpoint"]),
        "patch": transform_patch(base["patch"]),
    }


def build_result() -> dict[str, Any]:
    outputs = generate()
    actual = {
        name: hashlib.sha256(data).hexdigest()
        for name, data in outputs.items()
    }
    if actual != GENERATED_SHA256:
        raise SourceError(f"generated source identity changed: {actual}")
    return {
        "schema": SCHEMA,
        "verdict": VERDICT,
        "base": {
            name: {"path": str(BASE_PATHS[name]), "sha256": BASE_SHA256[name]}
            for name in sorted(BASE_PATHS)
        },
        "generated": {
            name: receipt(data) for name, data in sorted(outputs.items())
        },
        "gate_count": len(GATES),
        "driver_gate_count": sum(gate[3] is not None for gate in GATES),
        "stage_range": {
            "modules": [MODULE_STAGE_FIRST, MODULE_STAGE_LAST],
            "gates": [GATE_STAGE_FIRST, GATE_STAGE_LAST],
            "success": SUCCESS_STAGE,
        },
        "safety": {
            "host_only": True,
            "device_contact": False,
            "build": False,
            "image": False,
            "flash": False,
            "authority_created": False,
        },
    }


def main() -> int:
    try:
        result = build_result()
    except (
        SourceError,
        p243.AuditError,
        p243.p241.CheckError,
        p243.planner.PlanError,
        p243.boot_verify.BootVerifyError,
        p243.dtbo_contract.ContractError,
        OSError,
    ) as exc:
        print(json.dumps({"verdict": "FAIL_CLOSED", "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
