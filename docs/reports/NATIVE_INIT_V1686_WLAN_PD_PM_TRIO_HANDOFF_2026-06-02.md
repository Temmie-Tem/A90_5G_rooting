# Native Init V1686 WLAN-PD PM-trio Service-window Handoff

## Summary

- Cycle: `V1686`
- Type: one-run rollbackable WLAN-PD PM-trio service-window gate
- Decision: `v1686-pm-trio-child-failed-rollback-pass`
- Result: PASS
- Reason: one WLAN-PD PM-trio service-window gate run produced a fixed label and rollback verified
- Evidence: `tmp/wifi/v1686-wlan-pd-pm-trio-handoff`
- Rollback attempt: `from-native`

## Gate Label

- Label: `pm-trio-child-failed`
- legacy firmware-serve label: `firmware-not-requested`
- subsys_modem holder opened: `1`
- pm_proxy_helper running: `0`
- per_mgr running: `1`
- per_proxy running: `1`
- tftp running: `1`
- cnss-daemon started: `1`
- wlfw_start seen: `0`
- wlfw_service_request seen: `0`
- WLFW service 69 seen: `0`
- requested wlanmdsp: `0`
- companion order: `servicemanager,hwservicemanager,vndservicemanager,qrtr_ns,pd_mapper,rmt_storage,tftp_server,pm_proxy_helper,per_mgr,per_proxy,subsys_modem_holder,cnss_diag,cnss_daemon,pm-service-window-trigger-summary`

## Evidence Notes

- `pm_proxy_helper` did not crash: it exited with code `0`, signal `0`, and was reaped before the observation window. This matches the previously captured Android init contract where `vendor.per_proxy_helper` is a disabled `oneshot` service.
- `per_mgr` and `per_proxy` stayed observable/running until cleanup, then were terminated by the harness with signal `15`.
- `pm-service` and `pm-proxy` repeatedly logged Binder transaction failures: `transaction failed 29189/-22`.
- No `wlfw_start`, `wlfw_service_request`, WLFW service 69, `wlanmdsp.mbn` request, or `wlan0` appeared.
- The emitted `pm-trio-child-failed` label is conservative for V1686 because the helper summary treated `pm_proxy_helper_running=0` as failure even though the process completed as a one-shot with exit code `0`.

## Safety Scope

- `/dev/subsys_esoc0`, raw eSoC ioctl, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify, and BOOT_DONE spoof were not used.
- `mdm_helper`, Wi-Fi HAL, `wificond`, scan/connect, credentials, DHCP/routes, and external ping were not used.
- Mutation scope was test boot flash followed by rollback to `stage3/boot_linux_v724.img`.

## Rollback

- Rollback attempt: `from-native`
- Rollback result: PASS
- Post-rollback version: `A90 Linux init 0.9.68 (v724)`
- Post-rollback selftest: `fail=0`

## Next

- Stop after this one label.
- If label is `wlfw-start-reached`, the next gate may inspect WLFW service 69 / WLAN-PD / firmware serving.
- If label is `pm-trio-still-no-wlfw`, PM trio alone is not the missing WLAN-PD trigger; analyze Android-good PM/CNSS inputs before adding any lower-layer work.
- For this run, treat `pm-trio-child-failed` as a PM lifecycle/classifier issue, not a `pm_proxy_helper` crash.
- Next source/build work should classify `pm_proxy_helper` one-shot exit `0` as acceptable and focus on why `pm-service` / `pm-proxy` Binder transactions return `-22`.
- Do not proceed to MSA/BDF, Wi-Fi HAL, scan/connect, DHCP/routes, credentials, or external ping until WLFW service 69 or `wlfw-start-reached` appears.
