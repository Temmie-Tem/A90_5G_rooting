# Native Init V497 Scan-Only Surface Plan

- Date: 2026-05-21 KST
- Scope: bounded native-init scan-only proof inside the helper-owned active session
- Status: implemented as a gated helper/host runner; live run requires exact approval
- Final Wi-Fi objective status: not achieved yet

## Purpose

V497 is the first intentionally active scan step. It still is not Wi-Fi
bring-up. The goal is to prove that the V495 private service-manager/HAL/CNSS
session can trigger one `nl80211` scan and collect only redacted counts before
cleanup.

```text
V496 scan-only contract ready
  -> deploy execns helper v50
  -> V497 scan-only proof
  -> later bounded connect/DHCP/external ping work
```

## Preconditions

V497 requires:

```text
decision=v496-native-scan-only-contract-ready
pass=true
device_commands_executed=false
device_mutations=false
wifi_bringup_executed=false
credentials_read=false
scan_connect_executed=false
external_ping_executed=false
```

The remote helper must be `a90_android_execns_probe v50` and expose:

- `wifi-active-session-scan-only`
- `--allow-scan-only`
- `wifi_scan_only.begin`
- `wifi_scan_only.raw_results_redacted=1`

## Live Scope

The approved V497 run may:

- start private `servicemanager`, `hwservicemanager`, legacy Wi-Fi HAL, and
  `cnss-daemon` in the helper namespace;
- call `IWifi.start()` once if `IWifi/default` is returned;
- trigger one `NL80211_CMD_TRIGGER_SCAN`;
- dump `NL80211_CMD_GET_SCAN` only to count redacted BSS records;
- clean up the helper-owned processes and namespace.

The approved V497 run must not:

- read SSID, PSK, passphrase, or credential env values;
- connect, associate, link up, request DHCP, mutate routes, or ping externally;
- print SSID, BSSID, frequency, signal, IE, or raw BSS attributes;
- start `wificond`, `wpa_supplicant`, `hostapd`, or a persistent daemon;
- write Android partitions, load firmware, or mutate rfkill/ICNSS state.

## Approval Phrases

Deploy helper v50:

```text
approve v497 deploy execns helper v50 only; no daemon start and no Wi-Fi bring-up
```

Run scan-only proof:

```text
approve v497 native scan-only proof only; no connect/link-up/DHCP/routing/external ping
```

## Decision Rules

| decision | meaning |
|---|---|
| `v497-native-scan-only-pass-redacted` | scan triggered, redacted counts captured, cleanup passed |
| `v497-native-scan-only-interface-missing` | nl80211 exists but no selectable Wi-Fi interface appeared |
| `v497-native-scan-only-trigger-failed` | scan trigger failed; inspect errno and active-session state |
| `v497-native-scan-only-dump-failed` | trigger succeeded but redacted scan dump failed |
| `v497-native-scan-only-blocked` | helper/precondition/native health gate failed before live run |
| `v497-native-scan-only-approval-required` | exact run approval phrase was not supplied |

Only `v497-native-scan-only-pass-redacted` should unlock connect/DHCP planning.
