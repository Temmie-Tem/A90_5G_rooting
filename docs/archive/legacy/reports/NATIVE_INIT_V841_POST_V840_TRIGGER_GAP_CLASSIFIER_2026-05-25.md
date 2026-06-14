# Native Init V841 Post-V840 Trigger Gap Classifier Report

## Result

- decision: `v841-cnss-wlfw-start-gap-selected`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_post_v840_trigger_gap_classifier_v841.py`
- evidence: `tmp/wifi/v841-post-v840-trigger-gap-classifier/`

## Scope

V841 was host-only. It did not contact the device, start daemons, start
service-manager, start Wi-Fi HAL, scan/connect, use credentials, run DHCP,
change routes, ping externally, write sysfs/debugfs, write boot images, write
partitions, or flash a custom kernel.

## Key Signals

| Signal | Value |
| --- | --- |
| Android V622 lower path | service `180/74`, `wlfw_start`, WLAN-PD, QMI connected, BDF, FW-ready, `wlan0` present |
| Native V840 lower path | service `180/74`, CNSS netlink, CLD80211 present |
| Native V840 missing path | no `wlfw_start`, no WLAN-PD indication, no QMI connected, no BDF, no FW-ready, no `wlan0` |
| Android `service180 -> wlfw_start` | `1415.75 ms` |
| Android `service180 -> wlan_pd` | `2427.362 ms` |
| Android `service180 -> sysmon_esoc0` | `4491.638 ms` |
| `rfs_access` branch | closed by V618 |
| `mdm_helper` branch | closed by V746/V764 |

## Interpretation

V840 closes the combined provider-first CNSS retry plus prearmed listener timing
window. The remaining blocker is earlier than WLAN-PD `UP` and lower than Wi-Fi
HAL/link bring-up.

The important ordering correction is that Android V622 reaches `wlfw_start`
before the WLAN-PD indication, while `sysmon_esoc0` appears after WLAN-PD. That
makes `sysmon_esoc0` a downstream or parallel signal in the current evidence,
not the next prerequisite to chase.

The strongest next target is the gap where native `cnss-daemon` reaches
netlink/CLD80211 but never enters the WLFW start path.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_post_v840_trigger_gap_classifier_v841.py
python3 scripts/revalidation/native_wifi_post_v840_trigger_gap_classifier_v841.py \
  --out-dir tmp/wifi/v841-plan-check \
  plan
python3 scripts/revalidation/native_wifi_post_v840_trigger_gap_classifier_v841.py \
  --out-dir tmp/wifi/v841-post-v840-trigger-gap-classifier \
  run
```

Result:

```text
decision: v841-cnss-wlfw-start-gap-selected
pass: True
device_commands_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Next Gate

V842 should classify the Android/native `cnss-daemon` pre-WLFW launch/runtime
contract before any Wi-Fi HAL, scan/connect, DHCP/routes, credentials, or
external ping. Focus on argv/init service contract, property inputs, SELinux
domain, inherited file descriptors, Binder/vndbinder context, child lifetime,
and exit reason.
