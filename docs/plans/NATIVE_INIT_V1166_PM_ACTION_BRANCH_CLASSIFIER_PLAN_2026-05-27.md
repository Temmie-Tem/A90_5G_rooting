# Native Init V1166 PM-Service Action Branch Classifier Plan

Date: `2026-05-27`

## Goal

Classify why native V1165 reaches successful `pm-proxy`/`pm-service` PM connect
and `start_vote`, but still never produces Android's `/dev/subsys_esoc0`
open.  V1166 is host-only and uses existing V1159/V1165 evidence plus the
extracted `pm-service` binary.

## Inputs

- Android-good reference: `tmp/wifi/v1159-pm-thread-sampler-live-20260527-191019`
- Native reference: `tmp/wifi/v1165-late-per-proxy-actionability-live-after-v490/manifest.json`
- Vendor binary: `tmp/wifi/v1073-host-only/vendor-extract/files/pm-service`

## Scope

1. Confirm Android's known-good order:
   `vendor.per_proxy -> pm-service Binder -> /dev/subsys_esoc0 -> mdm_subsys_powerup -> wlan0`.
2. Confirm native V1165 reached:
   late `pm-proxy` alive, PM client/server connect return `0`, and no
   `/dev/subsys_esoc0`.
3. Disassemble the `pm-service` connect branch around offsets
   `0x95f4-0x9828`.
4. Identify exact V1167 tracefs offsets that separate:
   old voter count skip, reconnect/timer skip, and fresh state transition.

## Expected Branch Model

- `client+0x10` is the per-client connected flag.
- `entry+0x60` rejects connect while shutdown is in progress.
- `entry+0x5c` is the voter count.
- A nonzero old voter count returns success but skips a fresh state transition.
- `entry+0x58` is a reconnect/timer flag that also skips a fresh state transition.
- Only old voter count `0` and reconnect flag `0` reaches the state helper
  call at `0x97dc -> 0x92dc(state=2)`.

## Success Criteria

- Classifier exits `0`.
- Manifest decision is `v1166-pm-service-action-branch-probe-required`.
- The tracepoint plan includes offsets `0x9738`, `0x9740`, `0x9748`, `0x97dc`,
  and `0x92dc`.
- No live device command, Wi-Fi HAL, scan/connect, credentials, DHCP, route,
  external ping, flash, reboot, or partition write is executed.

## Next Gate

V1167 should rerun the bounded late `pm-proxy` gate with added tracefs probes
at the action-branch offsets.  The first live question is whether native skips
the state transition because the old voter count is already nonzero or because
the reconnect/timer path is active.
