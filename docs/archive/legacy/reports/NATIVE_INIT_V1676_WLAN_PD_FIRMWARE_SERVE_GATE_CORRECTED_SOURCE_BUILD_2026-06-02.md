# Native Init V1676 Corrected WLAN-PD Firmware-serve Gate Source Build

## Summary

- Cycle: `V1676`
- Type: source/build-only rollbackable WLAN-PD firmware-serve read-only test boot artifact
- Decision: `v1676-wlan-pd-firmware-serve-gate-corrected-source-build-pass`
- Result: PASS
- Reason: rebuilt the V1674 gate with helper v305 so tftp running state is sampled after observable-child capture
- Manifest: `tmp/wifi/v1676-wlan-pd-firmware-serve-gate-corrected-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1676-wlan-pd-firmware-serve-gate-corrected-test-boot/boot_linux_v1676_wlan_pd_firmware_serve_gate_corrected.img`
- Boot SHA256: `e79f2217e770b09dd562f4862d22e4768b06008b7f0a7b9101acfb6260e427da`
- Init: `A90 Linux init 0.9.121 (v1676-wlan-pd-firmware-serve-gate-corrected)`
- Init SHA256: `1b5aea5e9e94dd5c27e32cf8d8c4b6eede440daea8eea47c939621acd7292e79`
- Helper marker: `a90_android_execns_probe v305`
- Helper SHA256: `45769df9905d8beb8be11e69984a32ecfb3e3bdefe148a6fcf2d0fa7c7a2124a`

## Correction From V1675

- V1675 label `tqftpserv-not-running` is invalid because summary ran before `composite_capture_observable_children`.
- V1676 moves observable-child capture before `wlan_pd_firmware_serve_gate.*` summary and treats a non-reaped tftp child as running.
- The live gate must be repeated once as V1677; do not use V1675 for technical conclusions.
- Later V1678/V1680 work superseded V1677 because this V1676 artifact still lacked the required `/dev/subsys_modem` holder trigger.

## Gate Contract

- Active path is internal modem WLAN-PD only.
- Companion order: `qrtr_ns,pd_mapper,rmt_storage,tftp_server,cnss_diag,cnss_daemon`.
- No eSoC/subsys_esoc0, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Artifact Paths

- Log path: `/cache/native-init-wifi-test-boot-v1676.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1676.summary`
- Helper result path: `/cache/native-init-wifi-test-boot-v1676-helper.result`
