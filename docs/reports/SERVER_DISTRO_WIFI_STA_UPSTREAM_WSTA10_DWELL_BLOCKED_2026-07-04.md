# Server-Distro WSTA10 STA/L3 Dwell Blocked

- Date: 2026-07-04
- Scope: Debian STA/L3 persistence gate before any D-public tunnel retry
- Native resident: `0.11.140 (v3384-server-distro-hardware-contract)`
- Public exposure: not started
- Final device state: native V3384, `selftest fail=0`

## Summary

WSTA10 closed the stale-marker ambiguity from WSTA9 and proved the current blocker is
post-association L3 persistence.  The Debian STA helper now emits a per-run marker id,
phase events, and six dwell samples after the initial L3 pass.  The D-public firstboot
profile also gates cloudflared in WSTA mode: if `/etc/a90-dpublic/wifi-sta-enable` is
present, the tunnel starts only after the latest `wifi_sta_decision=wifi-sta-pass`.

Live result: the appliance reached initial association, DHCP, default route on `wlan0`,
gateway ARP, DNS, and TCP/443, but the dwell window failed at the final sample.  No API
probe or cloudflared retry was run after the dwell failure.

## Source Changes

- `a90_dpublic_wifi_sta.sh`
  - adds `wifi_sta_run_id`;
  - adds ordered `wifi_sta_event=<run>:<seq>:<phase>:<uptime_ms>` marker lines;
  - requires a six-sample dwell window before final `wifi-sta-pass`;
  - records sample-indexed dwell state for carrier, default route, gateway ARP, DNS, and TCP/443;
  - returns `wifi-sta-dwell-failed` when a later sample regresses.
- `a90_dpublic_firstboot.sh`
  - records `tunnel_wifi_sta_gate_*`;
  - blocks quick tunnel start in WSTA mode unless the latest Wi-Fi decision is `wifi-sta-pass`;
  - preserves non-WSTA manual/no-tunnel behavior.
- The WSTA rootfs preparer summary now records `dwell_gate_present`.

## Live Evidence

WSTA10 used the same guarded sequence as WSTA8/WSTA9:

```text
fresh native V3384 boot -> WSTA2 materialization pass -> D4 guarded userdata populate
-> no-clock Debian switch_root -> firstboot STA helper
```

The WSTA2 materialization gate passed with `wlan0_admin_up=true`.

Initial firstboot STA markers:

```text
wifi_sta_event=<run>:9:l3-initial-pass:<uptime_ms>
wifi_sta_wpa_completed=1
wifi_sta_carrier_up=1
wifi_sta_dhcp_rc=0
wifi_sta_default_route_iface=wlan0
wifi_sta_gateway_ping_rc=0
wifi_sta_dns_probe_rc=0
wifi_sta_tcp443_probe_rc=0
```

Dwell samples 1-5 remained good:

```text
wifi_sta_dwell_sample_1_ok=1
wifi_sta_dwell_sample_2_ok=1
wifi_sta_dwell_sample_3_ok=1
wifi_sta_dwell_sample_4_ok=1
wifi_sta_dwell_sample_5_ok=1
```

The final dwell sample failed while association still appeared complete:

```text
wifi_sta_dwell_sample_6_wpa_state=COMPLETED
wifi_sta_dwell_sample_6_carrier=1
wifi_sta_dwell_sample_6_default_route_iface=wlan0
wifi_sta_dwell_sample_6_gateway_arp_resolved=1
wifi_sta_dwell_sample_6_dns_rc=2
wifi_sta_dwell_sample_6_tcp443_rc=99
wifi_sta_dwell_sample_6_ok=0
wifi_sta_dwell_pass=0
wifi_sta_decision=wifi-sta-dwell-failed
```

Post-failure spot check still showed `wpa_state=COMPLETED` and carrier up, while DNS and
TCP remained failed.  This separates the next blocker from raw association failure: the
link can stay associated while the upstream L3 path degrades.

Tunnel gate markers:

```text
tunnel_wifi_sta_gate_required=1
tunnel_wifi_sta_gate_decision=wifi-sta-dwell-failed
tunnel_wifi_sta_gate_ok=0
tunnel_started=manual
tunnel_process_alive=0
tunnel_url_observed=0
tunnel_decision=manual
```

## Hygiene

- No public tunnel was started.
- No SSID, PSK, BSSID, MAC, DHCP lease, Wi-Fi private address, gateway, DNS server, public
  URL, generated hostname, or raw API response is recorded in this report.
- Raw transcripts remain under `workspace/private/runs/`.
- The device ended on native V3384 with `selftest: pass=12 warn=1 fail=0`.

## Next

WSTA11 should target associated-but-L3-degraded behavior:

- keep the WSTA10 phase/dwell markers;
- add redacted `wpa_cli SIGNAL_POLL` and `PING`/event-state samples during dwell;
- compare gateway ARP reachable versus gateway ping/DNS failure timing;
- test a bounded keepalive or reconnect policy only after the trace proves whether this is
  gateway reachability loss, resolver loss, DHCP route/lease behavior, or supplicant roaming state.
