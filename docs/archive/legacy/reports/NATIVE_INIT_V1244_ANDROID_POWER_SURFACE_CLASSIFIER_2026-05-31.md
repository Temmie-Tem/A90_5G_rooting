# V1244 Android/native SDX50M Power Surface Classifier

- report: `docs/reports/NATIVE_INIT_V1244_ANDROID_POWER_SURFACE_CLASSIFIER_2026-05-31.md`
- classifier: `scripts/revalidation/native_wifi_android_power_surface_classifier_v1244.py`
- evidence: `tmp/wifi/v1244-android-power-surface-classifier/manifest.json`
- result: `v1244-android-pmic-pcie-delta-classified`
- pass: `true`

## Scope

V1244 is a host-only classifier. It compares existing Android-positive boot
evidence against the V1243 native SDX50M response sampler. It does not run any
device command and does not mutate device state.

The goal is to avoid another blind `esoc0` retry and classify whether the native
path is missing the same PMIC/PCIe power surface that Android reaches before
GPIO142, PCIe RC1, MHI, WLFW, and `wlan0`.

## Inputs

| Input | Path |
| --- | --- |
| Android GPIO snapshot | `tmp/wifi/v1024-fast-fd-android-timing-handoff-live-20260526-181232/v1022-late-android-pm-esoc-timing/android/commands/gpio.txt` |
| Android dmesg | `tmp/wifi/v1024-fast-fd-android-timing-handoff-live-20260526-181232/v1022-late-android-pm-esoc-timing/android/commands/dmesg-full.txt` |
| Android PCIe reference | `docs/reports/NATIVE_INIT_V1045_PM_PIL_PREREQUISITE_DELTA_2026-05-26.md` |
| Native V1243 manifest | `tmp/wifi/v1243-sdx50m-power-prereq-response-live/manifest.json` |
| SDX50M DTS contract | `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/arch/arm64/boot/dts/samsung/renovation/sm8150-sec-r3q-kor-overlay-r00.dts` |

## Findings

| Surface | Android-positive | Native V1243 |
| --- | --- | --- |
| PM8150L soft-reset GPIO | `gpio9 : out normal vin-1 pull-down 10uA push-pull high low atest-1 dtest-0` | `pin 7 (gpio9): (MUX UNCLAIMED) c440000.qcom,spmi:qcom,pm8150l@4:pinctrl@c000:1270` |
| PCIe GDSC | PCIe RC1 link initialized at `8.820s` in the Android-positive reference | `pcie_1_gdsc` and `pcie_0_gdsc` remain `0mV` |
| GPIO142 / MDM status | Android reaches WLAN-PD, ICNSS-QMI, FW ready, and `wlan0` | GPIO142 count remains `[0]` |
| Downstream devices | Android reaches WLFW/BDF/`wlan0` | PCI device count `[0]`, MHI bus count `[0]`, `wlan0` `[0]` |

Android-positive dmesg contains the expected lower chain:

| Marker | Time | Meaning |
| --- | --- | --- |
| `cnss-daemon wlfw_start: Starting` | `8.198751` | CNSS upper path begins |
| `__subsystem_get: esoc0 count:0` | `8.301226` | `pm-service` enters SDX50M subsystem powerup |
| `msm/modem/wlan_pd` | `9.389949` | WLAN-PD notification arrives |
| `icnss_qmi: QMI Server Connected` | `9.392257` | ICNSS QMI connects |
| `icnss: WLAN FW is ready` | `14.400537` | WLAN firmware ready |
| `dev : wlan0 : event : 16` | `15.215998` | `wlan0` appears |

## Interpretation

V1244 narrows the active blocker below Binder/peripheral-manager delivery and
inside or immediately after the proprietary `mdm_subsys_powerup` path. The native
path reaches `pm-service` `/dev/subsys_esoc0`, but it does not reproduce
Android's PM8150L soft-reset pinctrl ownership, PCIe GDSC enablement, GPIO142
response, PCIe RC1 link-up, MHI, WLFW, or `wlan0`.

The most defensible next gate is not another blind late-`per_proxy` or CNSS/HAL
retry. V1245 should prove whether native `mdm_subsys_powerup` reaches PM8150L
soft-reset/GDSC operations, or reproduce Android's PMIC pinctrl setup before
another bounded `esoc0` trigger.

## Validation

| Command | Result |
| --- | --- |
| `python3 -m py_compile scripts/revalidation/native_wifi_android_power_surface_classifier_v1244.py` | pass |
| `python3 scripts/revalidation/native_wifi_android_power_surface_classifier_v1244.py run` | pass |

## Safety

- host-only classifier; no device command or mutation executed
- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, Wi-Fi bring-up, flash, boot image write, or partition write
