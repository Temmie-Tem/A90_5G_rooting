# Native Init V748 Non-bind ICNSS/QCA Power-up Trigger Plan

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_nonbind_powerup_trigger_v748.py`
- scope: host-only classifier

## Goal

Close the post-V747 decision gap before any more live mutation. V747 proved the
QCA6390 platform child driver-link gap is not a safe `bind`/`unbind` target, so
V748 must classify the remaining candidate set and select the next Wi-Fi
bring-up gate from existing evidence only.

## Basis Evidence

- `tmp/wifi/v747-qca6390-driver-binding-delta/`
- `tmp/wifi/v746-mdm-helper-sysmon-live-current/`
- `docs/reports/NATIVE_INIT_V701_PRE_WLFW_TRIGGER_CLASSIFIER_2026-05-24.md`
- `docs/reports/NATIVE_INIT_V703_ANDROID_NATIVE_BINDING_COMPARE_2026-05-24.md`
- `docs/reports/NATIVE_INIT_V716_QCA_BIND_RECONCILIATION_2026-05-24.md`
- `docs/reports/NATIVE_INIT_V727_LOWER_PREREQ_2026-05-24.md`
- `docs/reports/NATIVE_INIT_V728_PRIVATE_VENDOR_ROOT_2026-05-24.md`

## Candidate Matrix

V748 classifies these candidates:

| candidate | expected disposition |
| --- | --- |
| QCA6390 `bind`/`unbind` | reject unless V716/V747 are contradicted |
| `mdm_helper` retry | reject unless V746 did not actually start it |
| repeated CNSS/HAL start | reject unless lower markers already advanced |
| vendor firmware namespace | mark satisfied only if V727/V728 prove it |
| `wlan` module load | reject unless Android proves a loadable module path |
| non-bind ICNSS/QCA WLFW trigger | select if every other candidate is closed |

## Forbidden

- no device command execution
- no service-manager or Wi-Fi HAL start
- no scan/connect/link-up
- no credentials, DHCP, routes, or external ping
- no QCA6390 `bind`, `unbind`, or `driver_override`
- no persistent writes to Android partitions

## Success Criteria

- Produce `manifest.json` and `summary.md` under `tmp/wifi/v748-nonbind-powerup-trigger/`.
- Preserve the guardrail that Wi-Fi connection work remains blocked until
  WLFW/BDF/`wlan0` evidence exists.
- Select a single next gate with explicit rejected alternatives.
