# Native Init V1067 PM Observer Binder Materialization Report

## Summary

V1067 repaired the PM observer private namespace so the new observer mode now
materializes `/dev/binder`, `/dev/hwbinder`, and `/dev/vndbinder`.  Helper
`a90_android_execns_probe v185` was built, deployed over authenticated NCM/TCP,
and rerun with the same bounded PM observer gate.

Final live decision remained `v1066-observer-runtime-gap-clean` because the
runner classification label is shared, but the blocker moved forward:

- V1066 blocker: Binder devices absent, service managers could not open Binder.
- V1067 state: Binder devices present; `hwservicemanager` opened `hwbinder`;
  `servicemanager`/`vndservicemanager` still SIGABRT and `pm-service` still exits
  before opening `/dev/subsys_modem`.

## Evidence

| Item | Value |
| --- | --- |
| helper | `a90_android_execns_probe v185` |
| helper sha256 | `989554971ab11b97cb98a8d02455146b8b469b87825a2f3feee870ef9079158c` |
| build artifact | `tmp/wifi/v1067-execns-helper-v185-build/a90_android_execns_probe` |
| deploy evidence | `tmp/wifi/v1067-execns-helper-v185-deploy/deploy.txt` |
| remote sha evidence | `tmp/wifi/v1067-execns-helper-v185-deploy/remote-sha.txt` |
| live manifest | `tmp/wifi/v1067-pm-service-binder-materialization-live/manifest.json` |
| live transcript | `tmp/wifi/v1067-pm-service-binder-materialization-live/host/pm-service-trigger-observer.txt` |

## Positive Delta

| Marker | Value |
| --- | --- |
| `private_node.binder.exists` | `1` |
| `private_node.binder.major:minor` | `10:81` |
| `private_node.hwbinder.exists` | `1` |
| `private_node.hwbinder.major:minor` | `10:80` |
| `private_node.vndbinder.exists` | `1` |
| `private_node.vndbinder.major:minor` | `10:79` |
| `hwservicemanager` fd target | `/tmp/a90-v231-885/root/dev/hwbinder` |

This proves the V1066 missing-Binder-node defect is fixed for the observer
namespace.

## Remaining Runtime Gap

| Field | Value |
| --- | --- |
| helper result | `observer-runtime-gap` |
| helper reason | `child-exited-before-observe-window` |
| `pm-service` `/dev/subsys_modem` seen | `0` |
| `pm_proxy_helper` `/dev/subsys_modem` seen | `0` |
| `servicemanager` signal | `6` |
| `hwservicemanager` signal | `15` |
| `vndservicemanager` signal | `6` |
| `pm-service` exit_code | `255` |
| `pm-proxy` exit_code | `1` |
| all_postflight_safe | `1` |

The stderr no longer reports Binder open failure, but still shows SIGABRT for
`servicemanager` and `vndservicemanager`.  `hwservicemanager` became observable
and was terminated by cleanup, confirming that at least the hwbinder path can be
opened in the repaired namespace.

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

Postflight `selftest` remained `fail=0`, and NCM/tcpctl stayed running.

## Next Step

V1068 should capture the service-manager abort reason with a compact crash
surface that does not start `mdm_helper`, CNSS, Wi-Fi HAL, scan/connect, DHCP, or
external ping.  The useful target is a Binder-context-manager/startup proof for
`servicemanager` and `vndservicemanager`, including stderr, signal source, and
whether the abort is caused by SELinux, context-manager registration, or missing
Android runtime files/properties.
