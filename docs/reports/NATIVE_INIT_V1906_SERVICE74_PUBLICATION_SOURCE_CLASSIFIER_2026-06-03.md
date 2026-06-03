# Native Init V1906 Service74 Publication Source Classifier

## Summary

- Cycle: `V1906`
- Type: host/source classifier over V1905 Android-good/native evidence and kernel service-notifier source
- Decision: `v1906-service74-root-service-publication-edge-host-pass`
- Label: `service74-root-service-publication-edge`
- Result: PASS
- Reason: Android normal publishes service-notifier instances 74 and 180 before WLFW/wlan_pd, while native post-open publishes only 180; source shows publication is QRTR service lookup by ICNSS-provided domain instance_id before listener msg20/state-up msg22/ACK msg23
- Evidence: `tmp/wifi/v1906-service74-publication-source-classifier`

## Evidence Edge

- V1905 decision/label/pass: `v1898-service180-present-wlan-pd-stateup-gap-host-pass` / `service180-present-wlan-pd-stateup-gap` / `True`
- Android normal times: `{"service180": 7.207397, "service74": 7.212351, "ssctl_modem": 7.175047, "wlan0": 15.001322, "wlan_pd": 9.619173, "wlfw_request": 8.827674}`
- Android service74/service180/wlan_pd/wlanmdsp/wlan0: `1` / `1` / `2` / `20` / `15.001322`
- Android contamination pre-wlan0 PCIe-MHI/eSoC/degraded257: `0` / `0` / `False`
- Android pm-service msg22 hits: `0`
- Native PM/open/msg22: register `0` connect `0` open `/dev/subsys_modem` fd `0x7` state `0x2` msg22 `0`
- Native service180/service74/wlan_pd: `1,1,1` / `0,0,0` / `0,0,0`
- Native listener/WLFW69/wlanmdsp/wlan0: `uninit` -> `uninit` / `0` / `0` / `0`

## Source Edge

- ICNSS receives service-locator domains and registers each domain with service-notifier: `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/icnss.c:1967`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/icnss.c:2000`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/icnss.c:2006`
- service-notifier creates a QRTR lookup keyed by the requested instance id and logs `new_server` with that instance: `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier.c:545`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier.c:327`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier.c:337`
- after `new_server`, listener registration sends SERVREG msg20, and state-up is msg22 with ACK msg23: `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier.c:343`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier.c:273`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier-private.h:21`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier-private.h:25`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier-private.h:26`
- state constants: UP `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/include/soc/qcom/service-notifier.h:23`, UNINIT `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/include/soc/qcom/service-notifier.h:25`
- restart-PD source exists but remains forbidden/non-selected: `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier.c:648`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/icnss.c:2598`, `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/service-notifier-private.h:28`

## Selected Diff

- Label: `service74-root-service-publication-edge`.
- The missing native edge is before listener msg20 and before wlan_pd state-up msg22: service-notifier never receives/publishes instance 74 in native, while Android normal does.
- Opening `/dev/subsys_modem` remains only a modem `subsys_get()` precondition; it does not by itself make the WLAN guest PD root-service instance publish.
- This keeps the target on internal modem service-notifier/WLFW state-up and excludes SDX50M, PCIe/MHI, eSoC, GDSC, PMIC, GPIO, regulator, restart-PD, and Wi-Fi HAL paths.

## Safety Scope

V1906 is host-only. It reads retained manifests and local kernel source, then writes local evidence/report artifacts. It performs no device command, flash, reboot, tracefs write, service start, Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external ping, PMIC/GPIO/GDSC/regulator write, forced RC1/case write, `/dev/subsys_esoc0` open, fake ONLINE state, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, firmware write, boot write, partition write, or restart-PD request.

## Next

- Next live candidate should be read-only internal-modem observability around ICNSS service-locator domain registration and service-notifier instance 74 lookup/publication.
- Do not attempt native Wi-Fi connect/ping until native init proves WLFW service69 and `wlan0`.
