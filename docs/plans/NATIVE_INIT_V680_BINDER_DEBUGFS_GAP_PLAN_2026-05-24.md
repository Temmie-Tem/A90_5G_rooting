# Native Init V680 Binder Debugfs Gap Plan

## Objective

Classify why V679 registry snapshots executed but Binder debug files and
per-child Binder proc files were not captured. V680 is host-only and uses only
existing V679 evidence.

## Inputs

- V679 live manifest:
  `tmp/wifi/v679-v535-binder-registry-snapshot-orchestrated-live/manifest.json`
- V679 arm manifest:
  `tmp/wifi/v679-v535-binder-registry-snapshot-orchestrated-live/arm-v679-v535-registry/live/manifest.json`
- V679 helper transcript and dmesg delta under the same evidence tree.

## Gate

Run `scripts/revalidation/native_wifi_binder_debugfs_gap_classifier_v680.py` to:

1. confirm V679 and the V679 arm passed;
2. confirm property denials stayed at zero;
3. confirm V679 registry phases executed;
4. summarize Binder debug path and directory capture blocks;
5. classify `/sys/kernel/debug/binder*` ENOENT/open-error counts;
6. verify no mount/device/live action is performed by V680.

## Forbidden Actions

- No device command.
- No mount or bind mount.
- No sysfs write.
- No DSP boot-node write.
- No `esoc0` open.
- No daemon or service-manager start.
- No Wi-Fi HAL start.
- No supplicant or hostapd start.
- No scan/connect/link-up.
- No credential, DHCP, route change, or external ping.
- No boot image or partition write.

## Success Criteria

- V680 runs host-only.
- V679 registry snapshot phases are confirmed.
- Binder debugfs path failure is classified from captured evidence.
- Next routing is narrowed to either private read-only debugfs/Binder debug
  surface proof or an alternate Binder transaction capture primitive.

## Commands

```sh
python3 -m py_compile \
  scripts/revalidation/native_wifi_binder_debugfs_gap_classifier_v680.py

python3 scripts/revalidation/native_wifi_binder_debugfs_gap_classifier_v680.py \
  --out-dir tmp/wifi/v680-binder-debugfs-gap-plan \
  plan

python3 scripts/revalidation/native_wifi_binder_debugfs_gap_classifier_v680.py \
  --out-dir tmp/wifi/v680-binder-debugfs-gap \
  run
```

## Expected Routing

If V680 proves debugfs/Binder debug paths are unavailable while Binder failures
persist, V681 should be a bounded private read-only debugfs/Binder debug surface
proof. If debugfs is impossible or too risky, the alternate route is a narrower
Binder transaction capture primitive outside debugfs.
