# Native Init V1611 per_mgr Early-exit Trace Classifier

## Summary

- Cycle: `V1611`
- Type: host-only classifier over V1610 live evidence
- Decision: `v1611-ptrace-lite-intrusive-stop-limit-no-exit-cause`
- Result: `PASS`
- Reason: V1610 collected rollback-safe evidence but ptrace-lite changed the target behavior: pm-service stayed stopped for the full sampler window, recorded only faccessat('/dev/urandom'), hit the syscall stop limit, and never reached a PM contract fd
- Evidence: `tmp/wifi/v1611-per-mgr-early-exit-trace-classifier`

## Inputs

| input | path |
| --- | --- |
| v1610_manifest | tmp/wifi/v1610-per-mgr-early-exit-trace-handoff/manifest.json |
| v1610_helper_result | tmp/wifi/v1610-per-mgr-early-exit-trace-handoff/test-v1393-helper-result.stdout.txt |
| v1610_dmesg | tmp/wifi/v1610-per-mgr-early-exit-trace-handoff/test-v1393-dmesg.stdout.txt |
| v1610_report | docs/reports/NATIVE_INIT_V1610_PER_MGR_EARLY_EXIT_TRACE_HANDOFF_2026-06-02.md |

## Derived Checks

| check | value |
| --- | --- |
| handoff_and_rollback_ok | True |
| early_exit_trace_enabled | True |
| ptrace_stopped_process | True |
| only_one_selected_syscall_record | True |
| trace_hit_stop_limit | True |
| no_pm_contract_fd_seen | True |
| downstream_wifi_absent | True |

## Trace Summary

| field | value |
| --- | --- |
| handoff_pass | True |
| rollback_ok | True |
| progress_decision | modem-trigger-no-downstream |
| startup_sample_count | 51 |
| startup_last_alive_ms | 1000 |
| startup_first_gone_ms | -1 |
| startup_first_child_done_ms | -1 |
| startup_exit_code | -1 |
| child_exit_code | 0 |
| child_traced | 1 |
| trace_exec_captured | 1 |
| trace_exit_captured | 1 |
| syscall_record_count | 1 |
| syscall_stop_count | 128 |
| syscall_trace_stop_limited | 1 |
| trace_disable_reason | stop-limit |
| first_record | faccessat /dev/urandom ret=0 |
| max_subsys_modem_fd | 0 |
| max_subsys_esoc0_fd | 0 |
| pm_full_contract_seen | 0 |
| subsys_esoc0_open_attempted | 0 |

## Interpretation

V1610 did not reveal the clean V1607 `pm-service` exit cause.  It changed the process behavior.  With ptrace-lite enabled, the startup sampler sees `pm-service` in `ptrace_stop` for the entire 1s window, `first_gone_ms=-1`, and `first_child_done_ms=-1`.  Only one selected syscall record is produced: `faccessat('/dev/urandom')`, after which the tracer hits the syscall stop limit.

The postflight child exit still reports `exit_code=0`, but this is no longer equivalent to the natural V1607 early exit.  Treat V1608/V1610 ptrace-lite as intrusive for this target and do not base the next branch on lower eSoC/RC1 absence from this run.

## Next Gate

- Recommended cycle: `V1612`
- Type: source/build-only non-stopping pm-service startup classifier
- Focus: replace ptrace-lite syscall tracing with non-stopping evidence: stderr/stdout tails, service-manager/property/socket namespace snapshots, vendor init/env comparison, and host-only pm-service dependency/string analysis

### Avoid

- ptrace syscall tracing of pm-service
- ptrace of mdm_helper
- direct scoped /dev/subsys_esoc0 open
- Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, external ping
- PMIC/GPIO/GDSC direct writes, blind eSoC notify/BOOT_DONE

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, daemon start, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, blind eSoC notify/`BOOT_DONE` spoof, pci-msm debugfs write, global PCI rescan, or platform bind/unbind.
