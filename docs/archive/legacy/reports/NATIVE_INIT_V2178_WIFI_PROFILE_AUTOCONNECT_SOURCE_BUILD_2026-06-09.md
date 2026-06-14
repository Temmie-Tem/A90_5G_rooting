# Native Init V2178 Wi-Fi Profile Autoconnect Source Build

## Summary

- Candidate tag: `v2178-wifi-profile-autoconnect`
- Parent test route: `v2176-wifi-dhcp`
- Current rollback baseline: `v2174-wifi-urandom-connect`
- Type: promoted test/native-init baseline image after V2179 validation.
- Decision: `v2178-wifi-profile-autoconnect-source-build-pass`
- Result: PASS
- Reason: V2178 keeps the V2176 Wi-Fi connect/DHCP/cleanup route and adds profile inventory plus explicit autoconnect controls.
- Manifest: `workspace/private/builds/native-init/v2178-wifi-profile-autoconnect-test-boot/manifest.json`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v725_fasttransport.img`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2178_wifi_profile_autoconnect.img`
- Boot SHA256: `8ea6f468f997446e9fa3e80606db107ca27d067f3ee023ff45c2ecf159341047`
- Init: `A90 Linux init 0.9.253 (v2178-wifi-profile-autoconnect)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `99bdd67f0cd2fcaf6557478a97f85d405a0de3d6b0858ea17b4d46d7ce162ca1`

## Included Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v726/dev/__properties__`
- Preserved from V2176: `wifi connect [profile]`, `wifi dhcp [profile]`, `wifi cleanup`, standalone `wpa_supplicant`, V726 Wi-Fi lifecycle route, and `transport.contract=1` status fields.
- Added: `wifi profile list` and `wifi profile status [profile]` for redacted profile inventory and validation.
- Added: `wifi autoconnect status|enable [profile]|disable|once [profile]` with explicit opt-in config and no boot external ping.
- Added: boot-background autoconnect worker that returns immediately when disabled and stays off unless `autoconnect=1` is staged.
- Added: reset-per-run autoconnect log/result states, immediate `wifi-autoconnect-running`, disabled/no-config stale-result guard, profile-list dedupe counters, and Wi-Fi status/HUD decision surfacing.

## Safety Scope

- Raw SSID/PSK still live only in private config/secret files and generated runtime supplicant config.
- Boot autoconnect is disabled by default and does not run external ping.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE path is included.
