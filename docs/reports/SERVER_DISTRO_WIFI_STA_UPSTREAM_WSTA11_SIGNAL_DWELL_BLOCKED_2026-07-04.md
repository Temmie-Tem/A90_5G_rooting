# Server-Distro WSTA11 Signal Dwell Blocked

- Date: 2026-07-04
- Scope: associated-but-L3-degraded diagnostic before any D-public tunnel retry
- Native resident: `0.11.140 (v3384-server-distro-hardware-contract)`
- Public exposure: not started
- Final device state: native V3384, `selftest fail=0`

## Summary

WSTA11 kept the WSTA10 dwell gate and added redacted per-sample supplicant control and
signal markers.  The live result narrowed the persistence blocker: the Wi-Fi station stayed
associated and controllable, but L3 reachability degraded at the gateway-ping step before
DNS and TCP/443.

No API probe or cloudflared retry was run after the dwell failure.

## Source Changes

- `a90_dpublic_wifi_sta.sh`
  - samples `wpa_cli PING` and `SIGNAL_POLL` during each dwell sample;
  - records redacted RSSI, link speed, and frequency fields when supplicant reports them;
  - records a per-sample failure class instead of only a boolean;
  - records the first failing sample and first failing reason.
- `prepare_wsta3_sta_rootfs.py`
  - records `signal_dwell_present` so private rootfs summaries fail closed when the current
    diagnostic helper was not staged.
- Tests now assert the signal-dwell and first-failure markers.

## Live Evidence

WSTA11 used the guarded no-flash sequence:

```text
fresh native V3384 boot -> WSTA2 materialization pass -> D4 guarded userdata populate
-> no-clock Debian switch_root -> firstboot STA helper
```

The first D4 format attempt stopped before formatting because a stale e2fs toolroot device
node existed on SD runtime state.  After removing only that stale toolroot node, the retry
format and populate passed through the guarded D4 path with a journaled ext4 filesystem and
the WSTA11 rootfs marker.

Samples 1-5 passed with stable association/control and L3:

```text
wifi_sta_dwell_sample_1_wpa_state=COMPLETED
wifi_sta_dwell_sample_1_wpa_ping_rc=0
wifi_sta_dwell_sample_1_signal_poll_rc=0
wifi_sta_dwell_sample_1_gateway_ping_rc=0
wifi_sta_dwell_sample_1_dns_rc=0
wifi_sta_dwell_sample_1_tcp443_rc=0
wifi_sta_dwell_sample_1_failure=none
wifi_sta_dwell_sample_1_ok=1
...
wifi_sta_dwell_sample_5_wpa_state=COMPLETED
wifi_sta_dwell_sample_5_wpa_ping_rc=0
wifi_sta_dwell_sample_5_signal_poll_rc=0
wifi_sta_dwell_sample_5_gateway_ping_rc=0
wifi_sta_dwell_sample_5_dns_rc=0
wifi_sta_dwell_sample_5_tcp443_rc=0
wifi_sta_dwell_sample_5_failure=none
wifi_sta_dwell_sample_5_ok=1
```

The first failing sample was sample 6:

```text
wifi_sta_dwell_sample_6_wpa_state=COMPLETED
wifi_sta_dwell_sample_6_wpa_ping_rc=0
wifi_sta_dwell_sample_6_signal_poll_rc=0
wifi_sta_dwell_sample_6_carrier=1
wifi_sta_dwell_sample_6_default_route_iface=wlan0
wifi_sta_dwell_sample_6_gateway_ping_rc=1
wifi_sta_dwell_sample_6_gateway_arp_state=REACHABLE
wifi_sta_dwell_sample_6_gateway_arp_resolved=1
wifi_sta_dwell_sample_6_dns_rc=2
wifi_sta_dwell_sample_6_tcp443_rc=99
wifi_sta_dwell_sample_6_failure=gateway-ping
wifi_sta_dwell_sample_6_ok=0
wifi_sta_dwell_pass=0
wifi_sta_dwell_first_fail_sample=6
wifi_sta_dwell_first_fail_reason=gateway-ping
wifi_sta_decision=wifi-sta-dwell-failed
```

Interpretation: this is not the WSTA7/WSTA9 raw association failure.  The supplicant control
socket still answered `PING`, `wpa_state` remained `COMPLETED`, carrier stayed up, the default
route still pointed at `wlan0`, and gateway neighbor state was still resolved.  The first
observable break was gateway ping failure, with DNS failure following it.

Tunnel gate markers remained closed:

```text
tunnel_wifi_sta_gate_required=1
tunnel_wifi_sta_gate_decision=wifi-sta-dwell-failed
tunnel_wifi_sta_gate_ok=0
tunnel_started=manual
tunnel_decision=manual
```

## Hygiene

- No public tunnel was started.
- No SSID, PSK, BSSID, MAC, DHCP lease, Wi-Fi private address, gateway, DNS server, public
  URL, generated hostname, or raw API response is recorded in this report.
- Raw transcripts remain under `workspace/private/runs/`.
- The device ended on native V3384 with `selftest: pass=12 warn=1 fail=0`.

## Next

WSTA12 should diagnose the gateway reachability boundary before adding policy:

- keep the WSTA11 markers;
- add explicit gateway ping count/timing and neighbor refresh observations;
- compare DHCP lease/router state before and after the first gateway-ping failure;
- optionally test one bounded ARP or gateway keepalive candidate only after the trace proves
  it is addressing the observed failure;
- do not retry the API probe or cloudflared until the dwell window passes.
