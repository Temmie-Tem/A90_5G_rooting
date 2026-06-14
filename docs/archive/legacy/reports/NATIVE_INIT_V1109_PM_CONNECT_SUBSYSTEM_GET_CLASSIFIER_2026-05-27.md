# V1109 PM Connect Subsystem-Get Classifier Report

Date: 2026-05-27

## Result

- Decision: `v1109-cnss-pm-connect-triggers-subsystem-get-blocker`
- Pass: `true`
- Evidence: `tmp/wifi/v1109-pm-connect-subsystem-get-classifier/manifest.json`
- Source evidence: `tmp/wifi/v1108-pm-ordering-no-pre-cnss-per-proxy-live/manifest.json`

## Key Evidence

- V1108 ordering contract remained valid:
  - `per_proxy_start_executed=0`
  - `child.per_proxy.start_skipped=1`
  - `start_cnss_before_per_proxy=1`
- CNSS PM calls succeeded:
  - `pm_client_register_ret=['0x0']`
  - `pm_client_connect_ret=['0x0']`
- Post-connect pending waiter:
  - comm: `pm-service`
  - mutex: `0xb400007fa0026198`
  - waiter wchan set: `do_sigtimedwait`, `futex_wait_queue_me`
- Reconstructed owner:
  - comm: `Binder:30322_2`
  - tid: `30327`
  - same mutex: `0xb400007fa0026198`
  - owner return offset: `0x87c8`
  - owner wchan set: `__subsystem_get`, `_request_firmware`, `binder_ioctl_write_read`
- Lower state:
  - `mdm3_state=OFFLINING`

## Interpretation

V1108 closed the pre-CNSS `per_proxy` ordering blocker, but V1109 shows the successful CNSS PM connect path itself creates the next lower blocker. The PM server Binder thread that handles the CNSS request acquires the modem record mutex and then blocks in `__subsystem_get` / `_request_firmware`. The `pm-service` main thread later waits on that same mutex.

This means the current blocker is no longer PM provider registration or CNSS PM connect. The next missing evidence is the exact firmware path or subsystem target requested by the owner thread while it is blocked.

## Next Step

V1110 should be a bounded live capture around the same V1108 order, before any Wi-Fi HAL or scan/connect:

- enable syscall/openat or ptrace-lite capture for the `pm-service` owner thread;
- capture the exact path pointer or firmware/subsystem name involved in `_request_firmware`;
- capture dmesg delta for `request_firmware`, `subsys`, `esoc`, `mdm3`, `modem`, and `firmware_class`;
- keep `per_proxy` skipped before CNSS;
- keep Wi-Fi HAL, scan/connect, DHCP, credentials, routes, and external ping disabled.

