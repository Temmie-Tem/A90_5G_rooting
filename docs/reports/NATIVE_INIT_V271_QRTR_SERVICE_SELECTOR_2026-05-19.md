# Native Init v271 QRTR Service Selector Report

## Summary

- status: PASS
- boot image change: none
- device command: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- tool: `scripts/revalidation/wifi_qrtr_service_selector.py`
- evidence: `tmp/wifi/v271-qrtr-service-selector/`
- decision: `qrtr-service-selector-ready`

v271 is a host-only correlation step. It does not open a QRTR socket, send a
QRTR nameservice packet, send a QMI payload, or run any command on the device.
It combines v270 readback results with vendor binary evidence to choose a safer
next direction than another arbitrary service id lookup.

## Inputs

- v270 primary readback:
  `tmp/wifi/v270-qrtr-ns-readback-live-20260519-103623/manifest.json`
- v270 long readback:
  `tmp/wifi/v270-qrtr-ns-readback-live-long-20260519-103732/manifest.json`
- vendor export:
  `tmp/wifi/v226-vendor-root-live-export/vendor-source/`
- binaries:
  - `bin/cnss-daemon`
  - `lib64/libqmiservices.so`
  - `lib64/libqmi_cci.so`

## Validation

```bash
python3 scripts/revalidation/wifi_qrtr_service_selector.py \
  --out-dir tmp/wifi/v271-qrtr-service-selector \
  analyze

python3 -m py_compile \
  scripts/revalidation/wifi_qrtr_service_selector.py \
  scripts/revalidation/wifi_qrtr_nameservice_runner.py \
  scripts/revalidation/a90ctl.py

git diff --check
```

Result:

```text
decision: qrtr-service-selector-ready
pass: True
reason: service=1 readback is negative; DMS/WLFW/WLAN evidence requires service-object ID extraction before more live packets
```

## Key Checks

- `cnss-daemon-exists`: PASS
- `libqmiservices-exists`: PASS
- `libqmi_cci-exists`: PASS
- `v270-primary-timeout-zero-events`: PASS
- `v270-long-timeout-zero-events`: PASS
- `cnss-imports-qmi-client`: PASS
- `cnss-imports-dms-service-object`: PASS
- `cnss-has-wlfw-evidence`: PASS
- `qmi-cci-has-service-id-helper`: PASS

## Candidate Classification

| candidate | strength | interpretation |
| --- | --- | --- |
| service `1`, instance `1` | negative | v269/v270 send path works, but v270 returned zero events in both windows |
| DMS | strong | `cnss-daemon` references `dms_get_service_object_internal_v01`, and `libqmiservices.so` exports it |
| WLFW | strong but unresolved | `cnss-daemon` has WLFW/wlfw service strings, but current evidence does not show an exported service object symbol |
| WLAN | medium | `cnss-daemon` has WLAN service strings, but this may be QMI, local socket, or daemon-internal naming |

## Interpretation

- v270 did not fail at QRTR send mechanics; it failed to observe any service
  notification for the selected arbitrary service/instance.
- DMS is the clearest service-object-backed candidate because both
  `cnss-daemon` and `libqmiservices.so` expose matching evidence.
- WLFW is likely more Wi-Fi-specific, but the service object is not exposed by
  `libqmiservices.so` in current evidence, so it needs a locator or Android
  source mapping step.
- The next step should extract numeric service ids from real QMI service
  objects without sending QMI payloads.

## Guardrails Preserved

- no QRTR socket opened
- no QRTR nameservice packet sent
- no QMI payload sent
- no device command executed
- no Wi-Fi scan/connect/link-up
- no credentials, DHCP, routing, or Internet-facing exposure
- no `cnss-daemon`, `cnss_diag`, HAL, supplicant, wificond, or hostapd start
- no rfkill write, ICNSS bind/unbind, firmware mutation, Android partition
  write, property service mutation, perfd mutation, kmsg mutation, or reboot

## Next Step

v272 should be a QMI service-object ID extractor plan. It should execute only
bounded service-object introspection, such as calling service object accessors
and `qmi_idl_get_service_id`, and must still avoid QMI request payloads.
