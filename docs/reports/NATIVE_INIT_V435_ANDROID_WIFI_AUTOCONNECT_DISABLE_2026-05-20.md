# Native Init V435 Android Wi-Fi Auto-connect Disable Report

Date: 2026-05-20

## Summary

V435 added a bounded Android Wi-Fi auto-connect disable proof and Android
handoff wrapper.  The corrected live handoff passed with:

```text
decision: v435-android-wifi-autoconnect-contained-pass
pass: True
reason: Wi-Fi disable completed and post-cleanup route/DNS/connectivity exposure was removed
wifi_disable_executed: True
wifi_bringup_executed: False
```

The first live run executed the disable command and removed route exposure, but
the original classifier treated stale `dumpsys connectivity` `NetworkRequest`
history as active Wi-Fi validation.  The classifier was corrected to require
active `NetworkAgentInfo{...WIFI CONNECTED...}` evidence, and the final live
run verified the contained state.

## Implementation

- `scripts/revalidation/wifi_android_autoconnect_disable_v435.py`
  - permits exactly one mutation: `cmd wifi set-wifi-enabled disabled`;
  - requires explicit Wi-Fi-disable approval flags;
  - captures pre/post Wi-Fi status, route, local route lookup, `wlan0`,
    connectivity, and listener state;
  - blocks scan/connect, credentials, server exposure, external probes,
    DHCP/routing mutation, rfkill/sysfs writes, module operations, `setprop`,
    and daemon starts.
- `scripts/revalidation/android_wifi_autoconnect_disable_handoff_v435.py`
  - boots Android, runs V435 after boot-complete settle, and restores native
    init v319 through rollback;
  - records whether the disable step actually executed.

## Static Validation

```text
python3 -m py_compile \
  scripts/revalidation/wifi_android_autoconnect_disable_v435.py \
  scripts/revalidation/android_wifi_autoconnect_disable_handoff_v435.py

git diff --check
```

Both checks passed.

Plan and dry-run evidence:

```text
tmp/wifi/v435-android-wifi-disable-plan-20260520-162248/
tmp/wifi/v435-android-wifi-disable-handoff-plan-20260520-162248/
tmp/wifi/v435-android-wifi-disable-handoff-dryrun-20260520-162248/
tmp/wifi/v435-android-wifi-disable-handoff-dryrun-classifierfix-20260520-162702/
```

## Live Evidence

Corrected live handoff:

```text
tmp/wifi/v435-android-wifi-disable-handoff-live-statefix-20260520-163102/
decision: v435-android-wifi-autoconnect-contained-pass
pass: True
device_commands_executed: True
device_mutations: True
wifi_disable_executed: True
wifi_bringup_executed: False
```

Collector evidence:

```text
tmp/wifi/v435-android-wifi-disable-handoff-live-statefix-20260520-163102/v435-android-wifi-autoconnect-disable-run/
decision: v435-android-wifi-autoconnect-contained-pass
pass: True
```

Superseded live attempts:

```text
tmp/wifi/v435-android-wifi-disable-handoff-live-20260520-162258/
  Disable command rc=0 and route exposure removed, but the original classifier
  counted stale NetworkRequest/history lines as active validated Wi-Fi.

tmp/wifi/v435-android-wifi-disable-handoff-live-classifierfix-20260520-162708/
  PASS after active NetworkAgentInfo classifier fix, but state summary still
  allowed enabled/disabled ambiguity from global setting lag.
```

Rollback/postflight after corrected live:

```text
version: A90 Linux init 0.9.61 (v319)
selftest: pass=11 warn=1 fail=0
status: rc=0 status=ok
```

Redaction scan on corrected evidence:

```text
WPA_PSK: none
targetConfigKey=": none
BSSID=<raw-mac>: none
SSID=": none
Wifi is connected to "<raw>": none
networkType=TYPE_*: none
```

## Containment Findings

Corrected final live state:

| Item | Pre | Post |
| --- | --- | --- |
| `enabled_by_status` | `False` | `False` |
| `disabled_by_status` | `True` | `True` |
| `wlan0_has_ip` | `False` | `False` |
| `default_route_wlan` | `False` | `False` |
| `route_get_wlan` | `False` | `False` |
| `connectivity_validated_wifi` | `False` | `False` |
| `dns_surface_wlan` | `False` | `False` |
| `global_listener_observed` | `False` | `False` |

Derived containment checks:

```text
route_exposure_gone: True
connectivity_gone: True
listener_safe: True
```

The first live run is still useful transition evidence: Android accepted
`cmd wifi set-wifi-enabled disabled` with `rc=0`, `cmd wifi status` reported
`Wifi is disabled`, `wlan0` IP disappeared, and `wlan0` default/local-route
evidence disappeared.  The later corrected live verifies that the disabled
state persists across another Android boot-complete handoff.

## Interpretation

V435 closes the immediate V434 containment requirement.  Android Wi-Fi
auto-connect can be intentionally disabled through the Android framework, and
the post-cleanup state removes the `wlan0` route/DNS/connectivity exposure that
V433 mapped.

This does not yet approve scan/connect or server exposure.  It proves that the
lab can enter a contained Android state first.

## Next

Recommended next cycle: V436 Android Wi-Fi disabled persistence check.

V436 should boot Android without issuing another disable command and verify that
Wi-Fi remains disabled and route/DNS/connectivity exposure remains absent.  If
that passes, the next policy choice is controlled re-enable versus native-side
Wi-Fi work.
