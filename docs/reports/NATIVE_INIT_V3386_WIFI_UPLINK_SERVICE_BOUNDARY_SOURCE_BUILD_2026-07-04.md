# Native Init V3386 Wi-Fi Uplink Service Boundary Source Build

- Cycle: `V3386`
- Decision: `v3386-wifi-uplink-service-boundary-source-build`
- Init: `A90 Linux init 0.11.142 (v3386-wifi-uplink-service-boundary)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3386_wifi_uplink_service_boundary.img`
- Boot SHA256: `9c097e55a2cf1f371ebba581378eeeb058c192147cdf6964d1c6721c7350a55a`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3385_wifi_service_boundary.img`

## Change

- Carries forward the V3385 native-owned `wifi service` status/scan boundary unchanged.
- Adds a separate native-owned `wifi uplink-service [status|start|stop|once] <dir>` command surface.
- The uplink service supports `status` and token-gated `autoconnect` requests over the same request/response file pattern.
- `autoconnect` requires `confirm=A90_NATIVE_UPLINK_AUTOCONNECT_V1` and delegates to the existing native autoconnect/profile path.
- Public tunnel and external ping execution remain denied; credentials stay private-config-gated with `secret_values_logged=0`.
- This is source/build only; live association/DHCP requires a separate credential-gated validation unit.

## Validation

- Build: AArch64 helper/native-init compile, required-string audit, preserved-ramdisk overlay, boot image pack, and SHA256 capture.
- Static source checks: `tests.test_native_wifi_service_boundary_source`, `tests.test_native_wifi_uplink_service_source`.
- Builder regression: `tests.test_build_native_init_boot_v3386_wifi_uplink_service_boundary`.
- No device action, association, DHCP, ping, or public exposure was performed in this source unit.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `wifi-uplink-service-boundary`.
