# Native Init V1680 WLAN-PD Firmware-serve Gate Handoff

## Summary

- Cycle: `V1680`
- Type: one-run rollbackable read-only WLAN-PD firmware-serve gate
- Decision: `v1680-firmware-not-requested-rollback-pass`
- Result: PASS
- Reason: one read-only WLAN-PD firmware-serve gate run produced a fixed label and rollback verified
- Evidence: `tmp/wifi/v1680-wlan-pd-firmware-serve-modem-holder-handoff`
- Rollback attempt: `from-native`

## Gate Label

- Label: `firmware-not-requested`
- tftp running: `1`
- subsys_modem holder started: `1`
- subsys_modem holder opened: `1`
- subsys_modem holder postflight safe: `1`
- requested wlanmdsp: `0`
- requested modem image: `0`
- served wlanmdsp nonzero: `0`
- served modem.mdt nonzero: `1`
- served modem blob nonzero: `1`
- WLFW service 69 seen: `0`
- WLAN-PD uninit: `0`
- service-notifier state: `None`
- companion order: `qrtr_ns,pd_mapper,rmt_storage,tftp_server,subsys_modem_holder,cnss_diag,cnss_daemon`

## Internal Modem Trigger Proof

- `/dev/subsys_modem` holder started: `1`
- `/dev/subsys_modem` holder opened: `1`
- dmesg recorded `4080000.qcom,mss: modem: loading`.
- dmesg recorded `4080000.qcom,mss: modem: Brought out of reset`.
- `rmt_storage` received modem EFS open requests for `/boot/modem_fs1`, `/boot/modem_fs2`, and `/boot/modem_fsg`.
- No request for `wlanmdsp.mbn` or modem image was captured by tftp/tqftp during the observed window.

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
