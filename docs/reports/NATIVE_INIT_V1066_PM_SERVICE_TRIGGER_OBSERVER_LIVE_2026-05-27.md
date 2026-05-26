# Native Init V1066 PM-Service Trigger Observer Live Report

## Summary

V1066 ran the PM-service trigger observer live gate over authenticated NCM/TCP.
The final live run used helper `a90_android_execns_probe v184` because the first
attempts exposed helper-side observer plumbing defects:

- `v181`: new mode was missing from the top-level v235 allowlist.
- `v182`: `--property-root` validation still did not accept the observer mode.
- `v183`: mode launched, but verbose readiness snapshots exceeded the tcpctl
  transcript cap before final `result` markers.
- `v184`: compacted the observer output to PM fd snapshots and reached a final
  result.

Final decision: `v1066-observer-runtime-gap-clean` with `pass=true`.

## Evidence

| Item | Value |
| --- | --- |
| manifest | `tmp/wifi/v1066-pm-service-trigger-observer-live/manifest.json` |
| summary | `tmp/wifi/v1066-pm-service-trigger-observer-live/summary.md` |
| helper | `a90_android_execns_probe v184` |
| helper sha256 | `e654b4bdde6842e4723a51bc5c6d267827f8d2c6c0271f3dc80b23857edb6d94` |
| deploy evidence | `tmp/wifi/v1067-execns-helper-v184-deploy/deploy.txt` |
| remote sha evidence | `tmp/wifi/v1067-execns-helper-v184-deploy/remote-sha.txt` |

## Result

| Field | Value |
| --- | --- |
| helper result | `observer-runtime-gap` |
| helper reason | `child-exited-before-observe-window` |
| snapshot_count | `4` |
| `pm-service` `/dev/subsys_modem` seen | `0` |
| `pm_proxy_helper` `/dev/subsys_modem` seen | `0` |
| timed_out | `1` |
| all_observable | `0` |
| all_postflight_safe | `1` |
| `pm-service` exit_code | `255` |
| `pm-proxy` exit_code | `1` |
| `pm_proxy_helper` postflight_safe | `1` |

Interpretation: the bounded observer can now launch the intended service-manager
and PM actor set, but the PM stack still does not form the Android-positive
`/dev/subsys_modem` fd contract.  `pm-service` exits before the observe window
and `pm_proxy_helper` never exposes a modem fd in the captured snapshots.

## Guardrails

| Guard | Value |
| --- | --- |
| `mdm_helper_start_executed` | `false` |
| `cnss_daemon_start_executed` | `false` |
| `subsys_esoc0_open_attempted` | `false` |
| `wifi_hal_start_executed` | `false` |
| `wifi_bringup_executed` | `false` |
| `external_ping_executed` | `false` |
| postflight actor hits | `[]` |
| postflight Wi-Fi link hits | `[]` |
| cleanup reboot | `false` |

Postflight health remained normal: `bootstatus` reported `BOOT OK netservice`,
`selftest` reported `fail=0`, and NCM/tcpctl remained running.

## Source Changes

- `stage3/linux_init/helpers/a90_android_execns_probe.c`
  - bumped helper marker to `v184`;
  - added the observer mode to top-level mode allowlist;
  - added the observer mode to `--property-root` validation allowlist;
  - compacted PM observer output to avoid losing final markers through tcpctl.
- `scripts/revalidation/native_wifi_pm_service_trigger_observer_live_v1066.py`
  - added a repeatable NCM/tcpctl live runner with explicit guardrails,
    private evidence output, remote helper parity checks, and postflight health
    capture.

## Next Step

V1067 should classify why `pm-service` exits with code `255` under the native
observer runtime.  The next unit should stay below `mdm_helper`, CNSS, Wi-Fi HAL,
scan/connect, DHCP, and external ping.  Useful inputs are the `pm-service`
stderr/exit path, required properties, vndbinder service dependencies, and the
Android-positive PM actor command/environment delta.
