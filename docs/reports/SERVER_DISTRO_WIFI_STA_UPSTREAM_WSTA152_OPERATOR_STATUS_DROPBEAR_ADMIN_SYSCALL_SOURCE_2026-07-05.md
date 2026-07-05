# WSTA152 Operator Status Dropbear Admin Syscall Source Pass

Date: 2026-07-05 11:56 KST

## Verdict

WSTA152 folds the WSTA151 `dropbear-admin-usb` syscall trace proof into the
WSTA108 operator server-status bundle.  This was host-only.  It did not touch
the device, flash, reboot, connect Wi-Fi, run DHCP, open a public tunnel,
mutate packet filters, write userdata, or switch root.

Result: PASS.  WSTA108 now accepts a fail-closed
`--wsta151-dropbear-admin-syscall-proof-json` input, records
`DROPBEAR_ADMIN_SYSCALL_TRACE_LIVE_PROVEN`, removes `dropbear-admin-usb` from
remaining syscall profiles, and removes the stale syscall blocker when the
remaining syscall profile list becomes empty.

## Source Changes

- Added
  `workspace/public/src/scripts/server-distro/run_wsta151_dropbear_admin_syscall_trace_summary.py`.
  It re-reads the private WSTA151 live result and emits a compact redacted
  `wsta151_dropbear_admin_syscall_trace_live.json` proof.
- Extended
  `workspace/public/src/scripts/server-distro/run_wsta108_operator_server_status.py`
  with `--wsta151-dropbear-admin-syscall-proof-json`.
- Added WSTA108 checks for:
  - WSTA151 proof supplied;
  - Dropbear admin syscall trace live-proven;
  - accept observed;
  - private trace artifacts saved.
- Added focused tests for the WSTA151 summary runner and WSTA108 fail-closed
  behavior.

## Proof Folded

Generated WSTA151 summary decision:

```text
wsta151-dropbear-admin-syscall-trace-live-pass
```

Summary run:

```text
workspace/private/runs/server-distro/wsta152-wsta151-dropbear-admin-syscall-summary-20260705T1148KST/
```

Source live run:

```text
workspace/private/runs/server-distro/wsta151-dropbear-admin-syscall-trace-live-20260705T113918KST/
```

The folded proof includes:

- service `dropbear-admin-usb`, scope `dropbear-admin-usb-daemon`.
- daemon `/usr/sbin/dropbear`.
- root-boundary auth daemon model.
- bind `192.168.7.2:2222`, USB/NCM admin scope.
- UID/GID `3903/3903` admin-login proof.
- root SSH rejected.
- root `authorized_keys` absent.
- password login, root login, and forwarding disabled.
- core syscalls observed: `execve`, `socket`, `bind`, `listen`.
- accept observed.
- trace artifacts saved privately.
- syscall profile count `53`.

## Operator Status Result

Private WSTA108 status regeneration decision:

```text
wsta108-operator-server-status-source-pass
```

Status run:

```text
workspace/private/runs/server-distro/wsta152-operator-status-dropbear-admin-syscall-v2-20260705T1158KST/
```

Key resulting state:

- Server state: `SERVER_PROFILE_READY_DEFAULT_OFF`.
- Dropbear admin syscall state:
  `DROPBEAR_ADMIN_SYSCALL_TRACE_LIVE_PROVEN`.
- `dropbear_admin_syscall_trace_live_proven=true`.
- `dropbear_admin_syscall_accept_observed=true`.
- `dropbear_admin_syscall_trace_artifacts_saved=true`.
- Remaining syscall profiles: empty list.
- Operator next actions include
  `derive-seccomp-policy-from-live-syscall-baselines`.
- Public exposure remains default-off.
- No public URL value, admin public key value, or secret value is present in
  the public summary or generated markdown.

Remaining non-syscall status blocker:

```text
remaining service users/groups not live-proven beyond dpublic-smoke-httpd/dropbear-admin-usb/cloudflared-quick-tunnel
```

That residual is service-launcher/user coverage, not a syscall-profile gap.

## Validation

- `py_compile`:
  - `run_wsta151_dropbear_admin_syscall_trace_summary.py`
  - `run_wsta108_operator_server_status.py`
  - `test_server_distro_wsta151_dropbear_admin_syscall_trace_summary.py`
  - `test_server_distro_wsta108_operator_server_status.py`
- Focused WSTA151 summary + WSTA108 unit tests: `51 tests OK`.
- Full server-distro regression: `532 tests OK`.
- WSTA151 summary generation from the live WSTA151 private result: pass.
- WSTA108 operator status regeneration with WSTA151 proof: pass.

## Safety

This unit was source/status-only.  WSTA151's live capture was already completed
and reported separately.  WSTA152 only read private JSON artifacts and wrote new
private summary/status outputs.

## Next

Use the live syscall baselines to derive concrete seccomp policy, or first
close the remaining service-launcher/user coverage for the non-syscall profiles
that still show as residual status work.
