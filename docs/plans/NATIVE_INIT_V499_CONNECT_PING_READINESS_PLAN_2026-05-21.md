# Native Init V499 Connect/Ping Readiness Plan

- Date: 2026-05-21 KST
- Scope: fail-closed readiness gate before native-init connect, DHCP, and external ping
- Status: implemented as a no-connect preflight plus helper v51 tool-surface probe
- Final Wi-Fi objective status: not achieved yet

## Purpose

V499 is the final readiness gate before a live native connect implementation.
It intentionally does not connect yet. It verifies that the chain has reached a
state where a later V500 can safely attempt:

```text
private active session -> supplicant association -> DHCP lease -> interface-bound external ping
```

## Reference Basis

- AOSP Wi-Fi architecture separates the vendor HAL from the supplicant HAL and
  hostapd HAL surfaces:
  <https://source.android.com/docs/core/connect/wifi-hal>
- `wpa_supplicant` is the Linux WPA/WPA2/WPA3 supplicant and supports Linux
  `nl80211/cfg80211` drivers:
  <https://w1.fi/wpa_supplicant/>
- The Linux wireless documentation describes `nl80211`/`cfg80211` as the modern
  userspace interface and notes regulatory/setup interaction through userspace:
  <https://wireless.docs.kernel.org/en/latest/en/developers/documentation/mac80211.html>

Conclusion: direct scan-only `nl80211` is useful for V497, but WPA2/WPA3
association should route through `wpa_supplicant` rather than trying to
hand-code authentication/key negotiation in the execns helper.

## Preconditions

V499 requires all of:

- V497 decision `v497-native-scan-only-pass-redacted`;
- V498 decision `v498-native-private-policy-ready` or
  `v498-native-private-policy-ready-awaiting-v497`;
- helper v51 deployed with `wifi-connect-tool-surface`;
- supplicant, DHCP client, `ip`, and `ping` tool surfaces present;
- native health `fail=0`.

## Helper v51 Tool Surface

`a90_android_execns_probe v51` adds read-only mode:

```text
--mode wifi-connect-tool-surface
```

It mounts the private system/vendor namespace and reports only file presence,
executable bits, mode, size, and readiness booleans for:

- `/vendor/bin/hw/wpa_supplicant`
- `/vendor/bin/wpa_supplicant`
- `/system/bin/wificond`
- `/system/bin/ip`
- `/system/bin/ping`
- `/system/bin/dhcpcd`
- `/system/bin/udhcpc`
- `/cache/bin/busybox`
- `/cache/bin/toybox`

It does not read credentials, start daemons, connect, request DHCP, mutate
routes, or ping externally.

## Decision Rules

| decision | meaning |
|---|---|
| `v499-native-connect-ping-readiness-ready` | V497, V498, helper v51, and connect tools are ready for V500 implementation |
| `v499-native-connect-ping-readiness-blocked` | one or more readiness preconditions are missing |
| `v499-native-connect-ping-readiness-plan-ready` | plan-only; no device command executed |

Only `v499-native-connect-ping-readiness-ready` should unlock V500 live
connect/DHCP/external-ping implementation.

## Next Version

V500 should be the first live connect implementation. It should require a new
explicit approval phrase and must:

- materialize temporary private supplicant config without logging raw secrets;
- start only bounded helper-owned processes;
- wait for association on the selected WLAN interface;
- run a bounded DHCP client;
- ping an allowlisted external IP through that interface;
- always clean up supplicant, DHCP, addresses/routes, and temporary secret files.
