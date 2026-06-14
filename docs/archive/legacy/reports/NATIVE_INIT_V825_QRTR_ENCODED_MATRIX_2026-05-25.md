# Native Init V825 QRTR Encoded Matrix Report

## Result

- decision: `v825-encoded-publication-visible`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py`
- evidence: `tmp/wifi/v825-qrtr-encoded-matrix/`

## What Ran

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py

python3 scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py \
  --out-dir tmp/wifi/v825-qrtr-encoded-matrix-plan-check \
  plan

python3 scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py \
  --out-dir tmp/wifi/v825-qrtr-encoded-matrix-preflight-check \
  preflight

python3 scripts/revalidation/native_wifi_qrtr_encoded_matrix_v825.py \
  run
```

## Evidence Summary

| Signal | Result |
| --- | --- |
| V824 route | pass |
| helper | `a90_android_execns_probe v125` |
| helper deploy | executed, serial fallback |
| V817 lower window | pass, `v817-in-window-service-publication-advanced` |
| cleanup reboot | executed |
| expected matrix cases | `5` |
| matrix result | complete |
| AF_QIPCRTR sockets | all socket rc `0`, family `42` |
| nameservice lookup sends | all new/delete lookup rc `0` |
| timeouts | `0` |
| total service events | `2` |
| QMI payload | `0` |

## Matrix Rows

| Case | Label | Service | Encoded instance | Service events | End-of-list | Timeout | QMI attempted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `servloc` | `64` | `257` | `1` | `1` | `0` | `0` |
| 1 | `ssctl` | `43` | `4098` | `0` | `1` | `0` | `0` |
| 2 | `servnotif` | `66` | `18945` | `0` | `1` | `0` | `0` |
| 3 | `servnotif` | `66` | `46081` | `1` | `1` | `0` | `0` |
| 4 | `wlfw` | `69` | `1` | `0` | `1` | `0` | `0` |

## Interpretation

V825 proves that the raw-vs-encoded gap mattered. The same lower window that
returned clean-empty for V823 raw instances now reports service publication for
encoded service-locator `64/257` and encoded service-notifier instance
`66/46081`.

The result is still below Wi-Fi bring-up. SSCTL `43/4098`, service-notifier
`66/18945`, and WLFW `69/1` remain without service events, so there is still no
WLFW/service69, BDF, FW-ready, `wiphy`, or `wlan0` proof.

The next question is no longer "does userspace AF_QIPCRTR see anything?" It
does. The next blocker is the exact publication content and continuation:
identify node/port/version/instance details for the visible events and decide
whether service-notifier `180` visibility can be safely followed with a bounded,
non-HAL next step.

## Safety

- Helper deploy wrote only the approved helper path.
- Cleanup reboot restored healthy v724 native status.
- No custom kernel flash, boot image write, partition write, or bootloader
  handoff executed.
- No `esoc0` open, bind/unbind, driver override, or module load/unload
  executed.
- No QMI payload, service-manager, Wi-Fi HAL, wificond, scan/connect/link-up,
  credential use, DHCP, route change, or external ping executed.
- V775 custom OSRC kernel flashing pause remains active.
- No Wi-Fi secret material was written to tracked output.

## Next

V826 should add or use a no-QMI QRTR event-detail observer that records visible
nameservice event payloads for encoded `64/257`, `66/46081`, and adjacent
instances. It should not send QMI payloads or start service-manager, Wi-Fi HAL,
scan/connect, credentials, DHCP/routes, external ping, boot image writes,
partition writes, or custom kernel flashes.
