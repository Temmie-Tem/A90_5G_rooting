# Native Init V806 WLFW Service69 Live Gate Plan

## Goal

Execute the bounded V805-selected live gate: provider-first lower context plus
`boot_wlan` observe, then directly classify whether QRTR WLFW service `0x45` /
`69` appears before ICNSS `FW_READY`, BDF, wiphy, or `wlan0`.

## Scope

- Target script:
  - `scripts/revalidation/native_wifi_wlfw_service69_live_gate_v806.py`
- Reused live arm:
  - `scripts/revalidation/native_wifi_provider_first_boot_wlan_observe_orchestrator_v802.py`
- Inputs:
  - V805 host-only classifier manifest.
  - Current bridge/device state.
- Evidence output:
  - `tmp/wifi/v806-wlfw-service69-live-gate/`

## Hard Gates

- Allowed live actions:
  - hide native menu if active;
  - V802 current-boot prep;
  - helper v124 provider-first service74/PeripheralManager/CNSS retry context;
  - bounded `a90_wlanbootctl boot-observe`;
  - read-only QRTR/WLFW/ICNSS/QCA/WLAN surface capture;
  - runner-owned reboot cleanup.
- Forbidden actions:
  - custom kernel flash or boot image write;
  - Wi-Fi HAL, `wificond`, supplicant, hostapd;
  - scan/connect/link-up, credentials, DHCP, route change, external ping;
  - direct `qcwlanstate` write;
  - `esoc0` open/hold;
  - bind/unbind, `driver_override`, module load/unload.
- No Wi-Fi secret material in tracked output.

## Success Criteria

- V806 compiles and plan-only manifest passes.
- Live gate produces V802 orchestrator and direct arm manifests.
- Provider-first context and bounded `boot_wlan` execute.
- Forbidden connect/network actions remain false.
- Postflight cleanup proves v724 health.
- Decision selects one of:
  - service `69` absent after provider-first + `boot_wlan`;
  - service `69` published but ICNSS-QMI/FW-ready still gated;
  - FW-ready/driver/netdev advanced.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_wlfw_service69_live_gate_v806.py

python3 scripts/revalidation/native_wifi_wlfw_service69_live_gate_v806.py \
  --out-dir tmp/wifi/v806-wlfw-service69-live-gate-plan-check \
  plan

python3 scripts/revalidation/native_wifi_wlfw_service69_live_gate_v806.py run

git diff --check
```
