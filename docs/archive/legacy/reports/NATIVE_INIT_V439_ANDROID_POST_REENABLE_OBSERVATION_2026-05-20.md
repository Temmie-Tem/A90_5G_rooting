# Native Init V439 Android Post-reenable Observation Report

Date: 2026-05-20

## Summary

V439 added and ran a post-reenable Android Wi-Fi observation with final cleanup.
The live handoff passed with:

```text
decision: v439-android-wifi-post-reenable-exposure-observed-cleanup-pass
pass: True
reason: post-reenable observation saw Wi-Fi route/DNS/connectivity exposure; cleanup containment passed
wifi_disable_executed: True
wifi_bringup_executed: False
```

V439 did not enable Wi-Fi.  It booted Android after V438 had set framework
Wi-Fi enabled, observed that Android immediately auto-connected and exposed
`wlan0` IP/route/DNS/validated connectivity, then ran cleanup disable and
restored native v319.

## Implementation

- `scripts/revalidation/wifi_android_post_reenable_observation_v439.py`
  - samples post-reenable Android Wi-Fi state over a bounded window;
  - forbids Wi-Fi enable, scan/connect, credentials, server exposure, external
    probes, routing mutation, sysfs/rfkill writes, module operations, `setprop`,
    and direct daemon starts;
  - optionally performs only one cleanup mutation:
    `cmd wifi set-wifi-enabled disabled`.
- `scripts/revalidation/android_wifi_post_reenable_handoff_v439.py`
  - boots Android through the known baseline boot image;
  - waits for boot-complete;
  - runs the V439 collector;
  - restores native v319.

## Static Validation

```text
python3 -m py_compile \
  scripts/revalidation/wifi_android_post_reenable_observation_v439.py \
  scripts/revalidation/android_wifi_post_reenable_handoff_v439.py

git diff --check
```

Both checks passed.

Plan and dry-run evidence:

```text
tmp/wifi/v439-android-wifi-post-reenable-plan-20260520-170726/
tmp/wifi/v439-android-wifi-post-reenable-handoff-plan-20260520-170726/
tmp/wifi/v439-android-wifi-post-reenable-handoff-dryrun-20260520-170726/
```

## Live Evidence

Live evidence:

```text
tmp/wifi/v439-android-wifi-post-reenable-handoff-live-20260520-170736/
tmp/wifi/v439-android-wifi-post-reenable-handoff-live-20260520-170736/v439-android-wifi-post-reenable-observation-run/
```

Sample summary:

| Item | Value |
| --- | --- |
| `sample_count` | `7` |
| `enabled_seen` | `True` |
| `disabled_seen` | `False` |
| `wifi_connected_seen` | `True` |
| `exposure_seen` | `True` |
| `first_exposure_phase` | `sample-000` |
| `listener_safe` | `True` |

All seven samples, from `sample-000` through `sample-006`, showed:

| Item | Value |
| --- | --- |
| `enabled_by_status` | `True` |
| `disabled_by_status` | `False` |
| `wifi_connected` | `True` |
| `wlan0_has_ip` | `True` |
| `default_route_wlan` | `True` |
| `route_get_wlan` | `True` |
| `connectivity_validated_wifi` | `True` |
| `dns_surface_wlan` | `True` |
| `global_listener_observed` | `False` |

Cleanup summary:

| Item | Value |
| --- | --- |
| `cleanup_requested` | `True` |
| `cleanup_ok` | `True` |
| `cleanup_contained` | `True` |
| `cleanup.enabled_by_status` | `False` |
| `cleanup.disabled_by_status` | `True` |
| `cleanup.wlan0_has_ip` | `False` |
| `cleanup.default_route_wlan` | `False` |
| `cleanup.route_get_wlan` | `False` |
| `cleanup.connectivity_validated_wifi` | `False` |
| `cleanup.dns_surface_wlan` | `False` |
| `cleanup.global_listener_observed` | `False` |

The cleanup `wifi_connected` parser marker remained true because filtered
`dumpsys wifi` kept historical connected-state log lines after disable.  Active
network exposure was nevertheless removed by the direct IP/route/DNS/connectivity
checks above.

## Rollback Verification

Post-live native checks:

```text
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py --json selftest
python3 scripts/revalidation/a90ctl.py --json status
```

Results:

```text
A90 Linux init 0.9.61 (v319)
selftest: pass=11 warn=1 fail=0
exposure: guard=ok warn=0 fail=0 ncm=absent tcpctl=stopped rshell=stopped boundary=usb-local
```

Redaction scan over the live evidence passed for Wi-Fi credential, SSID/BSSID,
connection-name, and network-type patterns.

## Interpretation

V439 changes the Wi-Fi branch conclusion:

- Android-managed Wi-Fi is functional after framework re-enable.
- Saved Android auto-connect can immediately bring up `wlan0`, default routing,
  DNS, and validated connectivity on a fresh Android boot.
- No global listening sockets were observed during the sample window.
- Cleanup disable can remove active route/DNS/connectivity exposure again.

This proves Wi-Fi functionality exists in the Android-managed path, but it also
confirms the security model concern: enabling Android Wi-Fi creates an external
network surface before any serverization work.

## Next

Recommended next cycle: V440 Android Wi-Fi control policy after proven
auto-connect.

V440 should decide the operating mode before more testing:

- contained lab mode: keep Android Wi-Fi disabled unless a specific Wi-Fi test
  is running;
- exposure-aware Android Wi-Fi mode: allow auto-connect only for bounded
  read-only stability observations;
- explicit scan/connect mode: design credential handling and target-network
  allowlisting before issuing any scan/connect commands.

Server exposure and native service binding should remain blocked until V440
chooses and documents the policy.
