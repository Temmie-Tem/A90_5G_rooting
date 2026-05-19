# v329 Plan: Wi-Fi Readiness Dashboard

- date: `2026-05-19`
- scope: host-only Wi-Fi readiness aggregation
- boot image change: none planned
- device mutation: none planned
- status: implementation planned

## Summary

The Wi-Fi work now spans several tracks: vendor assets, ICNSS/QCA6390,
QRTR/WLFW, Binder/service-manager, Android property capture, private property
runtime, and approval-gated live proofs. The immediate live path is blocked by
the V317 exact approval phrase, but the broader state is hard to inspect from
one place.

v329 adds a host-only dashboard that reads existing evidence and produces a
single manifest/summary showing which tracks are pass, blocked, or review-only.

## Key Changes

- Add `scripts/revalidation/wifi_readiness_dashboard.py`.
- Read existing manifests only; execute no bridge/device command.
- Summarize:
  - vendor asset visibility;
  - ICNSS/QCA6390 start-only negative deltas;
  - Binder/service-manager prerequisites;
  - Android property baseline and private property runtime chain;
  - current approval/refusal state.
- Emit `tmp/wifi/v329-wifi-readiness-dashboard/manifest.json` and `summary.md`.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_readiness_dashboard.py
python3 scripts/revalidation/wifi_readiness_dashboard.py \
  --out-dir tmp/wifi/v329-wifi-readiness-dashboard \
  run
git diff --check
```

Expected result:

```text
decision: wifi-readiness-dashboard-ready-blocked-by-v317
pass: True
```

## Acceptance

- Dashboard generation is host-only.
- Device commands and mutations are false.
- Missing evidence would fail the dashboard, rather than silently producing a
  misleading readiness result.
- The next live gate remains the exact V317 approval phrase.
