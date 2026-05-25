# Native Init V823 SSCTL Nameservice Matrix Plan

## Goal

Extend the V821 helper v125 nameservice matrix with the sysmon SSCTL lookup
identified by V822: service `43`, instance `16`.

## Scope

- Target runner:
  - `scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py`
- Reused helper:
  - `stage3/linux_init/helpers/a90_android_execns_probe.c`
  - helper marker `a90_android_execns_probe v125`
- Inputs:
  - `tmp/wifi/v822-sysmon-nameservice-gap-classifier/manifest.json`
  - V817 lower-window orchestration
- Matrix:
  - `servloc:64:1`
  - `ssctl:43:16`
  - `servnotif:66:74`
  - `servnotif:66:180`
  - `wlfw:69:0`
  - `wlfw:69:1`

## Hard Gates

- No custom kernel flash, boot image write, partition write, or bootloader
  handoff.
- No `esoc0` open, `qcwlanstate on/off`, bind/unbind, driver override, or
  module load/unload.
- No QMI payload transmission; only QRTR nameservice lookup/readback.
- No service-manager, Wi-Fi HAL, wificond, supplicant, scan/connect/link-up, or
  credential use.
- No DHCP, route change, or external ping.
- Preserve V775 custom OSRC kernel flashing pause.

## Success Criteria

- V822 manifest exists and passed with decision
  `v822-sysmon-ssctl-matrix-gap-classified`.
- Helper v125 is available locally and on-device, or is redeployed under the
  existing helper-v125 deploy gate.
- V823 live run completes V817 lower window and cleanup.
- Matrix emits six cases, all with AF_QIPCRTR socket family `42`, lookup send
  rc `0`, delete lookup send rc `0`, and no timeouts.
- `ssctl:43:16` is explicitly present in the matrix rows.
- QMI payload, HAL/connect, credential, DHCP/route, and external ping guardrails
  remain false.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py

python3 scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py \
  --out-dir tmp/wifi/v823-ssctl-nameservice-matrix-plan-check \
  plan

python3 scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py \
  preflight

python3 scripts/revalidation/native_wifi_ssctl_nameservice_matrix_v823.py \
  run
```

## Next

If SSCTL publishes, the next gate should classify SSCTL-to-service-notifier and
WLAN-PD continuation. If SSCTL also returns clean-empty, the next gate should
classify kernel QMI client visibility versus userspace AF_QIPCRTR nameservice
visibility before any wider trigger.
