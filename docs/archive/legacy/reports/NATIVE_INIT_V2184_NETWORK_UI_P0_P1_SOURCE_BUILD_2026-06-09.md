# Native Init V2184 Network UI P0/P1 Source Build

## Summary

- Candidate tag: `v2184-network-ui-p0-p1`
- Parent baseline: `v2182-hud-menu-cleanup`
- Type: source/build-only test boot candidate.
- Decision: `v2184-network-ui-p0-p1-source-build-pass`
- Result: PASS
- Reason: V2184 keeps the V2182 HUD/menu baseline and adds network menu P0/P1 Wi-Fi screens.
- Manifest: `workspace/private/builds/native-init/v2184-network-ui-p0-p1-test-boot/manifest.json`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v725_fasttransport.img`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2184_network_ui_p0_p1.img`
- Boot SHA256: `d4d274a4e2b5b27a8136d45d4f176ed6b4adc1a3eb1c0195fa1361f0005d83f5`
- Boot SHA verification: source/build output only; live flash/readback/selftest must be recorded separately before promotion.
- Init: `A90 Linux init 0.9.256 (v2184-network-ui-p0-p1)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `99bdd67f0cd2fcaf6557478a97f85d405a0de3d6b0858ea17b4d46d7ce162ca1`

## Included Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v726/dev/__properties__`
- Added: `NETWORK > WIFI STATUS` read-only wlan0/link/IP/autoconnect screen.
- Added: `NETWORK > WIFI PROFILES` redacted profile/autoconnect inventory screen.
- Added: `NETWORK > WIFI SCAN` one-shot bounded nl80211 scan screen.
- Preserved: V2182 HUD storage/Wi-Fi glance, V2178 profile/autoconnect commands, and V2169 transport contract.

## Safety Scope

- Wi-Fi status and profile screens are read-only.
- Wi-Fi scan is bounded and credential-free; it does not associate, run DHCP, install routes/DNS, or ping.
- Scan result SSID/frequency/RSSI/security is rendered on screen only; raw BSSID/SSID results are not written to serial logs or public artifacts.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE path is included.
