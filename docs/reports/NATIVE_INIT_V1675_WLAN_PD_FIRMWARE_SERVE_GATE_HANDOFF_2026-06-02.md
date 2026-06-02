# Native Init V1675 WLAN-PD Firmware-serve Gate Handoff

## Superseded Result

- This report is retained as raw evidence only.
- The `tqftpserv-not-running` label below is invalid because the V1675 helper summarized tftp child state before observable-child capture.
- Use V1676/V1677 for the corrected classifier and final gate label.

## Summary

- Cycle: `V1675`
- Type: one-run rollbackable read-only WLAN-PD firmware-serve gate
- Decision: `v1675-tqftpserv-not-running-rollback-pass`
- Result: PASS
- Reason: one read-only WLAN-PD firmware-serve gate run produced a fixed label and rollback verified
- Evidence: `tmp/wifi/v1675-wlan-pd-firmware-serve-gate-handoff`
- Rollback attempt: `from-native`

## Gate Label

- Label: `tqftpserv-not-running`
- tftp running: `0`
- requested wlanmdsp: `0`
- requested modem image: `0`
- served wlanmdsp nonzero: `0`
- served modem.mdt nonzero: `1`
- served modem blob nonzero: `1`
- WLFW service 69 seen: `0`
- WLAN-PD uninit: `0`
- service-notifier state: `None`
- companion order: `qrtr_ns,pd_mapper,rmt_storage,tftp_server,cnss_diag,cnss_daemon`

## Safety Scope

- eSoC/subsys_esoc0, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, and BOOT_DONE spoof were not used.
- Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope was test boot flash followed by rollback to `stage3/boot_linux_v724.img`.

## Next

- Stop here for handoff. Do not spin timing/window variants for this gate.
- If label is `firmware-not-requested`, analyze why the modem never requests WLAN-PD firmware.
- If label is `firmware-requested-but-absent-at-served-path`, fix served-path parity in a separate approved gate.
- If label is `firmware-served-pd-still-uninit`, next work is modem-side WLAN-PD start trigger, not MSA.
- If label is `tqftpserv-not-running`, fix companion startup before any lower-layer expansion.
