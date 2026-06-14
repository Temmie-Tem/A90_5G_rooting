# Native Init V1174 PM Ack Body Live Report

Date: `2026-05-27`

## Result

- Decision: `v1174-state2-open-success-state3-no-esoc0`
- Pass: `true`
- Plan: `docs/plans/NATIVE_INIT_V1174_PM_ACK_BODY_LIVE_PLAN_2026-05-27.md`
- V401 evidence: `tmp/wifi/v1174-rerun-v401-selinuxfs-mount/manifest.json`
- V490 evidence: `tmp/wifi/v1174-rerun-v490-policy-load/manifest.json`
- Live evidence: `tmp/wifi/v1174-rerun-pm-ack-body-live-after-v490/manifest.json`
- Live summary: `tmp/wifi/v1174-rerun-pm-ack-body-live-after-v490/summary.md`

## Summary

V1174 traced the PM-service ack implementation at `pm-service+0x63f4` and the
state-transition body at `pm-service+0x8788`.  The primary `state=2` ack path
does not stop at the PM-service wrapper.  It clears the client pending state,
confirms all clients are acked, evaluates a negative device fd, calls `open()`,
receives fd `8`, and sets the PM state to `3`.

| key | value |
| --- | --- |
| body events | `34` |
| ack body states | `2, 3, 0, 1` |
| current states observed | `2, 3, 1` |
| state-2 all-acked | `true` |
| state-2 dependency flag | `0` |
| state-2 fd before open | `-1` |
| state-2 open result | `8` |
| state update after open | `3` |
| `/dev/subsys_esoc0` | not opened |
| `wlan0` | absent |

This closes the hypothesis that PM ack completion itself is missing or skipped.
PM-service performs its state-2 device open and internal state update
successfully, but that does not publish mdm3/WLFW or create `wlan0` in native
init.

## Key Evidence

| label | count |
| --- | --- |
| `pm_ack_impl_entry` | `4` |
| `pm_ack_impl_client_match` | `4` |
| `pm_ack_state_core_entry` | `4` |
| `pm_ack_state_client_clear` | `4` |
| `pm_ack_state_pending_scan_done` | `4` |
| `pm_ack_state_current` | `3` |
| `pm_ack_state2_dependency_ptr` | `1` |
| `pm_ack_state2_dependency_flag` | `1` |
| `pm_ack_state2_fd_eval` | `1` |
| `pm_ack_state2_open_call` | `1` |
| `pm_ack_state2_open_result` | `1` |
| `pm_ack_state_set_call` | `2` |
| `pm_ack_state_core_ret` | `4` |

For the primary `state=2` branch:

| key | value |
| --- | --- |
| PM-service manager | `0xb400007fa380a060` |
| PM handle | `0xb400007f1fa060e0` |
| peripheral object | `0xb400007fa3826180` |
| dependency object | `0xb400007fa3826000` |
| dependency flag | `0x0` |
| fd before open | `0xffffffff` (`-1`) |
| open result | `0x8` |
| state set call | `0x3` |
| body return | `0x0` |

The current trace records the opened path only as a pointer
`0xb400007fa3806198`.  V1175 should decode that string or sample PM-service fds
inside the same live window.

## Next Gate

V1175 should decode the opened device path and fd target:

- fetch the `device_path` string at `pm_ack_state2_open_call`, if tracefs string
  fetch supports it on this kernel
- otherwise sample `/proc/<pm-service>/fd` immediately after `open()` and map
  fd `8`
- compare whether Android-good opens the same path and what actor follows state
  `3` before mdm3/WLFW publication
- keep the next gate bounded; do not start Wi-Fi HAL, scan/connect, credentials,
  DHCP, route, external ping, boot image write, or partition write

## Validation

- `python3 -m py_compile scripts/revalidation/native_wifi_pm_ack_body_live_v1174.py`
- `python3 scripts/revalidation/native_wifi_pm_ack_body_live_v1174.py plan`
- Collector generation sanity confirmed `pm-service` event registration for
  `0x63f4`, `0x8788`, `0x898c`, `0x8cd0`, and `0x8cd4`.
- `git diff --check`
- V401 selinuxfs mount proof passed.
- V490 SELinux policy load proof passed.
- V1174 live gate passed.
- Post-cleanup native health:
  - `version`: `A90 Linux init 0.9.68 (v724)`
  - `selftest`: `pass=11 warn=1 fail=0`
  - `netservice`: disabled, `ncm0=absent`, `tcpctl=stopped`
