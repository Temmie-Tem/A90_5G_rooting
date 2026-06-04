# Native Init V1996 PD-Mapper Syscall Trace Handoff

## Summary

- Cycle: `V1996`
- Decision: `v1996-native-pd-mapper-no-modem-query-before-wlanmdsp-rollback-pass`
- Label: `native-pd-mapper-no-modem-query-before-wlanmdsp`
- Pass: `True`
- Reason: pd-mapper stayed traced without inbound QRTR payload and the modem still never requested wlanmdsp.mbn; the stall is before PD mapping/query reaches AP pd-mapper
- Evidence: `tmp/wifi/v1996-pd-mapper-syscall-trace-handoff`
- Inner handoff: `tmp/wifi/v1996-pd-mapper-syscall-trace-handoff/v1995-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | native-pd-mapper-no-modem-query-before-wlanmdsp | pd-mapper stayed traced without inbound QRTR payload and the modem still never requested wlanmdsp.mbn; the stall is before PD mapping/query reaches AP pd-mapper |
| helper_completion | True | version=a90_android_execns_probe v367 probe_rc=0 child_exit=0 timed_out=1 |
| rfs_bridge | True | exact_exists=1 nonzero=1 open_rc=0 source_nonzero=1 sda29_write=0 |
| light_observer | True | servloc=0 servnotif=0 qrtr_send=0 result=blocked |
| producer_alive | True | holder=True window=True |
| pd_mapper_trace | True | compiled=1 late=1 attach_rc=0 detach_rc=0 records=0 late_records=0 late_stops=1 late_ms=6029 truncated=0 |
| pd_mapper_payloads | False | inbound_recv=0 outbound_send=0 total_payload=0 qipcrtr=0 names={} |
| combined_prereq | True | service74=True service180=True pm_open=True holder=True |
| wlanmdsp_request | False | field=False tftp_lines=0 failures=0 |
| wlanmdsp_serve_load | False | available_nonzero=True pil_load=0 wlan_pd_up=0 wlfw69=0 wlan0=0 |
| android_v1982 | 1 | wlan_pd=9.567253 BDF=9.722886 wlan0=14.866239 lines=10 |

## First PD-Mapper Trace Records

- `none`

## Producer Child Snapshot

- `after_holder_start/pd_mapper` alive `1` state `S` fd_socket_count `2` task_count `2`
- `after_holder_start/pd_mapper` syscall `101 0x7fe3dcc6e8 0x7fe3dcc6e8 0x0 0x8 0x7f005fbcc0 0x7f80f6408c 0x7fe3dcc6e0 0x7f80f4fb9c`
- `after_holder_start/pd_mapper` syscall `72 0x5 0x7f005fbae0 0x0 0x0 0x0 0x0 0x7f005fba40 0x7f80f5049c`
- `after_holder_start/tftp_server` alive `1` state `S` fd_socket_count `11` task_count `1`
- `after_holder_start/tftp_server` syscall `73 0x557a1fe990 0xa 0x0 0x0 0x0 0x14 0x7fff0ffec0 0x7f9af9d4bc`
- `after_post_listener_window/pd_mapper` alive `1` state `S` fd_socket_count `2` task_count `2`
- `after_post_listener_window/pd_mapper` syscall `128 0x7fe3dcc6e8 0x7fe3dcc6e8 0x0 0x8 0x7f005fbcc0 0x7f80f6408c 0x7fe3dcc6e0 0x7f80f4fb9c`
- `after_post_listener_window/pd_mapper` syscall `72 0x5 0x7f005fbae0 0x0 0x0 0x0 0x0 0x7f005fba40 0x7f80f5049c`
- `after_post_listener_window/tftp_server` alive `1` state `S` fd_socket_count `11` task_count `1`
- `after_post_listener_window/tftp_server` syscall `running`

## First Native Wlanmdsp Lines

- `none`

## Branch

- `native-pd-mapper-no-modem-query-before-wlanmdsp`: modem never reaches AP `pd-mapper` before the missing WLAN image request.
- `native-pd-mapper-query-seen-no-wlanmdsp-request`: PD mapping traffic exists, but the modem still stalls before tftp `wlanmdsp.mbn`.
- `native-pd-mapper-query-and-wlanmdsp-progress`: request/publication edge appeared; stop before HAL/scan/connect and continue downstream.

## Android Comparator

- Report: `docs/reports/NATIVE_INIT_V1982_V1753_MINIMAL_ANDROID_GOOD_BASELINE_RERUN_2026-06-04.md`
- Timeline: WLAN-PD UP `9.567253`, BDF `9.722886`, wlan0 `14.866239`.
- Request evidence: requested_wlanmdsp `1`, wlanmdsp line count `10`.

## Steps

- `pre-version` rc `0` ok `True` evidence `host/pre-version.txt`
- `pre-selftest` rc `0` ok `True` evidence `host/pre-selftest.txt`
- `pre-flags` rc `0` ok `True` evidence `host/pre-flags.txt`
- `arm-clean-dsp-flag` rc `0` ok `True` evidence `host/arm-clean-dsp-flag.txt`
- `cleanup-leftover-clean-dsp-flag` rc `0` ok `True` evidence `host/cleanup-leftover-clean-dsp-flag.txt`
- `post-selftest` rc `0` ok `True` evidence `host/post-selftest.txt`
- `post-status` rc `0` ok `True` evidence `host/post-status.txt`
- `post-flags` rc `0` ok `True` evidence `host/post-flags.txt`

## Safety

- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping was used.
- No rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR readback, or QMI payload send was run.
- The only ptrace was the bounded single-child syscall payload trace of stock `pd-mapper`; no AP-side multi-strace was run.
- No direct `/dev/subsys_esoc0` open/control, forced RC1/case, PMIC/GPIO/GDSC/regulator, PCI rescan, platform bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V1995 test-boot flash-handoff, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
