# V1111 Tagged PM Connect Path Capture Report

Date: 2026-05-27

## Result

- Decision: `v1111-pm-connect-syscall-path-captured`
- Pass: `true`
- Evidence: `tmp/wifi/v1111-pm-connect-path-capture-live/manifest.json`
- Helper: `a90_android_execns_probe v209`

## Key Evidence

- V1108 ordering remained active:
  - `per_proxy_start_executed=0`
  - `child.per_proxy.start_skipped=1`
  - `start_cnss_before_per_proxy=1`
- CNSS phase remained bounded:
  - `cnss_daemon_start_executed=1`
  - Wi-Fi HAL, scan/connect, DHCP, route, credential use, and external ping were not executed.
- Blocked owner thread:
  - comm: `Binder:30533_2`
  - tid: `30538`
  - wchan: `__subsystem_get`
  - syscall: `openat`
  - original pointer: `0xb400007f7fc06198`
  - untagged pointer: `0x0000007f7fc06198`
  - captured path: `/dev/subsys_modem`
- `mdm3` still did not advance to Wi-Fi-ready state in this gate.

## Interpretation

The post-CNSS PM connect blocker is now concrete: the `pm-service` Binder owner thread opens `/dev/subsys_modem` and blocks in the kernel `__subsystem_get` path. The previous unknown `_request_firmware`/subsystem target is not a vendor firmware file path; it is the modem subsystem device node itself.

This narrows the next blocker to why `/dev/subsys_modem` does not return in native init after CNSS PM connect. The next gate should compare Android-good and native-bad modem subsystem preconditions before any Wi-Fi HAL or scan/connect attempt.

## Safety

- `wifi_hal_start_executed=0`
- `scan_connect_linkup=0`
- `external_ping=0`
- `subsys_esoc0_open_attempted=0`
- `all_postflight_safe=1`
- Postflight showed no forbidden Wi-Fi link or actor hits.
- Final `selftest` remained `pass=11 warn=1 fail=0`.

## Next Step

V1112 should classify `/dev/subsys_modem` open preconditions:

- compare native `/sys/bus/msm_subsys/devices/*` states and names;
- capture dmesg delta around `subsys_modem` open without opening `subsys_esoc0`;
- compare Android-good PM service behavior for `/dev/subsys_modem`;
- determine whether mss firmware mount, modem state, or PM service ordering is missing before expanding toward Wi-Fi HAL.

