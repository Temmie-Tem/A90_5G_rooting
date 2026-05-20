# Native Init V460 Wi-Fi Live Retry Pass Plan

Date: 2026-05-20

## Goal

V460 fixes the post-V459 live retry path and records the first bounded Android
Wi-Fi live pass.  The target outcome is not merely preflight readiness: V447
live must pass, cleanup containment must pass, and native rollback must be
verified afterward.

## Scope

Allowed:

- run V459 saved-profile preflight/live with local NetworkManager profile
  selection;
- boot/flash Android for bounded live Wi-Fi validation;
- explicitly scan/connect to the saved profile selected locally;
- forget the network, disable Wi-Fi, and rollback to native boot;
- patch host-side evidence routing and summary rendering bugs found during the
  live attempt.

Not allowed:

- print profile names, SSIDs, or PSKs;
- leave Wi-Fi enabled or connected after cleanup;
- proceed to server exposure or binding policy before cleanup proof passes.

## Implementation

- `scripts/revalidation/wifi_android_explicit_connect_live_v445.py`
  - render collector-mode summaries from `captures` as well as runner-mode
    `steps`.
- `scripts/revalidation/wifi_handoff_result_router_v449.py`
  - ignore stale live evidence older than the latest private preflight.
- `scripts/revalidation/wifi_operator_preflight_readiness_v450.py`
  - ignore stale live evidence older than the latest private preflight.
- `scripts/revalidation/wifi_live_cleanup_proof_v452.py`
  - ignore stale live evidence older than the latest private preflight;
  - read nested collector classification and V445 rollback steps.
- `scripts/revalidation/wifi_operator_session_outcome_v457.py`
  - ignore stale live evidence;
  - choose the newest cleanup proof instead of preferring stale `after-live`
    output.
- `scripts/revalidation/wifi_operator_session_bundle_v458.py`
  - include stale-live metadata in the sanitized bundle index.

## Validation Plan

```text
python3 -m py_compile \
  scripts/revalidation/wifi_android_explicit_connect_live_v445.py \
  scripts/revalidation/wifi_handoff_result_router_v449.py \
  scripts/revalidation/wifi_operator_preflight_readiness_v450.py \
  scripts/revalidation/wifi_live_cleanup_proof_v452.py \
  scripts/revalidation/wifi_operator_session_outcome_v457.py \
  scripts/revalidation/wifi_operator_session_bundle_v458.py

printf '1\nV447-LIVE\n' | \
  bash tmp/wifi/v459-nm-profile-handoff-packet-run-20260520-193122/run-v459-nm-profile-wifi-flow.sh

python3 scripts/revalidation/wifi_live_cleanup_proof_v452.py \
  --out-dir tmp/wifi/v452-wifi-live-cleanup-proof-postlive-<ts> \
  run

python3 scripts/revalidation/wifi_operator_session_outcome_v457.py \
  --out-dir tmp/wifi/v457-wifi-operator-session-outcome-postlive2-<ts> \
  run

python3 scripts/revalidation/wifi_operator_session_bundle_v458.py \
  --out-dir tmp/wifi/v458-wifi-operator-session-bundle-postlive2-<ts> \
  run

python3 scripts/revalidation/a90ctl.py --timeout 8 version
python3 scripts/revalidation/wifi_private_secret_guard_v446.py --include-untracked run
git diff --check
```

## Expected Decisions

- `v447-explicit-connect-flow-live-pass`
- `v449-wifi-live-pass-next-stability`
- `v452-wifi-live-cleanup-proof-pass`
- `v457-wifi-session-live-cleanup-pass`
- `v458-wifi-session-bundle-live-cleanup-pass`

## Pass Criteria

V460 passes only when:

- Android live Wi-Fi explicit scan/connect succeeds;
- cleanup forgets the network and disables Wi-Fi exposure;
- rollback restores native `A90 Linux init 0.9.61 (v319)`;
- V452 cleanup proof passes;
- V457/V458 route to bounded Wi-Fi stability or server binding policy;
- secret/leak scans remain clean.

## Next Gate

Plan bounded Wi-Fi stability before any server binding or broader exposure work.
