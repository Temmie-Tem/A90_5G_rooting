# Native Init V698 CNSS Retry Attribution Report

- date: `2026-05-24 KST`
- status: `host-only-pass`; Wi-Fi external ping is **not** complete
- evidence: `tmp/wifi/v698-cnss-retry-attribution-classifier-rerun/`
- decision: `v698-post-provider-cnss-retry-silent-after-netlink-classified`

## Scope

V698 used existing evidence only. It did not contact the device, start daemons,
start Wi-Fi HAL, scan/connect/link-up, use credentials, run DHCP, change
routes, ping externally, write sysfs/debugfs, or write boot partitions.

Inputs:

- V695 manifest:
  `tmp/wifi/v695-provider-confirmed-cnss-retry-orchestrated-live/manifest.json`
- V697 manifest:
  `tmp/wifi/v697-cnss-binder-runtime-target-classifier-rerun/manifest.json`
- V695 helper output:
  `tmp/wifi/v695-provider-confirmed-cnss-retry-orchestrated-live/arm-v695-v118-provider-confirmed-cnss-retry/live/native/companion-start-only-with-holder.txt`
- V695 native dmesg:
  `tmp/wifi/v695-provider-confirmed-cnss-retry-orchestrated-live/arm-v695-v118-provider-confirmed-cnss-retry/live/native/dmesg-delta.txt`

## Result

| check | status |
| --- | --- |
| input evidence ready | pass |
| Binder return code decoded | finding |
| Binder failure attributed to initial CNSS | finding |
| provider query precedes retry | finding |
| post-provider retry reaches netlink without Binder fail | finding |
| V697 target refined | finding |

## Evidence

| surface | result |
| --- | --- |
| initial `cnss-daemon` pid | `644` |
| retry `cnss-daemon` pid | `1192` |
| initial start order | `6` |
| `vndservicemanager` start order | `9` |
| `per_mgr` start order | `10` |
| `per_proxy` start order | `11` |
| retry start order | `12` |
| provider query before retry | `true` |
| Binder failure pid | `644` |
| Binder return | `29189` / `0x7205` / `BR_DEAD_REPLY` |
| Binder param | `-22` / `EINVAL` |
| Binder data size | `0` |
| Binder offsets size | `0` |
| initial Binder failures | `1` |
| retry Binder failures | `0` |
| initial CNSS netlink count | `5` |
| retry CNSS netlink count | `5` |
| `wlfw_start` count | `0` |

## Interpretation

The V695 Binder line:

```text
binder: 644:644 transaction failed 29189/-22, size 0-0 line 3206
```

belongs to the initial pre-provider `cnss-daemon` pid `644`, not the
post-provider retry pid `1192`.

Android Binder UAPI maps `_IO('r', 5)` to `BR_DEAD_REPLY`; decimal `29189`
is `0x7205`, so the observed pair is `BR_DEAD_REPLY/-EINVAL`. That should not
be treated as a vendor service method transaction code. It is consistent with a
dead/missing target at the time of the initial daemon's transaction.

The post-provider retry is different: it reaches CNSS netlink, has no matching
Binder transaction failure in the captured dmesg, and still does not reach
WLFW/BDF/`wlan0`. Therefore the next live gate should not simply “repair the
same Binder failure.” It should suppress the initial pre-provider
`cnss-daemon`, start the provider path first, then run one fresh `cnss-daemon`
with tighter stdout/stderr/proc/fd capture around the retry tail.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_cnss_retry_attribution_classifier_v698.py
python3 scripts/revalidation/native_wifi_cnss_retry_attribution_classifier_v698.py \
  --out-dir tmp/wifi/v698-cnss-retry-attribution-classifier-rerun \
  run
```

Result:

```text
decision: v698-post-provider-cnss-retry-silent-after-netlink-classified
pass: True
device_commands_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
wifi_bringup_executed: False
external_ping_executed: False
```

## Next Gate

Plan V699 as a provider-first, initial-suppressed `cnss-daemon` start-only live
gate:

- start QRTR/firmware/provider stack through `vendor.qcom.PeripheralManager`
  proof;
- do **not** start the initial pre-provider `cnss-daemon`;
- start exactly one fresh `cnss-daemon` after provider proof;
- capture retry stdout/stderr, pid, fd targets, maps, status, and dmesg tail;
- keep Wi-Fi HAL, scan/connect, DHCP, credentials, routes, and external ping
  blocked.

## References

- Android Binder UAPI header:
  `https://android.googlesource.com/kernel/common/+/5726a8d0f1958af80ad8e514bc2c18d213e739b7/include/uapi/linux/android/binder.h`
- Android Binder driver transaction failure logging:
  `https://android.googlesource.com/kernel/common/+/03329f99/drivers/android/binder.c`
