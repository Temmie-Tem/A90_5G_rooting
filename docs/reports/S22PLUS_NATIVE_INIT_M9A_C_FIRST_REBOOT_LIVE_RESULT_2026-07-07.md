# S22+ Native-Init M9A C First-Reboot Live Result - 2026-07-07

## Verdict

M9A produced a delayed automatic Samsung download-mode return, outside the
helper's 60 second self-download window.

Safety result passed: the exact SHA-pinned M9A boot-only AP flashed, the
original Odin endpoint disconnected, the helper's bounded 60 second observation
did not see a new Odin endpoint, the operator observed bootloop-like behavior,
host polling shortly after the helper timeout saw Samsung download mode appear
without a new candidate flash, the pinned Magisk boot-only rollback AP flashed
successfully, and Android returned to the rooted Magisk baseline.

Interpretation: do not call this a clean in-window PASS like M4T3. Do treat it
as a materially different result from M8A. M9A shows that freestanding C entry,
compiler-emitted NOTE/.eh_frame metadata, stack/helper path, and immediate
`reboot("download")` can eventually reach download mode. The next split should
move to M8A's first runtime side effects, not to M9B metadata removal.

## Candidate

```text
AP.tar.md5             c953f74fe7e3cdc226ebd3e1f0bac2142ee39e14483d87022714ae98e336d6b1
boot.img               4c998680a1ccdbd5017053d7da58858ab818fc0644f08ef5bb0fc5d0dcc2d981
M9A /init              46dfc4ecf92457260484d38360c70c0a45a1b7aead3a5cac567ec21ab2c7d97f
source                 6248617a4d2fe077768aef1324937659d33a0c93a453d0ecf9cd8cc3d3ec34a8
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                 bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
runtime                freestanding-c-raw-syscall
```

M9A intended runtime:

```text
direct PID1
freestanding C
build-id and .eh_frame present
explicit stack/helper path
no marker
no VFS
no kmsg
no mount
no sleep
no modules
no configfs or USB gadget
first live syscall = reboot("download")
park if reboot returns
```

## Live Timeline

Private live run log:

```text
workspace/private/runs/s22plus_m9a_c_first_reboot_live_gate_20260707T113641Z/s22plus_m9a_c_first_reboot_live_gate.txt
```

Key helper events:

```text
11:36:41Z  live helper start
11:37:03Z  Odin/download device appeared for candidate flash
candidate_odin_rc=0
11:37:06Z  original Odin endpoint absent; disconnect proof acquired
11:37:06Z  self-download observation window started
11:38:06Z  self-download observation ended, m9a_self_download_seen=0
```

After helper exit, Codex continued host-side polling because the operator
reported bootloop behavior. That extra polling saw Samsung download mode appear
at about `11:38:52Z`, roughly 106 seconds after the original Odin endpoint
disconnected. That late endpoint was outside the helper's proof window, so the
helper correctly exited `rc=4` and did not auto-rollback inside the live run.

Private rollback run log:

```text
workspace/private/runs/s22plus_m9a_c_first_reboot_live_gate_20260707T113925Z/s22plus_m9a_c_first_reboot_live_gate.txt
```

Rollback events:

```text
11:39:25Z  rollback helper start from Samsung download mode
magisk_rollback_odin_rc=0
11:40:10Z  Android returned with boot_completed=1 and Magisk root
```

## Post-Rollback Verification

Independent host check after helper completion:

```text
sample count            4
sys.boot_completed      1
init.svc.bootanim       stopped
boot reason             reboot,download
Magisk root             available
boot hash               2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

Retained evidence:

```text
pstore files             none
/proc/last_kmsg bytes    2097136
M9A marker in retained   no
```

The retained-marker result is expected: M9A intentionally has no marker and no
kmsg path. The proof channel is host-observed download-mode return.

## Interpretation

Updated live boundary:

```text
M4T3 raw assembly first-action reboot("download")          in-window PASS, about 44 s
M9A freestanding C first-action reboot("download")         delayed download, about 106 s
M8A freestanding C + VFS/kmsg/sleep before reboot          NO SELF-DOWNLOAD in prior run
```

This retires the immediate M9B path for now:

```text
remove build-id / .eh_frame / C metadata  not next
raw-assembly VFS staging                  not next
```

M9A shows the freestanding C runtime can reach the reboot request, but with
slow/bootloop-like behavior. The sharper next unit is host-only: build the
smallest M10A side-effect candidate that starts from M9A and adds only one
M8A-style side effect before reboot, then uses a longer self-download window.

Recommended M10A:

```text
freestanding C
first side effect: mkdirat("/dev", 0755)
no /dev/kmsg
no mknodat
no mount
no sleep
then reboot("download")
helper self-download wait >= 150 s
```

Branch logic:

```text
M10A delayed/in-window download:
  mkdirat("/dev") is survivable; add the next single side effect.

M10A no download:
  the first VFS syscall or pathname access is the failing boundary.
```

## Stop Rule

M9A is recovered. Do not repeat M9A merely to fit the previous 60 second helper
window. If repeated later for timing measurement, change the wait window and
report it as a timing run, not a new behavioral candidate.
