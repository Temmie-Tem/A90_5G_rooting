# WSTA232 D-HARDEN Complete Status

Date: 2026-07-06 KST
Scope: host-only D-harden close-out status

## Verdict

PASS.  WSTA232 consumes the WSTA231/WSTA108 private operator status and emits
one `D_HARDEN_COMPLETE_DEFAULT_OFF` status.  It consolidates the already-landed
D-harden levers and replaces the remaining server-endgame action with the
close-out sequence from the operator charter.

## Private Evidence

Representative host-only run:

```text
workspace/private/runs/server-distro/wsta232-dharden-complete-status-20260706T0001KST/wsta232_result.json
workspace/private/runs/server-distro/wsta232-dharden-complete-status-20260706T0001KST/wsta232_dharden_complete_status.json
workspace/private/runs/server-distro/wsta232-dharden-complete-status-20260706T0001KST/wsta232_dharden_complete_status.md
```

Decision:

```text
wsta232-dharden-complete-status-source-pass
```

## Status Result

Compacted status:

```text
state=D_HARDEN_COMPLETE_DEFAULT_OFF
complete=true
server_state=SERVER_PROFILE_READY_DEFAULT_OFF
public_state=PUBLIC_OFF
public_exposure_default_off=true
blocking_before_enforcement=[]
launcher_remaining_profiles=[]
syscall_remaining_profiles=[]
```

Landed D-harden levers:

```text
seccomp_real_services=true
capability_drop_nonroot_services=true
native_uplink_root_boundary=true
legacy_iptables_loopback_default_drop=true
cloudflared_egress_allowlist=true
apparmor_parked_unavailable=true
```

WSTA232 retires the source next-action
`continue-dpublic-server-endgame-after-cloudflared-egress-live` in its output
status and replaces it with close-out-only actions:

```text
keep-public-exposure-default-off
perform-attended-cold-boot-persistence-smoke-measurement
write-server-distro-epic-close-report
halt-after-server-distro-close-report
```

## Safety

WSTA232 is host-only.  It reads the existing private WSTA231/WSTA108 status and
emits a derived status bundle.

It did not perform any device action, boot flash, native reboot, Wi-Fi connect,
DHCP, public tunnel, public smoke, packet-filter mutation, rootfs mutation,
userdata write, LSM profile load, or switch-root.

No raw DNS/TLS route values, public URL values, tunnel credentials, Wi-Fi
credentials, confirm tokens, or route endpoints are included in this report.

## Validation

Static compile:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/run_wsta232_dharden_complete_status.py tests/test_server_distro_wsta232_dharden_complete_status.py
```

Focused WSTA232 tests:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_server_distro_wsta232_dharden_complete_status
```

Result: `6 tests OK`.

Full server-distro regression:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest discover -s tests -p 'test_server_distro*.py'
```

Result: `850 tests OK`.

## Next

D-harden close-out status is now complete.  The next chartered step is one
attended cold-boot persistence smoke measurement, not a new hardening lever or
new server scaffold.
