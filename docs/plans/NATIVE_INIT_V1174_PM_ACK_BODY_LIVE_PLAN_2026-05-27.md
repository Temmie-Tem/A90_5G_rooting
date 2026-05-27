# Native Init V1174 PM Ack Body Live Plan

Date: `2026-05-27`

## Goal

Trace the PM-service ack implementation body below V1173.  V1173 proved CNSS
`state=2` acknowledge reaches the PM-service Binder code `5` handler and returns
`0x0`, but `/dev/subsys_esoc0` is still not opened.  V1174 verifies where the
PM-service `pm-service+0x63f4` ack implementation and `pm-service+0x8788`
state-transition body exit before device open.

## Preconditions

- Native v724 is healthy.
- Serial bridge is available on `127.0.0.1:54321`.
- V401 selinuxfs mount and V490 policy-load proof are rerun in the same boot.
- Helper `a90_android_execns_probe v217` remains deployed.
- V1173 live result is `v1173-state2-ack-client-server-success-no-esoc0`.

## Host Classification

`pm-service+0x63f4` is not a direct eSoC open.  It is a wrapper that finds the
client handle and tail-calls the PM state-transition body:

| offset | meaning |
| --- | --- |
| `0x63f4` | PM-service ack implementation entry |
| `0x6474` | matching client handle found |
| `0x8788` | state-transition body entry |
| `0x882c` | clear matching client's pending state |
| `0x8894` | pending-client scan complete |
| `0x88d0` | current peripheral state loaded |
| `0x88e4` | state-2 dependency pointer loaded |
| `0x898c` | state-2 device fd evaluated |
| `0x8cd0` | state-2 device open call |
| `0x8d14` | state update call |

## Added Uprobes

| label | binary | offset | fetch |
| --- | --- | --- | --- |
| `pm_ack_impl_entry` | `pm-service` | `0x63f4` | `manager=%x0 handle=%x1 state=%x2` |
| `pm_ack_impl_client_match` | `pm-service` | `0x6474` | `client=%x21 handle=%x19 state=%x20` |
| `pm_ack_state_core_entry` | `pm-service` | `0x8788` | `peripheral=%x0 handle=%x1 state=%x2` |
| `pm_ack_state_client_clear` | `pm-service` | `0x882c` | `client=%x22 state=%x21` |
| `pm_ack_state_pending_scan_done` | `pm-service` | `0x8894` | `peripheral=%x20 all_acked=%x21` |
| `pm_ack_state_current` | `pm-service` | `0x88d0` | `peripheral=%x20 current_state=%x8 all_acked=%x21` |
| `pm_ack_state2_dependency_ptr` | `pm-service` | `0x88e4` | `peripheral=%x20 dependency=%x22` |
| `pm_ack_state2_dependency_flag` | `pm-service` | `0x88ec` | `dependency=%x22 dependency_flag=%x8` |
| `pm_ack_state2_fd_eval` | `pm-service` | `0x898c` | `peripheral=%x20 fd=%x8` |
| `pm_ack_state2_open_call` | `pm-service` | `0x8cd0` | `device_path=%x0 flags=%x1` |
| `pm_ack_state2_open_result` | `pm-service` | `0x8cd4` | `fd=%x0` |
| `pm_ack_state_set_call` | `pm-service` | `0x8d14` | `peripheral=%x20 state=%x1` |
| `pm_ack_state_core_ret` | `pm-service` | `0x8788` | `ret=$retval` |

## Success Criteria

- Manifest decision is one of:
  - `v1174-state2-fd-zero-skip-open-no-esoc0`
  - `v1174-state2-fd-eval-no-open-no-esoc0`
  - `v1174-state2-open-success-state3-no-esoc0`
  - `v1174-state2-open-call-no-esoc0`
  - `v1174-state2-current-no-fd-eval-no-esoc0`
  - `v1174-state2-body-exits-before-current-state`
  - `v1174-pm-ack-body-opened-esoc0`
- PM-service ack body `state=2` branch status is recorded.
- State-2 fd evaluation/open status is recorded.
- Cleanup returns to native v724 health.
- No Wi-Fi HAL, scan/connect, credential use, DHCP, route, external ping,
  partition write, boot image write, or flash is performed.

## Next Branches

- fd field is `0` and open is skipped: compare Android PM-service object fd
  initialization and native device-fd field before ack.
- fd field is negative and open is called: classify open result and post-open
  state transition.
- eSoC opens: move to bounded MHI/WLFW/BDF publication gate.
