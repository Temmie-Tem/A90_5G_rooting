# Native Init V1086 PM Service Success Path Trace Live Report

## Summary

V1086 passed. After V1085 fixed `get_system_info()`, `pm-service` reaches the
Binder service registration path but fails at `addService`. It then takes the
clean exit path and returns `0`.

This explains the V1085 observer state: `per_mgr` is not killed and no longer
fails in mdmdetect. It exits because the Binder service registration path fails
before QMI thread creation and before any `/dev/subsys_modem` hold.

## Change

- Added `scripts/revalidation/native_wifi_pm_service_success_path_trace_live_v1086.py`.
- Reused the bounded PM observer and tracefs-only dynamic uprobe harness.
- Traced `/mnt/vendor/bin/pm-service` offsets after `get_system_info()` success.

## Evidence

| item | path / value |
| --- | --- |
| runner | `scripts/revalidation/native_wifi_pm_service_success_path_trace_live_v1086.py` |
| plan | `docs/plans/NATIVE_INIT_V1086_PM_SERVICE_SUCCESS_PATH_TRACE_LIVE_PLAN_2026-05-27.md` |
| manifest | `tmp/wifi/v1086-pm-service-success-path-trace-live/manifest.json` |
| summary | `tmp/wifi/v1086-pm-service-success-path-trace-live/summary.md` |
| observer transcript | `tmp/wifi/v1086-pm-service-success-path-trace-live/host/pm-service-tracefs-uprobe-observer.txt` |
| final selftest | `tmp/wifi/v1086-pm-service-success-path-trace-live/host/post-selftest-final.txt` |

## Result

```text
decision: v1086-binder-add-service-failure
pass: True
reason: PM-service post-mdmdetect branch captured: binder-add-service-failure
```

## Trace Counts

```json
{
  "pm_success_branch_after_get_system_info": 1,
  "pm_init_with_driver_call": 1,
  "pm_default_service_manager_call": 1,
  "pm_add_service_call": 1,
  "pm_add_service_fail_log": 1,
  "pm_pthread_create_call": 0,
  "pm_qmi_service_start_log": 0,
  "pm_sigwait_call": 0,
  "pm_clean_exit_log": 1,
  "pm_clean_return_zero": 1
}
```

## PM Contract

```text
pm_service_trigger_observer.result=observer-runtime-gap
pm_service_trigger_observer.reason=child-exited-before-observe-window
pm_service_trigger_observer.child.per_mgr.exit_code=0
pm_service_trigger_observer.child.per_mgr.signal=0
pm_service_trigger_observer.child.per_mgr.term_sent=0
pm_service_trigger_observer.per_mgr_subsys_modem_seen=0
pm_service_trigger_observer.pm_proxy_helper_subsys_modem_seen=0
pm_service_trigger_observer.all_postflight_safe=1
```

## Interpretation

The next blocker is Binder service registration, not mdmdetect and not QMI
thread startup. `pm-service` reaches:

```text
get_system_info success
  -> ProcessState::initWithDriver("/dev/vndbinder")
  -> defaultServiceManager()
  -> addService("vendor.qcom.PeripheralManager", ...)
  -> addService failure log
  -> clean return 0
```

The next cycle should classify the `addService` failure reason. Most likely
targets are Binder context-manager readiness, service-context/SELinux service
labeling, or the private service-manager namespace not accepting
`vendor.qcom.PeripheralManager`.

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
