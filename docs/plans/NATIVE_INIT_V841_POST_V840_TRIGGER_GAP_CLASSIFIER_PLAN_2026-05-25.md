# Native Init V841 Post-V840 Trigger Gap Classifier Plan

## Goal

Classify the remaining native Wi-Fi lower-state blocker after V840 proved that
provider-first service-manager/PeripheralManager, CNSS retry, and a prearmed
WLAN-PD listener still leave `msm/modem/wlan_pd` in `UNINIT`.

## Scope

V841 is host-only. It reads existing evidence and does not contact the device,
start daemons, start service-manager, start Wi-Fi HAL, scan/connect, use
credentials, run DHCP, change routes, ping externally, write sysfs/debugfs,
write partitions, or flash boot images.

## Inputs

- V840 provider-first prearmed listener:
  `tmp/wifi/v840-provider-first-prearmed-listener-live/manifest.json`
- Android lower-stack positive reference:
  `tmp/wifi/v622-android-mdm-helper-timing-handoff-live-20260523-032506/v622-android-mdm-helper-timing-recapture-run/manifest.json`
- RFS alias classifier:
  `tmp/wifi/v618-rfs-alias-order-classifier/manifest.json`
- `mdm_helper` retry classifiers:
  `tmp/wifi/v746-mdm-helper-sysmon-live-current/manifest.json`
  and `tmp/wifi/v764-mdm-helper-service180-retry/manifest.json`

## Classification Rules

V841 passes if:

1. V840 is present and passed with `v840-provider-first-prearmed-no-indication`.
2. Android V622 shows service `180/74`, `wlfw_start`, WLAN-PD indication, BDF,
   firmware-ready, and `wlan0`.
3. Native V840 has service `180/74`, CNSS netlink, and CLD80211 access, but no
   `wlfw_start`, WLAN-PD indication, BDF, firmware-ready, or `wlan0`.
4. V618 keeps standalone `rfs_access` rejected.
5. V746/V764 keep blind `mdm_helper` retry rejected.

## Expected Decision

Expected result: `v841-cnss-wlfw-start-gap-selected`.

The key interpretation is that Android emits `cnss-daemon wlfw_start` before
WLAN-PD `UP`, while native `cnss-daemon` reaches netlink/CLD80211 but never
emits `wlfw_start`. Therefore the next useful gate is not another listener,
provider-first retry, `rfs_access`, or `mdm_helper`; it is a CNSS daemon
pre-WLFW launch/runtime-contract classifier.

## Next Gate

V842 should classify Android versus native `cnss-daemon` pre-WLFW conditions:

- service argv and init service contract
- required properties and property values
- SELinux domain and exec context
- inherited file descriptors and Binder/vndbinder context
- child lifetime, exit reason, and stderr/stdout

Keep Wi-Fi HAL, scan/connect, DHCP/routes, credentials, external ping, `esoc0`
open, subsystem writes, module load/unload, and boot image writes blocked.
