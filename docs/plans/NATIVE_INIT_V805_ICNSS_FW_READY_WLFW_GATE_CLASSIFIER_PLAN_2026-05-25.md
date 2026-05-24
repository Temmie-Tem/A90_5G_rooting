# Native Init V805 ICNSS FW_READY/WLFW Gate Classifier Plan

## Goal

Use V804, V802, V800, V797, stock tracepoint inventory, and Samsung OSRC source
to classify the exact first observable that must appear before ICNSS
`FW_READY`, HDD probe completion, BDF transfer, and `wlan0`.

## Scope

- Target script:
  - `scripts/revalidation/native_wifi_icnss_fw_ready_wlfw_gate_classifier_v805.py`
- Inputs:
  - V804 PLD/ICNSS register/probe prerequisite classifier manifest.
  - V802 provider-first `boot_wlan` evidence.
  - V800 provider-first ICNSS edge replay evidence.
  - V797 PIL trace payload evidence.
  - V776/V777 stock tracepoint inventory and format evidence.
  - Staged Samsung OSRC source under
    `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source`.
- Source targets:
  - `drivers/soc/qcom/icnss.c`
  - `drivers/soc/qcom/icnss_qmi.c`
  - `drivers/soc/qcom/wlan_firmware_service_v01.h`

## Hard Gates

- Host-only: no device command.
- No custom kernel flash, boot image write, partition write, or reboot.
- No Wi-Fi HAL, `wificond`, supplicant, hostapd, scan/connect, credentials,
  DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate`, `esoc0`, bind/unbind, module load/unload, or
  driver override.
- No Wi-Fi secret material in tracked output.

## Success Criteria

- V805 compiles and plan-only manifest passes.
- V804 is present, passed, and selected the `FW_READY`/probe gate.
- Source confirms WLFW service ID `0x45`/`69`, `qmi_add_lookup()`,
  `wlfw_new_server()`, `ICNSS_DRIVER_EVENT_SERVER_ARRIVE`,
  `QMI_WLFW_FW_READY_IND`, and `icnss_call_driver_probe()` ordering.
- Existing V800/V802/V797 evidence is consistent: lower/provider/PIL activity
  exists, but WLFW/QMI-connected/FW-ready/BDF/netdev is absent.
- Classifier selects the next bounded live gate without reviving custom-kernel
  flashing or crossing the Wi-Fi HAL/connect boundary.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_icnss_fw_ready_wlfw_gate_classifier_v805.py

python3 scripts/revalidation/native_wifi_icnss_fw_ready_wlfw_gate_classifier_v805.py \
  --out-dir tmp/wifi/v805-icnss-fw-ready-wlfw-gate-plan-check \
  plan

python3 scripts/revalidation/native_wifi_icnss_fw_ready_wlfw_gate_classifier_v805.py run

git diff --check
```
