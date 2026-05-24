# Native Init V747 QCA6390 Driver-binding Delta Plan

- date: `2026-05-24 KST`
- basis evidence:
  - `tmp/wifi/v746-mdm-helper-sysmon-live-current/`
  - `tmp/wifi/v717-provider-first-icnss-edge-long-observe-20260524-103333/`
  - `tmp/wifi/v717-icnss-edge-surface-classifier/`
  - `tmp/wifi/v717-qca-bind-reconciliation/`
- scope: host-only/read-only comparison first

## Goal

Classify why native init leaves
`/sys/bus/platform/devices/a0000000.qcom,cnss-qca6390/driver` missing after
QRTR TX, `sysmon-qmi`, and a safe `mdm_helper` start. The goal is to identify
the Android event or driver state that binds/powers the QCA6390 platform child
before MHI/WLFW, without performing any bind/unbind action.

## Current Evidence

V746:

- `mss=OFFLINING -> ONLINE -> ONLINE`
- `mdm3=OFFLINING -> OFFLINING -> OFFLINING`
- QRTR RX/TX and `sysmon-qmi` present
- `mdm_helper` started and cleaned safely
- service `180`/`74`, WLAN-PD, MHI, WLFW, BDF, `wlan0` absent
- `a0000000.qcom,cnss-qca6390` platform device exists
- QCA6390 device `driver` link absent
- MHI drivers exist but MHI devices are absent

V717/V715/V716 already classified the same surface as
`v715-qca6390-platform-child-unbound` and
`v716-qca-child-unbound-not-bind-target`, so V747 must not simply retry bind.

## Work Items

1. Re-read V717/V715/V716 and V746 evidence into one host-only manifest.
2. Extract native device tree/sysfs fields for:
   - `a0000000.qcom,cnss-qca6390`
   - `18800000.qcom,icnss`
   - `/sys/bus/platform/drivers/*cnss*`
   - `/sys/bus/platform/drivers/*icnss*`
   - `/sys/bus/mhi/devices`
   - `/sys/bus/mhi/drivers`
3. Locate Android reference evidence for the same paths, or mark the Android
   side missing and require a later Android handoff capture.
4. Classify one of:
   - `android-reference-has-driver-link`
   - `android-reference-missing`
   - `native-driver-present-device-unbound`
   - `native-driver-absent`
   - `mhi-controller-not-created`
   - `bind-action-blocked-by-policy`
5. Select the next live proof only if a non-bind, non-persistent, bounded
   trigger is justified.

## Forbidden

- no QCA6390 bind/unbind
- no `driver_override`
- no Wi-Fi HAL start
- no scan/connect/link-up
- no credentials, DHCP, routes, or external ping
- no persistent writes to Android partitions

## Success Criteria

- Produce a host-only report with a clear driver-binding classification.
- Preserve the existing safety boundary.
- If Android evidence is insufficient, explicitly require a narrow Android
  handoff capture instead of guessing.
