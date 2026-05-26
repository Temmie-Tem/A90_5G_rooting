# V1004 Service-window Subsystem Trigger Live Plan

## Goal

Run the first bounded native live gate that uses helper `v170` to attempt a
service-window-scoped `/dev/subsys_esoc0` child open.

V1004 follows V1000/V1001/V1002/V1003:

- V1000 showed Android reaches `/dev/subsys_esoc0` get before `wlfw_start`.
- V1001 classified the old WLFW-precondition gate as circular.
- V1002 added helper `v170` support for a narrower service-window trigger.
- V1003 deployed helper `v170` and proved remote sha/contract parity.

## Scope

1. Mount `/mnt/system/system` read-only for Android runtime visibility.
2. Mount `selinuxfs` for the current boot.
3. Run V490 current-boot SELinux policy-load proof using helper `v170`.
4. Run V997-style post-load domain proof using helper `v170` for the service
   window critical domains.
5. Run helper `v170` mode
   `wifi-companion-android-wifi-service-window-subsys-trigger-capture`.
6. Cleanup service-window actors; reboot only if postflight cleanup is not
   proven safe.

## Guardrails

Allowed only inside the bounded gate:

- read-only `mountsystem ro`;
- `selinuxfs` mount/cleanup;
- V490 policy write to `/sys/fs/selinux/load`;
- Android service-window actors;
- child open of `/dev/subsys_esoc0` only after `mdm_helper` is observed holding
  `/dev/esoc-0`.

Forbidden:

- `qcwlanstate`;
- `IWifi.start`;
- eSoC ioctl;
- Wi-Fi scan/connect/link-up;
- credential use;
- DHCP/routes;
- external ping;
- boot image or partition write;
- firmware mutation;
- GPIO/sysfs/debugfs write.

## Success Criteria

V1004 passes if it records one of these classified outcomes without violating
forbidden actions and with safe cleanup or cleanup reboot:

- `v1004-service-window-subsys-trigger-captured`;
- `v1004-mdm-helper-esoc-fd-missing-no-trigger`;
- `v1004-wlfw-precondition-observed`;
- `v1004-service-window-runtime-gap`.

A pass does not mean Wi-Fi is connected. It means the lower trigger frontier is
classified safely enough to choose the next Wi-Fi bring-up step.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_android_service_window_subsys_trigger_live_v1004.py
python3 scripts/revalidation/native_wifi_android_service_window_subsys_trigger_live_v1004.py plan
python3 scripts/revalidation/wifi_selinuxfs_toybox_mount_live_executor.py \
  --approval-phrase "approve v401 toybox mount selinuxfs runtime surface only; no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/a90ctl.py --timeout 60 mountsystem ro
python3 scripts/revalidation/native_selinux_policy_load_proof_v490.py \
  --helper-sha256 edbccfef2fd117c5264c140ff5b2f4cec5424c917151607cecc309268cd9c254 \
  --approval-phrase "approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/native_wifi_current_boot_selinux_domain_proof_v997.py \
  --helper-sha256 edbccfef2fd117c5264c140ff5b2f4cec5424c917151607cecc309268cd9c254 \
  --v490-manifest tmp/wifi/v490-native-selinux-policy-load-proof/manifest.json \
  --approval-phrase "approve v997 current-boot SELinux domain proof only; no policy load, no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/native_wifi_android_service_window_subsys_trigger_live_v1004.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-android-wifi-service-window \
  --allow-android-wifi-service-window-subsys-trigger-capture \
  --allow-cleanup-reboot \
  --assume-yes run
```
