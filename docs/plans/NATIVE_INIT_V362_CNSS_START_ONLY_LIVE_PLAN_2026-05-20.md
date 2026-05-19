# v362 Plan: Bounded CNSS Start-Only Live Run

- date: `2026-05-20`
- scope: one bounded `cnss-daemon -n -l` start-only attempt after V320/V361
- boot image change: none
- native baseline: `A90 Linux init 0.9.61 (v319)`
- prerequisite: V320 property lookup PASS, V360 runner refresh PASS, V361 approval packet PASS

## Summary

V362 executes the previously generated bounded start-only command. The allowed
scope is a single private-namespace `cnss-daemon -n -l` observation with a 10s
runtime limit, cleanup, process reap, and postflight checks.

This is daemon start only. It is not Wi-Fi scan/connect/link-up and does not
authorize supplicant, wificond, hostapd, Wi-Fi HAL, DHCP, routing, rfkill, ICNSS
bind/unbind, firmware mutation, credentials, or broader Wi-Fi bring-up.

## Preflight

Run no-start gates immediately before live execution:

```bash
python3 scripts/revalidation/wifi_cnss_start_only_runner.py \
  --out-dir tmp/wifi/v362-cnss-start-only-preflight-20260520 \
  preflight
python3 scripts/revalidation/wifi_cnss_live_approval_packet.py \
  --out-dir tmp/wifi/v362-cnss-start-only-approval-packet-20260520 \
  --live-out-dir tmp/wifi/v362-cnss-start-only-live-20260520 \
  --max-runtime-sec 10
```

Required decisions:

- `preflight-ready`
- `live-approval-packet-ready`
- `daemon_start_executed=false` before the live run

## Live Command

```bash
python3 scripts/revalidation/wifi_cnss_start_only_runner.py \
  --out-dir tmp/wifi/v362-cnss-start-only-live-20260520 \
  --max-runtime-sec 10 \
  run \
  --allow-daemon-start \
  --assume-yes \
  --i-understand-reboot-only-recovery
```

## Postflight Analysis

```bash
python3 scripts/revalidation/wifi_cnss_live_evidence_analyzer.py \
  --run-dir tmp/wifi/v362-cnss-start-only-live-20260520 \
  --out-dir tmp/wifi/v362-cnss-start-only-evidence-analysis-full-20260520 \
  --post-processes tmp/wifi/v362-cnss-start-only-live-20260520/commands/post-cnss-processes.txt
python3 scripts/revalidation/wifi_cnss_warning_disposition.py \
  --analysis-manifest tmp/wifi/v362-cnss-start-only-evidence-analysis-full-20260520/manifest.json \
  --out-dir tmp/wifi/v362-cnss-warning-disposition-20260520 \
  --surface-out-dir tmp/wifi/v362-cnss-warning-surface-20260520
```

## Acceptance

- live runner decision is `start-only-pass`;
- child is observable and then cleaned up;
- `postflight_safe=true`;
- `reaped=true`;
- no `cnss-daemon`/`cnss_diag` process remains;
- no `wlan*` interface appears;
- warning disposition is ready for start-only scope;
- Wi-Fi scan/connect/link-up remains blocked.
