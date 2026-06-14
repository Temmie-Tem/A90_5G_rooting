# Native Init V1175 PM Ack FD Target Live Report

Date: `2026-05-27`

## Result

- Decision: `v1175-state2-opened-subsys-modem-not-esoc0`
- Pass: `true`
- Plan: `docs/plans/NATIVE_INIT_V1175_PM_ACK_FD_TARGET_LIVE_PLAN_2026-05-27.md`
- V401 evidence: `tmp/wifi/v1175-v401-selinuxfs-mount/manifest.json`
- V490 evidence: `tmp/wifi/v1175-v490-policy-load/manifest.json`
- Live evidence: `tmp/wifi/v1175-pm-ack-fd-target-live-after-v490/manifest.json`
- Live summary: `tmp/wifi/v1175-pm-ack-fd-target-live-after-v490/summary.md`

## Summary

V1175 reproduced the V1174 PM-service state-2 ack body path and sampled
`/proc/<pm-service>/fd` while PM-service was still alive.  The state-2 device
open result fd `8` maps to `/tmp/a90-v231-1047/root/dev/subsys_modem`, not
`/dev/subsys_esoc0`.

| key | value |
| --- | --- |
| body events | `34` |
| state-2 open result | `8` |
| fd samples | `6` |
| samples with PM-service pid | `4` |
| fd records | `36` |
| fd `8` target | `/tmp/a90-v231-1047/root/dev/subsys_modem` |
| `/dev/subsys_modem` | seen |
| `/dev/subsys_esoc0` | not seen |
| mss after observer | `ONLINE` |
| mdm3 after observer | `OFFLINING` |
| `wlan0` | absent |

This closes the hypothesis that the PM-service state-2 ack body directly opens
eSoC.  Native PM-service opens the modem provider fd and reaches state `3`, but
no mdm3/WLFW publication follows.  The remaining gap is the Android state-3
post-open actor or request path that eventually opens or triggers
`/dev/subsys_esoc0`.

## Key Evidence

| fd | target |
| --- | --- |
| `0` | `/dev/null` |
| `1` | `pipe:[32992]` |
| `2` | `pipe:[32993]` |
| `3` | `pipe:[30296]` |
| `4` | `pipe:[30296]` |
| `5` | `/tmp/a90-v231-1047/root/dev/vndbinder` |
| `6` | `socket:[30297]` |
| `7` | `socket:[33007]` |
| `8` | `/tmp/a90-v231-1047/root/dev/subsys_modem` |

The fd table was stable across four PM-service pid samples.  No sample contained
`/dev/subsys_esoc0`, and post-observer surfaces still showed mdm3 `OFFLINING`
with no `wlan0`.

## Next Gate

V1176 should compare the Android-good state-3 post-open path against this native
state-3 stop point:

- trace or classify the PM-service state-3 follow-up actor after fd `8` is
  opened
- identify whether Android sends a second Binder/service request that triggers
  mdm3/eSoC
- keep the gate bounded; do not start Wi-Fi HAL, scan/connect, credentials,
  DHCP, route, external ping, boot image write, or partition write

## Validation

- `python3 -m py_compile scripts/revalidation/native_wifi_pm_ack_fd_target_live_v1175.py`
- `python3 scripts/revalidation/native_wifi_pm_ack_fd_target_live_v1175.py plan`
- Collector generation sanity confirmed `sample_pm_service_fds`, fd sample
  output, and `readlink` usage.
- V401 selinuxfs mount proof passed.
- V490 SELinux policy load proof passed.
- V1175 live gate passed.
- Post-cleanup native health:
  - `version`: `A90 Linux init 0.9.68 (v724)`
  - `selftest`: `pass=11 warn=1 fail=0`
  - `netservice`: disabled, `ncm0=absent`, `tcpctl=stopped`
