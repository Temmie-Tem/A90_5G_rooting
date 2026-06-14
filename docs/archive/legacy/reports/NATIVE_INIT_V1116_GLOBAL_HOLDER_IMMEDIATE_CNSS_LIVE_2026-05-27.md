# V1116 Global Holder Immediate CNSS Live Report

Date: `2026-05-27`

## Result

- Decision: `v1116-immediate-cnss-pm-register-path-reached`
- Pass: `true`
- Deploy evidence: `tmp/wifi/v1116-execns-helper-v210-deploy/manifest.json`
- Live evidence: `tmp/wifi/v1116-global-holder-immediate-cnss-live/manifest.json`
- Helper: `a90_android_execns_probe v210`

## Summary

V1116 deployed helper `v210` and executed the global holder immediate-CNSS gate.

Deploy:

```text
decision=execns-helper-v210-deploy-pass
method=serial appendfile + uudecode
serial_chunk_size=1850
sha256=05cf75f9410ec14b07fca0f21de10cf4c08ab618b33770632190099f360497ed
```

The larger `3000` and `1900` serial chunks were rejected by the deploy
preflight line-limit check, so the actual deploy used `1850`.

Live gate:

```text
decision=v1116-immediate-cnss-pm-register-path-reached
reason=register_entries=1 register_ret=['0xffffffff'] cnss_hits=2
firmware_mounts_executed=True
global_modem_holder_opened=True
tracefs_write_executed=True
cnss_daemon_start_executed=True
wifi_hal_start_executed=False
wifi_bringup_executed=False
external_ping_executed=False
```

## Key Evidence

Immediate-CNSS contract:

```text
start_cnss_immediate_after_per_mgr=1
child.per_mgr.post_start_probe_wait_ms=20
child.per_mgr.post_start_observable=0
child.per_mgr.exited=1
child.per_mgr.exit_code=0
per_proxy_start_executed=0
child.per_proxy.start_skipped=1
cnss_daemon_start_executed=1
```

Trace result:

```text
pm_client_register_entry: cnss-daemon=1
pm_client_register_ret: cnss-daemon=['0xffffffff']
pm_client_connect_entry: 0
pm_client_connect_ret: 0
cnss_daemon_hit_count=2
```

Lower surface:

```text
qrtr service 69=0
wlfw=0
wlan0=0
mdm3 remained OFFLINING
```

Cleanup:

```text
version_seen=True
status_healthy=True
selftest: pass=11 warn=1 fail=0
```

## Interpretation

V1116 proves the helper can start CNSS in the intended no-pre-CNSS-`per_proxy`
order under the global holder prerequisite. This is progress over V1114:
`cnss-daemon` now reaches `pm_client_register`.

The remaining blocker moved to the PM register result:

```text
pm_client_register_ret = 0xffffffff
```

Because `per_mgr` is already gone at the 20 ms sample, the likely next check is
whether CNSS must be forked with zero delay immediately after `per_mgr`, before
any early sample/drain step.

## Next

V1117 should add a zero-delay CNSS-after-`per_mgr` order:

```text
per_mgr fork
  -> skip vndservice query
  -> skip per_proxy
  -> fork cnss-daemon immediately
  -> then sample per_mgr/cnss/PM trace state
```

The guardrails remain unchanged: no Wi-Fi HAL, no scan/connect, no credentials,
no DHCP/routes, and no external ping.
