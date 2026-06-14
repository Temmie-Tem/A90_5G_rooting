# V876 eSoC Engine Register Helper v137 Build Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper build | `tmp/wifi/v876-execns-helper-v137-build/a90_android_execns_probe` | PASS |

V876 added source/build-only helper support for the next eSoC state-machine
stage. It did not deploy the helper and did not contact the device.

## Build Details

| Item | Value |
| --- | --- |
| helper marker | `a90_android_execns_probe v137` |
| sha256 | `e47eb52b0b2b2fb601fdbc4ecebdf72e2fda9519eac37e776d62c11d2d469aa3` |
| artifact | `tmp/wifi/v876-execns-helper-v137-build/a90_android_execns_probe` |
| link mode | static ARM64, no dynamic section |
| new mode | `wifi-companion-esoc-engine-register-preflight` |
| new allow flag | `--allow-esoc-engine-register-preflight` |

## Source Change

- Helper `v137` adds `wifi-companion-esoc-engine-register-preflight`.
- The mode uses private eSoC node materialization but does not classify as a
  service-manager or Wi-Fi companion actor mode.
- The mode rejects actor/HAL/scan/connect/proof allow flags that are unrelated
  to CMD/REQ registration.
- The guarded body is prepared for a later live gate to register CMD and REQ
  engines on separate `/dev/esoc-0` fds.

## Fail-closed Markers

The artifact strings include markers proving the blocked surfaces remain
explicitly represented:

- `esoc_engine_register_preflight.cmd_exe_attempted=0`
- `esoc_engine_register_preflight.pwr_on_attempted=0`
- `esoc_engine_register_preflight.wait_for_req_attempted=0`
- `esoc_engine_register_preflight.notify_attempted=0`
- `esoc_engine_register_preflight.subsys_esoc0_open_attempted=0`
- `esoc_engine_register_preflight.credentials=0`
- `esoc_engine_register_preflight.external_ping=0`

## Guardrails

- No helper deploy in V876.
- No live eSoC ioctl execution in V876.
- No `CMD_EXE`, `PWR_ON`, `WAIT_FOR_REQ`, `NOTIFY`, `/dev/subsys_esoc0` open,
  actor start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external
  ping.

## Next

V877 should deploy helper `v137` only. V878 should run the bounded live CMD/REQ
registration preflight after remote checksum/version/mode parity is proven.
