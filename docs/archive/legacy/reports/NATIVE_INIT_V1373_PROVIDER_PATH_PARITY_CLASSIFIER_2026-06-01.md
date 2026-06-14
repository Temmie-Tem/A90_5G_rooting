# Native Init V1373 Provider-path Parity Classifier

## Summary

- Cycle: `V1373`
- Type: host-only provider-path parity classifier
- Decision: `v1373-gap-is-android-participant-plus-rc1-combination`
- Result: PASS
- Script: `scripts/revalidation/native_wifi_provider_path_parity_classifier_v1373.py`
- Evidence:
  - `tmp/wifi/v1373-provider-path-parity-classifier/manifest.json`
  - `tmp/wifi/v1373-provider-path-parity-classifier/summary.md`

## Decision

existing evidence has tested PM actors without corrected RC1 enumerate, corrected RC1 enumerate without PM actors, and raw provider-hold plus corrected RC1 enumerate without Android mdm_helper/pm-service context; the untested narrow combination is Android participant parity plus corrected RC1 enumerate

## Checks

| check | status | detail |
| --- | --- | --- |
| android-positive-reference-still-valid | pass | Android reaches GPIO142, RC1 L0, FW-ready, and wlan0 |
| android-command-engine-before-lower-success | pass | Android has mdm_helper CMD_ENG/WAIT_FOR_REQ plus pm-service esoc0 path |
| native-pm-actor-path-does-not-enumerate-rc1 | pass | native PM path reaches mdm_helper/pm-service but keeps pcie1/GPIO142/WLFW silent |
| native-manual-rc1-path-lacks-android-participants | pass | V1370 exercises corrected RC1 enumerate without provider/PM participants and stops before L0 |
| native-raw-provider-plus-rc1-still-lacks-command-engine | pass | V1372 combines raw provider holder with RC1 enumerate, but not Android mdm_helper/pm-service context |

## Coverage Matrix

| path | mdm_helper CMD | pm-service esoc0 | provider | case11 | RC1 L0 | wlan0 | meaning |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Android V852/V1158 reference | True | True | True | False | True | True | known-good lower Wi-Fi path; no native credentials/connect involved |
| Native V1228/V1239/V1246 PM path | True | True | True | False | False | False | Android-like PM actors reach mdm_subsys_powerup, but RC1 remains off/silent |
| Native V1370 corrected RC1 enumerate | False | False | False | True | False | False | AP-side RC1 enumerate reaches PHY/LTSSM but no endpoint response |
| Native V1372 raw provider + corrected RC1 enumerate | False | False | True | True | False | False | direct provider holder plus RC1 enumerate still lacks endpoint readiness |

## Android Reference

| field | value |
| --- | --- |
| v852_positive | True |
| v1158_fw_ready | True |
| v1158_mdm_helper_cmd_engine | True |
| v1158_pm_service_esoc0 | True |
| v1371_android_esoc0_to_rc1_sec | 0.254929 |
| v1371_android_release_to_l0_sec | 0.016666 |
| v1239_android_gpio142_irq | 1 |
| v1239_android_pcie_l0_lines | 2 |
| v1239_android_wlan0 | True |

## Native Paths

| field | value |
| --- | --- |
| v1228_mdm_helper_wait_req | True |
| v1228_pm_service_attempt_no_downstream | True |
| v1239_pm_service_gap_after_esoc0 | True |
| v1246_same_run_gdsc_silent | True |
| v1370_case11_no_l0 | True |
| v1372_raw_provider_case11_no_l0 | True |
| v1372_no_gpio142_pci_mhi_wlan | True |

## V1246 Same-run Power Snapshot

| field | value |
| --- | --- |
| mdm_status_count_total | 0 |
| mhi_bus_count | 0 |
| mhi_pipe_exists | 0 |
| monotonic_ms | 836103 |
| pci_dev_count | 0 |
| pcie0_gdsc_line | pcie_0_gdsc                      0    1      0     0mV     0mA     0mV     0mV |
| pcie1_gdsc_line | pcie_1_gdsc                      0    2      0     0mV     0mA     0mV     0mV |
| phase | late_per_proxy_poll_00 |
| pmic_soft_reset_line | pin 7 (gpio9): (MUX UNCLAIMED) c440000.qcom,spmi:qcom,pm8150l@4:pinctrl@c000:1270 |
| wlan0_exists | 0 |

## V1374 Candidate

- Name: `android-participant-parity-plus-corrected-rc1-enumerate`
- Scope: source/build-only design first; live gate only after explicit script preflight
- Rationale: V1372 proved a raw provider holder is not equivalent to Android's mdm_helper plus pm-service/per_proxy path. The next narrow test must combine the Android participant set with the already-proven corrected RC1 enumerate path, rather than retrying upper Wi-Fi HAL or direct GPIO.

### Candidate Order

- preflight native selftest fail=0 and debugfs mount state
- start only lower Android participant parity needed for mdm_helper CMD_ENG and pm-service esoc0 path
- confirm /dev/esoc-0 fd, ESOC_WAIT_FOR_REQ/CMD_ENG evidence, and pm-service /dev/subsys_esoc0 wchan
- write only rc_sel=2 then case=11 after the provider window is confirmed
- capture GPIO142, LTSSM/L0, PCI/MHI, WLFW/BDF/wlan0 markers, cleanup, and post-selftest

### Hard Stops

- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping
- no direct PMIC/GPIO/GDSC writes
- no PERST assert/deassert debug cases beyond pci-msm case11's normal enumerate path
- no eSoC notify or BOOT_DONE spoof
- no flash, boot image write, or partition write

## Safety

- V1373 is host-only and executes no device command.
- No PM actor start, `/dev/subsys_esoc0` open, debugfs write,
  PMIC/GPIO/GDSC write, eSoC notify/`BOOT_DONE`, Wi-Fi HAL,
  scan/connect, credential handling, DHCP/routes, external ping, flash,
  boot image write, or partition write occurred.

## Next

V1374 should be a source/build-only design for a bounded live gate that starts mdm_helper/PM actor parity, confirms /dev/esoc-0 and /dev/subsys_esoc0 readiness, then runs corrected rc_sel=2 + case=11 with reboot cleanup; still no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping
