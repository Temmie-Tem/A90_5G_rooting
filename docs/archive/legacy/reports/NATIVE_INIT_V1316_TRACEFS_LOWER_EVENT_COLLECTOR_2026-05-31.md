# Native Init V1316 Tracefs Lower-Event Collector

## Summary

- Cycle: `V1316`
- Type: bounded live collector
- Decision: `v1316-critical-first-power-on-events-captured`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1316-tracefs-lower-event-collector-live/manifest.json`
  - `tmp/wifi/v1316-tracefs-lower-event-collector-live/summary.md`
- Script: `scripts/revalidation/native_wifi_tracefs_lower_event_collector_live_v1316.py`

V1316 extends the V1315 tracefs preflight into the bounded late `per_proxy`
PM-service path. It enables selected lower tracefs static events only during the
existing observation window, confirms `pm-service` reaches `/dev/subsys_esoc0`
/ `mdm_subsys_powerup`, records counts and sample lines, disables the events,
and cleans up tracefs.

## Result

| field | value |
| --- | --- |
| tracefs result | `tracefs-uprobe-pass` |
| PM-service eSoC reach basis | `top-observer-pm-service-actor-esoc0-attempt` |
| lower events enabled | `18` |
| total lower event count | `81174` |
| critical lower event count | `3936` |
| noise lower event count | `77238` |
| enable failures | `{}` |
| disable failures | `{}` |
| Wi-Fi bring-up executed | `false` |

Group counts:

| group | count |
| --- | --- |
| `regulator` | `2310` |
| `gpio` | `1582` |
| `msm_pil_event` | `44` |
| `power` | `0` |
| `irq` | `68124` |
| `clk` | `9114` |

Critical lower tracefs activity is visible during the `mdm_subsys_powerup`
window. This means the provider-internal first-power-on path is not completely
silent; the next step is to classify captured event lines and distinguish
SDX50M-relevant regulator/GPIO/PIL activity from background UFS/USB/timer noise.

## Decision

V1316 closes the question "can stock tracefs observe lower provider-internal
first-power-on activity during the bounded PM-service path?" with `yes`.

V1317 should parse and classify the captured trace lines by event content,
actor, device/name field, and timing. Priority targets:

- `regulator_*` names that may map to PCIe, MHI, SDX50M, or WLAN power rails
- `gpio_direction` / `gpio_value` line identifiers around the power-up window
- `msm_pil_event:pil_notif` content and subsystem names
- whether `power:*` being zero is meaningful or only unavailable for this path
- whether IRQ/clock noise should be dropped from the next live collector

## Safety

No PMIC write, userspace GPIO line request/hold, direct eSoC ioctl, direct GDSC
write, Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external
ping, flash, boot image write, or partition write occurred. Tracefs writes were
limited to bounded enable/disable of selected tracing events, and cleanup
disabled all selected events.
