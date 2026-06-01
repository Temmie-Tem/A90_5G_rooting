# Native Init V1570 MDM Helper FD Gate Classifier

## Summary

- Cycle: `V1570`
- Type: host-only mdm_helper fd-gate regression classifier
- Decision: `v1570-select-mdm-helper-launch-contract-delta`
- Result: PASS
- Reason: V1569 reproduces the service-window no-fd gate with complete result output while Android and reduced native paths prove mdm_helper can hold /dev/esoc-0; next work should compare mdm_helper launch contract, not retry RC1 or Wi-Fi connect
- Evidence: `tmp/wifi/v1570-mdm-helper-fd-gate-classifier`

## Inputs

- `android_mdm_helper_strace_v1158`: `docs/reports/NATIVE_INIT_V1158_ANDROID_MDM_HELPER_EXTENDED_STRACE_CAPTURE_2026-05-27.md`
- `native_reduced_positive_v1228`: `docs/reports/NATIVE_INIT_V1228_MDM_HELPER_EARLY_COMPACT_TRACE_LIVE_2026-05-31.md`
- `service_window_prior_negative_v1008`: `docs/reports/NATIVE_INIT_V1008_SERVICE_WINDOW_FD_POLL_LIVE_2026-05-26.md`
- `service_window_delta_v1009`: `docs/reports/NATIVE_INIT_V1009_V911_V1008_CONTRACT_COMPARATOR_2026-05-26.md`
- `current_v1569_report`: `docs/reports/NATIVE_INIT_V1569_SERVICE_WINDOW_RESULT_HANDOFF_2026-06-02.md`
- `helper_source`: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- `v1569_manifest`: `tmp/wifi/v1569-service-window-result-handoff/manifest.json`

## Checks

- `v1569_handoff_and_rollback_ok`: `True`
- `v1569_result_file_seen`: `True`
- `v1569_contract_seen`: `True`
- `v1569_no_esoc_fd`: `True`
- `v1569_trigger_not_attempted`: `True`
- `android_v1158_mdm_helper_esoc_fd`: `True`
- `native_v1228_mdm_helper_esoc_fd`: `True`
- `prior_service_window_same_negative`: `True`
- `prior_delta_positive_vs_negative`: `True`
- `helper_has_service_window_route`: `True`
- `helper_has_mdm_helper_positive_modes`: `True`

## Interpretation

V1569 is not an RC1/LTSSM failure in the active service-window route. It is a pre-RC1 fd-gate failure: `mdm_helper` starts but does not hold `/dev/esoc-0`, so the reviewed scoped `/dev/subsys_esoc0` trigger is not attempted.

This is a known delta rather than a one-off: Android V1158 and reduced native V1228 prove `/dev/esoc-0` ownership is achievable, while V1008/V1009 and V1569 show the Android service-window route still misses that ownership predicate.

## Next Gate

V1571 source/build-only: add a service-window mdm_helper launch-contract comparator that records mdm_helper argv/env/properties/dev-node/context, compares against known positive mdm-helper modes, and only then decides whether to start a bounded live fd acquisition gate

## Safety Scope

This classifier is host-only. It performs no device command, flash, reboot, partition write, Wi-Fi scan/connect, credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, blind eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind.
