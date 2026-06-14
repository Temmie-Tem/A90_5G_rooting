# Native Init V748 Non-bind ICNSS/QCA Power-up Trigger Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_nonbind_powerup_trigger_v748.py`
- plan evidence: `tmp/wifi/v748-nonbind-powerup-trigger-plan/`
- preflight evidence: `tmp/wifi/v748-nonbind-powerup-trigger-preflight/`
- run evidence: `tmp/wifi/v748-nonbind-powerup-trigger/`
- decision: `v748-icnss-qmi-wlfw-nonbind-trigger-selected`
- status: `pass`

## Summary

V748 is host-only. It consumes V746/V747 evidence plus the earlier Android and
vendor-firmware reports, then rejects the remaining dead-end candidates before
any live mutation.

```text
V746 mdm_helper started after sysmon-qmi but lower markers stayed 0
  + V747 QCA6390 child driver-link gap is not a bind/unbind target
  + Android reference has ICNSS parent netdev and WLFW/BDF readiness
  + private vendor firmware namespace is already proven
  + wlan module load is not justified by current evidence
  -> next gate is non-bind ICNSS/QCA WLFW power-up trigger capture
```

No device command, daemon start, service-manager start, Wi-Fi HAL, scan/connect,
DHCP/routing, credentials, external ping, partition write, or bind/unbind action
was executed.

## Checks

| check | result |
| --- | --- |
| QCA6390 bind/unbind eliminated | pass |
| `mdm_helper` retry eliminated | pass |
| lower marker progression absent | pass |
| Android ICNSS/WLFW reference usable | pass |
| repeated CNSS/HAL retry eliminated | pass |
| vendor namespace satisfied | pass |
| `wlan` module load eliminated | pass |
| V747 source coverage | pass |

## Candidate Decision

| candidate | disposition |
| --- | --- |
| QCA6390 `bind`/`unbind` | rejected |
| `mdm_helper` | rejected |
| repeated CNSS/HAL | rejected |
| vendor namespace | satisfied |
| `wlan` module load | rejected |
| non-bind ICNSS/QCA WLFW power-up trigger | selected |

## Evidence

V746 lower marker counts used by V748:

| marker | count |
| --- | ---: |
| QRTR RX | 1 |
| QRTR TX | 1 |
| `sysmon-qmi` | 1 |
| MHI | 0 |
| QCA6390 | 0 |
| WLFW | 0 |
| BDF | 0 |
| `wlan0` | 0 |
| WLAN-PD | 0 |

Report signal counts:

| signal | count |
| --- | ---: |
| Android ICNSS netdev reference | 4 |
| Android WLFW/BDF reference | 4 |
| V701 `cld80211` only evidence | 4 |
| V727 firmware visibility evidence | 10 |
| V728 private vendor namespace evidence | 3 |
| V727 static `wlan` surface evidence | 2 |

## Interpretation

The next unit should not start Wi-Fi HAL or attempt credentials. The gate is
still below connection level: prove, by read-only Android/native capture first,
which non-bind ICNSS/CNSS2/QCA path advances from the current native state to
WLFW/BDF/`wlan0`.

## Next Gate

V749 should be a read-only Android/native ICNSS-QMI/WLFW trigger capture:

1. compare Android and native ICNSS/CNSS2/QCA sysfs, dmesg, QRTR, and MHI state;
2. locate the first Android-only trigger between ICNSS parent readiness and WLFW
   service/BDF readiness;
3. keep bind/unbind, HAL start, scan/connect, credentials, DHCP/routes, and
   external ping forbidden until a lower trigger is proven.
