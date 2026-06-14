# Native Init V1607 per_mgr Startup Trace Classifier

## Summary

- Cycle: `V1607`
- Type: host-only classifier over V1606 live evidence
- Decision: `v1607-per-mgr-exits-before-any-contract-fd`
- Result: `PASS`
- Reason: V1606 proves pm-service runs only briefly, exits 0 around 21ms, and never opens /dev/subsys_modem, /dev/subsys_esoc0, binder nodes, sockets, or /dev/socket; the next gate should classify the pm-service pre-main/startup exit cause rather than retry lower eSoC/RC1
- Evidence: `tmp/wifi/v1607-per-mgr-startup-trace-classifier`

## Inputs

| input | path |
| --- | --- |
| v1606_manifest | tmp/wifi/v1606-per-mgr-startup-trace-handoff/manifest.json |
| v1606_helper_result | tmp/wifi/v1606-per-mgr-startup-trace-handoff/test-v1393-helper-result.stdout.txt |
| v1606_dmesg | tmp/wifi/v1606-per-mgr-startup-trace-handoff/test-v1393-dmesg.stdout.txt |
| v1606_summary | tmp/wifi/v1606-per-mgr-startup-trace-handoff/summary.md |
| v1606_report | docs/reports/NATIVE_INIT_V1606_PER_MGR_STARTUP_TRACE_HANDOFF_2026-06-02.md |
| helper_source | stage3/linux_init/helpers/a90_android_execns_probe.c |

## Derived Checks

| check | value |
| --- | --- |
| v1606_handoff_and_rollback_ok | True |
| startup_trace_enabled_and_sampled | True |
| per_mgr_alive_only_briefly | True |
| per_mgr_exited_cleanly | True |
| per_mgr_opened_no_contract_fds | True |
| pph_gate_still_closed | True |
| downstream_remains_absent | True |
| source_supports_trace | True |

## Startup Trace Summary

| field | value |
| --- | --- |
| mode | guarded-pm-proxy-contract-pm-first-late-per-proxy-pph-gate-per-mgr-startup-trace-lower-marker |
| pph_gate_seen | 1 |
| pph_gate_first_seen_ms | 301 |
| pm_proxy_helper_subsys_modem_fd_count | 1 |
| sample_count | 51 |
| alive_seen | 1 |
| first_alive_ms | 0 |
| last_alive_ms | 20 |
| first_child_done_ms | 21 |
| first_gone_ms | 41 |
| exit_code | 0 |
| signal | 0 |
| max_subsys_modem_fd | 0 |
| max_subsys_esoc0_fd | 0 |
| max_vndbinder_fd | 0 |
| max_hwbinder_fd | 0 |
| max_binder_fd | 0 |
| max_socket_fd | 0 |
| max_dev_socket_fd | 0 |

## First Samples

| sample | elapsed | alive | done | state | cmdline | cwd | wchan | fds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 0 | 1 | 0 | R | /vendor/bin/pm-service | /tmp/a90-v231-545/root | wait_on_page_bit_killable | modem=0 esoc0=0 vndbinder=0 |
| 01 | 20 | 1 | 0 | Z |  |  | 0 | modem=0 esoc0=0 vndbinder=0 |
| 02 | 41 | 0 | 1 | ? |  |  |  | modem=-1 esoc0=-1 vndbinder=-1 |

## Interpretation

`pm-service` is not failing after it talks to the PM provider contract.  It exits before any observed contract fd is opened: no `/dev/subsys_modem`, `/dev/subsys_esoc0`, binder node, socket, or `/dev/socket` fd is seen.  The first sample sees `/vendor/bin/pm-service` with cwd under the private root and `wait_on_page_bit_killable`; the next sample is already a zombie and the child is reaped by ~21ms.

Therefore the active blocker is a pre-contract startup/branch exit inside `pm-service`, not the lower SDX50M/eSoC/RC1 path.  Lower RC1/MHI/WLFW work should remain parked until this process stays alive long enough to register or open the expected PM surfaces.

## Next Gate

- Recommended cycle: `V1608`
- Type: source/build-only pm-service early-exit cause tracer
- Focus: instrument pm-service startup before it exits, preferably with bounded ptrace/exit or uprobe/openat/exit tracing around only /vendor/bin/pm-service

### Success Markers

- captures the syscall or library branch that leads to exit(0)
- records whether pm-service checks properties, init/service state, vndservicemanager, binder nodes, or peripheral state before exit
- does not ptrace mdm_helper or any long-running eSoC path
- preserves the PPH gate and startup trace guardrails
- still avoids Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, PMIC/GPIO/GDSC writes, eSoC notify/BOOT_DONE, global PCI rescan, and platform bind/unbind

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, daemon start, Wi-Fi HAL start, scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, blind eSoC notify/`BOOT_DONE` spoof, pci-msm debugfs write, global PCI rescan, or platform bind/unbind.
