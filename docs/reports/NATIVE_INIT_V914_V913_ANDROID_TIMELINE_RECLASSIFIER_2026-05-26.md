# Native Init V914 V913 Android Timeline Reclassifier Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| V913 handoff live | `tmp/wifi/v913-android-esoc-gpio-timeline-handoff-live/manifest.json` | `v913-handoff-collector-failed-rollback-complete` |
| V914 host-only reclassifier | `tmp/wifi/v914-v913-android-timeline-reclassifier/manifest.json` | `v914-v913-upper-positive-lower-postboot-negative` |

The V913 live handoff successfully booted Android, captured read-only evidence,
and restored native v724. The original V913 classifier failed because it treated
post-boot lower eSoC/GPIO markers as required positive markers. V914 reclassified
the raw evidence and corrected that interpretation.

## Key Findings

Android upper Wi-Fi path is positive:

| Marker | Time | Evidence |
| --- | --- | --- |
| service-notifier 180 connected | `6.975128` | QMI handle connected to 180 service |
| service-notifier 74 connected | `6.976821` | QMI handle connected to 74 service |
| WLFW start | `8.349631` | `cnss-daemon wlfw_start: Starting` |
| WLAN-PD indication | `9.414862` | `msm/modem/wlan_pd` state indication |
| BDF regdb | `9.476146` | `BDF file : regdb.bin` |
| BDF bdwlan | `9.487515` | `BDF file : bdwlan.bin` |
| wlan0 | `14.950217` | `dev : wlan0 : event : 16` |

Android post-boot lower markers are not positive:

| Marker | Value |
| --- | --- |
| `subsys9/state` | `OFFLINING`, `OFFLINING` |
| GPIO142 `mdm status` IRQ total | `0` |
| current `ks` process | `false` |
| current MHI pipe fd | `false` |
| `pm-service` holds `/dev/subsys_modem` | `true` |
| `pm-service` holds `/dev/subsys_esoc0` | `false` |
| `mdm_helper` holds `/dev/esoc-0` | `true` |

## Interpretation

The Android positive path proves that WLAN-PD, WLFW, BDF, and `wlan0` can appear
even when the sampled post-boot `mdm3` state is `OFFLINING`, GPIO142 IRQ count
is `0`, and `ks`/MHI are not currently visible.

Therefore the next native gate must not require post-boot `subsys9=ONLINE`,
GPIO142 IRQ increment, current `ks`, or current MHI pipe as mandatory success
criteria. Those should remain diagnostic lower markers. The primary success
criteria for the native trigger path should be progression to WLAN-PD, WLFW,
BDF, and eventually `wlan0`.

## Tool Fix

`scripts/revalidation/native_wifi_android_esoc_gpio_timeline_v913.py` was
updated so future V913 captures:

- ignore command-echo lines when searching timed dmesg markers;
- require exact BDF markers such as `BDF file`, `regdb.bin`, or `bdwlan.bin`;
- avoid treating the collector shell command itself as evidence of `ks`;
- avoid treating generic PCIe clock/GDSC lines as PCIe link establishment;
- classify Android upper Wi-Fi positivity separately from lower post-boot
  diagnostics.

## Rollback / Device Health

The handoff wrapper reports native rollback completed. Post-run serial checks
confirmed:

- native version: `A90 Linux init 0.9.68 (v724)`;
- `bootstatus`: `BOOT OK shell 4.1s`;
- `selftest`: `pass=11 warn=1 fail=0`;
- Wi-Fi bring-up in native: not executed;
- external ping: not executed.

## Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_android_esoc_gpio_timeline_v913.py \
  scripts/revalidation/native_wifi_v913_android_timeline_reclassifier_v914.py
python3 scripts/revalidation/native_wifi_v913_android_timeline_reclassifier_v914.py
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py bootstatus
```

## Next

Plan the next native trigger gate with corrected success criteria:

- primary positive path: WLAN-PD, WLFW, BDF, `wlan0`;
- lower diagnostics: `mdm_helper` `/dev/esoc-0`, `pm-service`
  `/dev/subsys_modem`, `subsys9/state`, GPIO142 IRQ, `ks`, MHI pipe;
- do not block solely on post-boot `mdm3=OFFLINING` or GPIO142 count `0`.
