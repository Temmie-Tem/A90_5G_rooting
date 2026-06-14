# Native Init V865 PeripheralManager Init Contract Helper Build Report

## Result

V865 completed as source/build-only.

| Unit | Evidence | Decision |
|---|---|---|
| helper source | `stage3/linux_init/helpers/a90_android_execns_probe.c` | helper `v134` implements PM init-contract model |
| build | `tmp/wifi/v865-execns-helper-v134-build/a90_android_execns_probe` | static ARM64 helper built |
| classifier | `tmp/wifi/v865-post-build-v864-classifier/manifest.json` | all source support markers present |

## Implemented

- Added `wifi-companion-peripheral-manager-init-contract-start-only` mode.
- Added distinct `per_proxy_helper` child targeting `/vendor/bin/pm_proxy_helper`.
- Added `/vendor/bin/pm_proxy_helper` SELinux exec-context mapping to
  `u:r:per_proxy_helper:s0`.
- Added `SYS_ioprio_set` realtime class priority `4` instrumentation for
  `per_mgr`.
- Added lifecycle evidence for `init.svc.vendor.per_mgr=running` before
  `per_proxy`.
- Added shutdown-stop evidence for `vendor.per_proxy` cleanup without setting
  `sys.shutdown.requested`.
- Preserved existing runtime `attr/current`, fd summary, fd link, and cleanup
  capture primitives.

## Validation

Executed:

```bash
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v865-execns-helper-v134-build/a90_android_execns_probe

python3 scripts/revalidation/native_wifi_pm_init_contract_support_v864.py \
  --out-dir tmp/wifi/v865-post-build-v864-classifier
```

Build output:

```text
artifact: tmp/wifi/v865-execns-helper-v134-build/a90_android_execns_probe
ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped
sha256: 92792fb954de42825d328c047498c5291be803185d9897d22dd734fd9bd77582
There is no dynamic section in this file.
```

Classifier source support matrix after V865:

| Requirement | Supported | Missing |
|---|---:|---|
| `per_proxy_helper` child model | yes | - |
| `per_proxy_helper` SELinux mapping | yes | - |
| `vendor.per_mgr` `ioprio rt 4` | yes | - |
| `vendor.per_proxy` property lifecycle | yes | - |
| `vendor.per_proxy` shutdown stop | yes | - |
| runtime domain capture | yes | - |
| subsystem fd capture | yes | - |

Classifier still returns `v864-init-contract-wrapper-needed` because the old
V861 live evidence still has two runtime blockers:

- runtime `attr/current` stayed `kernel`;
- `pm-service` did not prove `/dev/subsys_esoc0` or `/dev/subsys_modem` fd
  holds.

Those are no longer source-support gaps. They are V867 live evidence questions.

## Guardrails Held

- No helper deployment.
- No device actor start.
- No `mdm_helper`, `ks`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or
  external ping.
- No raw eSoC ioctl, GPIO/sysfs/debugfs/subsystem write, module load/unload,
  boot image write, or partition write.

## Next

Proceed to V866 deploy-only preflight/live deploy for helper `v134`. V867 is the
first bounded live start-only proof and must remain below `mdm_helper`, `ks`,
Wi-Fi HAL, scan/connect, DHCP/routes, and external ping.
