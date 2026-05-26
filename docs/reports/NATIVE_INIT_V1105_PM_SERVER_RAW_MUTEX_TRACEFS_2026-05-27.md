# Native Init V1105 PM Server Raw Mutex Tracefs Report

## Summary

V1105 passed. The V1095 provider-positive PM observer window was replayed while
tracefs-only uprobes were armed on both the V1104 `pm-service` connect helper
and the raw `pthread_mutex_lock@plt`/`pthread_mutex_unlock@plt` entries.

Decision:

```text
v1105-cnss-raw-pthread-lock-pending-on-modem-mutex
```

`pm-proxy` again completed the modem connect path through lock, start-vote,
unlock, helper return, and outer connect return. CNSS then reached the modem
record name helper and issued a raw `pthread_mutex_lock` call on the modem
record mutex, but no matching raw lock return was captured for that CNSS Binder
thread.

## Evidence

| item | path |
| --- | --- |
| live wrapper | `scripts/revalidation/native_wifi_pm_server_raw_mutex_tracefs_live_v1105.py` |
| predecessor evidence | `tmp/wifi/v1104-pm-server-connect-mutex-tracefs-live/manifest.json` |
| live evidence | `tmp/wifi/v1105-pm-server-raw-mutex-tracefs-live/manifest.json` |
| live summary | `tmp/wifi/v1105-pm-server-raw-mutex-tracefs-live/summary.md` |
| collector transcript | `tmp/wifi/v1105-pm-server-raw-mutex-tracefs-live/host/pm-server-raw-mutex-tracefs-observer.txt` |

## Result

```text
tracefs_result: tracefs-uprobe-pass
hit_count: 216
raw_mutex_event_count: 65
cnss_daemon_hit_count: 1
pm_server_event_hit_count: 201
per_mgr_binder_server_hit_count: 136
per_mgr_pid: 4668
mdm3_state: OFFLINING
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

CNSS raw pending lock:

```json
{
  "Binder:4668_3": [
    {
      "pid": "4680",
      "mutex": "0xb400007fbc226198",
      "label": "pm_raw_pthread_mutex_lock_call"
    }
  ]
}
```

Positive control:

```text
connect_complete_comms: ["Binder:4668_2"]
cnss_server_register_last_label: pm_server_name_helper_lock_call
```

## Interpretation

The blocker is now below the `pm-service` helper boundary and at the raw mutex
wait boundary:

```text
PM provider visible
  -> pm-proxy register succeeds
  -> pm-proxy connect helper locks modem mutex
  -> pm-proxy connect helper unlocks modem mutex
  -> pm-proxy connect returns 0
  -> cnss-daemon client register enters
  -> cnss-daemon reaches modem record helper
  -> cnss-daemon calls pthread_mutex_lock(modem mutex)
  -> no raw pthread_mutex_lock return for CNSS Binder thread
  -> cnss-daemon register does not return
  -> cnss-daemon never calls connect/vote
  -> mdm3 still OFFLINING
  -> WLFW service 69 absent
  -> wlan0 absent
```

V1105 rules out a pure helper instrumentation artifact. The next gate should
sample the blocked `pm-service` Binder thread state directly, especially
`/proc/<tid>/wchan`, stack, and futex/mutex ownership surface if available.

## Safety

- No Wi-Fi HAL, scan/connect/link-up, DHCP, route, credential use, or external
  ping executed.
- No `mdm_helper` executed.
- No eSoC open/ioctl, GPIO write, partition write, flash, or reboot executed.
- No BPF attach executed.
- Tracefs events were removed cleanly; no register/enable/cleanup failure
  remained in the passing run.
- Device remained healthy: post-run `selftest` reported `fail=0`; `netservice`
  stayed USB-local.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_server_raw_mutex_tracefs_live_v1105.py
python3 scripts/revalidation/native_wifi_pm_server_raw_mutex_tracefs_live_v1105.py \
  --out-dir tmp/wifi/v1105-plan-validation \
  plan
python3 scripts/revalidation/native_wifi_pm_server_raw_mutex_tracefs_live_v1105.py \
  --allow-tracefs-mount \
  --allow-tracefs-write \
  --allow-vendor-mount \
  --allow-selinuxfs-mount \
  --allow-pm-service-trigger-observer \
  --allow-cnss-daemon-start \
  --assume-yes \
  run
```

Result:

```text
decision: v1105-cnss-raw-pthread-lock-pending-on-modem-mutex
pass: True
selftest: fail=0
```
