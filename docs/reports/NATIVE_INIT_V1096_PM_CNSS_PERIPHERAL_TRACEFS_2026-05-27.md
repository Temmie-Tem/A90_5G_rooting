# Native Init V1096 PM CNSS Peripheral Tracefs Report

## Summary

V1096 passed. The V1095 provider-positive PM observer window was replayed while
tracefs-only uprobes were armed on vendor `libperipheral_client.so`.

Decision:

```text
v1096-cnss-peripheral-client-path-hit-mdm3-still-offline
```

This closes the hypothesis that `cnss-daemon` merely reaches Binder/netlink
surfaces but never enters the PeripheralManager client path. It does enter that
path: tracefs captured `cnss-daemon` hits on `pm_client_register` and
`pm_register_connect`. mdm3 still remained `OFFLINING`, and no WLFW/`wlan0`
progress occurred.

## Evidence

| item | path |
| --- | --- |
| live wrapper | `scripts/revalidation/native_wifi_pm_cnss_peripheral_tracefs_live_v1096.py` |
| predecessor evidence | `tmp/wifi/v1095-pm-cnss-voter-surface-live/manifest.json` |
| live evidence | `tmp/wifi/v1096-pm-cnss-peripheral-tracefs-live/manifest.json` |
| live summary | `tmp/wifi/v1096-pm-cnss-peripheral-tracefs-live/summary.md` |
| collector transcript | `tmp/wifi/v1096-pm-cnss-peripheral-tracefs-live/host/pm-cnss-peripheral-tracefs-observer.txt` |

## Result

```text
tracefs_result: tracefs-uprobe-pass
total_hit_count: 6
cnss_daemon_hit_count: 2
mdm3_state: OFFLINING
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

Tracefs counts:

```json
{
  "pm_client_ack": 1,
  "pm_client_connect": 1,
  "pm_client_disconnect": 0,
  "pm_client_register": 2,
  "pm_client_unregister": 0,
  "pm_find_lock": 0,
  "pm_register_connect": 2
}
```

Per-process hits:

```json
{
  "Binder:1057_1": {
    "pm_client_ack": 1
  },
  "cnss-daemon": {
    "pm_client_register": 1,
    "pm_register_connect": 1
  },
  "pm-proxy": {
    "pm_client_connect": 1,
    "pm_client_register": 1,
    "pm_register_connect": 1
  }
}
```

## Interpretation

The active blocker moved one step lower:

```text
PM provider visible
  -> pm-proxy PM client path hit
  -> cnss-daemon PM client path hit
  -> mdm3 still OFFLINING
  -> WLFW service 69 absent
  -> wlan0 absent
```

So the current question is no longer whether `cnss-daemon` calls into
`libperipheral_client.so`. It does. The next gate should classify what happens
after the client registration/connect call:

1. Whether `pm-service` receives and acknowledges a request that should vote or
   trigger the modem/eSoC path.
2. Whether the request is semantically incomplete because native init still
   lacks an Android property, Binder registration, or PM service input.
3. Whether the lower eSoC/MDM3 trigger remains independent of the PM client
   request path.

## Implementation Notes

- The first live attempt used `a90_tcpctl run` and hit the known 10 second
  device-side run timeout. The runner now uses serial `a90ctl run` for the
  tracefs collector.
- A stale-event hardening fix disables an existing tracefs event before removal
  and re-registration. This protects retries after a killed collector.
- The gate uses tracefs dynamic uprobes only; `bpf_attach_executed=False`.

## Safety

- No Wi-Fi HAL, scan/connect/link-up, DHCP, route, credential use, or external
  ping executed.
- No `mdm_helper` executed.
- No eSoC open/ioctl, GPIO write, partition write, flash, or reboot executed.
- Tracefs events were removed cleanly; no register/enable/cleanup failure
  remained in the passing run.
- Device remained healthy: post-run `selftest` reported `fail=0`; `netservice`
  stayed USB-local.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_cnss_peripheral_tracefs_live_v1096.py
python3 scripts/revalidation/native_wifi_pm_cnss_peripheral_tracefs_live_v1096.py plan
python3 scripts/revalidation/native_wifi_pm_cnss_peripheral_tracefs_live_v1096.py \
  --allow-tracefs-mount \
  --allow-tracefs-write \
  --allow-vendor-mount \
  --allow-selinuxfs-mount \
  --allow-pm-service-trigger-observer \
  --allow-cnss-daemon-start \
  --assume-yes \
  run
python3 scripts/revalidation/a90ctl.py selftest
python3 scripts/revalidation/a90ctl.py netservice status
```

Result:

```text
decision: v1096-cnss-peripheral-client-path-hit-mdm3-still-offline
pass: True
selftest: fail=0
```
