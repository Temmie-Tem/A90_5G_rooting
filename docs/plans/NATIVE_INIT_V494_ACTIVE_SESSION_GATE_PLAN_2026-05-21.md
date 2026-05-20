# Native Init V494 Active-Session Gate Plan

- Date: 2026-05-21 KST
- Scope: host-side routing gate from V490..V493 proofs to native Wi-Fi scan/connect/ping work
- Status: implementation-ready; no live device command in V494
- Final Wi-Fi objective status: not achieved yet

## Why V494 Exists

V493 is still a cleanup-contained proof. A successful V493 result can show that
`IWifi.start()` transiently creates a WLAN/wiphy/rfkill surface, but it also
proves the helper cleaned up service-manager, HAL, CNSS, and the surface after
the observation window. That evidence is necessary, but it is not a connected
Wi-Fi session.

Therefore the next step cannot be a direct V462 external ping unless a WLAN
surface intentionally remains available. The normal passing branch is:

```text
V493 transient surface observed + cleanup clean
  -> V495 bounded active-session helper
  -> V496 native scan-only proof
  -> V497 private credential materialization
  -> V498 native connect + DHCP + external ping
```

## Inputs

The V494 runner consumes the current chain evidence:

```text
--v490-manifest path/to/V490/manifest.json
--v491-manifest path/to/V491/manifest.json
--v492-manifest path/to/V492/manifest.json
--v493-manifest path/to/V493/manifest.json
```

If paths are omitted, it selects the latest passing manifest it can find for
each upstream gate.

Required upstream decisions:

| gate | required decision |
|---|---|
| V490 | `v490-selinux-policy-load-proof-pass` with `policy_load_executed=true` |
| V491 | `v491-post-load-domain-handoff-present` |
| V492 | `v492-samsung-registration-post-load-present` |
| V493 | one of the known post-registration `IWifi.start()` outcomes |

## Decision Rules

| decision | meaning |
|---|---|
| `v494-native-wifi-active-session-contract-ready` | V493 observed a transient surface and cleaned up; implement V495 bounded active-session helper |
| `v494-native-wifi-active-session-blocked` | V490, V491, V492, or V493 proof is missing/not passing |
| `v494-native-wifi-active-session-service-null` | V493 still cannot get `IWifi/default`; inspect registration namespace mismatch |
| `v494-native-wifi-active-session-transaction-review` | `IWifi.start()` transaction executed but failed; inspect raw hwbinder reply |
| `v494-native-wifi-active-session-driver-gap` | `IWifi.start()` returned but no WLAN surface appeared; inspect driver/CNSS mode-set gap |
| `v494-native-wifi-active-session-cleanup-review-required` | V493 leaked a WLAN surface after cleanup; inspect device state before widening scope |
| `v494-native-wifi-active-session-review-required` | V493 result is unclassified or unexpectedly mutating |

## Guardrails

V494 must not:

- execute device commands
- start daemons, HAL, CNSS, supplicant, DHCP, or ping
- read SSID/PSK env values
- write raw SSID, BSSID, password, passphrase, or PSK into evidence
- treat V493's cleaned transient surface as persistent connectivity

## Next Work

1. Run V490 live policy-load proof only after exact approval.
2. Run V491 with the V490 pass manifest.
3. Run V492 with the V491 pass manifest.
4. Run V493 with the V492 pass manifest.
5. Run V494 preflight to select the correct branch.
6. If V494 returns `contract-ready`, implement V495 active-session helper mode.
