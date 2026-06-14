# Native Init V931 CNSS Service-Manager Matrix Live Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| live matrix runner | `scripts/revalidation/native_wifi_cnss_service_manager_matrix_live_v931.py` | `py_compile pass` |
| bounded live proof | `tmp/wifi/v931-cnss-service-manager-matrix-live/manifest.json` | `v931-wlfw-precondition-missing-no-open` |

V931 ran helper `v154` in the CNSS/service-manager matrix mode with
`service_manager_order=after-mdm-helper-esoc-fd`. The run passed because it
started the intended lower actors, observed the `mdm_helper` `/dev/esoc-0`
window, started the service-manager trio and CNSS actors, then failed closed
without opening `/dev/subsys_esoc0` because the WLFW precondition never appeared.

## Implementation

- Added `scripts/revalidation/native_wifi_cnss_service_manager_matrix_live_v931.py`.
- Reuses the V923 live harness with helper `v154` defaults from V929/V930.
- Fixes the allowed-action set for this matrix by permitting
  `service_manager_start_executed` while continuing to forbid Wi-Fi HAL,
  scan/connect, credentials, DHCP/routes, external ping, controller eSoC
  notify, and controller `BOOT_DONE`.
- Default order is `after-mdm-helper-esoc-fd`:
  property shim, `pm-service`, `mdm_helper`, `/dev/esoc-0` fd gate,
  `servicemanager`, `hwservicemanager`, `vndservicemanager`, `cnss_diag`,
  `cnss-daemon`, WLFW-precondition gate, then the still-gated
  `/dev/subsys_esoc0` child.

## Findings

- Remote helper parity passed:
  - expected helper SHA-256 matched;
  - expected marker `a90_android_execns_probe v154` matched;
  - expected matrix mode support was present.
- Runtime actors were attempted:
  - `pm-service`;
  - `mdm_helper`;
  - `servicemanager`;
  - `hwservicemanager`;
  - `vndservicemanager`;
  - `cnss_diag`;
  - `cnss-daemon -n -l`.
- `mdm_helper` reached the expected lower window:
  - `/dev/esoc-0` fd count became `1`;
  - fd target was the private runtime namespace mirror.
- WLFW precondition did not appear:
  - `wlfw_precondition_observed=0`;
  - `compact_surface_poll=31`;
  - `surface_poll_count=32`;
  - result `wlfw-precondition-missing-no-open`.
- The gated subsystem trigger stayed closed:
  - `subsys_esoc0_open_attempted=0`;
  - `subsys_trigger.started=0`;
  - `reg_req_eng_attempted=0`;
  - `notify_attempted=0`;
  - `boot_done_attempted=0`.

## Interpretation

This closes the first service-manager matrix order. Starting service managers
after the `mdm_helper` `/dev/esoc-0` fd appears does not create the missing WLFW
precondition. That means the remaining blocker is not simply absence of Binder
service-manager processes in the lower window.

The next useful unit should be host-only classification of matrix-order deltas:

- V927: CNSS before eSoC without service-manager matrix;
- V603/V601-era evidence: service-manager effects on CNSS Binder failures;
- V931: service-manager after `mdm_helper` `/dev/esoc-0` fd.

The Android dmesg / GPIO / Magisk direction remains a fallback, not the next
default step. V913 already added the bounded Android read-only collector, and
V914 reclassified its evidence: Android proves WLFW/BDF/`wlan0` positivity, but
post-boot lower markers such as `subsys9=ONLINE`, GPIO142 count, current `ks`,
or current MHI pipe are not mandatory success criteria.

## Guardrails

- No Wi-Fi HAL start.
- No scan/connect/link-up.
- No credentials.
- No DHCP, route mutation, or external ping.
- No controller eSoC notify.
- No controller `BOOT_DONE`.
- No module load/unload.
- No boot image write.
- No partition write.
- No firmware mutation.
- No GPIO, sysfs, or debugfs write.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_cnss_service_manager_matrix_live_v931.py
python3 scripts/revalidation/native_wifi_cnss_service_manager_matrix_live_v931.py \
  --out-dir tmp/wifi/v931-cnss-service-manager-matrix-plan-check \
  plan
python3 scripts/revalidation/native_wifi_cnss_service_manager_matrix_live_v931.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-cnss-service-manager-matrix \
  --allow-cleanup-reboot \
  --assume-yes \
  run
```

Evidence:

- `tmp/wifi/v931-cnss-service-manager-matrix-live/summary.md`
- `tmp/wifi/v931-cnss-service-manager-matrix-live/manifest.json`
- `tmp/wifi/v931-cnss-service-manager-matrix-live/native/mdm-helper-cnss-before-esoc.txt`
- `tmp/wifi/v931-cnss-service-manager-matrix-live/native/post-dmesg-wifi-esoc-tail.txt`

## Next

Run a host-only V932 classifier for CNSS/service-manager ordering deltas before
trying another live matrix order. If that classifier selects another bounded
live order, keep the same WLFW-precondition gate and continue to block Wi-Fi
HAL, scan/connect, credentials, DHCP/routes, and external ping.
