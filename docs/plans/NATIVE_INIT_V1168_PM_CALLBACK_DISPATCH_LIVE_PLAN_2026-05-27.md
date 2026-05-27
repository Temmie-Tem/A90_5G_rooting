# Native Init V1168 PM-Service Callback Dispatch Live Plan

Date: `2026-05-27`

## Goal

Trace below the `pm-service` state helper that V1167 proved is called with
`state=2`.  V1168 determines whether the helper iterates a client record,
resolves a callback branch target, and where that target lives in the
`pm-service` address space.

## Preconditions

- Native v724 is healthy.
- Serial bridge is available on `127.0.0.1:54321`.
- V401 selinuxfs mount and V490 policy-load proof are rerun in the same boot.
- Helper `a90_android_execns_probe v217` remains the deployed helper.

## Added Uprobes

| label | offset | fetch |
| --- | --- | --- |
| `pm_state_helper_client_node` | `0x93bc` | `entry=%x19 node=%x21 head=%x23 state=%x20` |
| `pm_state_helper_client_callback_call` | `0x93c4` | `entry=%x19 node=%x21 client_record=%x0 state=%x1` |
| `pm_client_callback_entry` | `0x8630` | `client_record=%x0 state=%x1` |
| `pm_client_callback_target_ready` | `0x8640` | `target=%x0 vtable=%x9 state=%x1` |
| `pm_client_callback_branch` | `0x8644` | `target=%x0 vtable=%x9 callback=%x2 state=%x1` |

The collector also captures `/proc/<pm-service-pid>/maps` in the same window
to map the dynamic callback pointer to a binary or library offset.

## Success Criteria

- Manifest decision is one of:
  - `v1168-callback-branch-dispatched-but-no-esoc0`
  - `v1168-callback-dispatch-esoc0-advanced`
  - `v1168-callback-call-prepared-but-no-branch`
  - `v1168-state-helper-client-list-empty-or-skipped`
- `pm_callback_dispatch.event_count > 0`.
- Cleanup returns to native v724 health.
- No Wi-Fi HAL, scan/connect, credential use, DHCP, route, external ping,
  partition write, boot image write, or flash is performed.

## Next Branches

- Callback branch observed but no eSoC: trace inside the mapped callback
  target if it is vendor code.
- Callback call prepared but no branch: trace `0x8630-0x8644` at finer
  offsets.
- Client list empty/skipped: classify PM-service client registration list
  content before `state=2`.
- eSoC advanced: preserve evidence and gate MHI/WLFW readiness.
