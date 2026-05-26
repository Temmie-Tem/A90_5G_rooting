# Native Init V1084 mdmdetect Instruction Trace Live Report

## Summary

V1084 passed. Live tracefs uprobes against `libmdmdetect.so` show that
`get_system_info()` fails before subsystem enumeration: ESOC root `stat()` fails,
then the MSM subsystem fallback `opendir()` path is reached and fails.

The blocker is now concrete: the private Android execution namespace used for
`pm-service` does not expose `/sys/bus/msm_subsys/devices`, so
`libmdmdetect` cannot classify the modem subsystem and `pm-service` exits before
opening `/dev/subsys_modem`.

## Change

- Added `scripts/revalidation/native_wifi_mdmdetect_instruction_trace_live_v1084.py`.
- Reused the V1082 bounded PM observer and tracefs-only dynamic uprobe pattern.
- Switched the trace target from `/mnt/vendor/bin/pm-service` to
  `/mnt/vendor/lib64/libmdmdetect.so`.
- Captured the branch-level `get_system_info()` path without BPF, Wi-Fi HAL,
  scan/connect, DHCP, external ping, flash, or reboot.

## Evidence

| item | path / value |
| --- | --- |
| runner | `scripts/revalidation/native_wifi_mdmdetect_instruction_trace_live_v1084.py` |
| plan | `docs/plans/NATIVE_INIT_V1084_MDMDETECT_INSTRUCTION_TRACE_LIVE_PLAN_2026-05-27.md` |
| manifest | `tmp/wifi/v1084-mdmdetect-instruction-trace-live/manifest.json` |
| summary | `tmp/wifi/v1084-mdmdetect-instruction-trace-live/summary.md` |
| observer transcript | `tmp/wifi/v1084-mdmdetect-instruction-trace-live/host/pm-service-tracefs-uprobe-observer.txt` |
| cleanup mounts | `tmp/wifi/v1084-mdmdetect-instruction-trace-live/host/proc-mounts-after-cleanup.txt` |
| final selftest | `tmp/wifi/v1084-mdmdetect-instruction-trace-live/host/post-selftest-final.txt` |

## Result

```text
decision: v1084-msm-subsys-root-opendir-failure
pass: True
reason: libmdmdetect get_system_info branch captured: msm-subsys-root-opendir-failure
next: use the captured branch to decide whether to repair ESOC/MSM sysfs namespace parity or subsystem device path parity
```

## Trace Counts

```json
{
  "mdm_esoc_stat_fail_branch": 2,
  "mdm_failure_after_msm_open": 2,
  "mdm_get_system_info_entry": 2,
  "mdm_msm_opendir_call": 2,
  "mdm_msm_opendir_fail_log": 2,
  "mdm_stat_esoc_call": 2
}
```

Negative controls:

- `mdm_msm_readdir_first=0`
- `mdm_get_subsystem_info_modem_call=0`
- `mdm_success_return=0`
- `subsys_info_entry=0`

## Interpretation

The library does not reach `get_subsystem_info()`. Therefore the current
blocker is earlier than `/dev/subsys_%s` path synthesis. The private Android
namespace lacks the MSM subsystem sysfs root that `libmdmdetect` expects.

The next cycle should repair namespace parity first, not retry PM actor ordering:
bind or otherwise expose the host kernel `/sys/bus/msm_subsys/devices` read-only
inside the private execution namespace, then rerun the same branch trace to
verify that `get_system_info()` advances into subsystem enumeration.

## Safety

- `tracefs_write_executed=True`.
- `bpf_attach_executed=False`.
- `pm_actor_executed=True` under the bounded observer only.
- `wifi_hal_start_executed=False`.
- `scan_connect_executed=False`.
- `credential_use_executed=False`.
- `dhcp_route_executed=False`.
- `external_ping_executed=False`.
- `partition_write_executed=False`.
- `flash_executed=False`.
- `reboot_executed=False`.
- Postflight forbidden actors: none.
- Postflight Wi-Fi links: none.
- Temporary vendor, tracefs, and SELinuxfs mounts were cleaned up.
- Final selftest: `pass=11 warn=1 fail=0`.
