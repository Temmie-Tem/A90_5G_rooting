# Native Init V744 V122 CNSS-only Comparison Plan

- date: `2026-05-24 KST`
- base runner: `scripts/revalidation/native_wifi_current_cnss_only_observer_v735.py`
- target helper: `a90_android_execns_probe v122`
- target evidence: `tmp/wifi/v744-v122-cnss-only-comparison-retry/`

## Goal

Determine whether the V743 service-`74` gate miss is caused by helper v122
itself or by the new gated `mdm_helper` mode. Re-run the known V735 CNSS-only
sequence with helper v122, keeping the same no-HAL/no-connect boundary.

## Preconditions

1. Hide the auto menu before live prep so read-only preflight cannot return
   native `busy`.
2. Mount `/mnt/system/system` read-only.
3. Mount `selinuxfs` and run current-boot SELinux policy-load proof.
4. Use helper v122 SHA256
   `032fe43041b908577bb1a2e4b3ff7a7dfea24958169723907df5d403f811e989`.

## Safety Boundary

- Allowed: firmware read-only mounts, `subsys_modem` holder window, lower
  companion stack, `cnss_diag`, and `cnss-daemon` start-only observation.
- Forbidden: service-manager start, Wi-Fi HAL start, scan/connect/link-up,
  credentials, DHCP/routes, external ping, boot/partition writes.

## Success Criteria

- The V735 CNSS-only order still starts six children with helper v122.
- `mss` reaches `ONLINE`; `mdm3` state is captured.
- QRTR TX, `sysmon-qmi`, and service-notifier marker presence are classified.
- MHI/QCA6390/WLFW/BDF/`wlan0` remain separately classified if absent.
- Device reboots back to healthy native init after cleanup.
