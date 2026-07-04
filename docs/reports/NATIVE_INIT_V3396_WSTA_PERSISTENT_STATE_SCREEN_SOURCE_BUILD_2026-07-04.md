# Native Init V3396 WSTA Persistent State Screen Source Build

- Cycle: `V3396`
- Decision: `v3396-wsta-persistent-state-screen-source-build`
- Init: `A90 Linux init 0.11.152 (v3396-wsta-persistent-state-screen)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3396_wsta_persistent_state_screen.img`
- Boot SHA256: `499f2b348d5d6ed9a5d219043d4fbef25dc4c158f542a4eec014b293c5e9872f`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3395_wsta_screenapp_live.img`

## Change

- Carries forward V3395 WSTA screenapp live validation.
- Replaces the generic publish-only wording with a redacted persistent-state screen.
- Shows `PUBLIC_OFF`, host-private lease gating, WSTA55/WSTA58 proof lineage, and private-run-only URL redaction.
- Does not add Wi-Fi connect, DHCP, public tunnel, native reboot, or flash behavior to the WSTA screen.

## Validation

- Build: AArch64 helper/native-init compile, required-string audit, preserved-ramdisk overlay, boot image pack, and SHA256 capture.
- Static source checks: `tests.test_native_wsta_operator_screenapp_source`.
- Builder regression: `tests.test_build_native_init_boot_v3396_wsta_persistent_state_screen`.
- No association, DHCP, ping, public exposure, userdata, switch-root, or live display action was performed in this source build.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `wsta-persistent-state-screen`.
