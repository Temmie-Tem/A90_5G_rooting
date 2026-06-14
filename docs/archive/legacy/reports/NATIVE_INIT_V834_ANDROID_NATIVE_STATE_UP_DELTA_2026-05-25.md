# Native Init V834 Android/Native State-Up Delta Report

## Result

- decision: `v834-known-warning-state-listener-replay-selected`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_android_native_state_up_delta_v834.py`
- evidence: `tmp/wifi/v834-android-native-state-up-delta/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_android_native_state_up_delta_v834.py

python3 scripts/revalidation/native_wifi_android_native_state_up_delta_v834.py \
  --out-dir tmp/wifi/v834-android-native-state-up-delta-plan-check \
  plan

python3 scripts/revalidation/native_wifi_android_native_state_up_delta_v834.py run
```

V834 was host-only. It did not execute a device command and did not send any
QRTR/QMI payload.

## Evidence Summary

| Signal | Result |
| --- | --- |
| V829 service-locator | `wlan/fw -> msm/modem/wlan_pd`, instance `180` |
| V830 native listener | registered, current state `uninit` |
| V831 early native listener | registered, current state `uninit`, no indication |
| V833 Android listener | raw `0x1fffffff`, canonical `up` |
| V817 lower window | `mss=ONLINE`, `mdm3=OFFLINING`, WLFW/`wlan0` absent |
| V792 lower replay | service `180/74` present, known ASoC warning, WLFW/`wlan0` absent |
| V775 custom kernel | custom OSRC diagnostic kernel flashing remains paused |

## Classification

The V829 briefing path is already complete in the current repository. The
important result was not an empty pd-mapper domain list. V829 returned:

```text
msm/modem/wlan_pd instance 180
```

V830/V831 then proved native listener registration works but returns:

```text
current_state = uninit
```

V833 proved the same listener request returns Android state:

```text
current_state = up
```

Therefore the native gap is not service-locator reachability, pd-mapper DB
population, endpoint visibility, or listener payload format. The active gap is
the lower native state transition that makes `msm/modem/wlan_pd` report `UP`.

## Candidate Matrix

| Candidate | Classification | Reason |
| --- | --- | --- |
| repeat V829 service-locator `GET_DOMAIN_LIST` | reject | V829 already returned `msm/modem/wlan_pd` instance `180` |
| repeat V830/V831 native listener timing | reject | both native windows register successfully and return `UNINIT` |
| service-manager / Wi-Fi HAL / scan/connect / DHCP / external ping | blocked | WLAN-PD state-up, WLFW service69, BDF, wiphy, and `wlan0` are still absent |
| custom OSRC diagnostic kernel flash | paused | V775 classified stock-vs-OSRC boot incompatibility |
| known-ASoC-warning clean-DSP/CNSS listener replay | select-next | V792 is the best bounded native service `180/74` window and V833 validates the listener model |

## Safety

- No bridge command, device command, reboot, bootloader handoff, boot image
  write, partition write, or custom kernel flash executed.
- No QRTR socket opened and no QRTR/QMI packet transmitted.
- No service-manager, Wi-Fi HAL, scan/connect/link-up, credential use, DHCP,
  route change, or external ping executed.
- No `esoc0` open, subsystem state write, bind/unbind, driver override, or
  module load/unload executed.
- No Wi-Fi secret material was written to tracked output.

## Next

V835 should query the corrected service-notifier listener inside the
known-ASoC-warning clean-DSP/CNSS lower window and then reboot-clean.

Success branches:

1. native returns `UP`: continue below HAL/connect with WLFW/service69 readback
   and post-state-up timing;
2. native still returns `UNINIT`: the missing trigger remains below that
   clean-DSP/CNSS window, so mdm3/WLAN-PD state-up contract analysis continues.
