# Native Init V857 pm-service Property Contract Report

## Result

- decision: `v857-pm-property-contract-no-subsys-hold`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_pm_service_property_contract_start_only_v857.py`
- helper wrapper: `scripts/revalidation/wifi_execns_helper_v132_deploy_preflight.py`
- helper version: `a90_android_execns_probe v132`
- helper sha256: `a167500bd43f56a99da7e3644a8b240360de571aea5edc76b8afaa5215b1f5c7`
- evidence: `tmp/wifi/v857-pm-service-property-contract-start-only/`
- next: V858 should classify remaining `pm-service` property/context/service
  inputs before any `mdm_helper` or `ks` replay.

## Scope

V857 performed a bounded native live mutation. It prepared `mountsystem ro`,
mounted the V401 SELinuxfs runtime surface, deployed helper v132, materialized
V855-equivalent eSoC/subsys nodes, started only service-manager processes plus
`pm-service` and `pm-proxy`, allowed the two observed
`vendor.peripheral.shutdown_critical_list` property values, captured fd/runtime
evidence, cleaned up created nodes, and verified native health.

V857 did not start `mdm_helper`, `ks`, CNSS retry, Wi-Fi HAL, wificond,
supplicant, or hostapd. It did not scan/connect, use credentials, run DHCP,
change routes, ping externally, write GPIO/sysfs/debugfs, write subsystem state,
load/unload modules, write boot images, write Android partitions, or use raw
eSoC ioctl.

## Live Result

The helper reached the intended mode and order:

```text
mode=wifi-companion-peripheral-manager-property-contract-start-only
wifi_companion_start.allowed=1
wifi_companion_start.order=servicemanager,hwservicemanager,vndservicemanager,per_mgr,per_proxy
wifi_companion_start.peripheral_manager.enabled=1
wifi_companion_start.peripheral_manager.property_contract=1
wifi_hal_composite_start.property_service_shim.allow_peripheral_shutdown_list=1
```

Private node parity was present:

```text
wifi_companion_start.private_node.subsys_modem.exists=1
wifi_companion_start.private_node.subsys_esoc0.exists=1
wifi_companion_start.private_node.esoc_0.exists=1
```

The previously denied shutdown-critical-list writes succeeded:

```text
wifi_hal_composite_start.property_service_shim.request.3.name=vendor.peripheral.shutdown_critical_list
wifi_hal_composite_start.property_service_shim.request.3.value="SDX50M "
wifi_hal_composite_start.property_service_shim.request.3.allowed=1
wifi_hal_composite_start.property_service_shim.request.3.result=0x00000000
wifi_hal_composite_start.property_service_shim.request.5.name=vendor.peripheral.shutdown_critical_list
wifi_hal_composite_start.property_service_shim.request.5.value="SDX50M modem "
wifi_hal_composite_start.property_service_shim.request.5.allowed=1
wifi_hal_composite_start.property_service_shim.request.5.result=0x00000000
```

## Remaining Gap

V857 still did not prove Android-equivalent subsystem fd holds:

| Actor | fd evidence |
| --- | --- |
| `pm-service` | fd summary captured, but no fd targets remained by capture time |
| `pm-proxy` | `/dev/ttyGS0`, pipes, socket, and private `/dev/vndbinder`; no `subsys_*` fd |

The runtime result stayed:

```text
wifi_companion_start.result=start-only-runtime-gap
wifi_companion_start.reason=child-exited-before-observe-window
wifi_companion_start.all_postflight_safe=1
```

The new evidence closes the V856 property-set blocker but shows that it was not
sufficient to reproduce Android's `pm-service` subsystem-node holds.

## Newly Visible Follow-up

After the shutdown-critical-list writes were allowed, stderr still showed
property-context lookup gaps for service-specific read properties:

```text
libc: Could not find context for property "debug.ld.app.pm-service"
libc: Could not find context for property "arm64.memtag.process.pm-service"
libc: Could not find context for property "persist.log.tag.PerMgrSrv"
libc: Could not find context for property "log.tag.PerMgrSrv"
libc: Could not find context for property "debug.ld.app.pm-proxy"
libc: Could not find context for property "arm64.memtag.process.pm-proxy"
libc: Could not find context for property "persist.log.tag.PerMgrProxy"
libc: Could not find context for property "log.tag.PerMgrProxy"
```

These are property read/context gaps, not permission-denied set operations. V858
should classify whether Android's real property info/context files provide these
keys and whether adding the minimal property-context input changes
PeripheralManager lifetime or subsystem fd holds.

## Cleanup and Health

V857 removed all nodes created by the run:

```text
REMOVE /dev/esoc-0
REMOVE /dev/subsys_esoc0
REMOVE /dev/subsys_modem
```

Postflight stayed healthy:

```text
boot: BOOT OK shell 4.2s
selftest: pass=11 warn=1 fail=0
```

## Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_pm_service_property_contract_start_only_v857.py \
  scripts/revalidation/wifi_execns_helper_v132_deploy_preflight.py
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v857-execns-helper-v132-build/a90_android_execns_probe
python3 scripts/revalidation/native_wifi_pm_service_property_contract_start_only_v857.py \
  --out-dir tmp/wifi/v857-pm-service-property-contract-plan plan
python3 scripts/revalidation/native_wifi_pm_service_property_contract_start_only_v857.py \
  --out-dir tmp/wifi/v857-pm-service-property-contract-start-only \
  --allow-helper-deploy \
  --allow-netservice-start \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-node-materialization \
  --allow-node-cleanup \
  --allow-pm-service-start-only \
  --assume-yes run
```

Result:

```text
decision: v857-pm-property-contract-no-subsys-hold
pass: True
pm_service_start_only_executed: True
mdm_helper_start_executed: False
wifi_bringup_executed: False
external_ping_executed: False
```

## Next Gate

V858 should be a property-info/context classifier, not an actor escalation. It
should compare Android and native property inputs for the `pm-service` and
`pm-proxy` lookup keys above, then create a bounded helper proof that supplies
only the missing property context/input required for those reads. It must keep
`mdm_helper`, `ks`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external
ping, raw eSoC ioctl, GPIO/sysfs/debugfs/subsystem writes, module load/unload,
and boot-image changes out of scope.
