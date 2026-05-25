# Native Init V859 pm-service Property Delta Replay Report

## Result

- decision: `v859-v858-target-denials-removed-new-property-gap`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_pm_service_property_delta_replay_v859.py`
- evidence: `tmp/wifi/v859-pm-service-property-delta-replay-r2/manifest.json`

## Outcome

V859 proved V858 had the intended effect: all original V857 target denials were
removed.

```text
v858_target_remaining=[]
```

The run still did not prove Android-equivalent subsystem fd holds:

| Actor | Result |
| --- | --- |
| `pm-service` | observable, but no `/dev/subsys_esoc0` or `/dev/subsys_modem` fd target captured |
| `pm-proxy` | observable, but no `subsys_*` fd target captured |

## New Gap

After removing the V857 target denials, the next property gap moved to
service-manager/library logging and linker keys:

| Key | Count |
| --- | ---: |
| `persist.log.tag.vndservicemanager` | 104 |
| `log.tag.vndservicemanager` | 104 |
| `persist.log.tag.ServiceManager` | 102 |
| `log.tag.ServiceManager` | 102 |
| `debug.ld.app.vndservicemanager` | 20 |
| `persist.log.tag.PerMgrLib` | 4 |
| `log.tag.PerMgrLib` | 4 |
| `arm64.memtag.process.vndservicemanager` | 2 |

## Guardrails

- `helper_deploy_executed=false`
- `pm_service_start_only_executed=true`
- `mdm_helper_start_executed=false`
- `wifi_hal_start_executed=false`
- `wifi_bringup_executed=false`
- `external_ping_executed=false`
- created eSoC/subsys nodes were cleaned up
- postflight health remained good

## Next

V860 should extend the private property layout for the new
`vndservicemanager`/`ServiceManager`/`PerMgrLib` keys before any `mdm_helper` or
`ks` replay. The next attempt must preserve the same no-HAL/no-scan/no-connect
guardrails.
