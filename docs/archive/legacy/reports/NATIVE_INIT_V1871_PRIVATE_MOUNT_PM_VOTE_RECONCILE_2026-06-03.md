# Native Init V1871 Private Mount PM Vote Reconcile

## Summary

- Cycle: `V1871`
- Type: host-only private-mount PM-vote reconciliation
- Decision: `v1871-private-mount-does-not-close-pm-vote-gap-host-pass`
- Label: `private-mount-selection-closed-pm-vote-gap-open`
- Result: PASS
- Reason: V1870 proves the rollbackable private SDX50M mount and PM selection path, but firmware request, WLFW service 69, and wlan0 remain absent; continue with the V1755 narrow PM register/vote contract repair rather than another private-mount retry.
- Evidence: `tmp/wifi/v1871-private-mount-pm-vote-reconcile`

## Checks

| check | value |
|---|---:|
| `v1870_private_mount_contract_closed` | `True` |
| `v1870_pm_client_returned` | `True` |
| `v1870_firmware_request_absent` | `True` |
| `v1870_wifi_prereq_absent` | `True` |
| `v1755_pm_vote_split_gate_fixed` | `True` |
| `v1753_android_good_requests_firmware` | `True` |
| `v1736_service_route_still_no_request` | `True` |
| `hard_stops_preserved` | `True` |

## V1870 Private Mount

- decision/pass/rollback: `v1870-private-mount-sdx50m-selected-rollback-pass` / `True` / `True`
- private label/contract/bind: `private-mount-sdx50m-selected` / `True` / `0`
- PM client register/connect rc: `0` / `0`
- requested_wlanmdsp/WLFW69/wlan0: `0` / `0` / `0`

## PM Vote Split

- V1755 label: `pm-vote-contract-split-gate-needed`
- V1755 reason: static CNSS PM imports, Android-good PM vote, native V1736 CNSS-only progress, and V1686 PM-trio binder failure show a split gate: repair the PM register/vote contract, not broad PM/eSoC/HAL actors
- Android-good V1753 requested_wlanmdsp/requested_pd_image: `1` / `1`
- Native V1736 requested_wlanmdsp/WLFW69: `0` / `0`

## Interpretation

V1870 closes the rollbackable private SDX50M mount evidence gap, but it does not close the firmware-request gate. The route still has no `wlanmdsp` request, no WLFW service 69, and no `wlan0`; therefore Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping remain blocked.

The next information-gaining unit is the narrow V1755 PM register/vote contract repair. Another private-mount retry would only repeat a now-closed selection proof while leaving the same firmware-request absence.

## Next

- V1872 should be source/build-only first: repair or instrument the PM register/vote contract around the V1736 service-manager route.
- Success should be an observable PM vote plus `requested_wlanmdsp=1` or `requested_pd_image=1`; only then re-check WLFW service 69 and `wlan0`.
- Do not attempt Wi-Fi connect or ping until WLFW service 69 and `wlan0` are present.

## Safety Scope

V1871 is host-only. It does not contact the device, flash, reboot, start services, open `/dev/subsys_esoc0`, force RC1, fake ONLINE state, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE`, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
