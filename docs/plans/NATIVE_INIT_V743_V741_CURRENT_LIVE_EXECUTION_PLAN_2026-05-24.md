# Native Init V743 V741 Current Live Execution Plan

- date: `2026-05-24 KST`
- base runner: `scripts/revalidation/native_wifi_mdm_helper_gated_live_v741.py`
- target helper: `a90_android_execns_probe v122`
- target evidence: `tmp/wifi/v743-v741-mdm-helper-gated-live-current/`

## Goal

Execute the V741 service-`74` gated `mdm_helper` proof on the current boot
after helper v122 deployment, without crossing into Wi-Fi HAL, scan/connect,
credentials, DHCP/routes, or external ping.

## Preconditions

1. `/cache/bin/a90_android_execns_probe` is helper v122 with SHA256
   `032fe43041b908577bb1a2e4b3ff7a7dfea24958169723907df5d403f811e989`.
2. `/sys/fs/selinux` is mounted for the current boot.
3. Android split policy load proof has run for the current boot.
4. `mountsystem ro` and firmware partition mounts remain read-only.

## Safety Boundary

- Allowed: firmware read-only mounts, `subsys_modem` holder window, lower
  companion start-only, `cnss_diag`, `cnss-daemon`, and service-`74` gate.
- Conditionally allowed: `/vendor/bin/mdm_helper` only if service `74` gate
  opens inside the same helper window.
- Forbidden: service-manager start, Wi-Fi HAL start, scan/connect/link-up,
  credentials, DHCP/routes, external ping, boot/partition writes.

## Success Criteria

- Helper v122 mode/order contract is observed.
- Service `74` gate result is captured.
- If the gate opens, `mdm_helper` lifecycle is captured and postflight safe.
- If the gate stays closed, the result is classified as a gate/timing blocker
  rather than forcing `mdm_helper`.
- Device reboots back to healthy native init after cleanup.
