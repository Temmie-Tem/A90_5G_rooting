# Native Init V1074 PM Service Syscall Trace Plan

## Goal

Add a bounded `pm-service` syscall trace to the PM observer so the native init
path can classify why `per_mgr` fails before it opens `/dev/subsys_modem`.

## Background

V1073 closed host-only explanations for the `pm-service` exit-255 blocker:
Android init does not create a missing `vendor.per_mgr` socket, and the V1072
snapshot did not simply miss a persistent `/dev/subsys_modem` fd.  The remaining
question is which runtime input or syscall failure prevents `pm-service` from
advancing the peripheral-manager contract.

## Gate

- Build static `a90_android_execns_probe` with PM-observer syscall tracing.
- Deploy only `/cache/bin/a90_android_execns_probe` over the authenticated NCM
  `tcpctl` path.
- Run `wifi-companion-pm-service-trigger-observer` with `--capture-mode
  ptrace-lite`.
- Trace only the PM observer `per_mgr` child.
- Capture selected startup syscalls: path probes, socket setup, `ioctl`, and
  process exit.
- Keep output compact enough to preserve final `pm_service_trigger_observer`
  summary markers.

## Forbidden

- No `mdm_helper` start.
- No CNSS daemon start.
- No Wi-Fi HAL start.
- No scan/connect/DHCP/route/external ping.
- No `/dev/esoc*` open or eSoC ioctl.
- No `wlan.ko` load.
- No boot image or partition write.

## Success Criteria

- Helper reaches `pm_service_trigger_observer.end=1`.
- `per_mgr` has `syscall_trace_started=1`.
- At least one selected syscall record is captured.
- Postflight is safe: no lingering helper/PM actors and no Wi-Fi link appears.
- Device health remains `selftest fail=0` after the live gate.

## Expected Decision Use

If selected syscall records reveal an errno on `/dev/subsys_*`, binder, QRTR, or
QMI setup, route to a targeted runtime repair.  If ptrace captures no decisive
failure or perturbs the lifecycle, route to a lower-overhead uprobe/BPF gate.
