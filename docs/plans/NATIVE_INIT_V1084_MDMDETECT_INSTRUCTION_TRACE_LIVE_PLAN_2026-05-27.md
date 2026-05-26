# Native Init V1084 mdmdetect Instruction Trace Live Plan

## Objective

Trace `libmdmdetect.so::get_system_info()` directly during the bounded
`pm-service` observer run and classify the exact failing branch behind the
V1082/V1083 PM-service exit path.

## Background

V1082 proved `pm-service` exits after `get_system_info()` returns failure and
before Binder/QMI setup. V1083 classified the host-side library requirements:
ESOC/MSM SSR sysfs enumeration plus `/dev/subsys_%s` path synthesis. V1084 is
the live proof that determines which of those requirements is missing in the
native Android namespace.

## Scope

- Reuse the V1082 tracefs-only collector and PM observer pattern.
- Register dynamic uprobes against `/mnt/vendor/lib64/libmdmdetect.so`.
- Trace only bounded `get_system_info()` and `get_subsystem_info()` offsets.
- Preserve V1082 guardrails: no BPF attach and no Wi-Fi bring-up.

## Inputs

| item | path / value |
| --- | --- |
| V1083 manifest | `tmp/wifi/v1083-mdmdetect-system-info-classifier/manifest.json` |
| trace binary | `/mnt/vendor/lib64/libmdmdetect.so` |
| observer helper | `/cache/bin/a90_android_execns_probe` |

## Guardrails

- Explicit allow flags are required for tracefs mount/write, vendor read-only
  mount, SELinuxfs mount, and bounded PM-service observer start.
- No service-manager expansion beyond the existing observer contract.
- No Wi-Fi HAL start, scan/connect, credentials, DHCP, route change, external
  ping, partition write, flash, or reboot.
- Cleanup must remove tracefs events, unmount temporary mounts, and leave final
  selftest passing.

## Success Criteria

- V1083 predecessor is PASS.
- `libmdmdetect.so` is visible through the read-only vendor mount.
- Tracefs registers/enables/cleans all dynamic events.
- `mdm_get_system_info_entry` and `mdm_stat_esoc_call` fire.
- A terminal or actionable branch classification is produced.
- Postflight shows no forbidden actor or Wi-Fi link.
