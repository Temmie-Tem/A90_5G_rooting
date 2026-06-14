# Native Init V1322 SDX50M Response-input Classifier

## Summary

- Cycle: `V1322`
- Type: host-only response-input classifier
- Decision: `v1322-response-inputs-classified-next-provider-wait-cause`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1322-sdx50m-response-input-classifier/manifest.json`
  - `tmp/wifi/v1322-sdx50m-response-input-classifier/summary.md`
- Script: `scripts/revalidation/native_wifi_sdx50m_response_input_classifier_v1322.py`

V1322 consolidates the response-input branch after V1321. The native path
already reaches the PM userspace actor and `mdm_subsys_powerup`. Read-only
surfaces for SDX50M metadata, GPIO142 IRQ, PCIe, regulators, GDSC, TLMM,
and tracefs events are available or have been sampled. Static PMIC/TLMM
shape is not the shortest blocker anymore, and V1318 proves GPIO135 high is
visible in the first-power-on trace. The remaining blocker is the provider
wait/response cause: no GPIO142 IRQ, PCIe RC1/MHI, WLFW/BDF, or `wlan0`
follows native GPIO135 / `mdm_subsys_powerup`.

## Decision

Do not repeat image-link, PM actor delivery, static GPIO parity, or broad
read-only response-surface gates. V1323 should classify the provider wait
cause around `mdm_subsys_powerup`, GPIO142/MDM2AP, and `err_ready`: source
and host-only first, then only a bounded read-only or reboot-bounded live
gate if needed. Direct PMIC/GPIO/GDSC/eSoC writes and Wi-Fi HAL/connect
remain blocked.

## Safety

Host-only classifier. No device command, PM actor start, `mdm_helper` start,
tracefs write, live eSoC ioctl/notify, PMIC write, GPIO line request, direct
GDSC/eSoC write, Wi-Fi HAL start, scan/connect, credential use, DHCP/routes,
external ping, flash, boot image write, or partition write occurred.
