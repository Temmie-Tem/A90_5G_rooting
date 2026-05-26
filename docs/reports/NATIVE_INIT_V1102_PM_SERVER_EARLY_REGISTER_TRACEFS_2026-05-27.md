# Native Init V1102 PM Server Early Register Tracefs Report

## Summary

V1102 passed. The V1095 provider-positive PM observer window was replayed while
tracefs-only instruction uprobes were armed across the `pm-service` register
implementation from `0x6048` to `0x60cc`.

Decision:

```text
v1102-cnss-server-register-no-return-at-pm_server_register_name_helper_call
```

`pm-proxy` remains the positive control. It iterates the supported peripheral
list, compares `SDX50M` against requested `modem`, advances to the second entry,
compares `modem` against `modem`, reaches `pm_server_register_match`, and
returns `0x0`.

`cnss-daemon` follows the same path through the first `SDX50M` entry. It then
advances to the second list node and calls the name helper for that entry, but
the helper does not return before bounded cleanup. The blocker is now narrowed
to the supported-peripheral entry helper at `0x9538` when invoked for the
second/modem list entry in the CNSS Binder thread.

## Evidence

| item | path |
| --- | --- |
| live wrapper | `scripts/revalidation/native_wifi_pm_server_early_register_tracefs_live_v1102.py` |
| predecessor evidence | `tmp/wifi/v1101-pm-server-register-path-tracefs-live/manifest.json` |
| live evidence | `tmp/wifi/v1102-pm-server-early-register-tracefs-live/manifest.json` |
| live summary | `tmp/wifi/v1102-pm-server-early-register-tracefs-live/summary.md` |
| collector transcript | `tmp/wifi/v1102-pm-server-early-register-tracefs-live/host/pm-server-early-register-tracefs-observer.txt` |

## Result

```text
tracefs_result: tracefs-uprobe-pass
hit_count: 49
cnss_daemon_hit_count: 1
pm_server_event_hit_count: 44
per_mgr_binder_server_hit_count: 44
per_mgr_pid: 2744
mdm3_state: OFFLINING
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

CNSS server-side register classification:

```json
{
  "cnss_server_register_last_label": "pm_server_register_name_helper_call",
  "cnss_server_register_hits_by_comm": {
    "Binder:2744_3": {
      "pm_server_register_entry": 1,
      "pm_server_register_loop_node": 2,
      "pm_server_register_name_helper_call": 2,
      "pm_server_register_name_helper_return": 1,
      "pm_server_register_strcmp_result": 1
    }
  }
}
```

Observed string comparisons:

```text
pm-proxy:
  candidate="SDX50M" requested="modem" strcmp_ret=0xffffffffffffff98
  candidate="modem"  requested="modem" strcmp_ret=0x0

cnss-daemon:
  candidate="SDX50M" requested="modem" strcmp_ret=0xffffffffffffff98
  second list node name helper call does not return
```

Host-only disassembly of the helper at `0x9538` shows it takes the peripheral
entry pointer, locks the mutex at `entry + 0x18`, unlocks it, and returns the
entry pointer:

```text
0x9538: function entry
0x9544: x20 = x0 + 0x18
0x9550: pthread_mutex_lock(entry + 0x18)
0x9558: pthread_mutex_unlock(entry + 0x18)
0x955c: return entry pointer
```

## Interpretation

The PM chain is now narrowed below V1101:

```text
PM provider visible
  -> pm-proxy register/connect positive control succeeds
  -> cnss-daemon client register enters
  -> pm-service server register entry hit
  -> supported list first entry SDX50M is readable
  -> SDX50M != modem, loop advances
  -> second supported list node reached
  -> helper at 0x9538 called for second/modem entry
  -> helper does not return
  -> no modem strcmp/match for CNSS
  -> cnss-daemon register does not return
  -> cnss-daemon never calls connect/vote
  -> mdm3 still OFFLINING
  -> WLFW service 69 absent
  -> wlan0 absent
```

The next gate should trace helper `0x9538` directly for the second/modem entry.
The most likely immediate blocker is `pthread_mutex_lock(entry + 0x18)` on the
modem peripheral record while `pm-proxy` already holds or influences that
record's state.

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
python3 -m py_compile scripts/revalidation/native_wifi_pm_server_early_register_tracefs_live_v1102.py
python3 scripts/revalidation/native_wifi_pm_server_early_register_tracefs_live_v1102.py \
  --out-dir tmp/wifi/v1102-plan-validation \
  plan
python3 scripts/revalidation/native_wifi_pm_server_early_register_tracefs_live_v1102.py \
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
decision: v1102-cnss-server-register-no-return-at-pm_server_register_name_helper_call
pass: True
selftest: fail=0
```
