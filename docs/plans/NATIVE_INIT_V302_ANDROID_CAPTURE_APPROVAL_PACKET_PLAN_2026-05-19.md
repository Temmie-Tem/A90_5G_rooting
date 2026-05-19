# Native Init v302 Android Capture Approval Packet Plan

- date: `2026-05-19`
- scope: host-side approval packet for Android capture live handoff
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- target artifact: `scripts/revalidation/android_capture_approval_packet.py`
- prerequisites:
  - v299 decision `android-capture-handoff-ready-needs-operator`
  - v300 decision `android-capture-executor-dryrun-ready`
  - v300 refusal decision `android-capture-executor-approval-required`

## Summary

v300 created the fail-closed executor. v302 creates the final operator approval
packet from existing evidence and a read-only current native status check.

The packet is intentionally not an executor. It exists to make the approval
boundary explicit and auditable before the live command is run.

## Guardrails

- No reboot.
- No recovery transition.
- No boot partition write.
- No Android boot image flashing.
- No property mutation.
- No service-manager/HAL/Wi-Fi daemon execution.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.

## Required Evidence

- v299 preflight manifest confirms native rollback and Android boot image.
- v300 dry-run manifest records the full step sequence.
- v300 refusal manifest proves `run` fails without approval flags.
- current native bridge `version/status` read-only check still passes.

## Expected Decisions

PASS:

- `android-capture-approval-ready`

Failure:

- `android-capture-approval-input-missing`
- `android-capture-approval-stale-or-blocked`

## Validation

```bash
python3 -m py_compile scripts/revalidation/android_capture_approval_packet.py
python3 scripts/revalidation/android_capture_approval_packet.py \
  --out-dir tmp/wifi/v302-android-capture-approval-packet \
  run
git diff --check
```

## Acceptance

- The packet emits a single live command.
- The packet lists prerequisites, abort conditions, rollback path, and expected
  artifacts.
- The packet refuses readiness if current native control or v299/v300 evidence
  is missing.
