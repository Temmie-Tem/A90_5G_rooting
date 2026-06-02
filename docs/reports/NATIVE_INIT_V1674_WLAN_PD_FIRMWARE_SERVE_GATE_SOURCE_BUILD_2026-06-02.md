# Native Init V1674 WLAN-PD Firmware-serve Gate Source Build

## Summary

- Cycle: `V1674`
- Type: source/build-only rollbackable WLAN-PD firmware-serve read-only test boot artifact
- Decision: `v1674-wlan-pd-firmware-serve-gate-source-build-pass`
- Result: PASS
- Reason: built the corrected internal-modem WLAN-PD gate and explicitly excluded eSoC/RC1/MDM2AP triggers
- Manifest: `tmp/wifi/v1674-wlan-pd-firmware-serve-gate-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1674-wlan-pd-firmware-serve-gate-test-boot/boot_linux_v1674_wlan_pd_firmware_serve_gate.img`
- Boot SHA256: `528b67a2e4e39c58d7a78837f6bcd78c4d8d9a365ab1f18464adbdd5f433cfeb`
- Init: `A90 Linux init 0.9.120 (v1674-wlan-pd-firmware-serve-gate)`
- Init SHA256: `5a007d2a58c573bdbcc01687733859e849311f42ace00233612007062a9c9d19`
- Helper marker: `a90_android_execns_probe v304`
- Helper SHA256: `3804ce34a84147a0ce41be9f9c088468a4606f53d8c3bf27542881f69b40eaa9`

## Gate Contract

- Active path is internal modem WLAN-PD: `mss ONLINE -> tqftpserv/tftp_server -> wlanmdsp.mbn -> WLFW service 69 -> ICNSS -> wlan0`.
- Helper mode: `wifi-companion-wlan-pd-firmware-serve-gate-start-only`.
- Companion order: `qrtr_ns,pd_mapper,rmt_storage,tftp_server,cnss_diag,cnss_daemon`.
- Captures tftp/companion stdout/stderr, served firmware path snapshots, WLFW service 69 readback, and WLAN-PD service-notifier state.
- Labels exactly one of: `firmware-not-requested`, `firmware-requested-but-absent-at-served-path`, `firmware-served-pd-still-uninit`, `tqftpserv-not-running`.
- No eSoC/subsys_esoc0, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Artifact Paths

- Log path: `/cache/native-init-wifi-test-boot-v1674.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1674.summary`
- Helper result path: `/cache/native-init-wifi-test-boot-v1674-helper.result`

## Next

Run one rollbackable V1675 live handoff, restore `stage3/boot_linux_v724.img`, verify native `selftest fail=0`, then stop on the gate label.
