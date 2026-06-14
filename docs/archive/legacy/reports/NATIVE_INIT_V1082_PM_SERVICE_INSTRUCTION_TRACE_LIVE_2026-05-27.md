# Native Init V1082 PM Service Instruction Trace Live Report

## Summary

V1082 passed. Live instruction-level tracefs uprobes confirm the V1081
classification: `pm-service` takes the `get_system_info` failure branch, returns
nonzero to main, closes the pipe fds, and exits before Binder setup.

The decisive negative controls are also confirmed:

- `helper_get_system_info_success_path=0`
- `main_binder_driver_call=0`

So the next blocker is not Binder/QMI bring-up. It is the missing Android state
that makes `libmdmdetect` `get_system_info` fail in the native namespace.

## Change

- Added `scripts/revalidation/native_wifi_pm_service_instruction_trace_live_v1082.py`.
- Reused the tracefs-only collector path from V1079/V1080.
- Replaced PLT-level probes with instruction-level probes from V1081.

## Evidence

| item | path / value |
| --- | --- |
| runner | `scripts/revalidation/native_wifi_pm_service_instruction_trace_live_v1082.py` |
| manifest | `tmp/wifi/v1082-pm-service-instruction-trace-live/manifest.json` |
| summary | `tmp/wifi/v1082-pm-service-instruction-trace-live/summary.md` |
| observer transcript | `tmp/wifi/v1082-pm-service-instruction-trace-live/host/pm-service-tracefs-uprobe-observer.txt` |
| cleanup mounts | `tmp/wifi/v1082-pm-service-instruction-trace-live/host/proc-mounts-after-cleanup.txt` |
| final selftest | `tmp/wifi/v1082-pm-service-instruction-trace-live/host/post-selftest-final.txt` |

## Result

```text
decision: v1082-pm-service-get-system-info-failure-branch-confirmed
pass: True
reason: get_system_info failure branch hit; success path and Binder setup not reached
next: classify get_system_info Android-state requirements before another PM live retry
```

## Instruction Counts

```json
{
  "helper_entry": 1,
  "helper_get_system_info_branch": 1,
  "helper_get_system_info_call": 1,
  "helper_get_system_info_failure_log": 1,
  "helper_get_system_info_failure_return": 1,
  "helper_get_system_info_success_path": 0,
  "main_binder_driver_call": 0,
  "main_entry": 1,
  "main_error_close0": 1,
  "main_error_close1": 1,
  "main_helper_call": 1,
  "main_helper_return_branch": 1,
  "main_pipe_call": 1
}
```

Observed order:

```text
main_entry
main_pipe_call
main_helper_call
helper_entry
helper_get_system_info_call
helper_get_system_info_branch
helper_get_system_info_failure_log
helper_get_system_info_failure_return
main_helper_return_branch
main_error_close0
main_error_close1
```

## PM Contract

```text
pm_service_trigger_observer.result=observer-runtime-gap
pm_service_trigger_observer.reason=child-exited-before-observe-window
pm_service_trigger_observer.child.per_mgr.exit_code=255
pm_service_trigger_observer.child.per_proxy.exit_code=1
pm_service_trigger_observer.per_mgr_subsys_modem_seen=0
pm_service_trigger_observer.pm_proxy_helper_subsys_modem_seen=0
pm_service_trigger_observer.all_postflight_safe=1
```

## Safety

- `bpf_attach_executed=False`.
- `wifi_hal_start_executed=False`.
- `scan_connect_executed=False`.
- `credential_use_executed=False`.
- `dhcp_route_executed=False`.
- `external_ping_executed=False`.
- `partition_write_executed=False`.
- `flash_executed=False`.
- `reboot_executed=False`.
- Postflight actor list was clean.
- Postflight Wi-Fi link list was clean.
- Final selftest: `pass=11 warn=1 fail=0`.

## Interpretation

The current native PM path fails before the peripheral manager can register with
Binder or QMI. `get_system_info` from `libmdmdetect` is the earliest confirmed
failing dependency. The next cycle should be host-only first: classify
`libmdmdetect.so` strings/imports/disassembly and Android reference evidence to
identify the exact system node, property, device file, or sysfs surface required
for `get_system_info` to return success.
