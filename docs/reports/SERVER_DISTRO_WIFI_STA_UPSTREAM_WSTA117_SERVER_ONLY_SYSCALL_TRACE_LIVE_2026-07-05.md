# WSTA117 Server-Only Syscall Trace Live Pass

Date: 2026-07-05 04:03 KST

## Scope

WSTA117 folds the WSTA116 finding back into the WSTA114 syscall trace runner.
Instead of tracing the orchestration shell plus HTTP client, WSTA114 now traces
only the smoke server under `a90-service-launch`; the loopback HTTP client runs
outside the traced process tree. This unit did not flash a boot image, reboot
native init, associate Wi-Fi, run DHCP, open a public tunnel, run a public smoke
request, mutate packet filters, touch userdata, or switch root.

## Source Changes

- Updated `run_wsta114_syscall_trace_chroot_profile.py` to use the server-only
  trace shape:

```text
a90-service-launch dpublic-smoke-httpd strace -f -o <trace> a90-dpublic-smoke-httpd 127.0.0.1 8080
```

- The trace file is precreated writable so the dropped `a90www` process can
  write it after `setpriv`.
- The HTTP client is run by the SSH orchestration shell outside the traced
  process tree.
- Non-zero HTTP client results are now captured as explicit evidence instead of
  being swallowed by `set -e`.
- Updated WSTA114 tests for the server-only shape.

## Live Result

Run:

```text
workspace/private/runs/server-distro/wsta117-server-only-wsta114-live-v2-20260705T0407KST/
```

Decision:

```text
wsta114-syscall-trace-smoke-chroot-live-pass
```

Key proof:

- public exposure default-off.
- `strace` present.
- service launcher exec decision logged.
- smoke child ran with `NoNewPrivs=1`.
- smoke child effective capabilities were zero.
- loopback HTTP GET returned `A90_DPUBLIC_SMOKE_OK`.
- raw trace saved privately.
- syscall-name profile saved privately.
- core smoke-server syscalls observed: `execve`, `socket`, `bind`, `listen`.
- postcheck clean.
- final selftest `fail=0`.

Captured syscall-name profile:

```text
accept
bind
brk
close
execve
getrandom
listen
mprotect
prlimit64
readlinkat
rseq
rt_sigaction
rt_sigreturn
set_robust_list
set_tid_address
setsockopt
socket
write
```

Artifact metadata:

- raw trace: private artifact saved, size `2173` bytes.
- syscall list: private artifact saved, size `163` bytes.
- `trace_artifacts.all_saved=true`.

## Interpretation

The WSTA114/WSTA115 syscall trace blocker is resolved for the
`dpublic-smoke-httpd` service scope. WSTA116 proved ptrace and launcher tracing
were already working; WSTA117 proves the correct shape is server-only tracing
with the HTTP client outside the traced tree.

This is a smoke-service syscall profile proof only. It does not generalize to
Dropbear, Cloudflare tunnel, HUD, or other service profiles.

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta114_syscall_trace_chroot_profile.py \
  workspace/public/src/scripts/server-distro/run_wsta116_strace_isolation_ladder.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta114_syscall_trace_chroot_profile \
  tests.test_server_distro_wsta116_strace_isolation_ladder
```

Result:

- Focused WSTA114/WSTA116 tests: `18 tests OK`.
- WSTA114 server-only live: `wsta114-syscall-trace-smoke-chroot-live-pass`.
- Final device selftest: `fail=0`.

## Next

Fold this private WSTA114 pass proof into WSTA108/WSTA90 operator status so the
smoke-service syscall-trace blocker is retired there, without broadening the
claim beyond `dpublic-smoke-httpd`.
