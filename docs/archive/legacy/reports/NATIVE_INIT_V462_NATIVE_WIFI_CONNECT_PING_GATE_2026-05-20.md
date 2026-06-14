# Native Init V462 Native Wi-Fi Connect/Ping Gate

Date: 2026-05-20

## Summary

V462 added a fail-closed native Wi-Fi connect/ping gate for the next objective:
prove native init can connect Wi-Fi and pass an external ping.  The current
live native run does **not** satisfy that objective yet.

Current result:

```text
decision: v462-native-wifi-ping-blocked-no-wlan-surface
pass: False
reason: native init currently exposes no wlan interface and no wiphy surface
next_gate: recreate Android wlan driver/firmware readiness in native before credentials or ping
```

This is a hard pre-connect blocker.  V462 intentionally does not read Wi-Fi
credentials, scan, connect, or send an external ping until native init exposes a
real WLAN/wiphy surface.

## Implementation

- `scripts/revalidation/native_wifi_connect_ping_v462.py`
  - collects current native Wi-Fi surface evidence;
  - checks `wifiinv`, `wififeas`, `/sys/class/net`, `/proc/net/dev`,
    `/proc/net/wireless`, `/sys/class/ieee80211`, rfkill, firmware path, and
    Android ping/ip tool visibility;
  - blocks before credential handling if no WLAN/wiphy surface exists;
  - supports a future existing-connectivity ping proof only when a WLAN
    interface is visible and explicit packet-probe flags are present.

## Evidence

Plan:

```text
tmp/wifi/v462-native-wifi-connect-ping-plan-20260520-230603/
decision: v462-native-wifi-ping-plan-ready
pass: True
```

Preflight:

```text
tmp/wifi/v462-native-wifi-connect-ping-preflight-20260520-230603/
decision: v462-native-wifi-ping-blocked-no-wlan-surface
pass: False
```

Run mode with explicit packet-probe approval flags:

```text
tmp/wifi/v462-native-wifi-connect-ping-run-20260520-230620/
decision: v462-native-wifi-ping-blocked-no-wlan-surface
pass: False
credentials_read: False
scan_connect_executed: False
external_ping_executed: False
wifi_bringup_executed: False
```

Visible native interfaces:

```text
bond0
bonding_masters
dummy0
ip6_vti0
ip6tnl0
ip_vti0
lo
sit0
```

No `wlan*`, `swlan*`, `p2p*`, `wifi-aware*`, or `phy*` surface was visible.

## Validation

```text
python3 -m py_compile scripts/revalidation/native_wifi_connect_ping_v462.py
python3 scripts/revalidation/native_wifi_connect_ping_v462.py --out-dir tmp/wifi/v462-native-wifi-connect-ping-plan-20260520-230603 plan
python3 scripts/revalidation/native_wifi_connect_ping_v462.py --out-dir tmp/wifi/v462-native-wifi-connect-ping-preflight-20260520-230603 preflight
python3 scripts/revalidation/native_wifi_connect_ping_v462.py --out-dir tmp/wifi/v462-native-wifi-connect-ping-run-20260520-230620 --allow-external-ping --i-understand-native-wifi-packet-probe run
git diff --check
```

Static validation passed.  The live preflight/run commands intentionally
returned nonzero because the requested native Wi-Fi ping proof is not currently
available.

## Interpretation

Android Wi-Fi live validation already proved the AP, credentials, Android vendor
stack, and hardware can connect.  Native init is different: after rollback to
`A90 Linux init 0.9.61 (v319)`, the kernel/userland surface does not yet expose
the Wi-Fi network interface needed for scan/connect/DHCP/ping.

Therefore the next aligned task is not credential retry or external ping.  It is
native WLAN surface creation:

1. reproduce Android's `wlan_fw_ready` / driver readiness path under native;
2. identify the minimal Android services or kernel-side trigger that creates
   `wlan0` and `phy*`;
3. keep credentials and packet probes blocked until the interface exists;
4. once native `wlan0` exists, add bounded scan/connect/DHCP/ping execution.

## Next

Recommended next version: V463 native WLAN surface bring-up delta.

V463 should compare before/during/after native runtime attempts against the
Android timing evidence that showed `wlan_fw_ready`, driver logs, and `wlan0`
around Android boot.  The gate should still avoid credentials and external
traffic until `wlan0` or wiphy creation is proven.
