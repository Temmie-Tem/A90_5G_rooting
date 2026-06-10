# Native Init V2186 Wi-Fi UI Polish Source Build

## Summary

- Candidate tag: `v2186-wifi-ui-polish`
- Parent baseline: `v2185-network-ping-test`
- Type: source/build-only test boot candidate.
- Decision: `v2186-wifi-ui-polish-source-build-pass`
- Result: PASS
- Reason: V2186 keeps the V2185 network-ping baseline and polishes Wi-Fi status/HUD labels with redacted link metrics.
- Manifest: `workspace/private/builds/native-init/v2186-wifi-ui-polish-boot/manifest.json`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v725_fasttransport.img`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2186_wifi_ui_polish.img`
- Boot SHA256: `7a0db3bb76232f778869d3bf0788268f3a1942b230b094158dddf7a7d500fd32`
- Boot SHA verification: source/build output only; live flash/readback/selftest must be recorded separately before promotion.
- Init: `A90 Linux init 0.9.258 (v2186-wifi-ui-polish)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `99bdd67f0cd2fcaf6557478a97f85d405a0de3d6b0858ea17b4d46d7ce162ca1`

## Included Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v726/dev/__properties__`
- Added: `wifi status` runtime fields for WPA state, RSSI, link speed, and frequency.
- Added: `NETWORK > WIFI STATUS` clearer PASS/RUN/OFF/FAIL labels and RF line.
- Preserved: V2185 network ping menu/CLI, V2182 HUD storage/Wi-Fi glance, V2178 profile/autoconnect commands, and V2169 transport contract.

## Safety Scope

- Wi-Fi status and profile screens are read-only.
- Wi-Fi scan is bounded and credential-free; it does not associate, run DHCP, install routes/DNS, or ping.
- Wi-Fi ping is explicit user/test action only; it does not connect, run DHCP, change routes, or read credentials.
- Gateway target is redacted in command output; public reports must redact private LAN details.
- Scan result SSID/frequency/RSSI/security is rendered on screen only; raw BSSID/SSID results are not written to serial logs or public artifacts.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE path is included.
