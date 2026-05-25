# Native Init V845 mdm3/ext-sdx50m Surface Snapshot Report

## Result

- decision: `v845-mdm3-ext-sdx50m-surface-captured`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_mdm3_ext_sdx50m_surface_snapshot_v845.py`
- evidence: `tmp/wifi/v845-mdm3-ext-sdx50m-surface-snapshot/`

## Scope

V845 was a live read-only run. It executed bounded serial read commands and
postflight health checks. It did not open raw `esoc0`, write GPIO/sysfs/debugfs,
write subsystem state, bind/unbind drivers, load/unload modules, start daemons,
start service-manager, start Wi-Fi HAL, scan/connect, use credentials, run DHCP,
change routes, ping externally, write boot images, write partitions, or flash a
custom kernel.

## Key Signals

| Signal | Value |
| --- | --- |
| Runtime | stock native `0.9.68 (v724)` |
| Pre/post health | `BOOT OK`, selftest `fail=0` |
| mdm3 sysfs | present |
| eSoC bus/sysfs | present |
| `subsys_esoc0` surface | present |
| mdm3 state | `OFFLINING` |
| mss state at idle | `OFFLINING` |
| Live devicetree mdm3 | present |
| Live devicetree compatible | `qcom,ext-sdx50m` present |
| AP→MDM GPIO property | present |
| MDM→AP GPIO property | present |
| `/sys/kernel/debug/gpio` | not readable in current namespace |
| GPIO 135/142 sysfs exports | not exported |
| `/dev/esoc*` raw node | absent |
| `/dev/subsys*` raw node | absent |
| Existing writable candidates | `esoc_link`, `esoc_link_info`, `esoc_name`, `subsys9/state`, `subsys0/state` |
| Runtime WLFW/BDF/`wlan0` markers | absent |

## Interpretation

The mdm3/ext-sdx50m control surface exists in sysfs and live devicetree, but the
external mdm3 side remains `OFFLINING` and no WLFW/BDF/FW-ready/`wlan0` runtime
markers are present. Raw `/dev/esoc*` and `/dev/subsys*` nodes are absent, so the
previous raw-open hazard remains blocked by policy and by the observed node
surface.

The important new finding is that multiple sysfs files are both readable and
writable from the current context. That does not make them safe to write. It
only narrows V846: classify the OSRC eSoC/subsystem state-control semantics for
those exact files before any bounded write or GPIO action.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm3_ext_sdx50m_surface_snapshot_v845.py
python3 scripts/revalidation/native_wifi_mdm3_ext_sdx50m_surface_snapshot_v845.py \
  --out-dir tmp/wifi/v845-plan-check \
  plan
python3 scripts/revalidation/native_wifi_mdm3_ext_sdx50m_surface_snapshot_v845.py \
  --out-dir tmp/wifi/v845-mdm3-ext-sdx50m-surface-snapshot \
  --allow-live-readonly \
  --assume-yes \
  run
```

Result:

```text
decision: v845-mdm3-ext-sdx50m-surface-captured
pass: True
device_commands_executed: True
device_mutations: False
esoc0_open_executed: False
gpio_write_executed: False
sysfs_write_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Next Gate

V846 should be host-only/source-backed first. It should map each writable V845
candidate to OSRC eSoC/subsystem code paths and choose at most one bounded,
rollback-safe live state transition later. HAL/connect, DHCP/routes, credentials,
external ping, and boot-image work remain blocked.
