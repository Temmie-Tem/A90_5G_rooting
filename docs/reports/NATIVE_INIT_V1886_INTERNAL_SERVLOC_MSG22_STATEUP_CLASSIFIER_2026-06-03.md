# Native Init V1886 Internal Servloc/msg22 State-up Classifier

## Summary

- Cycle: `V1886`
- Type: host-only reconciliation classifier for internal-modem WLAN-PD discovery versus state-up
- Decision: `v1886-servloc-present-msg22-stateup-missing-host-pass`
- Label: `servloc-domain-present-msg22-stateup-missing`
- Result: PASS
- Reason: native already resolves the internal WLAN-PD service-locator domain and PM/open succeeds, so discovery is not the trigger; the missing edge is the post-PM msg22/servreg state-up transition that Android normal reaches before wlanmdsp
- Evidence: `tmp/wifi/v1886-internal-servloc-msg22-stateup-classifier`

## Reconciled Inputs

- V1737 prior decision/label/pass: `v1737-modem-side-wlan-pd-start-trigger-gap-pass` / `modem-side-wlan-pd-start-trigger-gap` / `True`
- V1834 decision/pass: `v1834-qipcrtr-bound-recv-poll-timeout-passive-rollback-pass` / `True`
- V1885 decision/label/pass: `v1885-internal-pm-qmi-servreg-trigger-source-diff-host-pass` / `pm-msg22-servreg-trigger-trace-gap` / `True`

## Service-locator Is Not The Trigger

- Domain label: `servloc-domain-wlan-pd-instance180`
- service-locator endpoint/status/result: `1`:`16464` / `found` / `domain-list-response-success`
- service-locator domain/name/instance: `1` / `msm/modem/wlan_pd` / `180`
- service-notifier early qmi/state/indication/result: `1` / `uninit` / `0` / `listener-response-success`
- service-notifier late qmi/state/indication/result: `1` / `uninit` / `0` / `listener-response-success`
- raw service-locator/servloc-domain/service180/service74/wlan_pd counts: `2,2,2` / `0,0,0` / `1,1,1` / `0,0,0` / `0,0,0`

## Msg22/State-up Edge

- pm-service msg22 dispatch/request/response/indication/pending-slot: `True` / `True` / `True` / `True` / `True`
- libperipheral QMI imports: `False`
- Android PM vote / WLFW request / wlanmdsp times: `04:17:30.688` / `04:17:30.756` / `04:17:31.380`
- Android wlan_pd / wlan0 seconds and PCIe/MHI-before-wlan0: `9.672951` / `15.242158` / `0`
- Android retained msg22 log hits / observable: `0` / `False`
- Native PM register/connect/open: `0` / `0` / `/dev/subsys_modem` fd `0x7` state `0x2`
- Native post-ack open/msg22-ind hits: `1` / `0`
- Native WLFW request/ind-register/cap hits: `1` / `0` / `0`
- Native wlanmdsp/WLFW69/wlan0 and states: `0` / `0` / `0` / `uninit` -> `uninit`

## Selected Diff

- Label: `servloc-domain-present-msg22-stateup-missing`.
- Native already has the internal `msm/modem/wlan_pd` service-locator domain response for instance `180`, so the remaining blocker is not domain discovery.
- Native PM register/connect succeeds and pm-service opens `/dev/subsys_modem`, but the post-ack msg22 indication path stays at zero and service-notifier remains `uninit`.
- Android normal reaches PM vote, WLAN-PD state indication, WLFW connection, `wlanmdsp.mbn`, and `wlan0` with zero PCIe/MHI contamination; retained Android logs still lack pm-service msg-id observability.
- The next live comparison must trace pm-service QMI msg IDs plus service-locator/service-notifier/SSCTL across the normal Android PM-vote to `wlanmdsp` window, then the same native post-open window.

## Safety Scope

V1886 is host-only. It reads retained manifests/reports and writes local classifier artifacts only. It performs no device command, flash, reboot, property staging, tracefs write, service start, Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external ping, PMIC/GPIO/GDSC write, forced RC1/case write, `/dev/subsys_esoc0` open, fake ONLINE state, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, firmware write, boot write, or device partition write.

## Next

- Capture only a normal Android boot window, not the degraded 257s boot: PM vote through first `wlanmdsp.mbn` request.
- Required read-only signals: pm-service QMI msg `0x20/0x21/0x22` request/response/indication, service-locator domain-list, service-notifier state/indication/ACK, SSCTL, tftp `wlanmdsp.mbn`, and absence of PCIe/MHI before `wlan0`.
- Do not attempt Wi-Fi connect or ping until native init proves WLFW service 69 and `wlan0` are both present.
