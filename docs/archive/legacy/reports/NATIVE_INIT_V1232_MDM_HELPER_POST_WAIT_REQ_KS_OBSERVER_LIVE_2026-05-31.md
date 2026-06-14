# V1232 mdm_helper Post-WAIT_FOR_REQ ks/MHI Observer Live Gate

- date: 2026-05-31
- scope: bounded live observer
- helper: `a90_android_execns_probe v256`
- live runner: `scripts/revalidation/native_wifi_mdm_helper_post_wait_req_ks_observer_live_v1232.py`
- evidence: `tmp/wifi/v1232-mdm-helper-post-wait-req-ks-observer-live/manifest.json`
- result: `v1232-wait-req-returned-no-ks-mhi`
- pass: `true`

## Purpose

V1228 proved `mdm_helper` reaches `ESOC_WAIT_FOR_REQ`. V1229 classified the
next blocker as the image-link handoff toward Android's `ks` + MHI path. V1232
enabled the direct subsystem-trigger path and used helper `v256` to observe the
post-wait branch without ptrace.

## Evidence Summary

| field | value |
|---|---|
| `post_wait_req.begin` | `true` |
| sample interval | `50 ms` |
| sample count | `84` |
| initial `ESOC_WAIT_FOR_REQ` thread count | `1` |
| transition detected | `1` |
| transition sample | `4` |
| post-transition sample count | `80` |
| max `ks` process count | `0` |
| max MHI pipe path exists | `0` |
| max global MHI pipe fd count | `0` |
| max `mdm_helper` MHI pipe fd count | `0` |
| WLFW / `wlan0` | absent |

The key observation is concrete: `mdm_helper` leaves the observed
`ESOC_WAIT_FOR_REQ` wait within roughly 200 ms, but the expected Android
image-link path does not appear during the bounded post-transition window.

## Interpretation

V1232 closes the previous ambiguity:

1. Native `mdm_helper` is not stuck forever in `ESOC_WAIT_FOR_REQ`.
2. The request-return edge is reached.
3. Returning from that wait does not launch or reach `ks`.
4. Without `ks`, `/dev/mhi_0305_01.01.00_pipe_10` remains absent.
5. Without MHI, WLFW/BDF/FW-ready/`wlan0` remain absent.

The active blocker moves from "does `ESOC_WAIT_FOR_REQ` return?" to "what
branch does `mdm_helper` take immediately after the wait returns, and why does
it not execute Android's `ks` image-link path?"

## Safety Audit

- Wi-Fi HAL start: `false`
- scan/connect/link-up: `false`
- credential use: `false`
- DHCP/route: `false`
- external ping: `false`
- `ESOC_NOTIFY`: not attempted
- `ESOC_BOOT_DONE`: not attempted
- boot image write / flash / partition write: `false`
- postflight selftest: `pass=11 warn=1 fail=0`
- postflight netservice: disabled, `ncm0=absent`, `tcpctl=stopped`

## Next

V1233 should classify the immediate post-return branch inside `mdm_helper`.
The useful next unit is source/build-only support for a denser post-wait
thread/fd/syscall snapshot around transition sample `4`, still without ptrace,
`ESOC_NOTIFY`, `ESOC_BOOT_DONE`, Wi-Fi HAL, scan/connect, credentials,
DHCP/routes, or external ping.
