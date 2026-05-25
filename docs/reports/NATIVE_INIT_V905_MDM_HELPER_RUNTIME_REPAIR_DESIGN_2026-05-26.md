# Native Init V905 mdm_helper Runtime Repair Design Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only classifier | `tmp/wifi/v905-mdm-helper-runtime-repair-design/manifest.json` | `v905-runtime-repair-design-mdm-helper-property-shim-first` |

V905 reconciles the proposed Android dmesg/Magisk direction with the newer V896-V904 evidence. The Android recapture is not the current blocker; the next useful work is a source/build-only runtime-contract capture mode for `mdm_helper`.

## Findings

- V896 already contains the Android positive evidence needed for this branch: GPIO 142 `mdm status` IRQ count reaches `1`, Android dmesg shows PCIe RC1 link initialization, and Android actors hold `/dev/esoc-0` plus the MHI pipe.
- V904 shows native direct `mdm_helper` is observable but stays in `kernel` context and never reaches `/dev/esoc-0`, `ks`, MHI, or subsystem fd surfaces.
- V478-V487 show accepted SELinux procattr writes do not produce a native child domain transition, so SELinux is not a safe primary repair gate yet.
- V867 shows full PeripheralManager init-contract replay with `pm_proxy_helper` can enter D-state and require reboot cleanup; that path must not be repeated blindly.
- Current helper source has `mdm_helper` identity support and property-shim infrastructure, but lacks explicit `mdm_helper`/`ks` default SELinux mappings.

## Selected Next Unit

V906 should be source/build-only. Add `wifi-companion-mdm-helper-runtime-contract-capture` with these constraints:

- start no live actor during V906; build and static-verify only;
- materialize existing node/path parity and property-service shim support;
- add default source mappings for `/vendor/bin/mdm_helper` and `/vendor/bin/ks` to `u:r:vendor_mdm_helper:s0`, while recording that runtime transition may still remain `kernel`;
- optionally start `pm-service` in a light ordering before `mdm_helper` in the later live gate, but do not start `pm_proxy_helper`;
- do not open `/dev/subsys_esoc0` from the controller; only observe whether `mdm_helper`/`ks` naturally reach `/dev/esoc-0`, MHI, GPIO142, `mdm3`, WLFW/BDF, or `wlan0`;
- keep service-manager, CNSS daemon, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, module load/unload, boot image writes, partition writes, GPIO/sysfs/debugfs writes blocked.

## Guardrails

- No device contact, Android boot, ADB command, Magisk module, actor start, eSoC ioctl, subsystem open, daemon start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, reboot, boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs write, or Wi-Fi bring-up occurred in V905.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_runtime_repair_design_v905.py
python3 scripts/revalidation/native_wifi_mdm_helper_runtime_repair_design_v905.py
```
