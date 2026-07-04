# WSTA115 Strace Image Prep + WSTA114 Trace Timeout Live

Date: 2026-07-05 03:27 KST

## Scope

This unit prepared a private strace-enabled SD work image, then ran the
WSTA114 syscall-trace live gate against the D-public smoke service. It did not
flash a boot image, reboot native init, associate Wi-Fi, run DHCP, open a public
tunnel, run a public smoke request, mutate packet filters, touch userdata, or
switch root.

## Host Preparation

- Confirmed the default local SD image did not contain `/usr/bin/strace`.
- Ran WSTA3 rootfs prep with `--stage-syscall-trace-tools`.
- Built a private ext4 SD image from that rootfs:
  - image: `workspace/private/runs/server-distro/wsta115-strace-rootfs-20260705T0309KST/debian-bookworm-arm64-wsta115-strace.img`
  - SHA256: `40a01268ae6f77d1548dd71f9ef30f4d31fdce437d90a6edcc7721f0e26dd159`
- Host-side image inspection verified:
  - `/usr/bin/strace` present and executable.
  - `a90-service-launch` present and executable.
  - D-public service-hardening policy present.
  - packet-filter helper dependencies present.
  - `/etc/a90-server-distro-stage` records the deferred syscall-trace target
    and public-default-off markers.

All image artifacts and fuller debug output remain under `workspace/private/`.

## Live Result

WSTA114 was run with the explicit live gates and the private trace-artifact
acknowledgement. The clean remote SD image was installed and verified with the
same SHA256 as the local private image.

The runner reached the expected setup gates:

- baseline selftest clean.
- local image and remote image ready.
- chroot mount ready.
- Dropbear/SSH marker reachable.
- service-hardening assets staged.
- D-public smoke helpers staged.
- syscall-trace marker staged.
- public exposure default-off.
- smoke binaries present.
- `strace` present in the chroot.
- final cleanup clean.
- final selftest `fail=0`.

The trace itself did **not** complete. The live decision was:

```text
wsta114-blocked-trace-timeout
```

The preserved partial marker sequence reached `A90WSTA114_STRACE_PRESENT=1`
but did not reach `A90WSTA114_TRACE_PROCESS_STARTED=1` or the service-child
begin marker. This places the timeout at the `strace ... a90-service-launch ...
/bin/sh service-child.sh` command boundary, after tool and policy presence were
verified but before the traced smoke child produced its first output.

## Non-Claims

- No syscall profile was captured.
- The `syscall traces not captured` blocker is not retired.
- WSTA108/WSTA90 hardening status must not consume this as a pass proof.
- The timeout is not evidence that the smoke service cannot run; WSTA110 already
  proved the smoke launcher path without strace.
- This does not generalize to Dropbear, tunnel, HUD, or other service profiles.

## Source Follow-Up

After the live timeout, the WSTA114 runner was tightened so SSH timeouts are
captured as structured blocked evidence instead of an opaque runner error:

- `run_trace_probe()` now preserves partial stdout/stderr on
  `subprocess.TimeoutExpired`.
- `classify()` now fails closed as `wsta114-blocked-trace-timeout` when the
  trace probe does not complete.
- The trace script now uses a self-contained service-child wrapper under
  `strace`, which removes the previous background-strace kill/wait ambiguity.

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta114_syscall_trace_chroot_profile.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta114_syscall_trace_chroot_profile

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  $(find workspace/public/src/scripts/server-distro -maxdepth 1 -type f \
    \( -name 'run_wsta*.py' -o -name 'prepare_wsta3_sta_rootfs.py' \) | sort -V)

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_prepare_wsta3_sta_rootfs \
  $(find tests -maxdepth 1 -type f -name 'test_server_distro_wsta*.py' \
    -printf '%f\n' | sort -V | sed 's/^/tests./; s/\.py$//' | tr '\n' ' ')

git diff --check
```

Result:

- Focused WSTA114 runner tests: `10 tests OK`.
- Full server-distro WSTA regression: `385 tests OK`.
- `git diff --check`: pass.
- The WSTA94 runner-error JSON printed during the full run is the expected
  exception-path fixture from that unit test; unittest completed OK.

## Next

Run a smaller WSTA116 isolation ladder before retrying the full smoke profile:

1. `strace /bin/true` inside the same chroot over SSH.
2. `strace a90-service-launch ... /bin/true`.
3. `strace` the smoke launcher with remote background execution and file polling
   so SSH foreground wait behavior is not conflated with ptrace behavior.

Only after this isolates ptrace versus launcher/service wait behavior should
WSTA114 be retried as a profile-capture pass.
