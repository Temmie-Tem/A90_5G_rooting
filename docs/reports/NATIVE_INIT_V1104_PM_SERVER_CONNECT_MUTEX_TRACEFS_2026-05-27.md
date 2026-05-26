# Native Init V1104 PM Server Connect Mutex Tracefs Report

## Summary

V1104 passed. The V1095 provider-positive PM observer window was replayed while
tracefs-only instruction uprobes were armed around the `pm-service` connect
helper at `0x95f4`.

Decision:

```text
v1104-pm-proxy-connect-unlocks-modem-cnss-lock-still-blocks
```

`pm-proxy` reaches the `pm-service` connect helper for the modem supported
peripheral record, locks the modem mutex, passes through the start-vote path,
unlocks the same mutex, and returns `0x0` from both the helper and outer connect
transaction.

`cnss-daemon` later reaches the same modem record helper lock call and still
does not receive a lock-return checkpoint. This rules out a simple
`pm-proxy` connect-path missing unlock. The remaining blocker is the modem
record mutex owner/waiter state after `pm-proxy` has returned.

## Evidence

| item | path |
| --- | --- |
| live wrapper | `scripts/revalidation/native_wifi_pm_server_connect_mutex_tracefs_live_v1104.py` |
| predecessor evidence | `tmp/wifi/v1103-pm-server-name-helper-tracefs-live/manifest.json` |
| live evidence | `tmp/wifi/v1104-pm-server-connect-mutex-tracefs-live/manifest.json` |
| live summary | `tmp/wifi/v1104-pm-server-connect-mutex-tracefs-live/summary.md` |
| collector transcript | `tmp/wifi/v1104-pm-server-connect-mutex-tracefs-live/host/pm-server-connect-mutex-tracefs-observer.txt` |

## Result

```text
tracefs_result: tracefs-uprobe-pass
hit_count: 151
cnss_daemon_hit_count: 1
pm_server_event_hit_count: 136
per_mgr_binder_server_hit_count: 100
per_mgr_pid: 3400
mdm3_state: OFFLINING
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

Connect helper classification:

```json
{
  "connect_complete_comms": [
    "Binder:3400_2"
  ],
  "cnss_server_register_last_label": "pm_server_name_helper_lock_call"
}
```

`pm-proxy` connect path:

```text
pm_server_connect_impl_entry
pm_server_connect_impl_mutex_ready mutex=...26198
pm_server_connect_impl_lock_call mutex=...26198
pm_server_connect_impl_lock_after lock_ret=0x0
pm_server_connect_impl_client_found
pm_server_connect_impl_state_check
pm_server_connect_impl_start_vote
pm_server_connect_impl_unlock_call mutex=...26198
pm_server_connect_impl_unlock_after unlock_ret=0x0
pm_server_connect_impl_return ret=0x0
pm_server_connect_impl_ret ret=0x0
pm_server_connect_ret ret=0x0
```

CNSS path:

```text
pm_server_register_name_helper_call entry=...26180
pm_server_name_helper_lock_call mutex=...26198
no pm_server_name_helper_lock_after
no modem strcmp
no register return
```

## Interpretation

The PM chain is now narrowed below V1103:

```text
PM provider visible
  -> pm-proxy register succeeds
  -> pm-proxy connect helper locks modem mutex
  -> pm-proxy connect helper unlocks modem mutex
  -> pm-proxy connect returns 0
  -> cnss-daemon client register enters
  -> cnss-daemon reaches modem record helper
  -> cnss-daemon blocks at pthread_mutex_lock(entry + 0x18)
  -> cnss-daemon register does not return
  -> cnss-daemon never calls connect/vote
  -> mdm3 still OFFLINING
  -> WLFW service 69 absent
  -> wlan0 absent
```

The next gate should inspect mutex owner/waiter state rather than continue
assuming the `pm-proxy` connect helper leaked the lock. Candidate directions:

- trace raw `pthread_mutex_lock@plt`/`pthread_mutex_unlock@plt` calls and
  returns for the modem mutex across all `pm-service` threads,
- sample `pm-service` Binder thread states while CNSS is blocked,
- classify whether another Binder thread enters the same modem mutex after CNSS
  and also waits.

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
python3 -m py_compile scripts/revalidation/native_wifi_pm_server_connect_mutex_tracefs_live_v1104.py
python3 scripts/revalidation/native_wifi_pm_server_connect_mutex_tracefs_live_v1104.py \
  --out-dir tmp/wifi/v1104-plan-validation \
  plan
python3 scripts/revalidation/native_wifi_pm_server_connect_mutex_tracefs_live_v1104.py \
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
decision: v1104-pm-proxy-connect-unlocks-modem-cnss-lock-still-blocks
pass: True
selftest: fail=0
```
