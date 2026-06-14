# Native Init V847 subsys_esoc0 Char-Device Open Smoke Report

## Result

- decision: `v847-subsys-esoc0-open-blocked-or-pending`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_subsys_esoc0_char_open_smoke_v847.py`
- evidence: `tmp/wifi/v847-subsys-esoc0-char-open-smoke/`

## Scope

V847 performed a bounded live mutation: it created `/dev/subsys_esoc0`, started
one background open/hold attempt, captured state/dmesg evidence, removed the
node, and rebooted for cleanup. It did not open raw `/dev/esoc*`, write
sysfs/GPIO/debugfs, bind/unbind drivers, load/unload modules, start daemons,
start service-manager, start Wi-Fi HAL, scan/connect, use credentials, run DHCP,
change routes, ping externally, write boot images, write partitions, or flash a
custom kernel.

## Key Signals

| Signal | Value |
| --- | --- |
| Preflight health | stock native v724, `BOOT OK`, selftest `fail=0` |
| Materialized node | `/dev/subsys_esoc0`, char `236:9` |
| Holder PID | present |
| Holder open status | no `holder.opened=1` within bounded window |
| Kernel entry | `__subsystem_get: esoc0 count:0` |
| Firmware name change | `Changing subsys fw_name to esoc0` |
| mdm3 state | remained `OFFLINING` |
| MHI/PCIe markers | absent |
| WLFW/BDF/`wlan0` markers | absent |
| Kernel warning/panic/fatal | no new warning/panic/fatal marker in V847 focus output |
| Cleanup | node removed, cleanup reboot restored native health |

## Interpretation

The char-device path is real: opening `/dev/subsys_esoc0` reached
`__subsystem_get(esoc0)` and began the subsystem start path. It did not report
open success before the observation window ended, and no MHI, WLFW, BDF,
FW-ready, or `wlan0` markers appeared. This narrows the blocker below
`subsystem_get()` and before any visible MHI/WLFW progression.

The next step should not be HAL/connect or a blind longer hold. V848 should
first classify the exact open-block boundary from V847 and OSRC source, then
decide whether a follow-up live run needs in-window task `wchan`/stack capture,
additional ext-mdm source/provider evidence, or a different source-backed
trigger.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_subsys_esoc0_char_open_smoke_v847.py
python3 scripts/revalidation/native_wifi_subsys_esoc0_char_open_smoke_v847.py \
  --out-dir tmp/wifi/v847-plan-check \
  plan
python3 scripts/revalidation/native_wifi_subsys_esoc0_char_open_smoke_v847.py \
  --out-dir tmp/wifi/v847-subsys-esoc0-char-open-smoke \
  --allow-mknod \
  --allow-subsys-char-open \
  --allow-reboot-cleanup \
  --assume-yes \
  --hold-sec 8 \
  --observe-sec 10 \
  run
```

Result:

```text
decision: v847-subsys-esoc0-open-blocked-or-pending
pass: True
device_commands_executed: True
device_mutations: True
mknod_executed: True
subsys_char_open_executed: True
reboot_cleanup_executed: True
raw_esoc_open_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Next Gate

V848 should be host-only/source-backed first. It should classify where the
`subsys_esoc0` open blocks after `__subsystem_get(esoc0)` and before MHI/WLFW,
using V847 evidence and OSRC `subsys_start()`/ext-mdm/MHI hook paths.
