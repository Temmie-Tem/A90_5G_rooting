# Native Init V825 QRTR Encoded Matrix Plan

## Goal

Run the V824 encoded QRTR nameservice matrix in the existing V817 lower window,
without sending any QMI payload or starting Android Wi-Fi components.

## Scope

- Target runner:
  - `scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py`
- Input:
  - `tmp/wifi/v824-qrtr-encoded-instance-classifier/manifest.json`
- Reused helper:
  - helper marker `a90_android_execns_probe v125`
  - helper sha256 `49194d47fc251d3201f6af65ff78909087f4734584383f1d600a5daab29d30da`
- Matrix:
  - `servloc:64:257`
  - `ssctl:43:4098`
  - `servnotif:66:18945`
  - `servnotif:66:46081`
  - `wlfw:69:1`

## Hard Gates

- No custom kernel flash, boot image write, partition write, or bootloader
  handoff.
- No `esoc0` open, `qcwlanstate on/off`, bind/unbind, driver override, or
  module load/unload.
- No QMI payload transmission.
- No service-manager, Wi-Fi HAL, wificond, supplicant, scan/connect/link-up, or
  credential use.
- No DHCP, route change, or external ping.
- Preserve the V775 custom OSRC kernel flashing pause.

## Success Criteria

- V824 manifest exists and passed with decision
  `v824-qmi-encoded-instance-gap-classified`.
- The matrix matches V824's `next_encoded_matrix`.
- Helper v125 is available locally and on-device, or is redeployed under the
  existing helper-v125 deploy gate.
- V817 lower window completes and cleanup reboot runs.
- All five encoded cases complete with AF_QIPCRTR socket family `42`, lookup
  send rc `0`, delete lookup send rc `0`, no timeouts, and no QMI payload.
- Guardrails remain false for HAL/connect, credential use, DHCP/routes,
  external ping, boot image writes, partition writes, and custom kernel flashes.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py

python3 scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py \
  --out-dir tmp/wifi/v825-qrtr-encoded-matrix-plan-check \
  plan

python3 scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py \
  --out-dir tmp/wifi/v825-qrtr-encoded-matrix-preflight-check \
  preflight

python3 scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py \
  run
```

## Next

If encoded nameservice publication is visible, the next gate should classify the
published services and payload details before any QMI payload or wider trigger.
If publication is still empty, the raw-vs-encoded explanation is closed and the
next gate should return to kernel QMI-client versus userspace AF_QIPCRTR
visibility.
