# Native Init V549 Vnd Service-Manager Companion Replay Plan

## Goal

Move the native Wi-Fi companion replay one step closer to Android boot-complete behavior by
starting `vndservicemanager /dev/vndbinder` in the same bounded private namespace as
`servicemanager`, `hwservicemanager`, QRTR, rmt/tftp, pd-mapper, `cnss_diag`, and
`cnss-daemon`.

## Basis

- V547 proved QRTR/rmt/tftp/pd-mapper/CNSS companion daemons can start, stay observable,
  and clean up, but no QRTR/QMI/WLFW/BDF/FW marker appears.
- V548 added `servicemanager` and `hwservicemanager`; all children were observable and
  cleaned, but `cnss-daemon` still emitted Binder transaction `-22` failures.
- V548 maps `/dev/vndbinder` in `cnss-daemon`, while Android reference evidence shows
  `vndservicemanager /dev/vndbinder` running as `u:r:vndservicemanager:s0`.
- Native evidence confirms `/mnt/vendor_ro/bin/vndservicemanager` and
  `/mnt/vendor_ro/etc/init/vndservicemanager.rc` exist; the init contract is `user system`,
  `group system readproc`.

## Scope

Allowed:

- deploy helper `a90_android_execns_probe v76`;
- bounded `wifi-companion-vnd-service-manager-start-only` replay;
- start and cleanup `servicemanager`, `hwservicemanager`, `vndservicemanager`, QRTR,
  rmt/tftp, pd-mapper, `cnss_diag`, and `cnss-daemon`;
- collect dmesg, process, fd/map, SELinux context, and cleanup evidence.

Forbidden:

- Wi-Fi HAL start;
- `wificond`, supplicant, or hostapd start;
- scan/connect/link-up, DHCP, routing, credentials, or external ping;
- boot image or partition writes.

## Success Criteria

V549 is successful if one of these bounded classifications is produced with cleanup evidence:

1. `v549-companion-vnd-service-manager-marker-observed`: QRTR/QMI/WLFW/BDF/FW marker appears.
2. `v549-companion-vnd-service-manager-binder-gap-cleared`: `vndservicemanager` is observable,
   all children clean up, and Binder transaction failures disappear.
3. `v549-companion-vnd-service-manager-binder-fail-persists`: all children clean up but the
   Binder failure remains, proving the blocker is beyond simply missing `vndservicemanager`.

## Commands

```bash
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v549-a90_android_execns_probe-v76/a90_android_execns_probe

python3 scripts/revalidation/wifi_execns_helper_v76_deploy_preflight.py plan
python3 scripts/revalidation/wifi_execns_helper_v76_deploy_preflight.py preflight
python3 scripts/revalidation/wifi_execns_helper_v76_deploy_preflight.py \
  --apply --assume-yes \
  --approval-phrase "approve v549 deploy execns helper v76 only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/native_wifi_companion_vnd_service_manager_replay_v549.py plan
python3 scripts/revalidation/native_wifi_companion_vnd_service_manager_replay_v549.py preflight
python3 scripts/revalidation/native_wifi_companion_vnd_service_manager_replay_v549.py \
  --apply --assume-yes \
  --approval-phrase "approve v549 companion vnd service-manager replay only; no Wi-Fi HAL start, no scan/connect/link-up and no external ping" \
  run
```
