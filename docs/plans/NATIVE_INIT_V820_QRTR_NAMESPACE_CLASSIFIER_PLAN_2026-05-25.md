# Native Init V820 QRTR Namespace Classifier Plan

## Goal

Classify whether the V819 blocker is caused by missing QRTR procfs/debugfs
visibility or by actual QRTR service-publication absence, using only existing
V819 evidence.

## Scope

- Target script:
  - `scripts/revalidation/native_wifi_qrtr_namespace_classifier_v820.py`
- Inputs:
  - `tmp/wifi/v819-mdm3-esoc-registration-catalogue/manifest.json`
  - `tmp/wifi/v819-mdm3-esoc-registration-catalogue/native/lower-companion-start-only.txt`
- Approach:
  - Parse V819 helper key/value output.
  - Classify companion child observability and guardrails.
  - Compare QIPCRTR protocol presence, procfs/debugfs visibility, AF_QIPCRTR
    readback behavior, service69 publication, and service-locator hints.

## Hard Gates

- Host-only classification; no device command.
- No custom kernel flash, boot image write, partition write, reboot, or
  bootloader handoff.
- No `esoc0` open, `qcwlanstate on/off`, bind/unbind, driver override, or
  module load/unload.
- No service-manager, Wi-Fi HAL, wificond, scan/connect/link-up, credential
  use, DHCP, route change, or external ping.
- Treat V775 custom OSRC kernel flashing pause as still active.

## Success Criteria

- V820 compiles and plan-only manifest passes.
- V819 manifest is present and passed.
- V819 helper output proves lower companion children were observable and
  postflight-safe.
- Guardrails remain zero for HAL/connect/networking/credential actions.
- QIPCRTR protocol is visible, AF_QIPCRTR readback works, and service69 remains
  empty.
- The next gate is narrowed to an in-helper QRTR nameservice matrix, not
  another broad lower retry or custom-kernel flash.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_qrtr_namespace_classifier_v820.py

python3 scripts/revalidation/native_wifi_qrtr_namespace_classifier_v820.py \
  --out-dir tmp/wifi/v820-qrtr-namespace-classifier-plan-check \
  plan

python3 scripts/revalidation/native_wifi_qrtr_namespace_classifier_v820.py run

git diff --check
```

## Next

V821 should run an in-helper QRTR nameservice matrix for service-locator,
service-notifier, WLAN-PD, and WLFW candidate services without QMI payload,
service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP, or external ping.
