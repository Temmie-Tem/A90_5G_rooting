# Native Init V778 BPF Attach Feasibility Report

## Result

- decision: `v778-custom-bpf-loader-build-needed`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_bpf_attach_feasibility_v778.py`
- evidence: `tmp/wifi/v778-bpf-attach-feasibility/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_bpf_attach_feasibility_v778.py
python3 scripts/revalidation/native_wifi_bpf_attach_feasibility_v778.py plan
python3 scripts/revalidation/native_wifi_bpf_attach_feasibility_v778.py run
```

## Evidence Summary

| Signal | Value |
| --- | --- |
| selected target | `msm_pil_event:pil_notif` |
| target fields | `event_name`, `code`, `fw_name` |
| device `bpftool`/`bpftrace` | not found |
| `/proc/sys/kernel/perf_event_paranoid` | `3` |
| `/proc/sys/kernel/unprivileged_bpf_disabled` | `0` |
| `/sys/kernel/tracing` | exists |
| `/sys/kernel/debug/tracing` | absent |
| host `aarch64-linux-gnu-gcc` | present |
| host `aarch64-linux-gnu-strip` | present |
| host `aarch64-linux-gnu-readelf` | present |
| host BPF/perf headers | present |

## Interpretation

V778 confirms that the target tracepoint is suitable, but the device has no
existing BPF loader. Therefore V778 must not proceed directly to attach. The
next gate is a build/review/deploy gate for a minimal static aarch64 helper.

The helper should be intentionally smaller than `bpftool`:

1. open one tracepoint id for `msm_pil_event:pil_notif`;
2. load one minimal BPF program or otherwise fail with explicit errno;
3. attach through `perf_event_open`/`ioctl`;
4. wait for a short idle window;
5. detach and close all fds;
6. print only bounded counters and errno/status.

V779 should be build-only first. V780 can deploy/preflight the helper. Only a
later gate should run attach/read/detach, and it should still avoid modem/Wi-Fi
triggers.

## Safety

V778 did not attach BPF, write ftrace controls, trigger Wi-Fi, start
service-manager/Wi-Fi HAL, scan, connect, use credentials, change DHCP/routes,
ping externally, reboot, flash, or write partitions.

## Next

V779 should create and statically build a minimal reviewed helper for
`msm_pil_event:pil_notif` attach feasibility. No live attach should be executed
until that helper is built, audited, and deployed in a separate gate.
