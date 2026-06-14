# Native Init V864 PeripheralManager Init Contract Support Report

## Result

V864 passed as a host-only classifier.

| Unit | Evidence | Decision |
|---|---|---|
| classifier | `scripts/revalidation/native_wifi_pm_init_contract_support_v864.py` | host-only source/evidence comparison |
| plan | `tmp/wifi/v864-pm-init-contract-support-plan/manifest.json` | `v864-init-contract-wrapper-needed` |
| run | `tmp/wifi/v864-pm-init-contract-support/manifest.json` | `v864-init-contract-wrapper-needed` |

## Findings

Prerequisites all passed:

- V861 decision: `v861-exec-target-accepted-current-kernel-no-subsys-hold`
- V862 decision: `v862-init-contract-classified-pm-proxy-helper-content-needed`
- V863 decision: `v863-pm-proxy-helper-contract-captured`
- helper source readable: yes

Current helper support:

| Requirement | Supported | Missing |
|---|---|---|
| `pm_proxy_helper` child model | no | `/vendor/bin/pm_proxy_helper`, `per_proxy_helper` |
| `pm_proxy_helper` SELinux mapping | no | `/vendor/bin/pm_proxy_helper`, `per_proxy_helper:s0` |
| `vendor.per_mgr` `ioprio rt 4` | no | `SYS_ioprio_set`, `IOPRIO_CLASS_RT`, `ioprio` |
| `vendor.per_proxy` property lifecycle | no | `init.svc.vendor.per_mgr` |
| `vendor.per_proxy` shutdown stop | no | `sys.shutdown.requested` |
| runtime domain capture | yes | - |
| subsystem fd capture | yes | - |

## Required V865 Changes

1. Add a distinct `per_proxy_helper` child that runs
   `/vendor/bin/pm_proxy_helper` once and captures exit, fd, and runtime domain
   evidence.
2. Add default exec-context mapping for `/vendor/bin/pm_proxy_helper` to the
   Android `per_proxy_helper` domain and record requested/current context.
3. Apply and record `SYS_ioprio_set` realtime class priority `4` for
   `vendor.per_mgr`.
4. Start `per_proxy` only after `per_mgr` is observable/running and emit the
   `init.svc.vendor.per_mgr=running` lifecycle marker.
5. Stop `per_proxy` explicitly during cleanup and record shutdown-stop
   semantics without setting `sys.shutdown.requested`.
6. Keep the V861 runtime-domain and subsystem-fd checks as blockers for
   `mdm_helper`/`ks` escalation.

## Guardrails

- No device contact, helper deploy, daemon start, `mdm_helper`, `ks`, Wi-Fi HAL,
  scan/connect, credentials, DHCP/routes, or external ping.
- No raw eSoC ioctl, GPIO/sysfs/debugfs/subsystem write, module load/unload,
  boot image write, or partition write.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_init_contract_support_v864.py
python3 scripts/revalidation/native_wifi_pm_init_contract_support_v864.py \
  --out-dir tmp/wifi/v864-pm-init-contract-support-plan plan
python3 scripts/revalidation/native_wifi_pm_init_contract_support_v864.py \
  --out-dir tmp/wifi/v864-pm-init-contract-support run
```

Output:

```text
decision: v864-init-contract-wrapper-needed
pass: True
```

## Next

Proceed to V865 source/build-only helper implementation. Do not deploy or start
actors until V865 static validation passes.
