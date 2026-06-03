# Native Init V1875 Lower Response Read-only Sampler Preflight

## Summary

- Cycle: `V1875`
- Type: host-only V1874 lower-response sampler artifact preflight
- Decision: `v1875-lower-response-readonly-sampler-preflight-pass`
- Label: `lower-response-readonly-sampler-live-ready`
- Result: PASS
- Reason: V1874 boot/helper artifacts are present, hash-matched, v357-marked, and configured for a read-only lower-response sampler with scan/connect and RC1 write paths blocked.
- Evidence: `tmp/wifi/v1875-lower-response-readonly-sampler-preflight`

## Checks

| check | value |
|---|---:|
| `v1874_manifest_present` | `True` |
| `v1874_decision_pass` | `True` |
| `v1874_report_present` | `True` |
| `helper_exists` | `True` |
| `boot_image_exists` | `True` |
| `helper_sha_matches_manifest` | `True` |
| `boot_sha_matches_manifest` | `True` |
| `helper_marker_v357_present` | `True` |
| `helper_contract_strings_present` | `True` |
| `boot_init_build_present` | `True` |
| `boot_property_root_present` | `True` |
| `boot_helper_result_present` | `True` |
| `private_sdx50m_route_enabled` | `True` |
| `lower_observer_mode_enabled` | `True` |
| `firmware_mounts_enabled` | `True` |
| `debugfs_mount_enabled_for_readonly_snapshots` | `True` |
| `scan_connect_credentials_blocked` | `True` |
| `rc1_writes_blocked` | `True` |

## Artifacts

- Manifest: `tmp/wifi/v1874-lower-response-readonly-sampler-test-boot/manifest.json`
- Report: `docs/reports/NATIVE_INIT_V1874_LOWER_RESPONSE_READONLY_SAMPLER_SOURCE_BUILD_2026-06-03.md`
- Helper binary: `tmp/wifi/v1874-lower-response-readonly-sampler-test-boot/a90_android_execns_probe_v357`
- Helper SHA256: `8ec9d4153e5dcc966888170bfef0c3428f2261b30c0e58836697c91442386d87`
- Boot image: `tmp/wifi/v1874-lower-response-readonly-sampler-test-boot/boot_linux_v1874_lower_response_readonly_sampler.img`
- Boot SHA256: `9f79cdf9b9dfaac1ac512fc04f712a352f0afb40e1bb0438303c9a4cb8171f5e`

## Next

- Cycle: `V1876`
- Type: `one-run rollbackable live handoff`
- Boot image: `tmp/wifi/v1874-lower-response-readonly-sampler-test-boot/boot_linux_v1874_lower_response_readonly_sampler.img`
- Required stop: do not attempt Wi-Fi connect or ping unless WLFW service 69 and wlan0 are both present

## Safety Scope

V1875 is host-only. It does not contact the device, flash, reboot, start services, open `/dev/subsys_esoc0`, force RC1, fake ONLINE state, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE`, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
