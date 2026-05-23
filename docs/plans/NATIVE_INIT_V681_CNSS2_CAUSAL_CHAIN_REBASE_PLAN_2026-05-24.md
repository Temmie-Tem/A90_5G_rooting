# Native Init V681 cnss2/WLFW Causal-chain Rebase Plan

## Objective

Reconcile the newly clarified Wi-Fi dependency model with the current V667 to
V680 evidence and route the next unit correctly.

The key distinction is:

```text
QRTR/userspace-visible service-notifier 180/74
  !=
cnss2/icnss kernel progression into QCA6390 WLFW service 69
```

V681 is host-only. It does not run a new live V666 retry. V666 was already used
for the repaired private CNSS retry, and the same investigation axis was then
implemented as V667/V668/V669.

## Inputs

- `tmp/wifi/v667-cnss2-pd-notifier-classifier/manifest.json`
- `tmp/wifi/v668-cnss2-focused-capture-live/manifest.json`
- `tmp/wifi/v669-android-cnss2-runtime-delta/manifest.json`
- `tmp/wifi/v680-binder-debugfs-gap/manifest.json`
- Source-backed WLFW service id reference:
  `docs/reports/NATIVE_INIT_V274_WLFW_SERVICE_LOCATOR_2026-05-19.md`
- Android kernel CNSS2 Kconfig reference:
  `https://android.googlesource.com/kernel/msm-modules/wlan-platform/+/refs/heads/android-msm-eos-android13-wear-kr3-pixel-watch/cnss2/Kconfig`

## Gate

Run `scripts/revalidation/native_wifi_cnss2_causal_chain_rebase_v681.py` to:

1. confirm V667/V668/V669/V680 evidence is present and passed;
2. confirm service-notifier `180/74` is positive while cnss2/WLFW/BDF/`wlan0`
   progression is still absent in native;
3. confirm Android advances through WLFW/BDF/`wlan0` on comparable evidence;
4. classify V680 Binder debugfs absence as a secondary observability gap unless
   cnss2/WLFW progression moves;
5. route the next live unit toward cnss2/WLFW progression observation rather
   than an old V666-style Binder-only retry.

## Forbidden Actions

- No device command.
- No mount or bind mount.
- No sysfs write.
- No DSP boot-node write.
- No `esoc0` open.
- No daemon or service-manager start.
- No Wi-Fi HAL start.
- No supplicant or hostapd start.
- No scan/connect/link-up.
- No credential, DHCP, route change, or external ping.
- No boot image or partition write.

## Success Criteria

- V681 runs host-only.
- Evidence routing proves V667/V668 already covered the proposed cnss2
  `pd_notifier` and modem-state read-only question.
- The next recommended gate is explicit: bounded cnss2/WLFW progression
  observation before any Wi-Fi connect attempt.
- Binder debugfs remains a diagnostic route, not the primary bring-up route.

## Commands

```sh
python3 -m py_compile \
  scripts/revalidation/native_wifi_cnss2_causal_chain_rebase_v681.py

python3 scripts/revalidation/native_wifi_cnss2_causal_chain_rebase_v681.py \
  --out-dir tmp/wifi/v681-cnss2-causal-chain-rebase-plan \
  plan

python3 scripts/revalidation/native_wifi_cnss2_causal_chain_rebase_v681.py \
  --out-dir tmp/wifi/v681-cnss2-causal-chain-rebase \
  run
```

## Expected Routing

If V681 passes, plan V682 as a bounded cnss2/WLFW progression observer. The live
unit should observe dmesg/sysfs/debug-surface state around service-notifier
`180/74` and CNSS retry, but still block Wi-Fi HAL scan/connect, DHCP, routes,
credentials, and external ping until `wlan0` exists.
