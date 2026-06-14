# Native Init V1329 Android-only SDX50M Prerequisite Classifier

## Summary

- Cycle: `V1329`
- Type: host-only classifier
- Decision: `v1329-android-prereq-is-earlier-sdx50m-response-sequence`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1329-android-only-sdx50m-prereq-classifier/manifest.json`
  - `tmp/wifi/v1329-android-only-sdx50m-prereq-classifier/summary.md`
- Script: `scripts/revalidation/native_wifi_android_only_sdx50m_prereq_classifier_v1329.py`

V1329 reconciles V1328 with Android-positive V852/V896/V1239 evidence.
Native reaches `mdm_subsys_powerup` and holds a full compact timing window,
but still gets no GPIO142/MDM2AP response, no MDM errfatal IRQ, no PCIe
RC1, no MHI/ks, no WLFW, and no `wlan0`. Android evidence contains the
complete downstream chain and shows PCIe L0 before the captured
`pm-service` eSoC timestamp, so the next unknown is an earlier Android-only
SDX50M response prerequisite or timing relation.

## Decision

The next useful unit is not Wi-Fi HAL, scan/connect, credentials, DHCP,
external ping, or a PMIC/GPIO/eSoC mutation. V1330 should design a focused
Android read-only timing recapture that puts earliest `per_mgr`/`per_proxy`,
`mdm_helper`, GPIO142, PCIe RC1, and `ks`/MHI on one monotonic timeline.

## Safety

Host-only classifier. No device command, helper deploy, actor start, tracefs
write, live eSoC ioctl/notify, PMIC write, GPIO request, GDSC/eSoC write,
Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external ping,
flash, boot image write, or partition write occurred.
