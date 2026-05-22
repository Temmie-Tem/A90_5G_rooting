# Native Init V635 Firmware CDSP-Only Proof Plan

- date: `2026-05-23 KST`
- cycle: `v635`
- scope: live bounded proof
- target: combine V634 firmware mount parity with a CDSP-only boot-node proof
  to see whether CDSP reaches SSCTL/service `74`

## Background

V631 isolated the active node:

```text
ADSP: returned
CDSP: timed out
SLPI: returned
```

V633 then showed native v319 has `firmware_class.path` pointing at
`/vendor/firmware_mnt/image`, but the matching firmware mount surface is absent.
V634 proved that the Android firmware partitions can be mounted read-only and
cleaned up:

```text
apnhlos -> /vendor/firmware_mnt
modem   -> /vendor/firmware-modem
```

Mount-only did not produce QRTR/sysmon/service-notifier deltas. V635 therefore
adds exactly one trigger: `/sys/kernel/boot_cdsp/boot`.

## Guardrails

V635 may:

- create temporary native tmpfs directories and block nodes;
- mount `apnhlos` and `modem` read-only;
- write only `/sys/kernel/boot_cdsp/boot` from a bounded child;
- kill/reap the child on timeout;
- capture CDSP/sysmon/service-notifier/WLAN-PD/WLFW markers;
- unmount and remove temporary mount artifacts.

V635 must not:

- write ADSP or SLPI boot nodes;
- touch `boot_wlan`, `qcwlanstate`, or `shutdown_wlan`;
- start companion daemons, service-manager, CNSS, Wi-Fi HAL, supplicant, or
  hostapd;
- scan/connect/link-up, use credentials, run DHCP, change routes, or ping
  externally;
- leave firmware mounts behind.

## Success Criteria

V635 passes if it classifies one of these outcomes with cleanup evidence:

- `v635-cdsp-service74-advanced`
- `v635-cdsp-sysmon-only`
- `v635-cdsp-still-times-out-with-firmware`
- `v635-cdsp-returned-no-lower-marker`
- `v635-cdsp-proof-inconclusive`

Only `service_notifier_74`, WLAN-PD, WLFW/BDF, or `wlan0` advancement can
justify moving toward CNSS/HAL/connection gates. Native Wi-Fi connect and
`google.com` ping remain blocked unless those lower markers advance.
