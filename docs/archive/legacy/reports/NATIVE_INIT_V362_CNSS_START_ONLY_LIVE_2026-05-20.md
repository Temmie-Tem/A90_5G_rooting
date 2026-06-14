# v362 Report: Bounded CNSS Start-Only Live Run

- date: `2026-05-20`
- scope: one bounded CNSS daemon start-only attempt
- boot image change: none
- native baseline: `A90 Linux init 0.9.61 (v319)`
- plan: `docs/plans/NATIVE_INIT_V362_CNSS_START_ONLY_LIVE_PLAN_2026-05-20.md`
- result: `PASS`

## Summary

V362 executed one approved bounded `cnss-daemon -n -l` start-only run inside the
existing private Android execution namespace. The child was observable, ran until
the 10s timeout, was terminated, reaped, and postflight process checks were clean.

This proves bounded CNSS daemon start-only is viable with the v11 helper profile.
It does not prove Wi-Fi scan/connect/link-up readiness.

## Evidence

| item | path | decision |
| --- | --- | --- |
| preflight | `tmp/wifi/v362-cnss-start-only-preflight-20260520/` | `preflight-ready` |
| approval packet | `tmp/wifi/v362-cnss-start-only-approval-packet-20260520/` | `live-approval-packet-ready` |
| live run | `tmp/wifi/v362-cnss-start-only-live-20260520/` | `start-only-pass` |
| evidence analysis | `tmp/wifi/v362-cnss-start-only-evidence-analysis-full-20260520/` | `cnss-start-only-evidence-classified` |
| warning disposition | `tmp/wifi/v362-cnss-warning-disposition-20260520/` | `cnss-warning-disposition-ready` |

## Live Result

```text
decision: start-only-pass
pass: True
reason: observed-until-timeout-clean-stop
daemon_start_executed: true
```

Key trusted markers:

```text
helper_status=namespace-ready
cnss_start.result=start-only-pass
cnss_start.reason=observed-until-timeout-clean-stop
cnss_start.exec_attempted=1
cnss_start.child_started=1
cnss_start.observable=1
cnss_start.timed_out=1
cnss_start.term_sent=1
cnss_start.kill_sent=1
cnss_start.reaped=1
cnss_start.postflight_safe=1
cnss_start.scan_connect_linkup=0
```

Postflight:

```text
pidof cnss-daemon: absent
postflight process clean: true
target_running_count: 0
target_zombie_count: 0
/proc/net/dev: no wlan* interface
wifiinv: wlan_like=0 rfkill_wifi=0
```

## Evidence Analyzer

```text
decision: cnss-start-only-evidence-classified
pass: True
reason: critical start-only evidence classified
```

All critical checks passed:

- runner start-only PASS;
- trusted `cnss_start` begin/end markers;
- child observable;
- cleanup/reap safe;
- uid/gid/groups/CAP_NET_ADMIN contract satisfied;
- namespace context valid;
- `/proc/status` and maps captured;
- postflight pidof absent;
- postflight netdev has no `wlan*`;
- postflight Wi-Fi inventory has no wlan-like interface;
- postflight CNSS process audit clean.

## Warning Disposition

```text
decision: cnss-warning-disposition-ready
pass: True
```

Warnings accepted for start-only scope:

| warning | status | interpretation |
| --- | --- | --- |
| `perfd-client-unavailable` | accepted-for-start-only | Android runtime service gap; not a start-only blocker |
| `kmsg-write-denied` | accepted-for-start-only | private namespace logging gap; do not relax `/dev/kmsg` silently |
| `shell-quote-noise` | coalesced | logging-path stderr noise |

## Guardrails

- No Wi-Fi scan/connect/link-up was executed.
- No credentials, DHCP, routing, supplicant, wificond, hostapd, or Wi-Fi HAL were used.
- No `cnss_diag` was started.
- No rfkill unblock, ICNSS bind/unbind, firmware mutation, Android property write,
  or partition write was performed.
- Start-only PASS does not authorize broader Wi-Fi bring-up.

## Decision

- decision: `bounded-cnss-start-only-pass`
- current status: CNSS daemon can start under the private namespace profile and cleanly stop/reap
- next step: plan a no-scan/no-connect readiness delta observer or another explicit approval boundary before any broader Wi-Fi action.
