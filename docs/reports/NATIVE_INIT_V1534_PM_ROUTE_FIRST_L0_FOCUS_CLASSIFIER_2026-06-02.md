# Native Init V1534 PM Route First-L0 Focus Classifier

- Generated: `2026-06-01T16:55:38.760572+00:00`
- Decision: `v1534-current-pm-route-supersedes-old-gap-first-l0-focus`
- Pass: `True`
- Reason: Current SDX50M PM route already reaches pm-service/esoc0 and mdm_subsys_powerup; native now reaches RC1 LTSSM but fails before L0, while ICNSS workqueue and MHI PM-resume are downstream or non-trigger leads

## Fixed-Point Checks

| check | value |
| --- | --- |
| old_pm_dependency_gap_known | True |
| current_sdx50m_route_reaches_pm_esoc0 | True |
| current_route_reaches_powerup | True |
| native_v1345_no_lower_response | True |
| native_v1496_rc1_progress_no_l0 | True |
| native_v1496_link_failed | True |
| native_v1517_rc1_progress_no_l0 | True |
| test11_common_enable_not_missing | True |
| mhi_pm_resume_downstream | True |
| icnss_workqueue_not_first_l0 | True |
| wifi_goal_still_not_reached | True |

## Route Summary

| surface | value |
| --- | --- |
| v1178_old_gap | "late per_proxy caused dependency flag/order gap; useful historical model, not the active lowest blocker once current SDX50M route reaches esoc/powerup" |
| v1343_current_route | {"decision": "v1343-sdx50m-route-esoc-powerup-observed", "per_mgr_esoc0_any": true, "sdx50m_registered": true, "wlan0_up": false, "wlfw_or_wlan_dmesg_seen": false} |
| v1345_lower_response | {"decision": "v1345-current-route-mdm2ap-full-window-no-transition", "gpio142_irq_delta": 0, "mhi_pipe_seen": false, "pcie_transition_seen": false, "reason": "current private SDX50M route reached mdm_subsys_powerup, but full timing window saw no GPIO142/errfatal/PCIe/MHI/ks/WLFW/wlan0 transition", "timing_pm_service_powerup_seen": true, "wlan0_seen": false} |
| v1496_rc1 | {"decision": "v1496-test-boot-downstream-progress-rollback-pass", "mhi_progress": false, "progress_decision": "rc1-ltssm-link-failed-no-l0", "provider_trigger": true, "rc1_l0": false, "rc1_link_failed": true, "rc1_progress": true, "wlan0_present": false} |
| v1533_icnss | {"decision": "v1533-icnss-queue-pair-is-hdd-register-path-not-first-l0-trigger", "icnss_queue_to_pm_esoc0_ms": 2781.081, "icnss_queue_to_qmi_ms": 3541.197} |

## Classification

| field | value |
| --- | --- |
| pm_actionability_status | superseded for the active blocker: current route has positive SDX50M registration and per_mgr_esoc0 evidence |
| active_lowest_blocker | PCIe RC1 endpoint readiness/link training: LTSSM progresses but L0 is absent and link fails |
| not_next | ['repeat old late-per_proxy dependency repair as the primary blocker', 'ICNSS workqueue/FW-ready/BDF analysis before native L0', 'MHI PM-resume or ks/MHI pipe analysis before PCI enumeration', 'Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping'] |

## Interpretation

- V1178 remains useful history for why late `per_proxy` could miss the dependency flag, but it is no longer the active lowest blocker once the current SDX50M route reaches `per_mgr_esoc0` and `mdm_subsys_powerup`.
- V1343/V1345 prove PM/eSoC actionability is available but lower response is absent; V1496/V1517 then move the failure further down to RC1 LTSSM progress with no L0.
- V1523 proves TEST:11 and normal pci-msm callers share the core enumerate/enable path, so the remaining difference is endpoint readiness or trigger semantics before successful L0.
- V1525 and V1533 close MHI PM-resume and ICNSS workqueue as immediate first-L0 leads.

## Next Gate

- Cycle: `V1535`
- Summary: design a bounded first-L0 trigger/readiness observer or test-boot focused on endpoint readiness around msm_pcie_enumerate, not PM registration or firmware/MHI
- Recommended: classify Android-good vs native-fail first-L0 trigger candidates using V1523 normal callers: endpoint wake GPIO104, sysfs/client enumerate, or vendor request path
- Recommended: if live is needed, capture only PCIe RC1/PERST/refclk/LTSSM/WAKE around the current provider trigger with rollback; do not start scan/connect
- Recommended: keep PM actor changes limited to already proven current SDX50M route unless evidence shows pm-service no longer opens esoc0

## Safety

Host-only classifier. It reads existing manifests and reports only; it performs no device command, flash, reboot, PM actor start, tracefs/sysfs/debugfs write, Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external ping, PMIC/GPIO/GDSC write, PCI rescan, or platform bind/unbind.
