# Native Init V620 DSP/MDM3 Safety Classifier Plan

- date: `2026-05-23 KST`
- cycle: `v620`
- scope: host-only classifier
- target: classify why native reaches sibling `sysmon-qmi` but not
  `service-notifier`, while direct DSP boot-node writes trigger `pm_qos`
  warnings and leave `mdm3=OFFLINING`

## Background

V619 executed the Android-order lower companion sequence and proved that
ordering alone is not enough:

```text
qrtr_ns -> pd_mapper -> rmt_storage -> tftp_server
```

The observer reached QRTR RX/TX and modem/adsp/cdsp/slpi `sysmon-qmi`, but
`service-notifier 180/74`, WLAN-PD, WLFW, BDF, firmware-ready, and `wlan0`
remained absent. It also reproduced the direct DSP boot-node `pm_qos` warning
class.

## Guardrails

V620 must not:

- contact the device;
- write sysfs, `boot_wlan`, `qcwlanstate`, or DSP boot nodes;
- start companion daemons, CNSS, service-manager, Wi-Fi HAL, `wificond`,
  supplicant, or hostapd;
- scan/connect/link-up, use credentials, run DHCP, change routes, or ping
  externally.

## Inputs

- V619 live evidence:
  `tmp/wifi/v619-android-order-post-sysmon-observer-run/manifest.json`
- V615 live evidence:
  `tmp/wifi/v615-dsp-boot-20260523-015352/v615-live/`
- V616/V617/V618 classifier manifests
- Android lower-surface evidence from V611/V612/V521/V525/V526
- Vendor init snapshot from V614

## Checks

1. Compare Android/native `pm_qos_add_request` warning presence and call traces.
2. Compare Android/native timing for ADSP/CDSP/SLPI boot, modem `sysmon-qmi`,
   sibling `sysmon-qmi`, service-locator, service-notifier, and `mdm3`.
3. Determine whether `mdm3=OFFLINING` is the stronger blocker than companion
   order.
4. Classify `vendor.mdm_launcher`, `vendor.mdm_helper`, `wcnss-service`, and
   `boot_wlan` as:
   - pre-service-notifier candidate;
   - later WLAN-only candidate;
   - unsafe/write-only candidate;
   - or unsupported by current evidence.
5. Produce a next live gate only if it avoids repeating direct DSP boot-node
   warnings.

## Success Criteria

V620 passes if it selects one of these outcomes using existing evidence:

- `v620-mdm3-trigger-gap-classified`
- `v620-direct-dsp-boot-unsafe-blocker`
- `v620-android-evidence-gap-needs-readonly-recapture`
- `v620-next-live-gate-ready`

Passing V620 does not authorize CNSS/HAL/Wi-Fi bring-up. If evidence is
insufficient, the next action should be Android read-only recapture, not another
native live write.

