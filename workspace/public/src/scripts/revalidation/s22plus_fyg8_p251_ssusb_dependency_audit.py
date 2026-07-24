#!/usr/bin/env python3
"""Reconstruct the exact P2.50 SSUSB timeout boundary.

Host-only. This checker pins the P2.49 runtime and plan, the P2.50 retained
result, FYG8 source and DT artifacts, the shipped dwc3-msm module, and the
same-build stock topology. It does not build, contact a device, or grant live
authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SCRIPT_DIR))

import s22plus_fyg8_p241_dtbo_role_contract as dtbo_contract  # noqa: E402
import s22plus_fyg8_p243_rpmh_dependency_audit as p243  # noqa: E402
import s22plus_fyg8_usb_role_static_re as usb_static_re  # noqa: E402


SCHEMA = "s22plus_fyg8_p251_ssusb_dependency_audit_v1"
VERDICT = "PASS_P251_SSUSB_DEPENDENCY_AUDIT_HOST_ONLY"
TARGET = "SM-S906N/g0q/S906NKSS7FYG8"

DEFAULT_VENDOR_DTB = Path(
    "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
    "extracted-images/unpack-vendor-boot/dtb"
)
DEFAULT_DWC3_MSM = Path(
    "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
    "extracted-images/ramdisk-list/vendor/extract/lib/modules/dwc3-msm.ko"
)
DEFAULT_VENDOR_BOOT = Path(
    "workspace/private/inputs/s22plus_firmware/S906NKSS7FYG8_SKC/"
    "extracted-images/raw/vendor_boot.img"
)
DEFAULT_CANDIDATE_BOOT = Path(
    "workspace/private/outputs/s22plus_fyg8_p249/candidate-a/boot.img"
)
DEFAULT_CONFIG = Path(
    "workspace/private/outputs/s22plus_fyg8_p249/artifacts-a/.config"
)
DEFAULT_PLAN = Path(
    "workspace/private/outputs/s22plus_fyg8_p249/intent/"
    "materialized-sources/s22plus_fyg8_p244_e2_plan.h"
)
DEFAULT_RUNTIME = Path(
    "workspace/private/outputs/s22plus_fyg8_p249/intent/"
    "materialized-sources/s22plus_fyg8_p248_e2_runtime.c"
)
DEFAULT_LIVE_RESULT = Path(
    "workspace/private/runs/device-action-f1-live-v2/"
    "p249-20260724-2/live-result.json"
)
DEFAULT_STOCK_TOPOLOGY = Path(
    "docs/module-map/s22plus-fyg8/stock-usb-runtime-topology.json"
)
DEFAULT_DEEP_STATIC = Path(
    "docs/module-map/s22plus-fyg8/deep-usb-re/static-analysis.json"
)
DEFAULT_STOCK_LIVE_CMDLINE = Path(
    "workspace/private/runs/s22plus_o3r1_native_retained_sysrq_live_gate_"
    "20260709T220014Z/sec_debug_state/pre_o3r1/proc__cmdline.txt"
)
DEFAULT_BASE_SOURCE = Path(
    "workspace/private/inputs/s22plus_kernel_source/"
    "SM-S906N_15_base_osrc/Kernel.tar.gz"
)
DEFAULT_DELTA_SOURCE = Path(
    "workspace/private/inputs/s22plus_kernel_source/"
    "S906NKSS7FYG8_osrc/S906NKSS7FYG8_kernel.tar.gz"
)

EXPECTED_SHA256 = {
    "vendor_dtb": "2cd64d43a4f6b89a7c5523f3ef73fbb84dcad92c6d857e649cd1f0baa7c0080e",
    "dwc3_msm": "8913b050419e88699033e957d927beef86742ed035f531dc5c4729f50cea60f1",
    "vendor_boot": "096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7",
    "candidate_boot": "2f59ff74d6afc2a8044562311c6f30cab26c661c9542f8d84795b454026fd47d",
    "config": "9fcc7c030095667674ec4da17768529a602c916ada1346132193e7968b57aaec",
    "plan": "874525283fe7d47ddbbddfa99b789eba73e283599a349af22c395014dec5f415",
    "runtime": "be7f994066ed419d0847aece1f96c5dae6246af34d52b71132eca62568bbcff5",
    "live_result": "76d46141d3b18be3b7e87357961385078723fd9e492c1946680aab5423011ad5",
    "stock_topology": "2ec89c47f79f82e86e306e8824b1fdaacd706a2ae23180196132bfcef8703c52",
    "deep_static": "d43752175c3613e8a903ef0dcce8d3b75e83f8e0addaed7deb4ba9b649549d69",
    "stock_live_cmdline": "a27cc8f2a1fbfecb5b38b28b5678f76f937c2f346421b1fc6a758814572e75c8",
    "base_source": "86e2f73412c65fadff0b15bbf0eac9140610f70250514ac0bddbf3b53fb5f7bf",
    "delta_source": "23ef2b27de8843e271d41405b3c0b1a71bfa668615c8f0f12a1e5c4395ec851a",
    "p241_helper": "40067ca4437aac0b06d9886f1c23ce495b23faa3bf06be3e0eebd34d57f98c3b",
    "p243_helper": "70d2c331c43d0dc5fdbbe885afd8dd178ebcfcd6715d3693a28a80c4ecc4ae60",
    "usb_static_helper": "35036db7f85339b79055359913e801533f1eb29e4b54a668d0ae21ae1b871baa",
    "p248_spec": "7325d7434256d8df67400fbaa5002fbb75d9a6ba8ea7c2b9c2cb32124c3145fe",
}

SOURCE_MEMBERS = {
    "driver_core": "kernel_platform/common/drivers/base/core.c",
    "driver_probe": "kernel_platform/common/drivers/base/dd.c",
    "of_property": "kernel_platform/common/drivers/of/property.c",
    "dwc3_msm": "kernel_platform/msm-kernel/drivers/usb/dwc3/dwc3-msm-core.c",
    "redriver": "kernel_platform/msm-kernel/drivers/usb/redriver/redriver.c",
    "gdsc": "kernel_platform/msm-kernel/drivers/clk/qcom/gdsc-regulator.c",
    "qnoc": "kernel_platform/msm-kernel/drivers/interconnect/qcom/waipio.c",
    "pdc": "kernel_platform/common/drivers/irqchip/qcom-pdc.c",
    "eud": "kernel_platform/msm-kernel/drivers/soc/qcom/eud.c",
    "hsphy": "kernel_platform/msm-kernel/drivers/usb/phy/phy-msm-snps-hs.c",
    "ssphy": "kernel_platform/msm-kernel/drivers/usb/phy/phy-msm-ssusb-qmp.c",
    "usb_dtsi": (
        "kernel_platform/qcom/proprietary/devicetree/qcom/waipio-usb.dtsi"
    ),
}

EXPECTED_MODELS = p243.EXPECTED_MODELS
SSUSB_NODE = "/soc/ssusb@a600000"
DWC3_NODE = SSUSB_NODE + "/dwc3@a600000"
EXPECTED_DIRECT_DT_PROVIDERS = {
    "clock": {"/soc/clock-controller@100000"},
    "gdsc": {"/soc/qcom,gdsc@149004"},
    "interconnect": {
        "/soc/interconnect@16e0000",
        "/soc/interconnect@1",
        "/soc/interconnect@1500000",
        "/soc/interconnect@19100000",
    },
    "pdc": {"/soc/interrupt-controller@b220000"},
    "extcon": {"/soc/qcom,msm-eud@88e0000"},
    "phy": {"/soc/hsphy@88e3000", "/soc/ssphy@88e8000"},
    "iommu": {"/soc/apps-smmu@15000000"},
}
EXPECTED_STOCK_SUPPLIERS = {
    "supplier:platform:100000.clock-controller",
    "supplier:platform:149004.qcom,gdsc",
    "supplier:platform:1500000.interconnect",
    "supplier:platform:16e0000.interconnect",
    "supplier:platform:19100000.interconnect",
    "supplier:platform:88e0000.qcom,msm-eud",
    "supplier:platform:b220000.interrupt-controller",
    "supplier:platform:soc:interconnect@1",
    "supplier:regulator:regulator.2",
}

REQUIRED_MODULES = {
    "gdsc-regulator.ko",
    "gcc-waipio.ko",
    "qcom-pdc.ko",
    "qcom_rpmh.ko",
    "clk-rpmh.ko",
    "rpmh-regulator.ko",
    "icc-bcm-voter.ko",
    "icc-rpmh.ko",
    "qnoc-waipio.ko",
    "arm_smmu.ko",
    "eud.ko",
    "phy-msm-ssusb-qmp.ko",
    "phy-msm-snps-hs.ko",
    "phy-msm-snps-eusb2.ko",
    "redriver.ko",
    "dwc3-msm.ko",
}

PROVIDER_CHECKS = (
    (
        "gdsc",
        "/sys/bus/platform/drivers/gdsc/149004.qcom,gdsc",
        "0xa01",
    ),
    (
        "pdc",
        "/sys/bus/platform/drivers/qcom-pdc/b220000.interrupt-controller",
        "0xa02",
    ),
    (
        "qnoc-aggre1",
        "/sys/bus/platform/drivers/qnoc-waipio/16e0000.interconnect",
        "0xa03",
    ),
    (
        "qnoc-mc-virt",
        "/sys/bus/platform/drivers/qnoc-waipio/soc:interconnect@1",
        "0xa04",
    ),
    (
        "qnoc-config",
        "/sys/bus/platform/drivers/qnoc-waipio/1500000.interconnect",
        "0xa05",
    ),
    (
        "qnoc-gem",
        "/sys/bus/platform/drivers/qnoc-waipio/19100000.interconnect",
        "0xa06",
    ),
    (
        "eud",
        "/sys/bus/platform/drivers/msm-eud/88e0000.qcom,msm-eud",
        "0xa07",
    ),
)
PHY_CHECKS = (
    (
        "hsphy",
        "/sys/bus/platform/drivers/msm-usb-hsphy/88e3000.hsphy",
        "0xa20",
    ),
    (
        "ssphy",
        "/sys/bus/platform/drivers/msm-usb-ssphy-qmp/88e8000.ssphy",
        "0xa21",
    ),
)

MODULE_RE = re.compile(
    r'^\s*\{"([^"]+\.ko)", "([^"]+)", "([^"]*)"\},\s*$',
    re.MULTILINE,
)
GATE_RE = re.compile(
    r'^\s*\{(\d+)U, "([^"]+)", "([^"]+)", "([^"]+)"\},\s*$',
    re.MULTILINE,
)


class AuditError(ValueError):
    pass


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "GOAL.md").is_file() and (parent / "AGENTS.md").is_file():
            return parent
    raise AuditError("repository root not found")


def ascii_text(data: bytes, label: str) -> str:
    try:
        return data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise AuditError(f"{label} is not ASCII") from exc


def source_text(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AuditError(f"{label} is not UTF-8 source") from exc


def json_object(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{label} root is not an object")
    return value


def receipt(data: bytes) -> dict[str, Any]:
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def require_tokens(text: str, label: str, tokens: tuple[str, ...]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AuditError(f"{label} source contract missing: {missing}")


def parse_phandle_array(
    nodes: tuple[dtbo_contract.FdtNode, ...],
    provider_map: dict[int, str],
    consumer: dtbo_contract.FdtNode,
    property_name: str,
    cells_property: str,
) -> tuple[str, ...]:
    raw = consumer.properties.get(property_name)
    if raw is None:
        raise AuditError(f"{consumer.path} missing {property_name}")
    values = p243.u32_cells(raw, f"{consumer.path} {property_name}")
    cursor = 0
    providers: list[str] = []
    while cursor < len(values):
        path = provider_map.get(values[cursor])
        if path is None:
            raise AuditError(
                f"{consumer.path} {property_name} has unresolved phandle"
            )
        provider = p243.require_node(nodes, path)
        raw_cells = provider.properties.get(cells_property)
        if raw_cells is None:
            raise AuditError(f"{path} missing {cells_property}")
        cell_count = p243.u32_cells(raw_cells, f"{path} {cells_property}")
        if len(cell_count) != 1:
            raise AuditError(f"{path} malformed {cells_property}")
        cursor += 1 + cell_count[0]
        if cursor > len(values):
            raise AuditError(f"{consumer.path} {property_name} is truncated")
        providers.append(path)
    return tuple(providers)


def parse_plain_phandles(
    provider_map: dict[int, str],
    consumer: dtbo_contract.FdtNode,
    property_name: str,
) -> tuple[str, ...]:
    raw = consumer.properties.get(property_name)
    if raw is None:
        raise AuditError(f"{consumer.path} missing {property_name}")
    paths: list[str] = []
    for value in p243.u32_cells(raw, f"{consumer.path} {property_name}"):
        path = provider_map.get(value)
        if path is None:
            raise AuditError(
                f"{consumer.path} {property_name} has unresolved phandle"
            )
        paths.append(path)
    return tuple(paths)


def audit_vendor_dtb(data: bytes) -> dict[str, Any]:
    blobs = p243.parse_concatenated_fdt(data)
    if len(blobs) != len(EXPECTED_MODELS):
        raise AuditError(f"expected four vendor DTBs, found {len(blobs)}")
    variants: list[dict[str, Any]] = []
    common_shape: dict[str, set[str]] | None = None
    for index, (blob, expected_model) in enumerate(zip(blobs, EXPECTED_MODELS)):
        nodes = dtbo_contract.parse_fdt(blob)
        providers = p243.phandle_map(nodes)
        root = p243.require_node(nodes, "/")
        parent = p243.require_node(nodes, SSUSB_NODE)
        child = p243.require_node(nodes, DWC3_NODE)
        if p243.strings(root, "model") != (expected_model,):
            raise AuditError(f"vendor DTB {index} model mismatch")
        if p243.strings(parent, "compatible") != ("qcom,dwc-usb3-msm",):
            raise AuditError(f"vendor DTB {index} SSUSB compatible mismatch")
        if p243.strings(child, "compatible") != ("snps,dwc3",):
            raise AuditError(f"vendor DTB {index} DWC3 compatible mismatch")
        if "ssusb_redriver" in parent.properties:
            raise AuditError(f"vendor DTB {index} unexpectedly has redriver")

        shape = {
            "clock": set(
                parse_phandle_array(
                    nodes, providers, parent, "clocks", "#clock-cells"
                )
            ),
            "gdsc": {
                p243.provider_path(
                    parent, "USB3_GDSC-supply", providers
                )
            },
            "interconnect": set(
                parse_phandle_array(
                    nodes,
                    providers,
                    parent,
                    "interconnects",
                    "#interconnect-cells",
                )
            ),
            "pdc": {
                path
                for path in parse_phandle_array(
                    nodes,
                    providers,
                    parent,
                    "interrupts-extended",
                    "#interrupt-cells",
                )
                if path == "/soc/interrupt-controller@b220000"
            },
            "extcon": set(
                parse_plain_phandles(providers, parent, "extcon")
            ),
            "phy": set(
                parse_plain_phandles(providers, child, "usb-phy")
            ),
            "iommu": {
                parse_phandle_array(
                    nodes, providers, child, "iommus", "#iommu-cells"
                )[0]
            },
        }
        if shape != EXPECTED_DIRECT_DT_PROVIDERS:
            raise AuditError(f"vendor DTB {index} supplier topology mismatch")
        if common_shape is not None and shape != common_shape:
            raise AuditError("vendor DTB variants disagree on SSUSB suppliers")
        common_shape = shape
        variants.append(
            {
                "index": index,
                "model": expected_model,
                "sha256": hashlib.sha256(blob).hexdigest(),
                "redriver_phandle": False,
            }
        )
    assert common_shape is not None
    return {
        "identity": receipt(data),
        "blob_count": len(variants),
        "variants": variants,
        "common_topology": {
            key: sorted(value) for key, value in common_shape.items()
        },
        "verified": True,
    }


def audit_source_contract(members: dict[str, bytes]) -> dict[str, Any]:
    text = {key: source_text(value, key) for key, value in members.items()}
    require_tokens(
        text["driver_core"],
        "driver core",
        (
            "static u32 fw_devlink_flags = FW_DEVLINK_FLAGS_ON;",
            "static bool fw_devlink_strict = true;",
            "static DEVICE_ATTR_RO(waiting_for_supplier);",
            "device_create_file(dev, &dev_attr_waiting_for_supplier)",
            "device_remove_file(dev, &dev_attr_waiting_for_supplier)",
        ),
    )
    require_tokens(
        text["driver_probe"],
        "driver probe",
        ("ret = device_links_check_suppliers(dev);",),
    )
    require_tokens(
        text["of_property"],
        "OF suppliers",
        (
            'DEFINE_SIMPLE_PROP(clocks, "clocks", "#clock-cells")',
            'DEFINE_SIMPLE_PROP(interconnects, "interconnects",',
            'DEFINE_SIMPLE_PROP(extcon, "extcon", NULL)',
            'DEFINE_SUFFIX_PROP(regulators, "-supply", NULL)',
            "{ .parse_prop = parse_interrupts, },",
        ),
    )
    require_tokens(
        text["dwc3_msm"],
        "dwc3-msm",
        (
            'devm_regulator_get(mdwc->dev, "USB3_GDSC")',
            "PTR_ERR(mdwc->dwc3_gdsc) == -EPROBE_DEFER",
            'devm_clk_get(mdwc->dev, "iface_clk")',
            'devm_clk_get(mdwc->dev, "core_clk")',
            "platform_get_irq_byname(pdev,",
            "of_get_next_available_child(node, NULL)",
            "devm_usb_get_phy_by_node(mdwc->dev, phy_node, NULL)",
            "dwc3_msm_interconnect_vote_populate(mdwc)",
            "mdwc->icc_paths[i] = of_icc_get(&pdev->dev,",
            "if (IS_ERR(mdwc->icc_paths[i]))",
            "mdwc->icc_paths[i] = NULL;",
            "usb_role_switch_register(mdwc->dev,",
            "dwc3_msm_check_extcon_prop(pdev)",
        ),
    )
    probe = text["dwc3_msm"].index(
        "static int dwc3_msm_probe(struct platform_device *pdev)"
    )
    ordering_tokens = (
        'usb_get_redriver_by_phandle(node, "ssusb_redriver", 0)',
        "dwc3_msm_get_clk_gdsc(mdwc)",
        "platform_get_irq_byname(pdev,",
        "of_get_next_available_child(node, NULL)",
        "mdwc->hs_phy = devm_usb_get_phy_by_node",
        "mdwc->ss_phy = devm_usb_get_phy_by_node",
        "dwc3_msm_interconnect_vote_populate(mdwc)",
        "usb_role_switch_register(mdwc->dev,",
        "dwc3_msm_check_extcon_prop(pdev)",
    )
    positions = [text["dwc3_msm"].index(token, probe) for token in ordering_tokens]
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise AuditError("dwc3-msm probe ordering mismatch")
    require_tokens(
        text["redriver"],
        "redriver",
        (
            "node = of_parse_phandle(np, phandle_name, index);",
            "if (!of_device_is_available(node)) {",
            "return NULL;",
            "return ERR_PTR(-EPROBE_DEFER);",
        ),
    )
    driver_tokens = {
        "gdsc": '.name = "gdsc"',
        "qnoc": '.name = "qnoc-waipio"',
        "pdc": '.name = "qcom-pdc"',
        "eud": '.name\t\t= "msm-eud"',
        "hsphy": '.name\t= "msm-usb-hsphy"',
        "ssphy": '.name\t= "msm-usb-ssphy-qmp"',
    }
    for label, token in driver_tokens.items():
        require_tokens(text[label], label, (token,))
    require_tokens(
        text["usb_dtsi"],
        "waipio USB DT",
        (
            "usb0: ssusb@a600000",
            "USB3_GDSC-supply = <&gcc_usb30_prim_gdsc>;",
            "interrupts-extended = <&pdc",
            "interconnects = <&aggre1_noc",
            "extcon = <&eud>;",
            "usb-phy = <&usb2_phy0>, <&usb_qmp_dp_phy>;",
        ),
    )
    return {
        "fw_devlink_default": "on-strict",
        "waiting_for_supplier_semantics": (
            "present before bind; value 1 means unresolved fwnode suppliers; "
            "removed after successful driver bind"
        ),
        "probe_order": list(ordering_tokens),
        "probe_fatal_boundaries": {
            "gdsc": "EPROBE_DEFER is fatal; other regulator errors are tolerated",
            "gcc_clocks_and_reset": "acquisition errors return from probe",
            "mandatory_irq": "missing or request failure returns from probe",
            "hsphy": "any devm_usb_get_phy_by_node error returns from probe",
            "ssphy": "any devm_usb_get_phy_by_node error returns from probe",
            "extcon": "registration error returns from probe",
        },
        "non_fatal_or_absent": {
            "redriver": "no DT phandle returns NULL",
            "interconnect_get": "of_icc_get errors are converted to NULL in probe",
        },
        "driver_names": {
            "gdsc": "gdsc",
            "qnoc": "qnoc-waipio",
            "pdc": "qcom-pdc",
            "eud": "msm-eud",
            "hsphy": "msm-usb-hsphy",
            "ssphy": "msm-usb-ssphy-qmp",
        },
        "verified": True,
    }


def audit_plan_and_runtime(
    plan_data: bytes, runtime_data: bytes
) -> dict[str, Any]:
    plan = ascii_text(plan_data, "P2.49 plan")
    runtime = ascii_text(runtime_data, "P2.49 runtime")
    modules = [match.group(1) for match in MODULE_RE.finditer(plan)]
    gates = [
        {
            "order": int(match.group(1)),
            "id": match.group(2),
            "kind": match.group(3),
            "path": match.group(4),
        }
        for match in GATE_RE.finditer(plan)
    ]
    if len(modules) != 59 or len(set(modules)) != len(modules):
        raise AuditError("P2.49 module plan is not the exact unique 59 entries")
    missing = sorted(REQUIRED_MODULES - set(modules))
    if missing:
        raise AuditError(f"P2.49 required SSUSB modules missing: {missing}")
    if len(gates) != 12 or [row["order"] for row in gates] != list(range(1, 13)):
        raise AuditError("P2.49 gate plan mismatch")
    if gates[8]["id"] != "gcc-waipio" or gates[9]["id"] != "ssusb":
        raise AuditError("P2.49 GCC/SSUSB frontier mismatch")

    require_tokens(
        runtime,
        "P2.49 runtime",
        (
            "#define S22_P241_GATE_TIMEOUT_SEC 20LL",
            "deadline.tv_sec += S22_P241_GATE_TIMEOUT_SEC;",
            "while (completed < S22PLUS_O2_BIND_GATE_COUNT)",
            "S22_P241_GATE_STAGE_BASE + (uint8_t)completed",
            "-ETIMEDOUT",
        ),
    )
    if runtime.count("deadline.tv_sec += S22_P241_GATE_TIMEOUT_SEC;") != 1:
        raise AuditError("P2.49 runtime does not use one global gate deadline")
    deadline_position = runtime.index(
        "deadline.tv_sec += S22_P241_GATE_TIMEOUT_SEC;"
    )
    loop_position = runtime.index(
        "while (completed < S22PLUS_O2_BIND_GATE_COUNT)"
    )
    if deadline_position >= loop_position:
        raise AuditError("P2.49 gate deadline ordering mismatch")
    return {
        "plan": receipt(plan_data),
        "runtime": receipt(runtime_data),
        "module_count": len(modules),
        "required_ssusb_modules_selected": sorted(REQUIRED_MODULES),
        "all_modules_checked_before_gate_deadline": (
            runtime.index("for (size_t index = 0; index < S22PLUS_O2_MODULE_PLAN_COUNT")
            < deadline_position
        ),
        "gcc_gate": gates[8],
        "ssusb_gate": gates[9],
        "global_gate_timeout_sec": 20,
        "deadline_scope": "all-12-gates-shared",
        "ssusb_observation_window_sec": {
            "lower_bound": 0,
            "upper_bound": 20,
            "exact": None,
        },
        "per_gate_timestamps_retained": False,
        "verified": True,
    }


def audit_live_result(data: bytes) -> dict[str, Any]:
    value = json_object(data, "P2.50 live result")
    try:
        observer = value["live_state"]["final_evidence"]["observer"]
        classification = observer["classification"]
        record = classification["records"][0]
        active = record["active"]
        slots = record["valid_slots"]
        health = value["live_state"]["final_evidence"]["health"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AuditError("P2.50 live result shape mismatch") from exc
    expected_active = {
        "detail": 110,
        "generation": 77,
        "item_index": 9,
        "outcome": 2,
        "slot_id": 1,
        "stage": 132,
    }
    expected_previous = {
        "detail": 0,
        "generation": 76,
        "item_index": 8,
        "outcome": 0,
        "slot_id": 0,
        "stage": 131,
    }
    if (
        value.get("verdict") != "NO_PROOF_F1_V2_CANDIDATE_ROLLED_BACK"
        or value.get("current_state") != "CLOSED"
        or classification.get("classification") != "E2_FAILURE_OBSERVED"
        or active != expected_active
        or slots != [expected_previous, expected_active]
        or not value["live_state"]["final_evidence"].get("rollback_verified")
        or not value["live_state"].get("final_verified")
        or not health.get("android_boot_completed")
        or not health.get("root_verified")
    ):
        raise AuditError("P2.50 live frontier or rollback contract mismatch")
    return {
        "identity": receipt(data),
        "formal_verdict": value["verdict"],
        "classification": classification["classification"],
        "previous_gate": {
            "id": "gcc-waipio",
            "stage": "0x83",
            "item_index": 8,
            "generation": 76,
            "outcome": "success",
        },
        "active_gate": {
            "id": "ssusb",
            "stage": "0x84",
            "item_index": 9,
            "generation": 77,
            "outcome": "failure",
            "detail": 110,
            "detail_name": "ETIMEDOUT",
        },
        "rollback_verified": True,
        "final_android_health_verified": True,
    }


def audit_stock_topology(data: bytes) -> dict[str, Any]:
    value = json_object(data, "stock USB topology")
    try:
        suppliers = set(value["sysfs"]["ssusb_suppliers"])
        stock_driver = value["sysfs"]["ssusb_driver"]
        stock_node = value["sysfs"]["ssusb_of_node"]
    except (KeyError, TypeError) as exc:
        raise AuditError("stock USB topology shape mismatch") from exc
    if (
        value.get("target") != TARGET
        or value.get("result") != "pass-stock-topology-partial"
        or suppliers != EXPECTED_STOCK_SUPPLIERS
        or stock_driver != "/sys/bus/platform/drivers/msm-dwc3"
        or stock_node
        != "/sys/firmware/devicetree/base/soc/ssusb@a600000"
    ):
        raise AuditError("stock SSUSB topology contract mismatch")
    return {
        "identity": receipt(data),
        "driver": stock_driver,
        "of_node": stock_node,
        "supplier_links": sorted(suppliers),
        "stock_parent_bound": True,
        "verified": True,
    }


def audit_module_identity(module_data: bytes, deep_data: bytes) -> dict[str, Any]:
    deep = json_object(deep_data, "deep USB static analysis")
    try:
        module = deep["modules"]["dwc3-msm.ko"]
        edges = deep["call_edges"]
    except (KeyError, TypeError) as exc:
        raise AuditError("deep USB static analysis shape mismatch") from exc
    edge_names = {
        (row.get("caller"), row.get("callee"))
        for row in edges
        if row.get("module") == "dwc3-msm.ko"
    }
    required_edges = {
        ("dwc3_msm_probe", "usb_role_switch_register"),
        ("dwc3_msm_core_init", "usb_role_switch_find_by_fwnode"),
    }
    if (
        module.get("sha256") != EXPECTED_SHA256["dwc3_msm"]
        or module.get("bytes") != len(module_data)
        or not required_edges.issubset(edge_names)
    ):
        raise AuditError("exact dwc3-msm ELF evidence mismatch")
    module_path = repo_root() / DEFAULT_DWC3_MSM
    symbols, symbols_by_address = usb_static_re.parse_symbols(module_path)
    calls = usb_static_re.parse_call_edges(module_path, symbols_by_address)
    required_probe_calls = {
        ("dwc3_msm_probe", "usb_get_redriver_by_phandle"),
        ("dwc3_msm_probe", "devm_regulator_get"),
        ("dwc3_msm_probe", "devm_clk_get"),
        ("dwc3_msm_probe", "platform_get_irq_byname"),
        ("dwc3_msm_probe", "of_get_next_available_child"),
        ("dwc3_msm_probe", "of_parse_phandle"),
        ("dwc3_msm_probe", "devm_usb_get_phy_by_node"),
        ("dwc3_msm_probe", "of_icc_get"),
        ("dwc3_msm_probe", "usb_role_switch_register"),
    }
    if (
        symbols.get("dwc3_msm_probe", {}).get("address") != 0x5DB0
        or symbols.get("dwc3_msm_probe", {}).get("size") != 0x12EC
        or not required_probe_calls.issubset(calls)
    ):
        raise AuditError("exact dwc3-msm probe relocation contract mismatch")
    extcon_calls = sorted(
        callee
        for caller, callee in calls
        if caller == "dwc3_msm_probe" and callee.startswith("extcon_")
    )
    if extcon_calls:
        raise AuditError(f"unexpected exact probe extcon calls: {extcon_calls}")
    return {
        "module": receipt(module_data),
        "deep_static": receipt(deep_data),
        "exact_elf_edges": sorted(
            f"{caller}->{callee}" for caller, callee in required_edges
        ),
        "probe_symbol": {"address": "0x5db0", "size": "0x12ec"},
        "exact_probe_call_relocations": sorted(
            callee for caller, callee in required_probe_calls
        ),
        "exact_probe_extcon_calls": [],
        "verified": True,
    }


def build_result() -> dict[str, Any]:
    root = repo_root()
    paths = {
        "vendor_dtb": root / DEFAULT_VENDOR_DTB,
        "dwc3_msm": root / DEFAULT_DWC3_MSM,
        "vendor_boot": root / DEFAULT_VENDOR_BOOT,
        "candidate_boot": root / DEFAULT_CANDIDATE_BOOT,
        "config": root / DEFAULT_CONFIG,
        "plan": root / DEFAULT_PLAN,
        "runtime": root / DEFAULT_RUNTIME,
        "live_result": root / DEFAULT_LIVE_RESULT,
        "stock_topology": root / DEFAULT_STOCK_TOPOLOGY,
        "deep_static": root / DEFAULT_DEEP_STATIC,
        "stock_live_cmdline": root / DEFAULT_STOCK_LIVE_CMDLINE,
        "base_source": root / DEFAULT_BASE_SOURCE,
        "delta_source": root / DEFAULT_DELTA_SOURCE,
        "p241_helper": SCRIPT_DIR / "s22plus_fyg8_p241_dtbo_role_contract.py",
        "p243_helper": SCRIPT_DIR / "s22plus_fyg8_p243_rpmh_dependency_audit.py",
        "usb_static_helper": (
            SCRIPT_DIR / "s22plus_fyg8_usb_role_static_re.py"
        ),
        "p248_spec": SCRIPT_DIR / "s22plus_fyg8_p248_contract_spec.py",
    }
    limits = {
        "vendor_dtb": 4 * 1024 * 1024,
        "dwc3_msm": 1024 * 1024,
        "vendor_boot": 128 * 1024 * 1024,
        "candidate_boot": 128 * 1024 * 1024,
        "config": 1024 * 1024,
        "plan": 1024 * 1024,
        "runtime": 1024 * 1024,
        "live_result": 1024 * 1024,
        "stock_topology": 1024 * 1024,
        "deep_static": 4 * 1024 * 1024,
        "stock_live_cmdline": 64 * 1024,
        "p241_helper": 1024 * 1024,
        "p243_helper": 2 * 1024 * 1024,
        "usb_static_helper": 2 * 1024 * 1024,
        "p248_spec": 1024 * 1024,
    }
    data = {
        label: p243.stable_read(
            path, label, EXPECTED_SHA256[label], limits[label]
        )
        for label, path in paths.items()
        if label not in {"base_source", "delta_source"}
    }
    base_source = p243.stable_sha256(
        paths["base_source"],
        "base source",
        EXPECTED_SHA256["base_source"],
        700 * 1024 * 1024,
    )
    delta_source = p243.stable_sha256(
        paths["delta_source"],
        "delta source",
        EXPECTED_SHA256["delta_source"],
        8 * 1024 * 1024,
    )
    members = p243.read_source_members(paths["base_source"], SOURCE_MEMBERS)
    delta_audit = p243.audit_delta_no_override(
        paths["delta_source"], SOURCE_MEMBERS
    )

    source = audit_source_contract(members)
    vendor_dtb = audit_vendor_dtb(data["vendor_dtb"])
    plan_runtime = audit_plan_and_runtime(data["plan"], data["runtime"])
    live = audit_live_result(data["live_result"])
    stock = audit_stock_topology(data["stock_topology"])
    module = audit_module_identity(data["dwc3_msm"], data["deep_static"])
    boot = p243.audit_boot_arguments(
        data["candidate_boot"],
        data["vendor_boot"],
        data["stock_live_cmdline"],
    )
    config = ascii_text(data["config"], "P2.49 config")
    if "CONFIG_DEBUG_FS=y" not in config:
        raise AuditError("P2.49 config does not carry DEBUG_FS")
    p248_spec = ascii_text(data["p248_spec"], "P2.48 detail spec")
    require_tokens(
        p248_spec,
        "P2.48 detail spec",
        (
            "DETAIL_RESERVED_MIN = 0xA00",
            "DETAIL_MAX = 0xFFF",
            'return "reserved"',
            "return False",
        ),
    )

    return {
        "schema": SCHEMA,
        "verdict": VERDICT,
        "target": TARGET,
        "inputs": {
            "base_source": base_source,
            "delta_source": delta_source,
            "source_delta": delta_audit,
            "helpers": {
                "p241": receipt(data["p241_helper"]),
                "p243": receipt(data["p243_helper"]),
                "usb_static": receipt(data["usb_static_helper"]),
                "p248_spec": receipt(data["p248_spec"]),
            },
            "config": receipt(data["config"]),
        },
        "live_frontier": live,
        "plan_runtime": plan_runtime,
        "source": source,
        "vendor_dtb": vendor_dtb,
        "stock_control": stock,
        "module_identity": module,
        "boot_arguments": {
            "candidate_boot": boot["candidate_boot"],
            "vendor_boot": boot["vendor_boot"],
            "fw_devlink_overrides": boot["fw_devlink_overrides"],
            "effective_source_default": boot["effective_source_default"],
            "candidate_runtime_cmdline_directly_observed": False,
        },
        "reasoning_ledger": [
            {
                "id": "R1",
                "evidence": (
                    "the module loop completes before gate timing starts; "
                    "P2.50 reached gate item 9"
                ),
                "inference": (
                    "all 59 insertion and /proc/modules checks completed"
                ),
                "limit": "module registration does not prove provider bind",
            },
            {
                "id": "R2",
                "evidence": "retained generation 76 proves gcc-waipio gate 0x83",
                "inference": "the upstream GCC provider chain reached bind",
                "limit": "downstream GDSC, qnoc, PDC, EUD, and PHY binds unknown",
            },
            {
                "id": "R3",
                "evidence": "one 20-second deadline is shared by all 12 gates",
                "inference": (
                    "SSUSB did not necessarily receive a dedicated 20 seconds"
                ),
                "limit": "no retained per-gate timestamps quantify its dwell",
            },
            {
                "id": "R4",
                "evidence": (
                    "strict fw_devlink parses clocks, supplies, interconnects, "
                    "interrupts, and extcon before bus probe"
                ),
                "inference": (
                    "an unresolved direct provider can block before "
                    "dwc3_msm_probe"
                ),
                "limit": "P2.50 did not read waiting_for_supplier",
            },
            {
                "id": "R5",
                "evidence": (
                    "exact DT and same-FYG8 stock sysfs agree on the direct "
                    "SSUSB supplier set"
                ),
                "inference": "the provider checks are board-specific, not generic",
                "limit": "stock bind does not prove direct-PID1 bind",
            },
            {
                "id": "R6",
                "evidence": (
                    "dwc3_msm_probe returns on deferred GDSC and missing PHYs, "
                    "plus several mandatory resource errors"
                ),
                "inference": (
                    "a supplier-ready parent can still remain unbound after "
                    "probe entry"
                ),
                "limit": "no probe-entry witness or deferred reason was retained",
            },
            {
                "id": "R7",
                "evidence": (
                    "the exact module has probe relocations for GDSC, clocks, "
                    "IRQs, PHYs, ICC, and role switch but no extcon call"
                ),
                "inference": (
                    "EUD is relevant as a strict fw_devlink supplier, not as "
                    "an active probe-internal extcon call in this binary"
                ),
                "limit": "EUD direct-PID1 bind remains unobserved",
            },
        ],
        "hypotheses": [
            {
                "id": "H1",
                "name": "pre-probe-fw-devlink-supplier-wait",
                "status": "OPEN_HIGH_PRIORITY",
                "basis": "strict source contract plus exact DT supplier closure",
            },
            {
                "id": "H2",
                "name": "probe-entered-gdsc-or-phy-defer",
                "status": "OPEN",
                "basis": "fatal acquisition paths in exact matched source",
            },
            {
                "id": "H3",
                "name": "probe-entered-permanent-resource-or-role-error",
                "status": "OPEN_LOWER_PRIORITY",
                "basis": "mandatory IRQ/resource/role paths remain unobserved",
            },
            {
                "id": "H4",
                "name": "shared-deadline-left-insufficient-ssusb-dwell",
                "status": "OPEN_CONFOUND",
                "basis": "zero-to-20-second unknown SSUSB observation window",
            },
            {
                "id": "H5",
                "name": "missing-module-or-gcc-provider",
                "status": "RULED_OUT_FOR_P250_FRONTIER",
                "basis": "module-loop completion and live GCC gate success",
            },
            {
                "id": "H6",
                "name": "missing-redriver",
                "status": "RULED_OUT",
                "basis": "no DT phandle and helper returns NULL when absent",
            },
            {
                "id": "H7",
                "name": "interconnect-get-error-directly-aborts-probe",
                "status": "RULED_OUT",
                "basis": "probe converts of_icc_get errors to NULL",
                "caveat": "qnoc can still block earlier through fw_devlink",
            },
        ],
        "bounded_discriminator": {
            "action": "classify-ssusb-timeout-without-module-growth",
            "frontier_stage": "0x84",
            "frontier_item_index": 9,
            "keep_monotonic_frontier": True,
            "add_modules": [],
            "first_read": (
                "/sys/devices/platform/soc/a600000.ssusb/"
                "waiting_for_supplier"
            ),
            "provider_checks": [
                {"id": name, "path": path, "detail": detail}
                for name, path, detail in PROVIDER_CHECKS
            ],
            "phy_checks": [
                {"id": name, "path": path, "detail": detail}
                for name, path, detail in PHY_CHECKS
            ],
            "structured_detail_partition": {
                "existing_errno": "0x000..0x7ff",
                "existing_regression": "0x800..0x8ff",
                "existing_read_error": "0x900..0x9ff",
                "ssusb_classifier": "0xa00..0xaff",
                "all_stable_providers_but_waiting": "0xa10",
                "all_checked_dependencies_ready_parent_unbound": "0xa30",
            },
            "current_contract_state": (
                "0xa00..0xfff is reserved and rejected by P2.48"
            ),
            "required_contract_change": (
                "define the exact SSUSB subset in the descriptor SoT and "
                "derive kernel validator plus host decoder acceptance"
            ),
            "bounded_timing_correction": {
                "condition": "all fixed dependencies ready at global deadline",
                "one_extra_ssusb_grace_sec": 5,
                "recheck_parent_bind": True,
                "maximum_added_runtime_sec": 5,
            },
            "do_not_add_yet": [
                "debugfs free-form deferred-reason parser",
                "new USB modules",
                "Samsung Type-C policy chain",
                "per-provider checkpoint stages",
            ],
            "decision_value": {
                "provider_missing": "pre-probe supplier branch localized",
                "waiting_1_all_fixed_ready": (
                    "unresolved dynamic or unenumerated supplier, likely "
                    "regulator link"
                ),
                "phy_missing": "probe-entry dependency branch localized",
                "all_ready_late_bind": "shared-deadline confound confirmed",
                "all_ready_still_unbound": (
                    "focus next H0 on internal probe failure/deferred reason"
                ),
            },
        },
        "conclusion": {
            "exact_root_cause_identified": False,
            "narrowed_to": [
                "pre-probe provider bind",
                "probe-time GDSC/PHY dependency",
                "probe-internal permanent failure",
                "shared-deadline late bind",
            ],
            "strongest_actionable_result": (
                "instrument the existing 0x84 timeout; do not add modules"
            ),
            "another_unchanged_live_candidate_justified": False,
        },
        "proof_limits": {
            "direct_pid1_provider_bind_state": False,
            "dwc3_msm_probe_entry": False,
            "exact_deferred_reason": False,
            "ssusb_dedicated_20_second_wait": False,
            "candidate_built": False,
            "device_contact": False,
            "live_authority": False,
        },
        "safety": {
            "host_only": True,
            "device_contact": False,
            "device_write": False,
            "image_build": False,
            "flash": False,
            "authority_created": False,
        },
    }


def main() -> int:
    try:
        result = build_result()
    except (
        AuditError,
        OSError,
        p243.AuditError,
        p243.boot_verify.BootVerifyError,
        dtbo_contract.ContractError,
        usb_static_re.StaticReError,
    ) as exc:
        print(json.dumps({"verdict": "FAIL_CLOSED", "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
