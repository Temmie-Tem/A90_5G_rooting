# Native Init V2170 Wi-Fi Config Prepare Source Build

## Summary

- Candidate tag: `v2170-wifi-config-prepare`
- Parent baseline: `v2169-transport-contract`
- Type: source/build-only test boot candidate.
- Decision: `v2170-wifi-config-prepare-source-build-pass`
- Result: PASS
- Reason: V2170 keeps the V2169 transport contract and adds explicit, non-boot `wifi config prepare [profile]` supplicant config generation.
- Manifest: `workspace/private/builds/native-init/v2170-wifi-config-prepare-test-boot/manifest.json`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v725_fasttransport.img`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2170_wifi_config_prepare.img`
- Boot SHA256: `e774812a0b29b8255d374d756f851a53eccfd1eb9d1ebd304d91c0ee839ff035`
- Boot SHA verification: source/build output only; live flash/readback/selftest must be recorded separately before promotion.
- Init: `A90 Linux init 0.9.248 (v2170-wifi-config-prepare)`
- Helper marker: `a90_android_execns_probe helper-v427` (binary marker string: `a90_android_execns_probe v427`)
- Helper SHA256: `99bdd67f0cd2fcaf6557478a97f85d405a0de3d6b0858ea17b4d46d7ce162ca1`

## Included Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2170/dev/__properties__`
- Preserved from V2169: V726 Wi-Fi lifecycle route, PID1 modem lifecycle holder, fasttransport ramdisk, and device-side `transport.contract=1` status fields.
- Added: `wifi config prepare [profile]` validates secret-file backed Wi-Fi profile metadata and writes `/cache/a90-wifi/wpa_supplicant.conf` as `1010:1010` mode `0600`.
- Not added: boot autoconnect, scan, association, DHCP, route installation, external ping, or credential logging.

## Safety Scope

- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE path is included.
- The live validation must remain credential-redacted and rollbackable to `workspace/private/inputs/boot_images/boot_linux_v2169_transport_contract.img`.
