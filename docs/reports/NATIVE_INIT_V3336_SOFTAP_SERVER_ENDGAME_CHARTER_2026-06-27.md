# Native Init V3336 SoftAP Server-Endgame Charter

## Summary

- Cycle: `V3336`
- Decision: `v3336-softap-server-endgame-chartered`
- Scope: host-only source/docs recon after GPU Z3 close.
- Device action: none.
- Flash action: none.
- Secrets/network identifiers: none used; no SSID, PSK, client identifier, MAC, BSSID, or concrete IP address is recorded.

V3336 pivots the active frontier from the closed GPU epic to the SoftAP server-endgame. The target is
not the existing phone/router transfer lab where A90 joins a Wi-Fi network as a client. The target is
A90 as the appliance: it brings up a private WPA2 SoftAP, runs a bounded local transfer endpoint,
accepts a client, proves download/upload SHA integrity, cleans up, and leaves native-init health green.

## Current Surface

- `docs/operations/NATIVE_INIT_WIFI_LIFECYCLE_COMMANDS.md` defines client-mode commands:
  `wifi status`, `scan`, `connect`, `dhcp`, `ping`, `cleanup`, profile, autoconnect, and config.
- `workspace/public/src/native-init/a90_wifi.c` dispatches the same client-mode surface and has no
  `softap` or AP-mode command.
- `wifiinv` / `wififeas` are available from the shell dispatcher and are the right read-only inventory
  entrypoints before AP-mode work.
- `a90_wifiinv.c` already searches for `hostapd`, `wpa_supplicant`, Wi-Fi firmware, vendor paths, and
  related assets, but does not start AP daemons.
- `docs/operations/A90_PHONE_WIFI_TRANSFER_SERVER.md` is a useful transfer-test pattern, but it assumes
  A90 is a client on the same router/LAN as a phone-side Termux server.
- `docs/operations/WIFI_TARGET_ALLOWLIST_V442.example.json` has `allow_server_exposure=false`; SoftAP
  work therefore needs an explicit bounded AP/server exposure contract before any daemon start.
- `docs/plans/NATIVE_INIT_V210_VENDOR_WIFI_CNSS_ASSET_CLASSIFIER_PLAN_2026-05-13.md` already records
  vendor hostapd/supplicant/CNSS asset categories and the guardrail that inventory may mention
  `hostapd` without starting it.

## Decision

SoftAP is a new active feature axis, not a continuation of client-mode `wifi connect`.

The implementation should be additive and explicit:

- keep existing client-mode commands unchanged;
- add a separate `wifi softap ...` surface rather than overloading `wifi connect` or autoconnect;
- require a dry-run/config-materialization stage before any AP daemon start;
- keep SSID/PSK material in `workspace/private/` on host and `/cache/a90-softap/` on device only;
- expose only redacted booleans, hashes, and decision labels in public reports;
- provide cleanup as a first-class command before live AP bring-up is considered complete;
- do not bridge/NAT to upstream networks by default.

## Ladder

### S0 Host-Only Charter/Recon

Done in V3336. Deliverable is this report plus the GOAL update.

### S1 Read-Only Live AP/Server Inventory

Run on the current resident without flashing if bridge health is clean:

```text
a90_bridge.py status --json
a90ctl version
a90ctl status
a90ctl selftest verbose
a90ctl wifi status
a90ctl wifiinv summary
a90ctl wifiinv full
a90ctl wififeas gate
a90ctl wififeas full
```

Allowed additions for S1 are read-only binary/applet presence checks for hostapd and candidate local
server/DHCP helpers. S1 must not scan, connect, run DHCP, ping, change interface mode, assign an address,
start hostapd, start a DHCP server, or expose a listener.

### S2 Source Contract and Dry-Run Config

Add a `wifi softap` command group with at least:

```text
wifi softap status
wifi softap plan
wifi softap prepare [profile]
wifi softap cleanup
```

`prepare` writes only bounded runtime config under `/cache/a90-softap/` and validates that required
assets are present. It must not start hostapd, assign addresses, or expose a server.

### S3 Bounded AP Bring-Up

After S1/S2 pass, add an explicit AP start command. Required properties:

- stop or reject conflicting client supplicant state first;
- configure AP mode only on the intended WLAN interface;
- assign only a private local AP address from private runtime config;
- start hostapd with private generated config;
- start a bounded DHCP service if available, or report `softap-dhcp-helper-missing`;
- default to no WAN bridge and no NAT;
- write a machine-readable runtime summary;
- implement cleanup that stops child workers and removes address/route/runtime residue.

### S4 Transfer Server Proof

Expose a bounded local transfer endpoint on the SoftAP and prove:

- client joins the AP;
- client downloads a generated test file from A90 and SHA matches;
- client uploads a generated test file to A90 and SHA matches;
- server and AP cleanup succeed;
- follow-up `selftest fail=0`.

Public artifacts must redact SSID, PSK, client identifiers, peer MAC/BSSID, and concrete network
addresses.

## Safety Notes

- No boot artifact was built.
- No flash was run.
- No live Wi-Fi action was run.
- No credentials were read.
- No server listener was exposed.
- No forbidden partition, PMIC, regulator, GDSC, GPIO, backlight, panel, or raw block path is touched.

## Next Unit

V3337 should be S1: read-only live AP/server inventory on the current resident, gated by bridge health
and native-init `version` / `status` / `selftest`. If S1 shows missing hostapd or DHCP/server helpers,
the next source unit should materialize the smallest private helper bundle or report the exact missing
asset before attempting AP mode.
