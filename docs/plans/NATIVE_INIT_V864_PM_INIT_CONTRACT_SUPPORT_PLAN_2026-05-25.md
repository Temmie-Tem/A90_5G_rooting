# Native Init V864 PeripheralManager Init Contract Support Plan

## Goal

Classify whether the current helper already supports the complete Android
PeripheralManager init contract exposed by V861-V863 before starting any new
actor.

## Inputs

- `tmp/wifi/v861-pm-service-domain-parity-live-r2/manifest.json`
- `tmp/wifi/v862-android-init-service-contract/manifest.json`
- `tmp/wifi/v863-pm-proxy-helper-rc-live/manifest.json`
- `stage3/linux_init/helpers/a90_android_execns_probe.c`

## Scope

1. Verify V861/V862/V863 prerequisite decisions.
2. Compare current helper source against the required contract:
   - `vendor.per_proxy_helper /vendor/bin/pm_proxy_helper` oneshot child;
   - `vendor.per_mgr` `ioprio rt 4`;
   - `vendor.per_proxy` start after `init.svc.vendor.per_mgr=running`;
   - shutdown stop semantics for `vendor.per_proxy`;
   - runtime domain and subsystem fd evidence capture.
3. Emit an implementation checklist for V865.

## Hard Gates

- Host-only: no device contact and no helper deployment.
- No service start: no `pm-service`, `pm-proxy`, `pm_proxy_helper`,
  `mdm_helper`, `ks`, Wi-Fi HAL, supplicant, or hostapd.
- No scan/connect/link-up, credential use, DHCP/routes, or external ping.
- No raw eSoC ioctl, GPIO write, sysfs/debugfs/subsystem write, module load,
  boot image write, or partition write.

## Success Criteria

- V861/V862/V863 evidence is present and matches expected decisions.
- Current helper support is classified requirement-by-requirement.
- Missing implementation items are concrete enough to drive V865.
- The next live gate remains blocked until V865 build/static checks pass.
