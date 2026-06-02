# Native Init V1679 WLAN-PD Firmware-serve Modem-holder Source Build

## Summary

- Cycle: `V1679`
- Type: source/build-only rollbackable WLAN-PD firmware-serve test boot artifact
- Decision: `v1679-wlan-pd-firmware-serve-modem-holder-source-build-pass`
- Result: PASS
- Reason: corrected V1676/V1677 gate by adding a modem-only `/dev/subsys_modem` holder to the firmware-serve window
- Manifest: `tmp/wifi/v1679-wlan-pd-firmware-serve-modem-holder-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1679-wlan-pd-firmware-serve-modem-holder-test-boot/boot_linux_v1679_wlan_pd_firmware_serve_modem_holder.img`
- Boot SHA256: `92019041bdee94ed5479fadeb750df81f5806c19ad35f792afd4e20467f8a709`
- Init: `A90 Linux init 0.9.122 (v1679-wlan-pd-firmware-serve-modem-holder)`
- Init SHA256: `baf6aed6ecb5519f711da9b95a87afe024a5ff74fec94c41caf64cf093fd1b7d`
- Helper marker: `a90_android_execns_probe v306`
- Helper SHA256: `805d65929fe72ce0255c7bed7d84e4677dfb22816afb0fb475e81f760350d657`

## Correction From V1677

- V1678 host-only audit showed V1677 did not open `/dev/subsys_modem`, so mss/PIL never triggered.
- V1679 keeps the same read-only WLAN-PD firmware-serve contract but inserts a modem-only holder after the companion stack is spawned.
- eSoC/subsys_esoc0, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping remain disabled.

## Artifact Paths

- Log path: `/cache/native-init-wifi-test-boot-v1679.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1679.summary`
- Helper result path: `/cache/native-init-wifi-test-boot-v1679-helper.result`
