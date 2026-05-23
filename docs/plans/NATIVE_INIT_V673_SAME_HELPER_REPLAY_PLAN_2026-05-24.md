# Native Init V673 Same-helper Replay Plan

- date: `2026-05-24 KST`
- cycle: `V673`
- status: planned
- runner: `scripts/revalidation/native_wifi_same_helper_replay_v673.py`
- helper: `a90_android_execns_probe v111`

## Goal

V672 showed that V668 and V671 both reached QRTR RX/TX and `sysmon-qmi`, but
only V668 published service-notifier `180/74`. V673 removes helper-version and
current-boot drift from the comparison by replaying both paths with helper v111
and a fresh V641/V401/V490 prep before each arm.

## Arms

| arm | path |
| --- | --- |
| V668-compatible | service `74` gated CNSS retry with cnss2 focused capture |
| V671 Android userspace | service `74` gated Android userspace-order start-only |

Each arm receives:

1. V641 clean-DSP one-shot reboot;
2. `mountsystem ro`;
3. V401 SELinuxfs runtime surface;
4. V490 Android SELinux policy-load proof;
5. bounded live proof with reboot cleanup.

## Guardrails

V673 allows only bounded replay actions needed to compare the two arms. It does
not authorize:

- supplicant or hostapd start;
- scan/connect/link-up;
- credential use;
- DHCP, route change, or external ping;
- boot image or partition writes.

## Decision Labels

| decision | meaning |
| --- | --- |
| `v673-same-helper-mode-regression-classified` | helper v111 reproduces V668-positive path but V671 mode still times out |
| `v673-service74-not-reproducible-on-current-boot` | even the V668-compatible v111 arm cannot reproduce service `74/180` |
| `v673-android-userspace-no-wlfw-advance` | V671 reaches gate and starts children but WLFW/BDF/`wlan0` remain absent |
| `v673-android-userspace-wifi-surface-advanced` | V671 advances lower Wi-Fi markers |
| `v673-*-prep-blocked` | V641/V401/V490 current-boot prep failed |

## Commands

```bash
python3 scripts/revalidation/native_wifi_same_helper_replay_v673.py \
  --out-dir tmp/wifi/v673-same-helper-replay-plan \
  plan

python3 scripts/revalidation/native_wifi_same_helper_replay_v673.py \
  --out-dir tmp/wifi/v673-same-helper-replay-live \
  run
```

## Next

If V673 isolates the regression to the V671 mode, V674 should compare pre-gate
mode differences: `--allow-wifi-hal-start-only`, `/dev/wlan` materialization,
Android userspace request flags, and helper setup performed before service
`74` gate wait. Wi-Fi connection remains blocked until service `74/180`
publication is reproducible in the intended path.
