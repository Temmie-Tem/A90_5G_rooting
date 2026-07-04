# Native Init V3388 Wi-Fi Autoconnect Scan Recovery Source Build

- Cycle: `V3388`
- Decision: `v3388-wifi-autoconnect-scan-recovery-source-build`
- Init: `A90 Linux init 0.11.144 (v3388-wifi-autoconnect-scan-recovery)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3388_wifi_autoconnect_scan_recovery.img`
- Boot SHA256: `2971367ef2421161ee18a30a2eeb8088fa1a04b377dbfdf208aa9130cfa6d1f9`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3387_wifi_uplink_service_redacted.img`

## Change

- Carries forward the V3387 uplink-service command surface and response redaction.
- Adds one bounded native autoconnect scan-recovery path: cleanup, AP-iftype add/delete probe, then rescan.
- Records only redacted recovery booleans/return codes in `autoconnect.result` and the uplink-service response.
- Keeps the confirmed-autoconnect gate, public tunnel denial, external ping denial, and `secret_values_logged=0` contract.

## Validation

- Build: AArch64 helper/native-init compile, required-string audit, preserved-ramdisk overlay, boot image pack, and SHA256 capture.
- Static source checks: `tests.test_native_wifi_uplink_service_source`.
- Builder regression: `tests.test_build_native_init_boot_v3388_wifi_autoconnect_scan_recovery`.
- No association, DHCP, ping, public exposure, userdata, or switch-root action was performed in this source unit.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `wifi-autoconnect-scan-recovery`.
