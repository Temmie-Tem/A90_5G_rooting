# Native Init V842 CNSS Pre-WLFW Contract Classifier Plan

## Goal

Classify whether the V841 blocker is still a broad `cnss-daemon` launch
contract gap, or a narrower live pre-WLFW stall inside an already-launched
native `cnss-daemon`.

## Scope

V842 is host-only. It reads existing evidence and does not contact the device,
start daemons, start service-manager, start Wi-Fi HAL, scan/connect, use
credentials, run DHCP, change routes, ping externally, write sysfs/debugfs,
write boot images, write partitions, or flash a custom kernel.

## Inputs

- V841 trigger-gap classifier:
  `tmp/wifi/v841-post-v840-trigger-gap-classifier/manifest.json`
- V840 provider-first prearmed listener:
  `tmp/wifi/v840-provider-first-prearmed-listener-live/manifest.json`
- V704 CNSS retry stall snapshot:
  `tmp/wifi/v704-cnss-retry-stall-snapshot/manifest.json`
- V697 CNSS Binder runtime target:
  `tmp/wifi/v697-cnss-binder-runtime-target-classifier-rerun/manifest.json`
- V525 Android companion identity capture:
  `tmp/wifi/v526-android-companion-identity-handoff-run/v525-android-companion-identity-run/`
- V622 Android lower-stack positive reference:
  `tmp/wifi/v622-android-mdm-helper-timing-handoff-live-20260523-032506/v622-android-mdm-helper-timing-recapture-run/manifest.json`

## Classification Rules

V842 passes if:

1. V841/V840/V704/V697/V525/V622 prerequisite manifests are present and pass.
2. Android `cnss-daemon` service contract is `/system/vendor/bin/cnss-daemon -n -l`.
3. Android runtime identity has `u:r:vendor_wcnss_service:s0`,
   `system` uid/gid, `wifi/inet/net_admin` groups, and `CAP_NET_ADMIN`.
4. Native CNSS retry also has matching SELinux domain, identity, capability,
   vndbinder fd, socket fds, and an alive sleeping process.
5. Native V840 still lacks `wlfw_start`, `wlfw_service_request`, WLAN-PD,
   QMI connected, BDF, FW-ready, and `wlan0`.

## Expected Decision

Expected result: `v842-current-window-cnss-stall-snapshot-selected`.

This means coarse launcher contract work is closed enough for the current
blocker. The next useful proof must capture the live wait/stall point of the
current provider-first `cnss-daemon` retry before cleanup.

## Next Gate

V843 should perform a bounded live current-window CNSS stall snapshot:

- preserve the V840 provider-first order;
- capture `cnss-daemon` `wchan`, syscall, task status/stat, optional stack,
  fd targets, socket inode mappings, and dmesg deltas;
- keep cleanup process-group safe;
- keep Wi-Fi HAL, scan/connect, DHCP/routes, credentials, external ping,
  `esoc0`, subsystem writes, module load/unload, and boot image writes blocked.
