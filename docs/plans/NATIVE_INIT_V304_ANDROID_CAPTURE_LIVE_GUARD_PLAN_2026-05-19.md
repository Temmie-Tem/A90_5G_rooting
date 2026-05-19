# v304 Plan: Android Capture Live Guard

- date: `2026-05-19`
- scope: host-only go/no-go guard immediately before v300 live handoff
- boot image change: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- status: planned

## Summary

v304 adds a host-only live guard that re-checks the approval packet, native
bridge state, rollback image, Android boot image, and postprocess state before
operator-approved v300 live handoff. It prints the live command only when all
preconditions are fresh and consistent.

The guard does not execute the live command. It exists to prevent stale approval
artifacts or accidental target drift from being used during a destructive boot
partition maintenance window.

## Key Checks

- v302 approval packet exists and decision is `android-capture-approval-ready`.
- v300 target propagation check is present and PASS.
- Native bridge `version/status` is reachable and reports
  `A90 Linux init 0.9.60 (v261)`.
- Android boot image and native rollback image still exist and match the hashes
  recorded in v302.
- v303 postprocess is still waiting for live handoff, not already seeded or
  failed.
- Optional repo cleanliness check warns if uncommitted files exist.

## Output

- `manifest.json` with individual guard checks.
- `summary.md` with go/no-go decision.
- `live-command.txt` copied from v302 only when the decision is GO.

## Decisions

- `android-capture-live-guard-go`
- `android-capture-live-guard-blocked`

## Safety Boundary

- No reboot/recovery/flash.
- No boot partition write.
- No Android boot handoff execution.
- No ADB command execution.
- No property mutation.
- No service-manager/HAL/Wi-Fi daemon execution.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.

## Validation

```bash
python3 -m py_compile scripts/revalidation/android_capture_live_guard.py
python3 scripts/revalidation/android_capture_live_guard.py \
  --out-dir tmp/wifi/v304-android-capture-live-guard \
  run
git diff --check
```

Expected while native v261 is running and v302/v303 are fresh:
`android-capture-live-guard-go`.

## Acceptance

- GO only if every blocker check passes.
- GO artifact includes the exact v300 live command but does not execute it.
- Any missing/stale image, stale approval packet, missing target propagation
  audit, failed native bridge check, or postprocess state other than waiting for
  live returns BLOCKED.
