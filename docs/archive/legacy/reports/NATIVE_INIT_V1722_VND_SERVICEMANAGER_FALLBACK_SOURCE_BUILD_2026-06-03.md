# Native Init V1722 VND Servicemanager Fallback Source Build

## Summary

- Cycle: `V1722`
- Type: source/build-only helper contract patch verifier
- Decision: `v1722-vnd-servicemanager-fallback-source-build-pass`
- Result: PASS
- Evidence: `tmp/wifi/v1722-vnd-servicemanager-fallback-source-build`
- Helper: `tmp/wifi/v1722-vnd-servicemanager-fallback-source-build/a90_android_execns_probe_v321`
- Helper SHA256: `57aa9f95395480fe8b9fa28a424ae71c3c46572846796f78d73b06e10cac599e`

## Change

- `COMPOSITE_ID_VND_SERVICE_MANAGER` now executes the system `servicemanager` binary with `/dev/vndbinder`.
- The VND manager child keeps the `u:r:vndservicemanager:s0` SELinux exec context through an identity/profile-aware context override.
- Logged argv contracts now report `/system/bin/servicemanager /dev/vndbinder`.
- Common Wi-Fi test-boot helper expectations now point at helper marker `v321` and the new SHA.

## Checks

- Source checks: `{'version_v321': True, 'vendor_profile_targets_system_servicemanager': True, 'vnd_context_override': True, 'composite_vnd_target_fallback': True, 'new_argv_logged': True, 'old_argv_not_logged': True}`
- Static AArch64 helper: `True`
- No dynamic section: `True`
- Marker present: `True`
- New argv present: `True`
- Old argv absent from helper strings: `True`
- VND SELinux context present: `True`

## Next Gate

- V1723 should deploy/use helper v321 and run one rollbackable live proof that starts only the service-manager bootstrap needed to unblock `defaultServiceManager()`.
- It must still not start PM trio, `vendor.qcom.PeripheralManager`, `boot_wlan`, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Safety Scope

This script performed host-side source/build work only. It did not contact the device, flash, reboot, start actors, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE`, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
