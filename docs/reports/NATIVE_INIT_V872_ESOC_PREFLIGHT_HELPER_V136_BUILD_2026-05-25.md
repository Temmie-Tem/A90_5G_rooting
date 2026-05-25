# V872 eSoC Preflight Helper v136 Build Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper build | `tmp/wifi/v872-execns-helper-v136-build/a90_android_execns_probe` | PASS |

V872 repairs helper classification for `wifi-companion-esoc-control-preflight`.
The mode still materializes the private eSoC nodes it needs, but it no longer
inherits service-manager/SELinuxfs startup requirements.

## Build Details

| Item | Value |
| --- | --- |
| helper marker | `a90_android_execns_probe v136` |
| sha256 | `76dce733b8444073fc615a44df240aa7f8256dfb7f6c123c3f5e388907356980` |
| artifact | `tmp/wifi/v872-execns-helper-v136-build/a90_android_execns_probe` |
| link mode | static ARM64, no dynamic section |

## Code Change

- `stage3/linux_init/helpers/a90_android_execns_probe.c` now separates
  PeripheralManager service-node materialization from private eSoC node
  materialization.
- `wifi-companion-esoc-control-preflight` remains allowed to create private
  `/dev/esoc-0`, `/dev/subsys_esoc0`, and `/dev/subsys_modem` nodes.
- The mode is no longer classified as requiring service-manager startup or
  SELinuxfs runtime setup.

## Guardrails

- No helper deploy in V872.
- No live eSoC ioctl in V872.
- No `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, `WAIT_FOR_REQ`, `NOTIFY`, or
  `PWR_ON`.
- No Android actor start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or
  external ping.

## Next

Run V873 helper `v136` deploy-only proof, then V874 bounded read-only eSoC
control preflight.
