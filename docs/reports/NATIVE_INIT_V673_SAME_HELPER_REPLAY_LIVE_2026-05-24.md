# Native Init V673 Same-helper Replay Live

- cycle: `v673`
- date: `2026-05-24`
- runner: `scripts/revalidation/native_wifi_same_helper_replay_v673.py`
- helper: `a90_android_execns_probe v111`
- evidence: `tmp/wifi/v673-same-helper-replay-live-retry2/`
- decision: `v673-android-userspace-no-wlfw-advance`
- pass: `true`

## Scope

V673 replayed both paths with the same helper v111 and a fresh current-boot prep
before each arm:

1. V641 clean-DSP one-shot reboot;
2. `mountsystem ro`;
3. V401 SELinuxfs runtime surface;
4. V490 Android SELinux policy-load proof;
5. bounded live proof with reboot cleanup.

It did not start supplicant, scan/connect, use credentials, run DHCP, change
routes, or perform an external ping.

## Result

| signal | V668-compatible arm | V671 Android-userspace arm |
| --- | --- | --- |
| arm decision | `v668-cnss2-focused-capture-gap-classified` | `v671-android-userspace-no-wlfw-advance` |
| service `74` gate | open, `wait_ms=15` | open, `wait_ms=15` |
| service-notifier `180` | `1` | `1` |
| service-notifier `74` | `1` | `1` |
| QRTR RX/TX | `1` / `1` | `1` / `1` |
| `sysmon-qmi` | `4` | `4` |
| Wi-Fi HAL legacy/ext child | not part of arm | started and cleanup-safe |
| `wificond` child | not part of arm | started and cleanup-safe |
| fresh `cnss-daemon` retry | cleanup-safe | cleanup-safe |
| WLFW / BDF / firmware-ready / `wlan0` | `0` | `0` |
| reboot cleanup | healthy | healthy |

## Interpretation

V673 overturns the V672 uncertainty: the V671 service `74/180` timeout was not a
stable lower-surface blocker. With fresh prep and helper v111, both arms
reproduce service `74/180` publication. The V671 Android-userspace arm starts
Wi-Fi HAL legacy/ext, `wificond`, and retry `cnss-daemon`, but lower Wi-Fi
markers still do not advance.

The blocker has therefore moved forward:

- no longer: service-notifier `74/180` reproducibility;
- now: HAL/`wificond`/fresh-CNSS-started state still does not trigger WLFW
  service `69`, BDF download, firmware-ready indication, or `wlan0`.

## Next Step

Plan V674 as a post-HAL/wificond runtime classifier. It should inspect the V673
V671-arm helper transcript, HAL/`wificond` stderr/stdout, binder/property
registration, service-manager visibility, and any kernel deltas between child
start and cleanup. Keep supplicant, scan/connect, credentials, DHCP, routing,
and external ping blocked until WLFW/BDF/`wlan0` advances.
