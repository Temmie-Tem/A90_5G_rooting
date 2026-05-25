# Native Init V857 pm-service Property Contract Plan

## Goal

Replay only the PeripheralManager property contract observed in V856, while
keeping the run below `mdm_helper`, `ks`, Wi-Fi HAL, scan/connect, DHCP/routes,
and external ping.

## Inputs

- V855 node parity evidence:
  `tmp/wifi/v855-esoc-node-parity-preflight/manifest.json`
- V856 pm-service evidence:
  `tmp/wifi/v856-pm-service-node-parity-start-only-r5/manifest.json`
- V856 finding: `vendor.peripheral.shutdown_critical_list` writes were denied
  by the private property shim, while the offline state properties were allowed.

## Method

1. Add helper v132 mode
   `wifi-companion-peripheral-manager-property-contract-start-only`.
2. Keep the same child order as V856:
   `servicemanager,hwservicemanager,vndservicemanager,per_mgr,per_proxy`.
3. Keep V855-equivalent private/global node parity.
4. Allow only the observed additional property set operations:
   - `vendor.peripheral.shutdown_critical_list=SDX50M `
   - `vendor.peripheral.shutdown_critical_list=SDX50M modem `
5. Capture whether `pm-service` now holds `/dev/subsys_esoc0` and
   `/dev/subsys_modem`.
6. Clean up created nodes and verify native health.

## Guardrails

- No `mdm_helper` or `ks` start.
- No CNSS retry, Wi-Fi HAL, wificond, supplicant, hostapd, scan/connect,
  credential use, DHCP/routes, or external ping.
- No raw eSoC ioctl, direct eSoC/subsys node open outside the actor process,
  GPIO/sysfs/debugfs write, subsystem state write, module load/unload, boot
  image write, or Android partition write.
- Property shim expansion is limited to the two exact
  `vendor.peripheral.shutdown_critical_list` values above.

## Success Criteria

- Helper v132 is deployed or already current.
- V401 SELinuxfs and `mountsystem ro` prerequisites pass.
- V855-equivalent nodes are created and cleaned up.
- Helper reports property contract mode, allowed `1`, property contract `1`, and
  shutdown-critical-list allow `1`.
- The observed shutdown-critical-list property requests return success.
- Postflight remains `BOOT OK` with selftest `fail=0`.

## Commands

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_pm_service_property_contract_start_only_v857.py \
  scripts/revalidation/wifi_execns_helper_v132_deploy_preflight.py

scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v857-execns-helper-v132-build/a90_android_execns_probe

python3 scripts/revalidation/native_wifi_pm_service_property_contract_start_only_v857.py \
  --out-dir tmp/wifi/v857-pm-service-property-contract-plan \
  plan

python3 scripts/revalidation/native_wifi_pm_service_property_contract_start_only_v857.py \
  --out-dir tmp/wifi/v857-pm-service-property-contract-start-only \
  --allow-helper-deploy \
  --allow-netservice-start \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-node-materialization \
  --allow-node-cleanup \
  --allow-pm-service-start-only \
  --assume-yes \
  run
```
