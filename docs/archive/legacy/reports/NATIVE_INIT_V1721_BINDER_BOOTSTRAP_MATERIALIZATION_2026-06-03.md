# Native Init V1721 Binder Bootstrap Materialization

## Summary

- Cycle: `V1721`
- Type: read-only Binder bootstrap input/materialization classifier
- Decision: `v1721-vndservicemanager-absent-servicemanager-vndbinder-fallback-required`
- Result: PASS
- Evidence: `tmp/wifi/v1721-binder-bootstrap-materialization`

## Basis

- V1720 fixed the current blocker at `defaultServiceManager()` inside `libperipheral_client.so`.
- This gate checks the concrete service-manager binary contract before starting any service-manager actor in a new live gate.

## Read-only Device Findings

- `mountsystem ro` ok: `True`
- `/mnt/system/system/bin/servicemanager` present: `True`
- `/mnt/system/system/bin/hwservicemanager` present: `True`
- `/mnt/system/system/lib64/libbinder.so` present: `True`
- direct `/vendor/bin/vndservicemanager` present: `False`
- mounted/system `vndservicemanager` candidates present: `False`

### `vndservicemanager` Search

- none

### `libbinder.so` Search

- `/mnt/system/system/lib64/libbinder.so`
- `/mnt/system/system/lib/libbinder.so`
- `/mnt/system/system/system_ext/apex/com.android.vndk.v30/lib64/libbinder.so`
- `/mnt/system/system/system_ext/apex/com.android.vndk.v30/lib/libbinder.so`
- `/mnt/system/system/apex/com.android.vndk.current/lib64/libbinder.so`
- `/mnt/system/system/apex/com.android.vndk.current/lib/libbinder.so`

## Host/Source Contract

- Host `servicemanager` artifact present: `True`
- Host `servicemanager` advertises usage string: `True`
- Host `servicemanager` contains `/dev/binder` string: `True`
- Host `servicemanager` depends on `libbinder.so`: `True`
- Helper hardcodes `/vendor/bin/vndservicemanager`: `True`
- Helper hardcodes `/dev/vndbinder` arg for VND manager: `True`

## Interpretation

- The mounted current image does not expose a standalone `vndservicemanager` binary.
- The existing helper still models the vendor Binder context manager as `/vendor/bin/vndservicemanager /dev/vndbinder`.
- For this firmware, the narrower next unit is source/build support for a `servicemanager`-binary vendor-Binder mode: execute `/system/bin/servicemanager /dev/vndbinder` under `u:r:vndservicemanager:s0`, then prove `defaultServiceManager()` can progress past the V1719 block.
- Do not reintroduce PM trio or `vendor.qcom.PeripheralManager` service startup until that service-manager-only proof passes.

## Next Gate

- V1722 source/build-only helper patch: add a `COMPOSITE_ID_VND_SERVICE_MANAGER` path that can use `/system/bin/servicemanager` with `/dev/vndbinder` when standalone `vndservicemanager` is absent.
- V1723 live should be service-manager-only or CNSS-plus-service-manager bootstrap proof, still no PM trio, no `boot_wlan`, no `/dev/subsys_esoc0`, no Wi-Fi HAL, no scan/connect, no credentials, no DHCP/routes, no external ping.

## Safety Scope

The live part only ran `hide`, `version`, `selftest`, `mountsystem ro`, `stat`, `cat`, and `toybox find` read-only commands. It did not start Android daemons, service managers, PM actors, `boot_wlan`, Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE`, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
