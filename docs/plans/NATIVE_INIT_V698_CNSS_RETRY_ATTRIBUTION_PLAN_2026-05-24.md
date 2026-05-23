# Native Init V698 CNSS Retry Attribution Plan

- date: `2026-05-24 KST`
- cycle: `v698`
- type: host-only classifier

## Goal

V697 narrowed the blocker to the `cnss-daemon` vendor Binder runtime path, but
the V695 dmesg line must be attributed to the correct `cnss-daemon` instance
before changing live behavior.

V698 separates:

- initial pre-provider `cnss-daemon`;
- provider-confirmed post-registration `cnss-daemon` retry.

The key question is whether Binder `29189/-22` belongs to the fresh
post-provider retry or to the earlier initial `cnss-daemon` instance that ran
before `vendor.qcom.PeripheralManager` was proven.

## Gate

Expected success label:

- `v698-post-provider-cnss-retry-silent-after-netlink-classified`

Other labels:

- `v698-cnss-retry-attribution-classifier-blocked`
- `v698-cnss-retry-attribution-inconclusive`

## Guardrails

V698 must not:

- contact the device;
- mount or bind mount filesystems;
- start daemons, service managers, Wi-Fi HAL, `wificond`, supplicant, or
  hostapd;
- scan, connect, link up, use credentials, run DHCP, change routes, or external
  ping;
- write sysfs/debugfs, boot images, or partitions.

## Implementation

Add `scripts/revalidation/native_wifi_cnss_retry_attribution_classifier_v698.py`
to:

1. read V695 provider-confirmed CNSS retry evidence;
2. read V697 Binder runtime target evidence;
3. parse V695 helper output for initial/retry `cnss-daemon` pids and start
   order;
4. parse V695 dmesg for CNSS netlink and Binder transaction failure lines;
5. decode Binder return value `29189` as `BR_DEAD_REPLY` using Android Binder
   UAPI semantics;
6. classify whether the Binder failure belongs to the initial daemon or the
   post-provider retry;
7. route the next live unit to provider-first initial-suppressed CNSS start-only
   if the retry reaches netlink without a Binder failure.

## Validation Plan

```bash
python3 -m py_compile scripts/revalidation/native_wifi_cnss_retry_attribution_classifier_v698.py
python3 scripts/revalidation/native_wifi_cnss_retry_attribution_classifier_v698.py \
  --out-dir tmp/wifi/v698-cnss-retry-attribution-classifier-rerun \
  run
git diff --check
```

## References

- Android Binder UAPI header:
  `https://android.googlesource.com/kernel/common/+/5726a8d0f1958af80ad8e514bc2c18d213e739b7/include/uapi/linux/android/binder.h`
- Android Binder driver transaction failure logging:
  `https://android.googlesource.com/kernel/common/+/03329f99/drivers/android/binder.c`
