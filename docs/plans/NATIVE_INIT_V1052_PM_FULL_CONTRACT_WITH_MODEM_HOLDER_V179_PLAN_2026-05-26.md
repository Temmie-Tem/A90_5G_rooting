# V1052 PM Full-Contract with Modem Holder v179 Plan

## Goal

Rerun the bounded PM full-contract-with-modem-holder live gate using deployed
helper `v179`, after V1050 moved the modem pre-holder into the helper private
root.

## Preconditions

- V1051 deployed helper `v179` to `/cache/bin/a90_android_execns_probe`.
- Current boot must refresh SELinux state before actor exec:
  1. V401 selinuxfs mount
  2. `mountsystem ro`
  3. V490 policy-load proof using helper v179 sha
  4. PM SELinux domain proof over the four PM domains

## Inputs

- Live runner:
  `scripts/revalidation/native_wifi_pm_full_contract_with_modem_holder_live_v1052.py`
- Helper sha256:
  `9cb6d49849af181a87a5619e7b3ed7f0f513223ef97ce8b0599ce43694453a7b`
- V1051 deploy evidence:
  `tmp/wifi/v1051-execns-helper-v179-deploy/manifest.json`

## Method

1. Verify helper v179 sha/marker.
2. Run current-boot SELinux preconditions.
3. Run order:
   `after-mdm-helper-esoc-fd-with-pm-full-contract-with-modem-holder`.
4. Use an outer/toybox timeout long enough for the helper's 90 s pre-holder
   wait window.
5. Confirm whether the private-root pre-holder reaches these outputs:
   - `modem_pre_holder_child_chroot=1`
   - `modem_pre_holder_open_reported=1`
   - `modem_pre_holder_confirmed=1`
   - `pm_full_contract_seen=1`
6. Cleanup by reboot if any actor is not proven stopped.

## Hard Gates

No `ks`, MHI pipe transfer, Wi-Fi HAL, `wificond`, scan/connect, credentials,
DHCP/routes, external ping, controller eSoC notify, BOOT_DONE spoofing, boot
image write, partition write, firmware mutation, GPIO write, sysfs write, or
debugfs write. `/dev/subsys_esoc0` remains WLFW-precondition gated.

## Success Criteria

- Runtime-domain guard does not block PM actor exec domains.
- Matrix order is active.
- The pre-holder reaches private root and attempts `/dev/subsys_modem`.
- If pre-holder opens successfully, both `pm_proxy_helper` and `pm-service` hold
  `/dev/subsys_modem`.
- Cleanup restores `bootstatus`/`selftest fail=0`.

## Next

If private-root open returns a driver errno, classify that errno before retrying
service-manager, HAL, scan/connect, or Wi-Fi bring-up.
