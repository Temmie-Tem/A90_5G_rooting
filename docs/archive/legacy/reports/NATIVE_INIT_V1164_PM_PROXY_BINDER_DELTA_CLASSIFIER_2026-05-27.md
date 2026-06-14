# Native Init V1164 PM Proxy Binder Delta Classifier Report

Date: `2026-05-27`

## Result

- Decision: `v1164-pm-proxy-binder-actionability-gap`
- Pass: `true`
- Classifier: `scripts/revalidation/native_wifi_pm_proxy_binder_delta_v1164.py`
- Plan: `docs/plans/NATIVE_INIT_V1164_PM_PROXY_BINDER_DELTA_CLASSIFIER_PLAN_2026-05-27.md`
- Evidence: `tmp/wifi/v1164-pm-proxy-binder-delta-classifier/manifest.json`
- Summary: `tmp/wifi/v1164-pm-proxy-binder-delta-classifier/summary.md`

## Summary

V1164 confirms the blocker is no longer simply missing `pm-proxy` or missing
current-boot policy. Android V1159 shows the good path:

```text
vendor.per_proxy starts
  -> pm-service Binder thread enters mdm_subsys_powerup
    -> /dev/subsys_esoc0 get appears
      -> ICNSS QMI, BDF, FW ready, wlan0
```

Native V1163-after-V490 reaches the PM client/server connect path, including
`pm-proxy` client register/connect success and PM server `start_vote` events,
but `pm-service` remains idle and never opens `/dev/subsys_esoc0`.

## Key Evidence

| key | Android V1159 | Native V1163-after-V490 |
| --- | --- | --- |
| `per_proxy` | starts at `8.824458` | late start succeeds |
| `pm-service` modem get | `8.854707` | `/dev/subsys_modem` count `1` in every late poll |
| `pm-service` eSoC get | `9.491382` | `/dev/subsys_esoc0` count `0` in every late poll |
| PM client connect | inferred by Android good path | `pm-proxy` `pm_client_connect_ret=['0x0']` |
| PM server connect | Binder thread reaches `mdm_subsys_powerup` | server `connect/start_vote` hit count `2` |
| lower Wi-Fi path | ICNSS QMI `10.263706`, FW ready `15.344607`, `wlan0` `15.784281` | no MHI, WLFW, service `69`, or `wlan0` |

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_proxy_binder_delta_v1164.py
python3 scripts/revalidation/native_wifi_pm_proxy_binder_delta_v1164.py
```

Result:

```text
decision: v1164-pm-proxy-binder-actionability-gap
pass: True
```

The classifier is host-only and did not execute any device command.

## Safety

- Wi-Fi HAL, scan/connect/link-up, credential use, DHCP, route, external ping,
  partition writes, boot image writes, flash, and reboot were not executed.
- No Wi-Fi credential is written by the classifier.

## Next Gate

V1165 should instrument the late `pm-proxy` post-connect window rather than
retrying the same V1163 sequence. Minimum useful additions:

1. Capture `pm-proxy` stdout/stderr and exit state after late start.
2. Extend late post-connect polling beyond the six short polls.
3. Add PM server connect state/action argument capture around the existing
   `pm_server_connect_impl_start_vote` hits.
4. Keep V401 + V490 as mandatory current-boot prerequisites for live PM/CNSS
   gates.
