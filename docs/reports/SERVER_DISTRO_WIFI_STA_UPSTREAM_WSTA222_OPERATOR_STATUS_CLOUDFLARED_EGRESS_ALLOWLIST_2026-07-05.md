# WSTA222 Operator Status Cloudflared Egress Allowlist

Date: 2026-07-05
Scope: host-only WSTA108 status folding

## Result

PASS.  WSTA222 folds the WSTA221 cloudflared egress allowlist policy into the
WSTA108 operator server status bundle.

Representative host-only status run:

```text
workspace/private/runs/server-distro/wsta222-operator-status-cloudflared-egress-allowlist-20260705T221905KST/wsta108_operator_server_status.json
workspace/private/runs/server-distro/wsta222-operator-status-cloudflared-egress-allowlist-20260705T221905KST/wsta108_operator_server_status.md
```

Decision:

```text
wsta108-operator-server-status-source-pass
```

## Status State

`run_wsta108_operator_server_status.py` now accepts:

```text
--wsta221-cloudflared-egress-allowlist-policy-json
```

The supplied JSON must be a private WSTA221 pass.  WSTA108 fail-closes if the
proof is non-pass or if any required policy condition is missing.

The compact status object is:

```text
server_status.hardening.cloudflared_egress_allowlist_policy
```

Pass state:

```text
CLOUDFLARED_EGRESS_ALLOWLIST_HARDENING_POLICY_DEFINED
```

Accepted status fields include:

```text
cloudflared_egress_allowlist_policy_defined=true
hardening_lever=legacy-iptables-cloudflared-egress-allowlist
activation=explicit-operator-gated-after-default-drop
default_public_off=true
live_execution_requested=false
packet_filter_mutation_by_wsta221=false
owner_match_fail_closed=true
preserve_existing_default_drop=true
restore_exact_required=true
control_plane_must_survive_apply=true
target_user=a90tunnel
target_uid=3902
```

## Operator Actions

With WSTA219 attended default-drop live evidence and WSTA221 policy evidence
both supplied, WSTA108 now reports:

```text
keep-public-exposure-default-off
use-explicit-wsta88-live-gate-only-when-attended
prepare-attended-cloudflared-egress-allowlist-live-gate
move-to-cloudflared-egress-allowlist-live-gate
```

The previous abstract action is retired from the current status:

```text
move-to-next-hardening-layer-after-attended-default-drop-live
```

## Safety

WSTA222 is host-only.  It reads existing private run artifacts and emits a
status bundle.

It did not perform any device action, boot flash, native reboot, Wi-Fi connect,
DHCP, public tunnel, public smoke, packet-filter mutation, rootfs mutation,
userdata write, LSM profile load, or switch-root.

## Validation

Static compile:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/run_wsta108_operator_server_status.py workspace/public/src/scripts/server-distro/run_wsta221_cloudflared_egress_allowlist_policy.py tests/test_server_distro_wsta108_operator_server_status.py tests/test_server_distro_wsta221_cloudflared_egress_allowlist_policy.py
```

Focused WSTA108/WSTA221 tests:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest tests/test_server_distro_wsta108_operator_server_status.py tests/test_server_distro_wsta221_cloudflared_egress_allowlist_policy.py
```

Result: `67 tests OK`.

Full server-distro regression:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest discover -s tests -p 'test_server_distro*.py'
```

Result: `816 tests OK`.

## Next

Proceed only through an attended cloudflared egress allowlist live gate.  That
gate should preflight owner-match and restore support, keep the existing
default-drop path active, avoid logging public URL values or secrets, and prove
control-plane survival before declaring success.
