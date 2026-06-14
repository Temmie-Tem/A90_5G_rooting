# Native Init v280 CNSS QCA6390 Probe Expectation Report

## Summary

- status: PASS
- boot image change: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- new tool: `scripts/revalidation/wifi_cnss_qca6390_probe_expectation.py`
- evidence: `tmp/wifi/v280-cnss-qca6390-probe-expectation/`
- decision: `cnss2-driver-dir-missing-qca-unbound`
- packet transmission: none
- daemon execution: none
- QMI payload: none
- sysfs/control writes: none

v280 compared source-derived CNSS2 probe expectations against live read-only
sysfs/kernel state. The QCA6390 device-tree compatible is visible, but this
kernel reports `CONFIG_CNSS2=n`, has no `/sys/bus/platform/drivers/cnss2`, and
leaves the QCA6390 platform node unbound. The only live CNSS-like platform
driver directory observed is `icnss`.

## Source Expectation

Primary sources used:

- Qualcomm CNSS2 source: `cnss2` platform driver, `qcom,cnss-qca6390` OF match,
  and probe path through resources, power, bus, sysfs, QMI, and misc init:
  https://android.googlesource.com/kernel/msm.git/+/28ec0fbdef41e99b01d87e5d4d267f72dddf1dec/drivers/net/wireless/cnss2/main.c
- CNSS2 Kconfig: QMI support and QCA6390-specific config entries:
  https://android.googlesource.com/kernel/msm.git/+/89594f79eb3779e02c47b5fd47427c55497cd5c9/drivers/net/wireless/cnss2/Kconfig
- Linux driver binding documentation: device/driver registration and matching
  produce sysfs binding links after successful probe:
  https://docs.kernel.org/driver-api/driver-model/binding.html

## Live Findings

| field | result |
| --- | --- |
| QCA6390 compatible/modalias | `qcom,cnss-qca6390` / `of:Nqcom,cnss-qca6390TCqcom,cnss-qca6390` |
| QCA6390 driver link | absent |
| `/sys/bus/platform/drivers/cnss2` | absent |
| `/sys/bus/platform/drivers/icnss` | present |
| `/sys/kernel/cnss` | absent |
| `/sys/kernel/shutdown_wlan` | present |
| `wlan*` netdev | absent |
| wiphy | absent |
| CNSS process table | clean |

Kernel config sample:

| key | value |
| --- | --- |
| `CONFIG_WLAN` | `y` |
| `CONFIG_QCA_CLD_WLAN` | `y` |
| `CONFIG_CNSS_UTILS` | `y` |
| `CONFIG_CNSS2` | `n` |
| `CONFIG_CNSS_QCA6390` | `n` |
| `CONFIG_CNSS2_QMI` | unset |
| `CONFIG_CNSS_QMI_SVC` | unset |

Relevant kernel log extraction was readable and mostly showed prior bounded
`cnss-daemon` netlink activity, not a successful QCA6390 platform-driver bind.

## Interpretation

- The earlier CNSS2 source model is not the live kernel's active binding model:
  `CONFIG_CNSS2=n` and no `cnss2` platform driver directory exists.
- The live kernel instead exposes an `icnss` platform driver, an ICNSS platform
  device, and a separate QCA6390 device-tree node that remains unbound.
- This explains why repeating `cnss-daemon` start-only does not change QCA6390
  binding: the blocker is below userspace daemon startup and closer to the
  kernel's ICNSS/QCA6390 binding model.
- The next useful step should shift from CNSS2/start-only repetition to ICNSS
  source/sysfs expectation comparison.

## Guardrails Preserved

- no daemon/service start
- no QRTR nameservice packet or QMI payload
- no Wi-Fi scan/connect/link-up
- no credentials, DHCP, routing, or Internet-facing exposure
- no `cnss_diag`, HAL, supplicant, wificond, or hostapd start
- no rfkill unblock, ICNSS bind/unbind, `driver_override`, recovery, ramdump, or
  assert controls
- no firmware path mutation, Android partition write, reboot, or remount

## Validation

Static:

- `python3 -m py_compile scripts/revalidation/wifi_cnss_qca6390_probe_expectation.py scripts/revalidation/wifi_qca6390_driver_param_classifier.py scripts/revalidation/a90ctl.py`: PASS
- `git diff --check`: PASS

Live read-only:

```bash
python3 scripts/revalidation/wifi_cnss_qca6390_probe_expectation.py \
  --out-dir tmp/wifi/v280-cnss-qca6390-probe-expectation \
  run
```

Result:

- decision: `cnss2-driver-dir-missing-qca-unbound`
- pass: `True`
- reason: source expects `cnss2` driver binding, but live sysfs has no `cnss2`
  platform driver directory and QCA6390 remains unbound

Postflight:

- `version`: `A90 Linux init 0.9.60 (v261)`
- `status`: shell responsive, `selftest fail=0`, `netservice: disabled tcpctl=stopped`
- `pidof cnss-daemon`: rc `1`, process absent
- `/proc/net/dev`: `ncm0` present; no `wlan*` interface observed

## Next Step

v281 should be an ICNSS model comparison:

- locate source references for the live `icnss` driver model;
- compare expected ICNSS device attributes, sysfs links, module params, and
  probe/firmware path against current live state;
- remain read-only first: no bind/unbind, no `driver_override`, no rfkill, no
  daemon start, no QRTR/QMI payloads, and no Wi-Fi link actions.
