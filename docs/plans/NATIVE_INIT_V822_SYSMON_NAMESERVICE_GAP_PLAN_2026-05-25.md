# Native Init V822 Sysmon Nameservice Gap Plan

## Goal

Classify why V821 sees kernel sysmon/service-locator progress in existing
evidence while userspace AF_QIPCRTR nameservice lookup returns clean-empty.

## Scope

- Target script:
  - `scripts/revalidation/native_wifi_sysmon_nameservice_gap_classifier_v822.py`
- Inputs:
  - `tmp/wifi/v821-qrtr-nameservice-matrix/manifest.json`
  - Samsung OSRC source under `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/`
- Source anchors:
  - `drivers/soc/qcom/sysmon-qmi.c`
  - `drivers/soc/qcom/service-locator-private.h`
  - `drivers/soc/qcom/service-locator.c`
  - `drivers/soc/qcom/service-notifier-private.h`
  - `drivers/soc/qcom/service-notifier.c`
  - `drivers/soc/qcom/wlan_firmware_service_v01.h`
  - `drivers/soc/qcom/icnss_qmi.c`
  - `arch/arm64/boot/dts/samsung/renovation/sm8150-sec-r3q-kor-overlay-r02.dts`

## Hard Gates

- Host-only classification; no bridge or device command.
- No QRTR socket open and no QRTR/QMI packet transmission.
- No custom kernel flash, boot image write, partition write, reboot, or
  bootloader handoff.
- No service-manager, Wi-Fi HAL, scan/connect/link-up, credential use, DHCP,
  route change, or external ping.
- Preserve V775 custom OSRC kernel flashing pause.

## Success Criteria

- V821 manifest exists and passed with decision
  `v821-qrtr-nameservice-matrix-empty-below-hal`.
- V821 matrix transport is valid: socket/readback ok, lookup ok, zero timeouts,
  zero service events.
- OSRC source constants are readable:
  - service-locator `0x40/1`
  - service-notifier `0x42/1`
  - sysmon SSCTL `0x2b/2`
  - WLFW `0x45/1`
- Board DTS exposes the mdm3 SSCTL instance `0x10`.
- V822 identifies whether the V821 matrix already covered the actual sysmon
  QMI lookup path.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_sysmon_nameservice_gap_classifier_v822.py

python3 scripts/revalidation/native_wifi_sysmon_nameservice_gap_classifier_v822.py \
  --out-dir tmp/wifi/v822-sysmon-nameservice-gap-plan-check \
  plan

python3 scripts/revalidation/native_wifi_sysmon_nameservice_gap_classifier_v822.py \
  run
```

## Next

If V822 confirms that V821 did not cover sysmon SSCTL, V823 should extend the
helper v125 matrix with `ssctl:43:16` before any QMI payload, service-manager,
Wi-Fi HAL, scan/connect, credential, DHCP, route, external ping, or custom
kernel flash.
