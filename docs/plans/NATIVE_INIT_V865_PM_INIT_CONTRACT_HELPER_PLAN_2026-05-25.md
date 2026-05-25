# Native Init V865 PeripheralManager Init Contract Helper Plan

## Goal

Implement source/build-only helper support for the Android PeripheralManager
init contract classified by V864. V865 must not deploy the helper or start any
actor.

## Inputs

- `docs/reports/NATIVE_INIT_V864_PM_INIT_CONTRACT_SUPPORT_2026-05-25.md`
- `tmp/wifi/v865-post-build-v864-classifier/manifest.json` after implementation
- `stage3/linux_init/helpers/a90_android_execns_probe.c`
- `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/subsystem_restart.c`

## Rationale

V864 proved the current helper already captures runtime domain and fd evidence,
but does not model Android init behavior for `vendor.per_mgr`,
`vendor.per_proxy`, and `vendor.per_proxy_helper`. The OSRC kernel source also
contains a `pm_proxy_helper`-specific branch in `subsystem_restart.c`, so the
helper must model this actor separately before any `mdm_helper` or Wi-Fi HAL
escalation.

## Scope

1. Bump `a90_android_execns_probe` to helper `v134`.
2. Add `wifi-companion-peripheral-manager-init-contract-start-only` mode.
3. Add a distinct `per_proxy_helper` child for `/vendor/bin/pm_proxy_helper`.
4. Add default SELinux exec-context mapping for `/vendor/bin/pm_proxy_helper`.
5. Apply and record `ioprio rt 4` for the `per_mgr` child via `SYS_ioprio_set`.
6. Gate `per_proxy` after `per_mgr` is observable and emit
   `init.svc.vendor.per_mgr=running` lifecycle evidence.
7. Record shutdown-stop semantics for `vendor.per_proxy` during bounded cleanup
   without setting `sys.shutdown.requested`.
8. Build the static ARM64 helper and rerun the V864 classifier against the new
   source.

## Hard Gates

- Source/build only: no helper deploy and no device actor start.
- No `pm-service`, `pm-proxy`, `pm_proxy_helper`, `mdm_helper`, `ks`, Wi-Fi HAL,
  supplicant, hostapd, scan/connect, credentials, DHCP/routes, or external ping.
- No raw eSoC ioctl, GPIO write, sysfs/debugfs/subsystem write, module load,
  boot image write, or partition write.

## Success Criteria

- Helper builds as a static ARM64 executable.
- V864 classifier reports all source support markers present:
  `pm_proxy_helper`, SELinux mapping, `ioprio`, property lifecycle,
  shutdown-stop, runtime-domain capture, and subsystem-fd capture.
- Remaining gaps, if any, are evidence/runtime gaps reserved for V867 or later.
- Docs and next-work routing make V866 deploy-only and V867 bounded live proof
  the next separate units.
