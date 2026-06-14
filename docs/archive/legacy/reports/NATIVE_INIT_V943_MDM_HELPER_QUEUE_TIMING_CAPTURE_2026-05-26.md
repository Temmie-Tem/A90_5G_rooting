# V943 mdm_helper Queue-Timing Capture Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| bounded live capture | `tmp/wifi/v943-mdm-helper-queue-timing-capture-live/manifest.json` | `v943-mdm-helper-queue-timing-captured` |

V943 reran the bounded `mdm_helper` runtime-contract capture using deployed
helper `v156`. The new `mdm_helper_queue_timing.*` evidence was captured with
no service-manager, CNSS, Wi-Fi HAL, scan/connect, DHCP/routes, credential use,
external ping, `/dev/subsys_esoc0` open, or eSoC ioctl.

## Implementation

- Added wrapper:
  `scripts/revalidation/native_wifi_mdm_helper_queue_timing_capture_v943.py`
- Required helper marker:
  `a90_android_execns_probe v156`
- Required helper sha256:
  `ff5a87694bbb9c557aaaaacf61e1ceb0af9dffb3984d9f6887a2f93c8bceceb8`
- Evidence:
  `tmp/wifi/v943-mdm-helper-queue-timing-capture-live/summary.md`

## Live Findings

| Marker | Value |
| --- | --- |
| result | `mdm-helper-esoc-fd-observed` |
| queue timing keys | `482` |
| `mdm_helper` pid | `1230` |
| fresh queue-failure pid | `1231` |
| `mdm_helper` `/dev/esoc-0` window count | `1` |
| `mdm_helper` `/dev/esoc-0` final count | `1` |
| `ks` final count | `0` |
| MHI pipe final count | `0` |
| cleanup reboot | `false` |

Timing deltas:

| Phase | Monotonic ms | Key observation |
| --- | ---: | --- |
| `after_per_mgr_settle` | `10282879` | `per_mgr` alive, state `S`, no subsystem fd |
| `after_mdm_helper_spawn` | `10282913` | `mdm_helper` alive, state `R`, no `/dev/esoc-0` fd yet |
| `window` | `10282927` | `mdm_helper` alive, state `S`, `/dev/esoc-0` fd count `1` |
| `final` | `10294971` | `mdm_helper` still alive, `/dev/esoc-0` fd count `1`, no `ks`/MHI |

The `mdm_helper` process reaches `/dev/esoc-0` roughly `14ms` after the
post-spawn snapshot. The fresh dmesg queue failure is attributed to
`mdm_helper` thread pid `1231` at kernel timestamp `10282.918067`, within the
same lower window.

## PM / Provider Surface

Across `after_per_mgr_settle`, `window`, and `final`:

- `pm-service` process count is `1`.
- `pm-proxy` process count is `0`.
- `pm_proxy_helper` process count is `0`.
- `per_mgr` `/dev/subsys_modem` fd count is `0`.
- `per_mgr` `/dev/subsys_esoc0` fd count is `0`.
- `per_mgr` `/dev/esoc-0` fd count is `0`.

This confirms the active queue failure occurs while `pm-service` is alive but
without Android-equivalent subsystem fd ownership or proxy/helper lifecycle.

## Postflight

Manual postflight after V943:

- `bootstatus`: `BOOT OK`, `selftest fail=0`.
- `selftest`: `pass=11 warn=1 fail=0`.
- `netservice status`: flag disabled, `ncm0` present, `tcpctl` stopped.

## Guardrails

- No service-manager start.
- No CNSS daemon start.
- No Wi-Fi HAL start.
- No scan/connect/link-up.
- No credential use.
- No DHCP/route mutation.
- No external ping.
- No `/dev/subsys_esoc0` open.
- No eSoC ioctl or notify.
- No boot image or partition write.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_queue_timing_capture_v943.py
python3 scripts/revalidation/native_wifi_mdm_helper_queue_timing_capture_v943.py \
  --out-dir tmp/wifi/v943-mdm-helper-queue-timing-plan-check plan
python3 scripts/revalidation/native_wifi_mdm_helper_queue_timing_capture_v943.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-runtime-contract-capture \
  --allow-cleanup-reboot \
  --assume-yes \
  run
```

## Interpretation

V943 narrows the blocker: the native path reaches the eSoC request side, but
`mdm_helper` still cannot queue the SDX50M event because the PeripheralManager
provider/proxy side is not equivalent to Android at that moment. The missing
piece is no longer basic `/dev/esoc-0` reachability.

## Next

V944 should be host-only classification of V943. It should decide whether the
next implementation is:

1. model `vendor.per_proxy` / `vendor.per_proxy_helper` lifecycle more closely;
2. add a narrower PM provider readiness probe;
3. refresh Android read-only timing evidence;
4. or stop this branch and choose another lower trigger.

Do not open `/dev/subsys_esoc0`, send eSoC notifications, start Wi-Fi HAL, or
scan/connect before V944.
