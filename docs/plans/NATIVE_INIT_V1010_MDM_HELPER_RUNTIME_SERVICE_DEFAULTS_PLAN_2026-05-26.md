# V1010 mdm_helper Runtime Contract Service-defaults Plan

## Goal

Run the reduced V911-style `mdm_helper` runtime-contract path, but force
service-defaults SELinux context handling. This isolates whether the V911
fd-positive result depended on its actual `kernel` execution context.

## Scope

1. Use deployed helper `v171`.
2. Keep the reduced V911 order:
   - private property shim;
   - `per_mgr_light`;
   - `mdm_helper`.
3. Add `--android-selinux-context-mode service-defaults`.
4. Poll and classify whether `mdm_helper` opens `/dev/esoc-0`.
5. Cleanup actors, with cleanup reboot only if postflight safety is not proven.

## Guardrails

Allowed:

- `mountsystem ro`;
- `selinuxfs` mount/umount;
- private property shim;
- `per_mgr_light`;
- `mdm_helper`;
- read-only `/proc/<pid>/fd`, status, and namespace evidence;
- cleanup reboot only if required.

Forbidden:

- service-manager, CNSS, Wi-Fi HAL, `wificond`, or full service-window actors;
- `/dev/subsys_esoc0` controller open;
- eSoC ioctl;
- Wi-Fi scan/connect/link-up;
- credential use;
- DHCP/routes;
- external ping;
- boot image, partition, firmware, GPIO, sysfs, or debugfs mutation.

## Success Criteria

V1010 passes if it records one of these classified outcomes without forbidden
actions:

- service-defaults reduced path still observes `/dev/esoc-0`;
- service-defaults reduced path no longer observes `/dev/esoc-0`;
- setup/precondition failure is safely classified with cleanup evidence.

A pass is not the final Wi-Fi objective. It determines whether the next route is
actor-order/peripheral-manager lifecycle or reduced-path SELinux/runtime input.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_runtime_contract_service_defaults_v1010.py
python3 scripts/revalidation/native_wifi_mdm_helper_runtime_contract_service_defaults_v1010.py \
  --out-dir tmp/wifi/v1010-mdm-helper-runtime-contract-service-defaults-plan \
  plan
```
