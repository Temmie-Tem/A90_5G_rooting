# V384 Service-Manager SIGABRT Early-Crash Capture

## Summary

- Implemented local `a90_android_execns_probe v15` support for `service-manager-start-only` with `--capture-mode ptrace-lite`.
- Added V384 fail-closed deploy/live wrappers for later explicit approval.
- No V384 deploy, daemon start, Wi-Fi HAL start, scan, connect, DHCP, routing, or link-up was executed in this work.

## Artifact

- local helper: `tmp/wifi/v384-a90_android_execns_probe-v15/a90_android_execns_probe`
- marker: `a90_android_execns_probe v15`
- sha256: `dfd543c02ccefbbbcf2fe0eb7ee168b40d40363927a63104c7aef0b9aed0bb16`
- file: `ELF 64-bit LSB executable, ARM aarch64, statically linked`

## Code Changes

- `stage3/linux_init/helpers/a90_android_execns_probe.c`
  - bumped helper marker to v15
  - allows `--capture-mode ptrace-lite` for `service-manager-start-only` only with `--allow-service-manager-start-only`
  - adds service-manager-specific ptrace-lite bounded execution path
  - captures exec/crash stop markers, siginfo, limited register set, status, maps, mountinfo, stdout, and stderr
  - preserves bounded timeout and postflight cleanup behavior
- `scripts/revalidation/wifi_service_manager_start_only_live_runner.py`
  - adds `--capture-mode {none,ptrace-lite}` with default `none`
- `scripts/revalidation/wifi_execns_helper_v15_deploy_preflight.py`
  - V384 deploy wrapper for helper v15 only
- `scripts/revalidation/wifi_service_manager_start_only_v384_live_runner.py`
  - V384 live wrapper fixed to helper v15, private property root, private-empty data tree, and ptrace-lite capture
- `scripts/revalidation/wifi_service_manager_runtime_gap_classifier.py`
  - recognizes ptrace crash evidence and classifies captured SIGABRT as `service-manager-runtime-gap-servicemanager-sigabrt-captured`

## Validation

```text
$ aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -o tmp/wifi/v384-a90_android_execns_probe-v15/a90_android_execns_probe stage3/linux_init/helpers/a90_android_execns_probe.c
PASS

$ sha256sum tmp/wifi/v384-a90_android_execns_probe-v15/a90_android_execns_probe
dfd543c02ccefbbbcf2fe0eb7ee168b40d40363927a63104c7aef0b9aed0bb16

$ strings tmp/wifi/v384-a90_android_execns_probe-v15/a90_android_execns_probe | rg 'a90_android_execns_probe v15|service-manager-start-only|ptrace-lite'
PASS

$ python3 -m py_compile scripts/revalidation/wifi_service_manager_runtime_gap_classifier.py scripts/revalidation/wifi_service_manager_start_only_live_runner.py scripts/revalidation/wifi_execns_helper_v15_deploy_preflight.py scripts/revalidation/wifi_service_manager_start_only_v384_live_runner.py
PASS

$ python3 scripts/revalidation/wifi_service_manager_runtime_gap_classifier.py --out-dir tmp/wifi/v384-classifier-regression regression
service-manager-runtime-gap-classifier-regression-pass

$ python3 scripts/revalidation/wifi_service_manager_start_only_v384_live_runner.py --out-dir tmp/wifi/v384-live-no-approval-regression run
service-manager-start-only-live-approval-required
```

## Approval Boundary

Deploy v15 later requires exact phrase:

```text
approve v384 deploy execns helper v15 only; no daemon start and no Wi-Fi bring-up
```

Live crash capture later requires exact phrase:

```text
approve v384 service-manager ptrace-lite crash capture only; no Wi-Fi HAL start and no Wi-Fi bring-up
```

The older V382/V373 approval phrases are not sufficient for V384 deploy/live.

## Next

1. Run V384 deploy wrapper with exact v15 deploy approval.
2. Run V384 service-manager ptrace-lite crash-capture wrapper with exact live crash-capture approval.
3. Route/classify the captured evidence.
4. Decide whether the next blocker is Binder, SELinux/service context, property runtime, linker namespace, or another fatal check.
