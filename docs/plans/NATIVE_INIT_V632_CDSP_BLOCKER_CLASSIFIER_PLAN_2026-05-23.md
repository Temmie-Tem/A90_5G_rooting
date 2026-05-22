# Native Init V632 CDSP Blocker Classifier Plan

- date: `2026-05-23 KST`
- cycle: `v632`
- scope: host-only classifier
- target: classify the V631 CDSP timeout before another live write or Wi-Fi
  bring-up attempt

## Background

V631 split the V630 sibling SSCTL proof by node:

```text
ADSP: write returned
CDSP: write blocked until timeout, child reaped
SLPI: write returned
```

No service `74`, WLAN-PD, WLFW/BDF, Wi-Fi link-up, or external ping advanced.
This makes CDSP the current active blocker below CNSS/HAL and before Wi-Fi
connection testing.

## Guardrails

V632 must not:

- contact the device;
- write sysfs or repeat ADSP/CDSP/SLPI boot-node writes;
- build or flash a boot image;
- start companion daemons, service-manager, CNSS, Wi-Fi HAL, supplicant, or
  hostapd;
- touch `boot_wlan`, `qcwlanstate`, or `shutdown_wlan`;
- scan/connect/link-up, use credentials, run DHCP, change routes, or ping
  externally.

## Inputs

- V631 live proof report and evidence:
  `docs/reports/NATIVE_INIT_V631_PER_NODE_SIBLING_SSCTL_PROOF_LIVE_2026-05-23.md`
- V622 Android same-boot timing:
  `tmp/wifi/v622-android-mdm-helper-timing-handoff-live-20260523-032506/`
- V629 sibling SSCTL host-only classifier:
  `tmp/wifi/v629-sibling-ssctl-trigger-classifier/manifest.json`
- V614 vendor init read-only snapshot:
  `tmp/wifi/v614-mdm3-trigger-path-classifier/native/vendor-init-readonly-snapshot.txt`
- External context from Android kernel/device references for CDSP loader and
  Qualcomm ADSP/CDSP/SLPI boot-device ordering

## Checks

1. Parse V631 per-node result and confirm CDSP is the only node that blocks.
2. Compare Android V622 CDSP SSCTL, service `74`, WLAN-PD, and firmware-ready
   timing against native V631.
3. Confirm V614 vendor init writes ADSP/CDSP in `early-boot` and SLPI through
   the sensors init path.
4. Treat adjacent Qualcomm references as context only: CDSP boot nodes are
   firmware/subsystem-loader surfaces, not Wi-Fi connect surfaces.
5. Decide whether the next gate should be read-only CDSP surface collection,
   CDSP-only bounded write proof, or evidence refresh.

## Success Criteria

V632 passes if it classifies one of these outcomes without device mutation:

- `v632-cdsp-prerequisite-gap-classified`
- `v632-cdsp-evidence-gap`
- `v632-cdsp-live-write-not-justified`

Passing V632 does not authorize Wi-Fi HAL, `boot_wlan`, `qcwlanstate`,
scan/connect, credentials, DHCP, route changes, or external ping. The next
action should remain below Wi-Fi connection until CDSP/service `74`/WLAN-PD
markers advance under native init.
