# V2403 — AUD-5A Android/Magisk settle root-check failure

Date: 2026-06-15  
Scope: exact-gated AUD-5A Android/Magisk ACDB live rerun after V2402 handoff hardening  
Device action: boot-partition-only Android handoff, then checked rollback to V2321

## Decision

`aud5a-android-boot-ok-settle-rootcheck-command-bug-rollback-pass`

The V2402 rollback hardening worked, but the new post-handoff Magisk-root settle check was encoded
incorrectly for `adb shell su -c`. No ACDB/AppType capture ran.

## Evidence

Private run directory:

- `workspace/private/runs/audio/v2397-android-acdb-measurement-20260615-074051`

Preflight before live:

- resident native-init: `0.9.285 (v2321-usb-clean-identity-rodata)`;
- resident `selftest fail=0`;
- rollback V2321 SHA256 matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`;
- deeper fallback V2237 and V48 images were present;
- dry-run: `ok=True`, `future_live_ready=True`, `future_live_blockers=[]`, `command_safety_ok=True`.

Live sequence:

- Android boot handoff succeeded through the checked helper;
- Android post-handoff settle steps 0 and 1 passed:
  - `adb wait-for-device`;
  - boot-complete re-check;
- settle step 2 failed before staging:
  - command intent: Magisk-root `id` re-check;
  - observed stderr: `/system/bin/sh: syntax error: unexpected 'gid=2000'`;
  - no stage, probe, logcat stimulus, ACDB/AppType snapshot, mixer, native `/dev/snd`, or ACDB ioctl ran.

Rollback:

- V2402 rollback path waited for Android ADB, issued Android `adb reboot recovery`, and then used the
  checked helper to flash V2321;
- recovery ADB was observed after about 30 s;
- V2321 boot readback SHA matched;
- final native-init version was `0.9.285` and `selftest fail=0`.

## Root cause

The complex root check was passed through `adb shell su -c` as multiple shell tokens. Android's remote
shell interpreted part of the `id` output as shell syntax, producing `unexpected 'gid=2000'`. The fix
should not embed compound shell logic in this `su -c` path.

## Required next fix

Use a simple `su -c id` command for the settle step and validate `uid=0` on the host side from the
captured stdout. This preserves the root assertion without depending on fragile remote shell quoting.

Because AUD-5A has now had two live handoff failures with safe rollback, do not blind-rerun again in
the same loop without first landing and validating this host-only root-check fix.

## Safety result

- Forbidden partitions: not touched.
- Boot partition writes: checked helper only.
- Native rollback target: V2321 restored by the hardened checked-helper rollback path.
- Final health: native-init `selftest fail=0`.
