# Native Init V701 Pre-WLFW Trigger Classifier Plan

- date: `2026-05-24 KST`
- cycle: `v701`
- type: host-only classifier

## Goal

V700 proved that helper v119 can suppress the initial pre-provider
`cnss-daemon`, confirm `vendor.qcom.PeripheralManager`, and start one fresh
post-provider `cnss-daemon` retry. It still did not advance WLFW/BDF/`wlan0`.

V701 classifies that remaining gap using V700 evidence only:

- confirm the old CNSS Binder `-22` path is gone;
- identify whether userspace reaches only `cld80211`/netlink;
- decide whether the single kernel warning is Wi-Fi-relevant or secondary;
- keep Wi-Fi HAL/scan/connect/DHCP/external ping blocked until WLFW or `wlan0`
  appears.

## Inputs

- `tmp/wifi/v700-provider-first-cnss-orchestrated-run/manifest.json`
- `tmp/wifi/v700-provider-first-cnss-orchestrated-run/arm-v700-v119-provider-first-cnss/live/native/dmesg-delta.txt`
- `tmp/wifi/v700-provider-first-cnss-orchestrated-run/arm-v700-v119-provider-first-cnss/live/native/companion-start-only-with-holder.txt`
- `tmp/wifi/v700-provider-first-cnss-orchestrated-run/arm-v700-v119-provider-first-cnss/live/native/proc-net-dev.txt`
- `tmp/wifi/v700-provider-first-cnss-orchestrated-run/arm-v700-v119-provider-first-cnss/live/native/rpmsg-after-companion.txt`
- `tmp/wifi/v700-provider-first-cnss-orchestrated-run/arm-v700-v119-provider-first-cnss/live/native/mss-state-after-companion.txt`
- `tmp/wifi/v700-provider-first-cnss-orchestrated-run/arm-v700-v119-provider-first-cnss/live/native/mdm3-state-after-companion.txt`

## Guardrails

V701 must not:

- contact the device;
- mount or bind mount filesystems;
- start daemons or service managers;
- start Wi-Fi HAL, `wificond`, supplicant, or hostapd;
- scan, connect, link up, use credentials, DHCP, route changes, or external
  ping;
- write sysfs/debugfs, boot images, or partitions.

## Implementation

Add `scripts/revalidation/native_wifi_pre_wlfw_trigger_classifier_v701.py`.

The classifier parses:

- V700 manifest counters and runtime surface;
- helper key/value output;
- V700 dmesg timeline markers;
- read-only state snippets for `/proc/net/dev`, RPMSG, MSS, and MDM3.

## Decision Criteria

`v701-pre-wlfw-kernel-progression-gap-classified` requires:

- V700 provider-first gate passed;
- initial CNSS is suppressed;
- `vendor.qcom.PeripheralManager` exact query passed;
- post-provider CNSS retry started;
- CNSS Binder failure count is zero;
- `cnss-daemon` reaches netlink/`cld80211`;
- ICNSS/QCA/WLFW/BDF/`wlan0` markers remain absent;
- `pm_qos` warning call trace is attributed to audio deferred probe rather than
  a WLAN/cnss2 call trace.

## Validation Plan

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_pre_wlfw_trigger_classifier_v701.py

python3 scripts/revalidation/native_wifi_pre_wlfw_trigger_classifier_v701.py \
  --out-dir tmp/wifi/v701-pre-wlfw-trigger-plan-check plan

python3 scripts/revalidation/native_wifi_pre_wlfw_trigger_classifier_v701.py \
  --out-dir tmp/wifi/v701-pre-wlfw-trigger-classifier run
```

## Next Gate

If V701 classifies the pre-WLFW kernel progression gap, plan V702 as a bounded
read-only cnss2/icnss/QCA platform-state capture in the same provider-first
retry window. Do not start Wi-Fi HAL or attempt scan/connect until WLFW/BDF or
`wlan0` moves.
