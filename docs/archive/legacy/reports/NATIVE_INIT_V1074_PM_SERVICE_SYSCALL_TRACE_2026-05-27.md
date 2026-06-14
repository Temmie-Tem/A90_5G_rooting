# Native Init V1074 PM Service Syscall Trace Report

## Summary

V1074 added a bounded `pm-service` syscall trace to the PM observer.  The final
V196 live gate passed: `per_mgr` syscall tracing started, one selected startup
syscall was captured, the helper reached final summary markers, and postflight
was safe.

The captured syscall was only `faccessat(/dev/urandom) = 0`.  It did not expose
the natural exit-255 failure seen in V1072.  Under ptrace-lite, `per_mgr` stayed
observable until the bounded observer cleanup sent `SIGTERM`.  This makes
continuous ptrace too intrusive and too low-yield for the next step.  The next
best gate is a lower-overhead PM-service binary/uprobes path.

## Change

- Updated `stage3/linux_init/helpers/a90_android_execns_probe.c` to helper
  `a90_android_execns_probe v196`.
- Added selected syscall tracing for the PM observer `per_mgr` child.
- Added bounded stop/record accounting and compact observable-child summary.
- Suppressed PM observer ptrace-lite preexec context dumps to avoid NCM/tcpctl
  output truncation before final summary.
- Added deploy wrapper
  `scripts/revalidation/wifi_execns_helper_v196_deploy_preflight.py`.
- Added live runner
  `scripts/revalidation/native_wifi_pm_syscall_trace_live_v1074.py`.

## Evidence

| item | path / value |
| --- | --- |
| helper source | `stage3/linux_init/helpers/a90_android_execns_probe.c` |
| local helper | `tmp/wifi/v1074-execns-helper-v196-build/a90_android_execns_probe` |
| helper sha256 | `61b8ac54460f05e1d3a6fc6b68d8873c04537c171054921b4266be1ef6a0fb59` |
| deploy evidence | `tmp/wifi/v1074-execns-helper-v196-deploy/manifest.json` |
| live manifest | `tmp/wifi/v1074-pm-service-syscall-trace-live-v196/manifest.json` |
| live transcript | `tmp/wifi/v1074-pm-service-syscall-trace-live-v196/host/pm-service-trigger-observer.txt` |

## Final Live Result

```text
decision: v1074-pm-service-syscall-boundary-captured
pass: True
reason: per_mgr_exit=-1 syscall_stop_count=80 syscall_record_count=1
next: classify captured open/socket/bind/connect/ioctl/exit records for the next PM input repair
```

Important helper contract markers:

```text
pm_service_trigger_observer.result=observer-runtime-gap
pm_service_trigger_observer.reason=child-exited-before-observe-window
pm_service_trigger_observer.end=1
pm_service_trigger_observer.timed_out=1
pm_service_trigger_observer.all_postflight_safe=1
pm_service_trigger_observer.per_mgr_subsys_modem_seen=0
pm_service_trigger_observer.pm_proxy_helper_subsys_modem_seen=0
```

`per_mgr` syscall trace markers:

```text
pm_service_trigger_observer.child.per_mgr.syscall_trace_started=1
pm_service_trigger_observer.child.per_mgr.syscall_stop_count=80
pm_service_trigger_observer.child.per_mgr.syscall_record_count=1
pm_service_trigger_observer.child.per_mgr.syscall_error_count=0
pm_service_trigger_observer.child.per_mgr.signal=15
```

Captured syscall:

```text
pm_service_trigger_observer.syscall.per_mgr.record_000.name=faccessat
pm_service_trigger_observer.syscall.per_mgr.record_000.path.text=/dev/urandom
pm_service_trigger_observer.syscall.per_mgr.record_000.ret=0
pm_service_trigger_observer.syscall.per_mgr.record_000.error_name=none
```

## Iteration Notes

- V193 missed syscall tracing because the live runner did not inject
  `--capture-mode ptrace-lite`.
- V194 traced syscalls but left the child stopped at `ptrace_stop` when the
  bounded run ended.
- V195 reached the live path but NCM/tcpctl output truncated before the final
  helper summary.
- V196 compacted PM observer output and preserved final summary markers.

## Safety

The V196 live gate kept all forbidden actions disabled:

```text
mdm_helper_start_executed=False
cnss_daemon_start_executed=False
subsys_esoc0_open_attempted=False
wifi_hal_start_executed=False
wifi_bringup_executed=False
external_ping_executed=False
```

Post-live device health:

```text
selftest: pass=11 warn=1 fail=0
netservice: ncm0=present tcpctl=running
```

No cleanup reboot was required after the final V196 run.

## Interpretation

V1074 proves the PM observer can collect bounded `per_mgr` syscall records
without losing final evidence.  It does not prove the exit-255 root cause.
Continuous ptrace appears to perturb or slow the `pm-service` lifecycle enough
that the natural exit path is not reproduced before cleanup.

## Next Gate

Use the V1074 result to pivot from continuous ptrace to lower-overhead binary
classification and uprobe/BPF instrumentation:

1. Host-only `pm-service` binary analysis: `readelf`, `objdump`, dynamic libs,
   strings, entry point, and candidate function/call offsets.
2. Validate tracefs/uprobe event support on the current native boot.
3. Build a focused uprobe helper that arms probes before `pm-service` starts and
   observes entry/exit or selected libc/libbinder/libqmi call sites without
   continuous syscall-stop overhead.

The same safety boundary remains: no `mdm_helper`, CNSS, Wi-Fi HAL,
scan/connect/DHCP/route/external ping, `/dev/esoc*`, or boot image writes.
