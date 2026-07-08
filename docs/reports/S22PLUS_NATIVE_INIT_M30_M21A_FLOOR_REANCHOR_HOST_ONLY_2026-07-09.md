# S22+ Native-Init M30/M21A Floor Re-Anchor Host-Only (2026-07-09 KST)

## Verdict

HOST-ONLY READY / NO LIVE AUTH.

M29 weakened the collection-timing hypothesis. Capturing retained evidence at
the first post-candidate rollback boot still produced an Android
`reboot,download` log, not an S24 native-init marker. The next useful live unit
is not another S24 dependency-complete run. It is a smaller floor discriminator
with an externally distinguishable pre-download state.

The best existing shape is M21A: raw AArch64 PID1, direct `nanosleep(90s)`,
then direct `reboot(..., "download")`, then infinite park if the reboot syscall
returns. This re-anchors whether a direct native `/init` can execute one raw
syscall and self-enter Download mode without relying on retained logs or module
loading.

No flash, reboot, device write, or live rollback was performed in this unit.

## Why M29 Changes The Plan

M29 showed:

```text
m29_S24_self_download_seen=0
m29_S24_result=no-self-download-manual-download-required
```

The first post-M29 rollback capture contained:

```text
last_kmsg_bytes=2097136
m29_marker_count=0
s22_native_count=0
android_reboot_download_count=1
android_really_probe_count=49
watchdog_count=30
```

That means the retained channel is alive, but it resolved to an Android boot
that handled `sys.powerctl='reboot,download'`. It did not observe the S24
candidate. Repeating S24 or moving to F43 under the old model would keep
spending attended flashes on an unobserved failure surface.

## Why S24 Is Not The Next Unit

The S24 `/init` emits its native marker before module loading:

```text
setup_minimal_fs();
emit(k_marker);
load_modules();
reboot_download_then_park();
```

S24 marker count was still zero. That pushes the uncertainty below the
dependency-complete module closure: direct `/init` acceptance, first syscalls,
minimal filesystem setup, or retained-evidence replacement. It is not evidence
that module 1-24 dependency closure still needs more broad module permutation.

## M21A Host Artifact Re-Check

Rebuilt host-only with:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_m21a_raw_nanosleep_download.py \
  --force
```

Current private output:

```text
workspace/private/outputs/s22plus_native_init/m21a_raw_nanosleep_download_v0_1/
```

Pinned hashes:

```text
AP.tar.md5        d1949a56c60c71498d68753d2ffd6064719fafce1ad0e3959ebb8a4255bb6c79
boot.img          61d7dc9818b79c810b30370edfe4df2b55ec451588defb48458fefae9c6c00a5
/init             10f525760b170cba4ec55d7fd4955c466601253258371cb571eb45515bd9cf30
source            300ed990c8ea476c3744e18327ae08277c0d27dc443e99245aeecba457968c4f
base Magisk boot  2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel            bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
```

Runtime shape:

```text
svc #0 count        2
syscalls            nanosleep(101), reboot(142)
dwell               90 seconds
filesystem setup    none
kmsg/pstore write   none
module insertion    none
configfs/USB role   none
Android/Magisk      no handoff
AP tar member       boot.img.lz4 only
```

The no-change `magiskboot unpack/repack` probe remains byte-identical to the
known-booting Magisk boot, and the candidate preserves the Magisk-patched
kernel hash.

## Helper Hardening

`s22plus_m21a_raw_nanosleep_download_live_gate.py` now has:

- `missing_policy_markers()` for testable fail-closed AGENTS policy checks.
- Canonical `timeline.json` writer using exactly `events:[{name,timestamp_utc}]`.
- Live event coverage for candidate flash start/done, candidate boot-ready
  observation start, rollback flash start/done, rollback boot ready, and session
  start/end.
- Unit tests for early Odin rejection, post-dwell Odin acceptance, current
  retired-policy failure, raw-source constraints, current private manifest
  verification, and canonical timeline shape.

Current `AGENTS.md` still intentionally retires M21A. The helper therefore
must fail closed until a fresh M30/M21A exception is added with the exact hashes
above and a new one-shot ack.

## Future Live Interpretation

A fresh M30/M21A live gate should be interpreted as:

- PASS: no manual key intervention, original Odin endpoint disconnects after
  candidate flash, no Odin before the 90s dwell threshold, and Odin appears only
  after dwell plus grace.
- FAIL / no proof: Odin appears before 90s, Android returns, the device visibly
  loops before dwell, or no Download mode appears after dwell plus grace.
- RECOVERY ONLY: operator enters Download manually before the helper asks for
  rollback.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m21a_raw_nanosleep_download_live_gate.py \
  tests/test_s22plus_m21a_raw_nanosleep_download_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_s22plus_m21a_raw_nanosleep_download_live_gate

Ran 8 tests in 0.010s
OK
```

## Next

If live testing is selected, do not reuse the retired M21A authorization. Add a
fresh, narrow M30/M21A boot-only exception to `AGENTS.md` with the exact AP,
boot, `/init`, source, base boot, and kernel hashes above; require no manual key
entry until the helper reaches dwell+grace timeout or asks for rollback; then
run a dry-run/preflight before any live flash.
