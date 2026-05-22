# Native Init V643 V642 Publisher Gap Classifier Plan

- date: `2026-05-23 KST`
- cycle: `v643`
- scope: host-only classifier
- target: compare V642 clean-DSP no-CNSS evidence against V598/V625/V627
  CNSS-including partial-positive evidence before selecting the next live gate

## Background

V642 proved a clean, warning-free path from V641 DSP state to:

```text
QRTR RX -> QRTR TX -> sysmon-qmi
```

but it did not publish service-notifier. Earlier V598/V625/V627 safe paths did
publish service-notifier `180`, but those companion windows included
`cnss_diag` and `cnss-daemon`.

## Guardrails

V643 is host-only and must not:

- contact the device;
- write sysfs or mount anything;
- start companion daemons, CNSS, service-manager, Wi-Fi HAL, `wificond`,
  supplicant, or hostapd;
- scan/connect/link-up, use credentials, run DHCP, change routes, or ping
  externally.

## Inputs

- V598: `tmp/wifi/v598-modem-holder-wlfw-readback/manifest.json`
- V619: `tmp/wifi/v619-android-order-post-sysmon-observer-run/manifest.json`
- V625: `tmp/wifi/v625-fresh-v598-class-live/manifest.json`
- V627: `tmp/wifi/v627-post-180-observer-live-v2/manifest.json`
- V642: `tmp/wifi/v642-live-20260523-070145/manifest.json`

## Checks

1. Compare companion order and child count:
   - V642/V619: `qrtr_ns,pd_mapper,rmt_storage,tftp_server`
   - V598/V625/V627:
     `qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon`
2. Compare QRTR TX, `sysmon-qmi`, service-notifier, WLAN-PD, WLFW/QMI, BDF,
   and `wlan0` markers.
3. Compare kernel warning presence to keep V619's direct DSP boot-node warning
   class out of the next live path.
4. Compare `mdm3_after_companion` and service `74` status.

## Success Criteria

V643 passes if it classifies whether:

- service-notifier `180` correlates with the CNSS-including child window rather
  than clean-DSP/no-CNSS state alone;
- service `74`/WLAN-PD/WLFW remains a separate lower publisher gap;
- the next live gate should remain bounded below HAL/scan/connect.

## Next Gate

Expected next gate is V644: a clean-DSP CNSS/WLFW readback replay that reuses
V641/V642 prerequisites but intentionally tests the CNSS-including path below
HAL/scan/connect.
