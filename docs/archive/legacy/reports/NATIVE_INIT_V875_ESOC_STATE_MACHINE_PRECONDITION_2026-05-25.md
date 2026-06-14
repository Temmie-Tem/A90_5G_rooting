# V875 eSoC State-machine Precondition Classifier Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only classifier | `tmp/wifi/v875-esoc-state-machine-precondition-classifier/manifest.json` | `v875-esoc-state-machine-precondition-pass` |

V875 did not contact the device and did not execute any eSoC ioctl. It selected
helper-only CMD/REQ registration support as the next implementation step.

## Evidence Used

| Evidence | Decision | Pass |
| --- | --- | --- |
| V849 blind `/dev/subsys_esoc0` open sampler | `v849-subsys-esoc0-block-provider-powerup-or-opaque` | `true` |
| V874 read-only `/dev/esoc-0` control preflight | `v874-esoc-readonly-ioctl-probe-pass` | `true` |

## Source Contract

| Condition | Result |
| --- | --- |
| `/dev/subsys_esoc0` open calls `subsystem_get_with_fwname` | `true` |
| `subsystem_get` enters `subsys_start` only at refcount zero | `true` |
| `subsys_start` calls provider `desc->powerup` | `true` |
| `subsys_start` waits for `err_ready` | `true` |
| `err_ready` timeout is 10000 ms | `true` |
| `state` sysfs attribute is read-only in SSR source | `true` |
| eSoC client hook API exists | `true` |
| proprietary provider source is absent from local OSRC | `false` |

## Operation Classification

| Operation | Classification | V875 Result |
| --- | --- | --- |
| `ESOC_REG_CMD_ENG` | mutating registration, no direct `PWR_ON` argument | next source/build helper support |
| `ESOC_REG_REQ_ENG` | mutating registration, can unblock provider wait but no direct `PWR_ON` | next source/build helper support |
| `ESOC_CMD_EXE(ESOC_PWR_ON)` | explicit power command | blocked |
| `ESOC_WAIT_FOR_REQ` | blocking firmware request loop | blocked |
| `ESOC_NOTIFY` | mutating firmware/boot response | blocked |
| `/dev/subsys_esoc0` open | subsystem refcount/powerup path | blocked until sequencing is defined |

## Selected Sequence

1. V876: source/build-only helper `v137` with fail-closed CMD/REQ registration
   mode.
2. V877: deploy-only helper `v137` checksum/version/mode proof.
3. V878: bounded live CMD/REQ registration preflight only.
4. Later gate: firmware request loop and only then explicit `PWR_ON`
   consideration.

## Guardrails

- `live_device_contact=false`.
- `mutating_esoc_ioctl_executed=false`.
- No `CMD_EXE`, `PWR_ON`, `WAIT_FOR_REQ`, `NOTIFY`, actor start, Wi-Fi HAL,
  scan/connect, credentials, DHCP/routes, or external ping.

## Next

Implement V876 helper `v137` source/build-only support for a fail-closed
`wifi-companion-esoc-engine-register-preflight` mode. It should expose explicit
markers for `REG_CMD_ENG`/`REG_REQ_ENG` while keeping `CMD_EXE`, `PWR_ON`,
`WAIT_FOR_REQ`, `NOTIFY`, `/dev/subsys_esoc0` open, and all actor/Wi-Fi paths
blocked.
