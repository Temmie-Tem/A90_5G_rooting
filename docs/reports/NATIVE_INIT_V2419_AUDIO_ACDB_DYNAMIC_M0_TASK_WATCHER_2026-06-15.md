# NATIVE_INIT V2419 — ACDB payload capture dynamic M0 task watcher

## Scope

- Unit: AUD-5D / N3-CAP follow-up after V2418.
- Goal: keep the Android/Magisk-root M0 observer model but fix the coverage gap
  found by V2418, where the real ACDB worker TID was created after the one-time
  task snapshot.
- Device action: none. This is host-only source/test work.
- Safety boundary unchanged: no native calibration ioctl, no native speaker
  write, no persistent Magisk module, no committed raw payload bytes.

## V2418 blocker recap

V2418 proved that Android speaker playback still triggered the stock-good ACDB
sequence, but the ioctl observer saw zero `msm_audio_cal` entries. The decisive
detail was the thread identity:

- logcat ACDB edge: audio HAL TID `4278`;
- pre-playback task snapshot for audio HAL PID `798`: did not include `4278`;
- helper outputs: 29 per-TID JSONL files, zero ioctl entries.

Therefore the miss was not yet an early-payload miss and did not justify M1. It
was a dynamic-thread coverage miss.

## Implementation

V2419 updates the existing V2415 capture infrastructure instead of adding a new
Magisk tier.

### Controller script

`capture_shell_script()` now generates a dynamic task watcher:

- establishes a capture deadline using `START_TS` / `END_TS`;
- polls `pidof android.hardware.audio.service` and `pidof audioserver` during
  the capture window;
- snapshots `/proc/<pid>/task` repeatedly into
  `proc-<pid>-tasks-snapshots.txt`;
- deduplicates observed TIDs through `seen-tids.txt`;
- starts one helper for each newly observed TID;
- passes `--duration-sec "$remaining"` so late-created TIDs are traced only for
  the remaining capture window;
- records helper launches in `capture-controller.log` with
  `A90_V2415_HELPER_START pid=<pid> tid=<tid> remaining=<sec>`;
- records helper process ownership in `helper-pids.txt`.

The default poll interval is `A90_V2415_TASK_POLL_SEC=0.1`, overrideable by env.

### Ptrace helper

`a90_acdb_ioctl_capture_v2415.c` no longer blocks indefinitely in a plain
`waitpid()` while tracing idle threads:

- uses `waitpid(..., WNOHANG)` polling with a deadline;
- emits a private JSONL `timeout` event when a traced thread stays idle past the
  helper lifetime;
- always emits `stop` with `timed_out=true|false`;
- attempts a bounded stop-for-detach path before `PTRACE_DETACH` if the tracee
  is still running when the deadline expires.

This makes future runs auditable: `start`-only JSONL files should no longer be
the normal idle-thread outcome.

## Magisk decision

M1 temporary Magisk boot-module capture remains deferred.

The Wi-Fi-style pattern is still the right model: use Magisk only as an
Android-good measurement capsule, not as a native-init runtime dependency. M1 is
reserved for the narrower case where this dynamic M0 watcher still misses a
logcat-proven ACDB edge.

Practical ladder:

- **M0 transient helper, default:** boot Android through the checked handoff, use
  Magisk `su` to stage a run-local observer under `/data/local/tmp`, collect
  private artifacts, clean up, then roll back to V2321. This matches the current
  Wi-Fi-style measurement handoff and is what V2419 improves.
- **M1 temporary boot module, gated:** package an observer so it is present at
  Android boot only if dynamic M0 proves a true early-payload miss. It must be a
  separate V-iteration with its own exact gate, rollback proof, no persistent
  native dependency, and no committed module ZIP/raw payload bytes.
- **M2 vendor/HAL wrapping, out of current scope:** wrapping audio HAL or ACDB
  loader behavior would be vendor-behavior modification, not observation. Do not
  start it unless both M0 and M1 fail to expose the single needed payload edge.

So the immediate direction is not "install a module now"; it is "make M0
complete enough that M1 has a precise, falsifiable trigger." V2419 closes the
known M0 coverage gap before escalating.

## Validation

Host-only validation performed for this unit:

- Python compile checks for touched revalidation scripts/tests.
- AArch64 static helper materialization through the V2415 dry-run path.
- Focused AUD-5D unit suite:
  `python3 -m unittest discover -s tests -p 'test_native_audio_acdb_payload_capture*241*.py' -v`.

Full-suite validation should be run before commit.

## Next unit

The next meaningful unit is a rollbackable Android live rerun using this dynamic
M0 observer, under the same AUD-5D boundary:

- transient Magisk-root observer only;
- no native calibration ioctl;
- no native speaker write;
- rollback to V2321;
- raw payload bytes stay private.

Expected discriminator:

- `captured-msm-audio-cal-payload-events` → decode request headers, command
  order, private payload hashes, mem-handle policy, and cleanup behavior.
- `dynamic-m0-missed-logcat-proven-acdb-edge` → only then design an M1 temporary
  Magisk boot-module observer as a separate exact-gated measurement unit.
