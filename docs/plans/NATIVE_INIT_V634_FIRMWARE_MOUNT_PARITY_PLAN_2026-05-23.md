# Native Init V634 Firmware Mount Parity Plan

- date: `2026-05-23 KST`
- cycle: `v634`
- scope: live read-only mount proof
- runner: `scripts/revalidation/native_wifi_firmware_mount_parity_v584.py`
- target: verify that the firmware partitions required by V633 can be mounted
  read-only and cleaned up before any CDSP write retry

## Background

V633 proved native v319 currently has:

```text
firmware_class.path=/vendor/firmware_mnt/image
/vendor/firmware_mnt: missing
/vendor/firmware-modem: missing
cdsp state: OFFLINING
sysmon_cdsp: missing
```

V594 previously showed Android-style firmware mounts are important for lower
modem readiness. V634 reuses the existing V584 mount-parity runner, but only to
verify mountability and cleanup. It does not attempt CDSP boot, companion
daemons, CNSS, HAL, scan/connect, credentials, DHCP, routing, or external ping.

## Guardrails

V634 may:

- create temporary directories and block nodes in native tmpfs;
- mount `apnhlos` and `modem` partitions read-only;
- inspect mount contents and dmesg markers;
- unmount and remove temporary nodes/directories.

V634 must not:

- write ADSP/CDSP/SLPI boot nodes;
- touch `boot_wlan`, `qcwlanstate`, or `shutdown_wlan`;
- start companion daemons, service-manager, CNSS, Wi-Fi HAL, supplicant, or
  hostapd;
- scan/connect/link-up, use credentials, run DHCP, change routes, or ping
  externally;
- leave firmware mounts or `/vendor` shim changes behind.

## Success Criteria

V634 passes if:

- `apnhlos` and `modem` partitions resolve;
- `/vendor/firmware_mnt` and `/vendor/firmware-modem` mount read-only;
- cleanup unmounts both targets and removes temporary paths;
- post-check keeps native boot healthy;
- Wi-Fi bring-up remains unexecuted.

No QRTR/service-notifier delta is required for V634 because mount-only is not
expected to trigger CDSP or modem by itself. If mount parity succeeds and no
delta appears, the next gate should combine firmware mount parity with a
CDSP-only bounded proof.
