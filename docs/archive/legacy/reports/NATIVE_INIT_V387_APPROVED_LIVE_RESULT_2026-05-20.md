# Native Init v387 Approved Live Result

## Summary

V387 helper v18 deployment succeeded, and the approved service-manager start-only live smoke fixed the V386 `hwservicemanager` cleanup blocker.

`system-hwservicemanager` now reaches exec, stays observable until the bounded timeout, receives a cleanup signal through the ptrace stop path, exits cleanly, and reports `service_manager_start.postflight_safe=1`. The V386 temporary zombie/residual PGID failure did not reproduce.

The run still stops before Wi-Fi HAL because `system-servicemanager` exits early with SIGABRT. The crash is captured and classified for the next runtime-repair step.

This is not Wi-Fi bring-up. Wi-Fi HAL, scan, connect, credentials, DHCP, routing, rfkill writes, firmware mutation, and driver bind/unbind were not executed.

## Approvals Used

Deploy:

```text
approve v387 deploy execns helper v18 only; no daemon start and no Wi-Fi bring-up
```

Live:

```text
approve v387 service-manager ptrace timeout cleanup only; no Wi-Fi HAL start and no Wi-Fi bring-up
```

## Evidence

- Serial deploy: `tmp/wifi/v387-approved-deploy-serial-20260520-055534/`
  - decision: `execns-helper-v18-deploy-pass`
  - method: `serial appendfile + uudecode`
  - device mutation: helper install only
  - daemon start: `False`
  - Wi-Fi bring-up: `False`
- Approved live run: `tmp/wifi/v387-approved-live-20260520-060136/`
  - decision: `service-manager-start-only-live-runtime-gap`
  - pass: `True`
  - daemon start executed: `True`
  - Wi-Fi bring-up: `False`
- Runtime-gap classifier: `tmp/wifi/v387-approved-live-20260520-060136/classify/`
  - decision: `service-manager-runtime-gap-servicemanager-sigabrt-captured`
  - pass: `True`
- Postflight captures:
  - `tmp/wifi/v387-approved-live-20260520-060136/post-status.json`
  - `tmp/wifi/v387-approved-live-20260520-060136/post-ps.txt`
  - `tmp/wifi/v387-approved-live-20260520-060136/post-proc-net-dev.txt`

## Deploy Result

Remote helper was updated to v18:

```text
1131f0e3dd61bafc5023c25d7fb019303902cdf6cea76dd2e09b44b13a42378e  /cache/bin/a90_android_execns_probe
```

The deploy wrapper reports:

```text
decision: execns-helper-v18-deploy-pass
pass: True
device_mutations: True
daemon_start_executed: False
wifi_bringup_executed: False
```

## Live Result

### `system-servicemanager`

`servicemanager` still exits before the observe window. V387 captures the crash and proves cleanup safe.

Key fields:

```text
capture.crash.siginfo.signo=6
capture.crash.siginfo.code=-1
capture.crash.siginfo.addr=0x3e8000006fb
service_manager_start.capture_exec=1
service_manager_start.capture_crash=1
service_manager_start.signal=6
service_manager_start.reaped=1
service_manager_start.residual_kill_sent=0
service_manager_start.residual_cleared=1
service_manager_start.postflight_safe=1
service_manager_start.result=start-only-runtime-gap
service_manager_start.reason=child-exited-before-observe-window
```

Captured stderr:

```text
libc: Fatal signal 6 (SIGABRT), code -1 (SI_QUEUE) in tid 1787 (servicemanager), pid 1787 (servicemanager)
```

Interpretation:

- The service-manager runtime gap remains.
- Crash evidence is now captured and classifier-readable.
- Cleanup is safe for this target.

### `system-hwservicemanager`

`hwservicemanager` is the V387 improvement. It no longer reports residual PGID/zombie failure.

Key cleanup fields:

```text
capture.exec_stop=1
service_manager_start.timed_out=1
service_manager_start.observable=1
service_manager_start.term_sent=1
service_manager_start.kill_sent=0
service_manager_start.signal=15
service_manager_start.reaped=1
service_manager_start.cleanup.term.stop.signal=15
service_manager_start.cleanup.term.stop.event=0
service_manager_start.cleanup.term.stop.deliver_signal=15
service_manager_start.cleanup.term.signal=15
service_manager_start.cleanup_stop_continued=1
service_manager_start.cleanup_stop_last_signal=15
service_manager_start.cleanup_continue_errors=0
service_manager_start.residual_kill_sent=0
service_manager_start.residual_cleared=1
service_manager_start.residual_before_count=-1
service_manager_start.residual_after_count=-1
service_manager_start.postflight_safe=1
service_manager_start.result=start-only-pass
service_manager_start.reason=observed-until-timeout-clean-stop
```

Interpretation:

- V387 fixed the V386 cleanup semantics bug for stopped ptrace tracees.
- The helper continued the stopped tracee with `SIGTERM` and waited for terminal signal state before claiming `reaped=1`.
- No residual PGID scan was needed because the process group was already clear.

## Classifier Result

Runtime-gap classifier result:

```text
decision: service-manager-runtime-gap-servicemanager-sigabrt-captured
pass: True
reason: servicemanager SIGABRT was captured by ptrace-lite crash evidence
next: inspect captured siginfo/register/maps/status evidence before runtime repair
remaining: servicemanager-sigabrt-evidence
```

This means service-manager lifecycle cleanup is now good enough to move the next blocker from process cleanup to `servicemanager` runtime dependencies or abort cause.

## Postflight Device State

Manual read-only checks after the run:

- `status`: PASS, `selftest: pass=11 warn=1 fail=0`.
- `ps`: no `servicemanager`, `hwservicemanager`, `vndservicemanager`, `a90_android_execns_probe`, or temporary `a90-v231` process remains.
- `/proc/net/dev`: no Wi-Fi link.
- `netservice`: disabled, `tcpctl=stopped`, `rshell=stopped`.

The live wrapper postflight also reports:

```text
postflight.clean=True
manager_processes=0
wifi_links=0
```

## Conclusion

V387 resolved the V386 cleanup blocker. `hwservicemanager` bounded start-only is now `start-only-pass` with safe cleanup.

Wi-Fi HAL/start/scan/connect remains blocked by `servicemanager` SIGABRT. The next version should not start Wi-Fi HAL yet; it should analyze the captured crash context and add a targeted runtime repair or narrower proof for `servicemanager`.

## Next Step

V388 should perform `servicemanager` SIGABRT evidence triage:

- parse compact crash `siginfo`, status, maps, mountinfo, auxv, and register-size evidence.
- compare the private namespace runtime with what Android `servicemanager` expects.
- identify whether the abort is caused by property runtime, Binder device state, SELinux/null handling, linker namespace, `/dev` layout, `/proc` exposure, or missing Android runtime files.
- keep the next live scope bounded to service-manager runtime repair only; no Wi-Fi HAL/start/scan/connect until `servicemanager` no longer exits early or the abort is classified as acceptable for the Wi-Fi path.
