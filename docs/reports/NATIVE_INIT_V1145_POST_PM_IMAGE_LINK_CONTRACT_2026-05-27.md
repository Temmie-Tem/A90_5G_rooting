# Native Init V1145 Post-PM Image-Link Contract Report

Date: `2026-05-27`

## Result

- Decision: `v1145-select-post-pm-esoc-req-img-verifier-build`
- Pass: `true`
- Runner: `scripts/revalidation/native_wifi_post_pm_image_link_contract_v1145.py`
- Manifest: `tmp/wifi/v1145-post-pm-image-link-contract/manifest.json`
- Summary: `tmp/wifi/v1145-post-pm-image-link-contract/summary.md`

## Summary

V1145 is host-only. It reconciles the current V1143/V1144 post-PM eSoC wait
state with older Android-positive and native-negative `mdm_helper`/`ks`/MHI
evidence.

Current state:

```text
post-policy PM/CNSS register/connect OK
  -> mdm_helper opens /dev/esoc-0
  -> mdm_helper worker waits in ESOC_WAIT_FOR_REQ
  -> no /dev/subsys_esoc0 trigger in V1143/V1144
  -> no ks, MHI pipe, mdm3 ONLINE, WLFW, BDF, or wlan0
```

Android-positive state from V896/V968/V1024:

```text
pm_proxy_helper -> /dev/subsys_modem
pm-service      -> /dev/subsys_modem
mdm_helper      -> /dev/esoc-0
ks              -> /dev/mhi_0305_01.01.00_pipe_10
WLFW/FW-ready   -> wlan0
```

## Evidence Matrix

| item | result |
| --- | --- |
| V1144 current ioctl contract | `ESOC_WAIT_FOR_REQ` classified |
| V1143 current subsystem trigger | not attempted |
| V1024 Android PM fd contract | captured |
| V1024 Android WLFW/FW-ready/`wlan0` chain | captured |
| V968 Android dmesg order | WLFW start, `/dev/subsys_esoc0` get, WLAN-PD, BDF, FW-ready, `wlan0` |
| V900 old `mdm_helper` before subsystem live | insufficient; no `ks`/MHI and reboot cleanup required |
| V938 repaired runtime lower capture | `mdm_helper` reaches `/dev/esoc-0`, but no `ks`/MHI |
| V939 property-context classifier | exact property-context gap is not sufficient as next blocker |

## Current Helper Gap

The helper currently has two relevant but separate surfaces:

| surface | status |
| --- | --- |
| `wifi-companion-post-pm-mdm-helper-esoc-observer` | present |
| `--allow-post-pm-mdm-helper-lower-trace` | present |
| `wifi-companion-mdm-helper-ks-image-contract-preflight` | present |
| expected `ks` command line literal | present |
| post-PM eSoC request verifier mode | absent |
| post-PM bounded subsystem-trigger verifier flag | absent |

So the next implementation should not repeat V900 or V1020 as-is. The missing
unit is a combined post-PM verifier that keeps the V1143 PM/CNSS route, confirms
`mdm_helper` is waiting in `ESOC_WAIT_FOR_REQ`, and only then performs a bounded
subsystem trigger in a separate live cycle.

## Selected Route

V1146 should be source/build-only helper work:

```text
add fail-closed post-PM eSoC request verifier mode
  -> reuse V1143 PM/CNSS + mdm_helper-after-CNSS order
  -> confirm /dev/esoc-0 fd and ESOC_WAIT_FOR_REQ before trigger
  -> prepare bounded /dev/subsys_esoc0 trigger gate
  -> capture ks/MHI/mdm3/WLFW/BDF/wlan0
  -> keep HAL/scan/connect/credentials/DHCP/external ping blocked
```

Live deployment and live subsystem triggering should remain separate after the
source/build unit passes.

## Safety

- Device commands executed: `false`
- Actor start: `false`
- Live eSoC ioctl: `false`
- `/dev/subsys_esoc0` open: `false`
- Wi-Fi HAL start: `false`
- Scan/connect/link-up: `false`
- Credential use: `false`
- DHCP/route: `false`
- External ping: `false`
- Boot image/partition write/flash: `false`

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_post_pm_image_link_contract_v1145.py
python3 scripts/revalidation/native_wifi_post_pm_image_link_contract_v1145.py
```

## Next

Implement V1146 helper support only. Do not run the live subsystem trigger until
the new verifier mode is built, statically validated, deployed, and preflighted.
