# Native Init v280 CNSS QCA6390 Probe Expectation Plan

## Summary

- target: v280 no-start CNSS/QCA6390 source/sysfs probe expectation comparator
- boot image change: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- new tool: `scripts/revalidation/wifi_cnss_qca6390_probe_expectation.py`
- packet transmission: none
- daemon execution: none
- QMI payload: none
- sysfs/control writes: none

v279 proved that bounded `cnss-daemon` start-only does not bind QCA6390 or
change WLAN parameters. v280 stops live start attempts and compares
source-derived CNSS2 probe expectations with current read-only sysfs/kernel
state.

## References

- Qualcomm CNSS2 source defines a `cnss2` platform driver, includes
  `qcom,cnss-qca6390` in its OF match table, and on successful probe creates
  CNSS sysfs links before initializing QMI/misc services:
  https://android.googlesource.com/kernel/msm.git/+/28ec0fbdef41e99b01d87e5d4d267f72dddf1dec/drivers/net/wireless/cnss2/main.c
- CNSS2 Kconfig describes QMI support and QCA6390-specific support options:
  https://android.googlesource.com/kernel/msm.git/+/89594f79eb3779e02c47b5fd47427c55497cd5c9/drivers/net/wireless/cnss2/Kconfig
- Linux driver binding documentation states that driver/device binding creates
  sysfs links and that driver registration triggers matching against devices:
  https://docs.kernel.org/driver-api/driver-model/binding.html

## Scope

Read-only captures:

- QCA6390 `uevent`, `modalias`, `driver`, and `driver_override`
- `/sys/bus/platform/drivers/cnss2` and `/sys/bus/platform/drivers/icnss`
- `/sys/kernel/cnss` and `/sys/kernel/shutdown_wlan`
- platform driver list and `*cnss*`/`*qca6390*` sysfs nodes
- selected kernel config keys from `/proc/config.gz`
- filtered kernel log tail from `dmesg`
- process table and WLAN readiness surfaces

## Decision Model

Expected likely decision:

```text
cnss2-driver-dir-missing-qca-unbound
```

This means:

- source expectation says `qcom,cnss-qca6390` should match the `cnss2` platform
  driver;
- live QCA6390 compatible/modalias exists;
- QCA6390 has no `driver` symlink;
- live sysfs does not expose `/sys/bus/platform/drivers/cnss2`.

Alternative decisions:

- `cnss2-driver-dir-present-qca-unbound`: `cnss2` exists, but QCA6390 remains
  unbound, suggesting probe failure/defer investigation.
- `cnss-qca6390-driver-bound-no-readiness`: QCA6390 is bound, but no WLAN
  readiness surface appears.
- `cnss-qca6390-readiness-visible`: WLAN netdev or wiphy appeared.
- `cnss-qca6390-probe-expectation-incomplete`: required read-only evidence is
  missing or unsafe.

## Guardrails

v280 must not:

- start `cnss-daemon`, `cnss_diag`, HAL, supplicant, wificond, or hostapd
- transmit QRTR nameservice packets or QMI request payloads
- perform Wi-Fi scan/connect/link-up/credential/DHCP/routing
- write to sysfs/control paths, including rfkill, ICNSS bind/unbind,
  `driver_override`, recovery, ramdump, or assert controls
- mutate firmware paths or Android partitions
- reboot or remount

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_cnss_qca6390_probe_expectation.py \
  scripts/revalidation/wifi_qca6390_driver_param_classifier.py \
  scripts/revalidation/a90ctl.py

git diff --check
```

Live read-only:

```bash
python3 scripts/revalidation/wifi_cnss_qca6390_probe_expectation.py \
  --out-dir tmp/wifi/v280-cnss-qca6390-probe-expectation \
  run
```

Postflight:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py run /cache/bin/toybox pidof cnss-daemon || true
python3 scripts/revalidation/a90ctl.py cat /proc/net/dev
```

## Acceptance

- v280 starts no daemon and sends no packets.
- source expectation is explicit in manifest and report.
- live sysfs confirms whether `cnss2` driver directory exists.
- QCA6390 driver-link, kernel CNSS links, config sample, and relevant dmesg tail
  are captured.
- postflight remains clean: no `cnss-daemon`, no `wlan*` interface.
