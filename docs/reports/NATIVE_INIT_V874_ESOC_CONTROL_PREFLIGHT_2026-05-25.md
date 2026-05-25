# V874 eSoC Control Preflight Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| plan | `tmp/wifi/v874-esoc-control-preflight-plan/manifest.json` | `v874-esoc-control-preflight-plan-ready` |
| live | `tmp/wifi/v874-esoc-control-preflight-live/manifest.json` | `v874-esoc-readonly-ioctl-probe-pass` |

V874 proved the bounded read-only `/dev/esoc-0` control preflight with helper
`v136`. This was not an mdm3 bring-up attempt.

## Live Findings

| Item | Value |
| --- | --- |
| helper mode | `wifi-companion-esoc-control-preflight` |
| `/dev/esoc-0` open | fd `3` |
| `GET_STATUS` | rc `0`, errno `0`, value `0` |
| `GET_ERR_FATAL` | rc `0`, errno `0`, value `0` |
| `GET_LINK_ID` | rc `-1`, errno `22`, value `0` |
| helper result | `read-only-ioctl-probe-complete` |

Private node proof:

- `/dev/esoc-0`: present in helper namespace
- `/dev/subsys_esoc0`: present in helper namespace
- `/dev/subsys_modem`: present in helper namespace

## Cleanup and Health

| Check | Result |
| --- | --- |
| created nodes removed | pass |
| postflight bootstatus | pass |
| postflight selftest | `pass=11 warn=1 fail=0` |
| actor hits | `0` |
| Wi-Fi link hits | `0` |

## Guardrails

- `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, `WAIT_FOR_REQ`, `NOTIFY`, and
  `PWR_ON` were not attempted.
- `mdm_helper`, `ks`, `pm_proxy_helper`, CNSS, service-manager trio, Wi-Fi HAL,
  scan/connect, credentials, DHCP/routes, and external ping were not executed.
- No module load/unload, boot image write, partition write, or firmware mutation
  occurred.

## Interpretation

The `/dev/esoc-0` control path is reachable enough for read-only status ioctls.
The next blocker is no longer node visibility or helper classification; it is
safe sequencing for a future CMD/REQ engine registration gate.

## Next

V875 should be host-only first: define the exact state-machine contract for
`REG_CMD_ENG` and `REG_REQ_ENG`, including fd ownership, timeout, cleanup,
rollback, and explicit proof that `PWR_ON` remains blocked until a later gate.
