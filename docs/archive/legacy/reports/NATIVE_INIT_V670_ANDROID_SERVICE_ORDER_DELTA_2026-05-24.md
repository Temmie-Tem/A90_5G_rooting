# Native Init V670 Android/native Wi-Fi Service-order Delta Report

- date: `2026-05-24 KST`
- status: `host-only-pass`; Wi-Fi external ping is **not** complete
- script: `scripts/revalidation/native_wifi_android_service_order_delta_v670.py`
- plan evidence: `tmp/wifi/v670-android-service-order-delta-plan/`
- run evidence: `tmp/wifi/v670-android-service-order-delta/`
- decision: `v670-android-service-order-delta-classified`

## Scope

V670 compares Android service order and native V668 companion order. It consumes
existing evidence only. It does not contact the device, start services, start
Wi-Fi HAL, scan/connect, run DHCP, change routes, use credentials, or ping
externally.

Inputs:

- V668 native companion order;
- V669 Android/native runtime-delta result;
- V206 Android props, init rc, and process context evidence;
- V649 Android dmesg service-start timing where available.

## Result

The host-only classifier passed:

| key | value |
| --- | --- |
| decision | `v670-android-service-order-delta-classified` |
| pass | `True` |
| device_commands_executed | `False` |
| device_mutations | `False` |
| daemon_start_executed | `False` |
| wifi_hal_start_executed | `False` |
| wifi_bringup_executed | `False` |
| external_ping_executed | `False` |

## Android Service Order

Android service boottime ordering shows Wi-Fi HAL legacy/ext, `cnss_diag`, and
`wificond` already running before `cnss-daemon`:

| service | state | boottime ms | delta to `cnss-daemon` ms | SELinux context |
| --- | --- | --- | --- | --- |
| `vendor.wifi_hal_legacy` | running | `6831.389` | `-1281.54` | `u:r:hal_wifi_default:s0` |
| `vendor.wifi_hal_ext` | running | `6950.518` | `-1162.412` | `u:r:hal_wifi_default:s0` |
| `cnss_diag` | running | `7808.6` | `-304.33` | `u:r:vendor_wcnss_service:s0` |
| `wificond` | running | `7915.98` | `-196.949` | `u:r:wificond:s0` |
| `cnss-daemon` | running | `8112.93` | `0.0` | `u:r:vendor_wcnss_service:s0` |
| `wpa_supplicant` | running | `14904.94` | `6792.011` | `u:r:hal_wifi_supplicant_default:s0` |

Android init rc evidence contains service definitions for:

- `vendor.wifi_hal_legacy`;
- `vendor.wifi_hal_ext`;
- `cnss_diag`;
- `wificond`;
- `cnss-daemon`;
- `wpa_supplicant`.

## Native V668 Order

V668 native companion order:

```text
qrtr_ns
  -> rmt_storage
  -> tftp_server
  -> pd_mapper
  -> cnss_diag
  -> cnss_daemon
  -> service74_gate
  -> servicemanager / hwservicemanager / vndservicemanager
  -> cnss_daemon retry
```

That order intentionally omits Wi-Fi HAL and `wificond`, and starts CNSS before
the service-manager trio. This was useful for isolating the lower CNSS path, but
V669 now shows Android's successful path has a broader userspace surface in
place before `cnss-daemon`.

## Interpretation

V670 selects the next live mutation candidate:

```text
service74-positive lower companion
  -> Android-like service-manager surface
  -> Wi-Fi HAL legacy/ext + wificond start-only
  -> fresh cnss-daemon retry
```

The gate should still exclude supplicant, scan/connect, DHCP, routes,
credentials, and external ping. `wpa_supplicant` is late in Android boottime
relative to `cnss-daemon`, so it should remain blocked until `wlan0` exists.

## Next Gate

Plan V671 as a bounded live start-only proof:

- preserve the V668 service `74` gate and cleanup model;
- start the service-manager surface before Wi-Fi HAL/wificond;
- start Wi-Fi HAL legacy/ext and `wificond` only as bounded start-only;
- retry `cnss-daemon` after the Android-like userspace surface is present;
- observe WLFW/BDF/firmware-ready/`wlan0`;
- keep supplicant, scan/connect, DHCP, routes, credentials, and external ping
  blocked.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_android_service_order_delta_v670.py
python3 scripts/revalidation/native_wifi_android_service_order_delta_v670.py --out-dir tmp/wifi/v670-android-service-order-delta-plan plan
python3 scripts/revalidation/native_wifi_android_service_order_delta_v670.py --out-dir tmp/wifi/v670-android-service-order-delta run
```
