# Native Init V679 Binder Registry Snapshot Plan

## Objective

Capture Binder registry/debug state around the V677/V678 failing window. V678
proved the private property runtime is clean and the remaining blocker is the
`cnss-daemon` vndbinder transaction failure before WLFW/BDF/`wlan0`. V679 adds
read-only Binder registry snapshots to the same Android userspace-order path.

## Inputs

- V678 classifier:
  `tmp/wifi/v678-binder-failure-targets/manifest.json`
- V677 replay evidence:
  `tmp/wifi/v677-v676-residual-property-replay-live/manifest.json`
- Helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`
- V535 private property root:
  `/mnt/sdext/a90/private-property-v317/v535/dev/__properties__`

## Implementation

V679 adds helper v112 mode:

```text
wifi-companion-service74-gated-android-userspace-cnss-retry-registry-snapshot-start-only
```

This mode reuses the V676/V677 sequence:

```text
qrtr-ns -> rmt_storage -> tftp_server -> pd-mapper
  -> cnss_diag -> initial cnss-daemon
  -> service74 gate
  -> servicemanager -> hwservicemanager -> vndservicemanager
  -> vndservicemanager readiness
  -> initial cnss-daemon cleanup
  -> Wi-Fi HAL legacy/ext -> wificond -> fresh cnss-daemon retry
  -> registry snapshot
```

Snapshot phases:

- `before_initial_cnss_cleanup`
- `after_initial_cnss_cleanup`
- `after_cnss_retry_spawn`
- `window`

Captured surfaces are bounded:

- `/sys/kernel/debug/binder/{state,stats,transactions,transaction_log,failed_transaction_log}`
- `/sys/kernel/debug/binder/proc`
- per-child `/sys/kernel/debug/binder/proc/<pid>`
- private namespace `/dev/__properties__`
- private namespace `/dev/socket`

## Forbidden Actions

- No supplicant or hostapd start.
- No scan/connect/link-up.
- No credential use.
- No DHCP, route change, or external ping.
- No sysfs subsystem state write.
- No direct ADSP/CDSP/SLPI boot-node write.
- No `esoc0` open.
- No boot image or partition write.

## Success Criteria

- Helper v112 builds as a static AArch64 binary.
- Helper v112 deploy/preflight passes.
- V679 current-boot prep refreshes V641/V401/V490 prerequisites.
- V679 live arm starts only the bounded Android userspace-order surface.
- Registry snapshot phases reach `end=1` after CNSS retry spawn and during the
  window.
- Property denials stay at zero.
- No scan/connect, DHCP, route change, credential use, Wi-Fi bring-up, or
  external ping occurs.
- Reboot cleanup returns to healthy native control.

## Commands

```sh
python3 -m py_compile \
  scripts/revalidation/native_wifi_v535_binder_registry_snapshot_v679.py \
  scripts/revalidation/native_wifi_v535_binder_registry_snapshot_orchestrator_v679.py \
  scripts/revalidation/wifi_execns_helper_v112_deploy_preflight.py

bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v679-execns-helper-v112-build/a90_android_execns_probe

python3 scripts/revalidation/wifi_execns_helper_v112_deploy_preflight.py \
  --out-dir tmp/wifi/v679-execns-helper-v112-deploy-postfix \
  --transfer-method serial \
  --apply \
  --assume-yes \
  --approval-phrase "approve v679 deploy execns helper v112 only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/native_wifi_v535_binder_registry_snapshot_orchestrator_v679.py \
  --out-dir tmp/wifi/v679-v535-binder-registry-snapshot-orchestrated-live \
  --apply \
  --assume-yes \
  run
```

## Expected Routing

If snapshot phases are captured but Binder debug files are unavailable, V680
should classify Binder debugfs availability and alternate Binder transaction
observation paths before another runtime repair. If WLFW/BDF/`wlan0` advances,
route toward the first supplicant/scan gate instead.
