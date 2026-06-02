# Native Init V1723 CNSS Output Visibility Reclassification

## Summary

- Cycle: `V1723`
- Type: host-only correction/reclassification classifier
- Decision: `v1723-wlfw-start-reached-downstream-block-by-nonlog-pass`
- Result: `PASS`
- Evidence: `tmp/wifi/v1723-cnss-output-visibility-reclassify`

## Corrections Applied

- Retract the QCACLD-register-as-WLFW-trigger premise: `icnss_register_driver` waits for later firmware readiness and is not a WLFW server trigger.
- Treat native `wlfw_start` dmesg/log absence as a measurement artifact: `cnss-daemon` logs through Android logging unless its kmsg path is visible.
- Stop adding PM/service-window actors for this gate; use only the existing internal-modem firmware-serve route evidence.

## Reused One-Run Evidence

- V1695 output label: `cnss-output-still-invisible`
- V1695 property lookup all_match: `1`
- V1695 kmsg/debug property match: `1 / 1` / `4 / 1`
- V1695 first init failure slug: `none`
- V1716 non-log label: `pm-init-register-call-no-return`
- V1716 `wlfw_start` uprobe hit: `True`
- V1716 `pm_client_register` no-return: `True`
- V1719 non-log label: `peripheral-default-service-manager-call-no-return`
- V1719 default service-manager block: `True`

## Fixed Label

- Contract label: `wlfw-start-reached-downstream-block`
- Refined blocker: `vendor-binder-default-service-manager-acquisition`

The strict output-only branch still reads `cnss-output-still-invisible`, but V1716/V1719 non-log trace proves `cnss-daemon` reaches `wlfw_start`. Therefore the corrected classifier resolves the gate as `wlfw-start-reached-downstream-block`, refined to the current Binder bootstrap blocker before `String16('vendor.qcom.PeripheralManager')`.

## Checks

- `v1695_output_gate_ran`: `True`
- `v1695_no_service_manager_pm_scope`: `True`
- `v1695_kmsg_property_match`: `True`
- `v1695_debug_property_match`: `True`
- `v1703_logging_artifact_accepted`: `True`
- `v1716_wlfw_start_hit`: `True`
- `v1716_pm_register_no_return`: `True`
- `v1719_default_service_manager_block`: `True`
- `v1720_qcacld_premise_retracted`: `True`
- `v1722_fallback_ready`: `True`

## Safety Scope

This script performed host-only analysis only. It did not contact the device, flash, reboot, start service-manager or PM actors, start `boot_wlan`, use `/dev/subsys_esoc0`, force RC1, fake ONLINE state, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE`, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.

## Next Gate

- Do not repeat output-visibility live variants; V1695 already set the output-only label and V1716/V1719 supplied the non-log discriminator.
- V1722 remains the prepared source/build fix for the next bounded live step: service-manager-binary VND Binder bootstrap using `/system/bin/servicemanager /dev/vndbinder`.
- The next live gate must be scoped as service-manager-only bootstrap, not PM trio, `vendor.qcom.PeripheralManager`, `boot_wlan`, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.
