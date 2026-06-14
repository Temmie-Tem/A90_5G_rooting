# Native Init V805 ICNSS FW_READY/WLFW Gate Classifier Report

## Result

- decision: `v805-wlfw-service69-arrival-gate-selected`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_icnss_fw_ready_wlfw_gate_classifier_v805.py`
- evidence: `tmp/wifi/v805-icnss-fw-ready-wlfw-gate-classifier/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_icnss_fw_ready_wlfw_gate_classifier_v805.py

python3 scripts/revalidation/native_wifi_icnss_fw_ready_wlfw_gate_classifier_v805.py \
  --out-dir tmp/wifi/v805-icnss-fw-ready-wlfw-gate-plan-check \
  plan

python3 scripts/revalidation/native_wifi_icnss_fw_ready_wlfw_gate_classifier_v805.py run
```

V805 was host-only. It did not execute any device command.

## Evidence Summary

| Signal | Result |
| --- | --- |
| V804 `FW_READY`/probe gate input | pass |
| WLFW service ID | `0x45` / `69` |
| WLFW service version | `1` |
| ICNSS lookup source | `qmi_add_lookup(... WLFW_SERVICE_ID_V01 ...)` |
| WLFW arrival path | `wlfw_new_server()` -> `ICNSS_DRIVER_EVENT_SERVER_ARRIVE` |
| FW-ready path | `QMI_WLFW_FW_READY_IND` -> `ICNSS_DRIVER_EVENT_FW_READY_IND` -> `icnss_call_driver_probe()` |
| V800 provider-first service-notifier `74/180` | `1 / 1` |
| V800 QRTR RX/TX markers | `1 / 1` |
| V800 WLFW/QMI-connected/FW-ready/BDF/`wlan0` | `0 / 0 / 0 / 0 / 0` |
| V802 `boot_wlan` loading marker | `1` |
| V802 ICNSS-QMI/FW-ready/WLFW/BDF/wiphy/`wlan0` | `0 / 0 / 0 / 0 / 0 / 0` |
| V797 PIL trace payload | `8` events, codes `2/3/6/7` |
| V797 WLFW/BDF/`wlan0` | `0 / 0 / 0` |

## Classification

V805 identifies the first missing observable before driver probe completion:

```text
icnss_register_fw_service()
  -> qmi_add_lookup(WLFW_SERVICE_ID_V01 = 0x45 / 69)
  -> wlfw_new_server()
  -> ICNSS_DRIVER_EVENT_SERVER_ARRIVE
  -> QMI Server Connected
  -> WLFW indication registration / MSA / capability exchange
  -> QMI_WLFW_FW_READY_IND
  -> ICNSS_FW_READY
  -> icnss_call_driver_probe()
  -> hdd_wlan_startup()
  -> BDF / wiphy / wlan0
```

Existing evidence shows lower/provider-side activity is not enough:

- V800 has service-notifier `74/180` and QRTR RX/TX but no WLFW/QMI-connected.
- V802 reaches `wlan: Loading driver` but no FW-ready, BDF, wiphy, or `wlan0`.
- V797 proves PIL notifications occur, but WLFW service publication still does
  not appear.

Therefore the next live gate should directly observe whether QRTR service `69`
is published during the provider-first + `boot_wlan` window. If service `69` is
absent, the blocker remains before WLFW publication. If service `69` appears
but `QMI Server Connected`/`FW_READY` does not, the blocker moves into
ICNSS-QMI connection or WLFW handshake.

## Safety

- Host-only classifier; no device command executed.
- No custom kernel flash, boot image write, partition write, or reboot.
- No Wi-Fi HAL, `wificond`, supplicant, hostapd, scan/connect, credential use,
  DHCP, route change, or external ping.
- No `boot_wlan`, `qcwlanstate`, `esoc0`, bind/unbind, module load/unload, or
  driver override.
- No Wi-Fi secret material was written to tracked output.

## Next

V806 should be a bounded stock-kernel live gate that:

- hides the native menu if needed;
- refreshes current-boot prep only if required;
- enters the known provider-first lower context;
- executes only the existing bounded `boot_wlan` observe path;
- captures QRTR service `69`, WLFW, ICNSS-QMI, FW-ready, BDF, wiphy, and
  `wlan0` signals;
- stops before Wi-Fi HAL, scan/connect, credentials, DHCP, route changes, or
  external ping.
