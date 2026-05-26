# V968 Android dmesg eSoC/GPIO Timing Plan

- date: `2026-05-26`
- type: Android read-only evidence classifier
- prerequisite: device can boot Android normally and `adb shell` is available
- selected after: V966/V967 service-window route, user-provided Magisk/Android dmesg direction

## Objective

Classify the Android-good boot sequence around MDM3/eSoC GPIO timing so native experiments stop guessing where SDX50M powerup diverges.

The specific questions:

1. When does AP2MDM status GPIO assert during Android boot?
2. Does PMIC soft-reset deassert happen in the Android-good path?
3. When does MDM2AP status GPIO IRQ fire, and how many times?
4. When does PCIe/eSoC/MDM3 become ready relative to Wi-Fi HAL, `mdm_helper`, and `cnss-daemon wlfw_start`?
5. Does Android dmesg expose enough history without a Magisk module?

## Rationale

Magisk `post-fs-data.sh` or `service.sh` can collect early boot samples, but it adds boot-time script risk and may still start after the earliest MDM3 transition.

The lower-risk first pass is:

```bash
adb shell dmesg > android-dmesg-full.txt
adb shell 'cat /proc/interrupts' > android-proc-interrupts.txt
adb shell 'find /sys/bus/msm_subsys/devices -maxdepth 2 -type f -print -exec cat {} \;' > android-msm-subsys.txt
adb shell 'cat /sys/kernel/debug/gpio' > android-debug-gpio.txt
```

Then classify the captured logs host-side with focused patterns:

```text
mdm
esoc
gpio
ap2mdm
mdm2ap
pmic
pm8150
pcie
subsys
cnss
wlfw_start
wlan_pd
```

## Safety Boundaries

- read-only Android collection only
- no Magisk module install in the first pass
- no native boot image change
- no `/dev/esoc-0` or `/dev/subsys_esoc0` open
- no Wi-Fi scan/connect credential use
- no DHCP/route/external ping

## Implementation Shape

Add a host-side classifier script:

```text
scripts/revalidation/native_wifi_android_dmesg_esoc_gpio_timing_v968.py
```

Inputs:

- V913 Android dmesg and process/fd evidence if still sufficient
- optional fresh Android `adb shell dmesg`
- optional `/proc/interrupts`
- optional `/sys/kernel/debug/gpio`
- optional `/sys/bus/msm_subsys/devices/*/state`

Outputs:

- first timestamp for `mdm_helper`, `cnss-daemon`, `wlfw_start`, `__subsystem_get`, WLAN-PD, ICNSS QMI, BDF, FW ready, and `wlan0`
- first timestamp and surrounding lines for eSoC/GPIO/PMIC/PCIe markers
- GPIO/IRQ attribution if marker names are visible
- decision label:
  - `android-dmesg-gpio-timing-attributed`
  - `android-dmesg-no-gpio-names-visible`
  - `android-dmesg-needs-magisk-early-sampler`
  - `android-dmesg-insufficient`

## Success Criteria

- Host-side manifest records input evidence paths and hashes.
- Classifier extracts Android-good ordering around `wlfw_start`, eSoC/GPIO/PCIe, and WLAN-PD.
- If GPIO labels are not visible, the result explicitly says a Magisk early sampler is justified.
- No live native mutation is performed.

## Follow-up

If V968 gets a clear Android-good GPIO/eSoC timeline, compare it against V963/V964 native post-provider trigger evidence before running V967 helper `v161` live. If Android logs are insufficient, create a minimal Magisk collection plan with strict timeout and bounded sampling.
