# Native Init V594/V595 Global Firmware Modem Readiness Plan

- date: `2026-05-22 KST`
- objective: prove whether Android-style global firmware mounts let native init drive modem PIL/QRTR readiness before any Wi-Fi HAL, scan, connect, or external ping attempt

## Background

V593 classified the native blocker as a firmware visibility gap:

- `firmware_class.path=/vendor/firmware_mnt/image`
- native global `/vendor/firmware_mnt` and `/vendor/firmware-modem` were absent
- `subsys_modem` open entered modem PIL loading but failed to locate `modem.bXX`

V584 already proved both firmware partitions can be mounted read-only and cleaned:

- `apnhlos -> /vendor/firmware_mnt`
- `modem -> /vendor/firmware-modem`

The remaining question is whether those global mounts must be active while the modem subsystem char device is opened.

## Guardrails

- No daemon start.
- No service-manager.
- No Wi-Fi HAL or `IWifi.start()`.
- No `qcwlanstate` or driver-state sysfs write.
- No supplicant, hostapd, or wificond.
- No scan/connect/link-up.
- No credentials, DHCP, route changes, or external ping.
- Firmware partitions are mounted read-only only.
- Temporary mount/node cleanup is required; reboot is the fallback cleanup.

## V594

Combine:

1. V584 global read-only firmware mounts.
2. V592 helper-owned `subsys-hold-open-proof`.

Success criteria:

- `/vendor/firmware_mnt` and `/vendor/firmware-modem` are mounted read-only.
- `firmware_class.path` remains Android-equivalent.
- `modem.b00` is visible under the mounted modem firmware partition.
- `subsys_modem` open reaches PIL/QRTR readiness.
- All helper children and temporary mounts are cleaned.

Failure criteria:

- Global firmware mounts are incomplete.
- `subsys_modem` still fails firmware loading.
- Any helper child remains unclean.
- Any daemon/HAL/scan/connect action occurs.

## V595

If V594 reaches readiness but gets stuck on the helper's `esoc0` open path, split the trigger:

1. Mount global firmware partitions read-only.
2. Create only a temporary `subsys_modem` char node.
3. Open, briefly hold, and close only the modem char device.
4. Capture modem state, rpmsg/QRTR, dmesg, cleanup, and post-health.

Success criteria:

- `subsys_modem` open completes without residual process.
- QRTR modem readiness or equivalent lower marker appears.
- Firmware mounts and temporary node are cleaned.
- No daemon/HAL/scan/connect action occurs.

Safety stop:

- Any kernel WARNING, reference mismatch, residual process, or mount leak blocks repetition and requires a safer hold/release design.

