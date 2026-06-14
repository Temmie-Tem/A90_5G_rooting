# Native Init V460 Wi-Fi Live Retry Pass Report

Date: 2026-05-20

## Summary

V460 completed the first bounded Android Wi-Fi live validation from the native
workflow.  The first live attempt connected and cleaned up, but failed reporting
because V445 collector-mode summary rendering expected `steps`.  After fixing
that and stale-live retry routing, the second live attempt passed end-to-end.

```text
live: v447-explicit-connect-flow-live-pass
cleanup proof: v452-wifi-live-cleanup-proof-pass
outcome: v457-wifi-session-live-cleanup-pass
bundle: v458-wifi-session-bundle-live-cleanup-pass
native rollback: A90 Linux init 0.9.61 (v319)
```

## Implementation

- `scripts/revalidation/wifi_android_explicit_connect_live_v445.py`
  - collector summaries now render `captures`, so successful collector output
    is not converted into a runner failure.
- `scripts/revalidation/wifi_handoff_result_router_v449.py`
  - ignores live evidence older than the latest private preflight.
- `scripts/revalidation/wifi_operator_preflight_readiness_v450.py`
  - ignores stale live evidence when routing retry.
- `scripts/revalidation/wifi_live_cleanup_proof_v452.py`
  - reads nested collector cleanup classification;
  - checks restore-native in V445 runner steps;
  - ignores stale live evidence older than a newer preflight.
- `scripts/revalidation/wifi_operator_session_outcome_v457.py`
  - treats V459 as the latest operator packet and selects the newest cleanup
    proof.
- `scripts/revalidation/wifi_operator_session_bundle_v458.py`
  - indexes stale-live metadata and packages the final post-live state.

## Evidence

Live pass:

```text
tmp/wifi/v447-explicit-connect-flow-live-20260520-194306/
decision: v447-explicit-connect-flow-live-pass
reason: explicit scan/connect produced Wi-Fi connection evidence and cleanup containment passed
```

Post-live gates:

```text
tmp/wifi/v449-wifi-handoff-result-router-postlive-20260520-194829/
tmp/wifi/v452-wifi-live-cleanup-proof-postlive-20260520-194829/
tmp/wifi/v457-wifi-operator-session-outcome-postlive2-20260520-194857/
tmp/wifi/v458-wifi-operator-session-bundle-postlive2-20260520-194857/
```

Native rollback verification:

```text
A90 Linux init 0.9.61 (v319)
```

## Validation

Validated commands:

```text
python3 -m py_compile scripts/revalidation/wifi_android_explicit_connect_live_v445.py
python3 -m py_compile scripts/revalidation/wifi_handoff_result_router_v449.py
python3 -m py_compile scripts/revalidation/wifi_operator_preflight_readiness_v450.py
python3 -m py_compile scripts/revalidation/wifi_live_cleanup_proof_v452.py
python3 -m py_compile scripts/revalidation/wifi_operator_session_outcome_v457.py
python3 -m py_compile scripts/revalidation/wifi_operator_session_bundle_v458.py
```

V446 secret guard passed with zero findings.  V458 post-live bundle reported
zero leak findings.

## Interpretation

The core Wi-Fi bring-up path now works in a bounded live run:

- Android boot/flash succeeded;
- Wi-Fi enabled;
- scan/connect produced connected/IP/validated evidence;
- target network was forgotten;
- Wi-Fi exposure was disabled/contained;
- native v319 rollback succeeded.

This is not yet a long-running Wi-Fi stability claim.  It proves bounded
bring-up and cleanup only.

## Next

Plan bounded Wi-Fi stability testing and server binding policy.  Do not widen
network exposure until stability and binding policy are explicitly validated.
