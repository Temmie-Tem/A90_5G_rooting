# Native Init V1166 PM-Service Action Branch Classifier Report

Date: `2026-05-27`

## Result

- Decision: `v1166-pm-service-action-branch-probe-required`
- Pass: `true`
- Plan: `docs/plans/NATIVE_INIT_V1166_PM_ACTION_BRANCH_CLASSIFIER_PLAN_2026-05-27.md`
- Evidence: `tmp/wifi/v1166-pm-action-branch-classifier/manifest.json`
- Summary: `tmp/wifi/v1166-pm-action-branch-classifier/summary.md`
- Disassembly evidence: `tmp/wifi/v1166-pm-action-branch-classifier/pm-service-connect-branch-0x95f4-0x9828.S`

## Summary

V1166 confirms the next useful live gate is not another plain late `pm-proxy`
retry.  Android V1159 proves `pm-service` Binder reaches
`/dev/subsys_esoc0` and `mdm_subsys_powerup`; native V1165 proves late
`pm-proxy` can stay alive and return `0` from PM client/server connect while
`pm-service` still never opens `/dev/subsys_esoc0`.

The extracted `pm-service` branch model explains how this can happen: a
successful connect can increment the voter count and return success while
skipping the fresh state transition if the old voter count is already nonzero
or the reconnect/timer flag is set.

## Key Evidence

| key | value |
| --- | --- |
| Android `vendor.per_proxy` start | `8.824458` |
| Android `pm-service` modem get | `8.854707` |
| Android `pm-service` eSoC get | `9.491382` |
| Android ICNSS QMI | `10.263706` |
| Android FW ready | `15.344607` |
| Android `wlan0` | `15.784281` |
| Android `pm-service` powerup samples | `8` |
| Native late `pm-proxy` started | `true` |
| Native late gate positive | `true` |
| Native `mdm_helper` `/dev/esoc-0` count | `1` |
| Native poll count | `12` |
| Native `pm-proxy` connect return | `0x0` |
| Native PM server connect implementation returns | `0x0`, `0x0` |
| Native PM server `start_vote` hits | `2` |
| Native `pm-service` `/dev/subsys_modem` | count `1` in every late poll |
| Native `pm-service` `/dev/subsys_esoc0` | count `0` in every late poll |

## PM-Service Branch Model

The `pm-service` connect branch at `0x95f4-0x9828` contains all expected
patterns:

| pattern | meaning |
| --- | --- |
| `client+0x10` connected flag | duplicate connect returns `-22` |
| `entry+0x60` shutdown byte | nonzero blocks connect as shutdown-in-progress |
| `entry+0x5c` voter count | increments on successful connect |
| old voter count branch | nonzero old count skips fresh state transition |
| `entry+0x58` reconnect flag | reconnect/timer path skips fresh state transition |
| `0x97dc -> 0x92dc(state=2)` | fresh state/action helper path |

## V1167 Tracepoint Plan

| name | offset | fetch |
| --- | --- | --- |
| `pm_server_connect_vote_count_before` | `0x9738` | `voters_before=%w8` |
| `pm_server_connect_vote_count_after_store` | `0x9740` | `voters_before=%w8 voters_after=%w9` |
| `pm_server_connect_reconnect_flag_check` | `0x9748` | `reconnect_flag=%w8` |
| `pm_server_connect_powerup_state_call` | `0x97dc` | `entry=%x0 state=%w1` |
| `pm_server_state_transition_entry` | `0x92dc` | `entry=%x0 state=%w1` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_action_branch_classifier_v1166.py
python3 scripts/revalidation/native_wifi_pm_action_branch_classifier_v1166.py
```

Both commands passed.  V1166 is host-only and did not execute a device command,
Wi-Fi HAL, scan/connect, credential use, DHCP, route, external ping, partition
write, boot image write, flash, or reboot.

## Next Gate

V1167 should rerun the bounded late `pm-proxy` gate with these action-branch
tracepoints.  The first question is whether native skips state transition
because the old voter count is nonzero, the reconnect/timer flag is set, or
the state helper is called but its client callback does not open
`/dev/subsys_esoc0`.
