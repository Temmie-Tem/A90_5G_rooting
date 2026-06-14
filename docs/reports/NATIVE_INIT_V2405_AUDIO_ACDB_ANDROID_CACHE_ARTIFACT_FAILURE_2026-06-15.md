# V2405 — AUD-5A Android/Magisk cache artifact path failure

Date: 2026-06-15  
Scope: exact-gated AUD-5A Android/Magisk ACDB/AppType live rerun after V2404 root-check fix  
Device action: checked Android boot handoff, transient Magisk-root settle, failed first staging command, checked rollback to V2321

## Decision

`aud5a-root-ok-cache-artifact-path-blocked-rollback-pass`

V2405 proved the V2404 root-check fix works live: Android booted, post-handoff ADB settle passed,
and `adb shell su -c id` returned Magisk root with `uid=0`. The run then failed at the first staging
command before any ACDB/AppType probe or Android playback because the M0 transient helper still used
`/cache/a90-audio-acdb-v2396` as its artifact directory.

The device rolled back through the checked helper to V2321 and final selftest remained `fail=0`.

## Private evidence

Run directory:

- `workspace/private/runs/audio/v2397-android-acdb-measurement-20260615-075409`

Key evidence:

```text
android-post-handoff-settle-2 stdout:
uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0

stage-0 stderr:
chmod: /cache/a90-audio-acdb-v2396: Permission denied
```

Step summary from `result.json`:

| Step | Result |
| --- | --- |
| `flash_android` | ok |
| `android-post-handoff-settle-0` (`adb wait-for-device`) | ok |
| `android-post-handoff-settle-1` (boot-complete recheck) | ok |
| `android-post-handoff-settle-2` (`su -c id`) | ok, `uid=0` |
| `stage-0` | failed before being recorded in `steps`; runner exception reason points to `stage-0` |
| `android-wait-device-before-rollback` | ok |
| `android-reboot-recovery-for-rollback` | ok |
| `rollback-v2321` | ok |

Final native verification after rollback:

```text
A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)
selftest: pass=11 warn=1 fail=0
```

## Root cause

This is a staging-path bug, not an audio result and not a Magisk-root failure.

Current V2396/V2397 M0 code has `/cache/a90-audio-acdb-v2396` hard-coded in three places:

- `REMOTE_ARTIFACT_DIR = "/cache/a90-audio-acdb-v2396"`;
- the generated `a90_acdb_probe.sh` sets `OUT="/cache/a90-audio-acdb-v2396"`;
- `service.sh` appends to `/cache/a90-audio-acdb-v2396/service.log`.

On the Android handoff image, Magisk root can run commands, but `chmod` on that `/cache` child path
returns permission denied. Since this happens during `stage-0`, no probe, logcat playback, artifact
pull, or post-live analysis ran.

## Required next fix

Host-only before any further live retry:

1. Move the M0 artifact directory under the already staged writable tree, e.g.
   `/data/local/tmp/a90-audio-acdb-v2396/artifacts`.
2. Update `REMOTE_ARTIFACT_DIR`, generated `a90_acdb_probe.sh`, generated `service.sh`, collection,
   cleanup, optional strace output, tests, dry-run safety expectations, and docs.
3. Keep M0 as the default transient helper. Do not escalate to M1 boot module; V2405 did not prove an
   early timing miss, only a bad Android artifact path.
4. After host validation, run a fresh bounded AUD-5A live rerun.

## Safety result

- Forbidden partitions: not touched.
- Boot partition writes: checked helper only.
- Android boot image: sealed private 0600 copy with expected SHA.
- Rollback: checked helper restored V2321.
- Final health: native-init `selftest fail=0`.
