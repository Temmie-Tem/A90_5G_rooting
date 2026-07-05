# WSTA221 Cloudflared Egress Allowlist Policy

Date: 2026-07-05

## Verdict

PASS.  WSTA221 selects the next D-public hardening layer after the attended
default-drop live proof: a cloudflared-specific egress allowlist policy using
the existing legacy-iptables backend.

This is a host-only policy unit.  It does not apply packet-filter rules or
start public exposure.

Private evidence:

```text
workspace/private/runs/server-distro/wsta221-cloudflared-egress-allowlist-policy-20260705T221840KST/wsta221_result.json
workspace/private/runs/server-distro/wsta221-cloudflared-egress-allowlist-policy-20260705T221840KST/wsta221_cloudflared_egress_allowlist_policy.json
workspace/private/runs/server-distro/wsta221-cloudflared-egress-allowlist-policy-20260705T221840KST/wsta221_cloudflared_egress_allowlist_policy.md
```

Decision:

```text
wsta221-cloudflared-egress-allowlist-policy-source-pass
```

## Policy State

The emitted policy records:

```text
schema=a90-wsta221-cloudflared-egress-allowlist-policy-v1
state=CLOUDFLARED_EGRESS_ALLOWLIST_HARDENING_POLICY_DEFINED
hardening_lever=legacy-iptables-cloudflared-egress-allowlist
service=cloudflared-quick-tunnel
backend=legacy-iptables
policy=cloudflared-egress-allowlist
activation=explicit-operator-gated-after-default-drop
default_public_off=true
live_execution_requested=false
packet_filter_mutation_by_wsta221=false
target_user=a90tunnel
target_uid=3902
```

The candidate rule shape is intentionally not applied here.  The next live gate
must preflight owner-match support, derive the redacted DNS/TLS route in the
attended session, apply only after loopback default-drop is active, prove the
cloudflared public smoke still works, prove unrelated services are not opened,
prove USB/NCM control-plane survival, and restore the exact rules before
declaring `PUBLIC_OFF` success.

## Evidence Folded

WSTA221 accepts the policy only when all source evidence agrees:

```text
WSTA220 operator status: attended default-drop live proven, public exposure default-off
WSTA122 cloudflared model: non-root a90tunnel identity, no new privs, zero effective caps, outbound-only model
WSTA125 runtime proof: outbound-only cloudflared observed, private URL artifact redacted, cleanup and packet-filter restore passed
```

Representative checks:

```text
operator_status_ready=true
cloudflared_model_ready=true
cloudflared_runtime_ready=true
policy_ready=true
```

## Safety

This was host-only policy generation.  No device action, boot flash, native
reboot, Wi-Fi connect/association, DHCP, ping, public tunnel, public smoke,
packet-filter mutation, rootfs mutation, userdata write, LSM profile load, or
switch-root occurred.

Safety fields remained:

```text
device_action=false
boot_flash=false
native_reboot=false
wifi_connect=false
dhcp=false
public_tunnel=false
public_smoke=false
packet_filter_mutation=false
userdata_touch=false
switch_root=false
public_url_value_logged=false
secret_values_logged=0
```

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/run_wsta221_cloudflared_egress_allowlist_policy.py tests/test_server_distro_wsta221_cloudflared_egress_allowlist_policy.py
PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest tests/test_server_distro_wsta221_cloudflared_egress_allowlist_policy.py
PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest discover -s tests -p 'test_server_distro*.py'
```

Results:

```text
WSTA221 unit tests: 4 tests OK
server-distro regression: 816 tests OK
host-only WSTA221 run: PASS
```

## Code Changes

- Added `run_wsta221_cloudflared_egress_allowlist_policy.py`.
- Added focused WSTA221 tests for the valid policy, explicit/private gates,
  runtime-evidence gating, and no-mutation regression.

## Next

Fold WSTA221 into the WSTA108 operator status bundle so the operator surface
shows the concrete egress-allowlist hardening state and can move to the attended
egress allowlist live gate.
