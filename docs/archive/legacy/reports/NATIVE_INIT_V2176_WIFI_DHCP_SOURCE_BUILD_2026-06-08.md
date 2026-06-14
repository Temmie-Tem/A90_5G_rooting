# Native Init V2176 Wi-Fi DHCP Source Build

## Summary

- Candidate tag: `v2176-wifi-dhcp`
- Parent baseline: `v2174-wifi-urandom-connect`
- Type: source/build-only test boot candidate.
- Decision: `v2176-wifi-dhcp-source-build-pass`
- Result: PASS
- Reason: V2176 keeps the V2174 Wi-Fi carrier baseline and adds explicit native-init DHCP/cleanup primitives.
- Manifest: `workspace/private/builds/native-init/v2176-wifi-dhcp-test-boot/manifest.json`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v725_fasttransport.img`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2176_wifi_dhcp.img`
- Boot SHA256: `1defb35d2fbbefba5972046ba2c15391329db10bfc2201bdbd0b787279aa668d`
- Boot SHA verification: source/build output only; live flash/readback/selftest must be recorded separately before promotion.
- Init: `A90 Linux init 0.9.252 (v2176-wifi-dhcp)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `99bdd67f0cd2fcaf6557478a97f85d405a0de3d6b0858ea17b4d46d7ce162ca1`

## Included Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v726/dev/__properties__`
- Preserved from V2174: `wifi status`, `wifi scan [delay_ms]`, `wifi connect [profile]`, `/dev/random` and `/dev/urandom`, V726 Wi-Fi lifecycle route, and `transport.contract=1` status fields.
- Added: `wifi dhcp [profile]` requires an existing carrier, runs bounded `udhcpc`, installs temporary route/DNS through a generated `/cache/a90-wifi/udhcpc-wlan0.script`, records redacted DHCP status, and refreshes the Wi-Fi HUD/runtime summary.
- Added: `wifi cleanup` terminates the private supplicant control path, stops DHCP residue, removes temporary wlan0 route/address/DNS state, and refreshes the runtime summary.
- Not added: boot autoconnect, unbounded ping, raw credential logging, or permanent Wi-Fi profile storage.

## Safety Scope

- DHCP and route/DNS mutation are explicit Wi-Fi connectivity scope only.
- External ping remains runner/test scope, not part of `wifi dhcp [profile]`.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE path is included.
