# WSTA226 Cloudflared Egress Execute Gate

Date: 2026-07-05

## Verdict

PASS.  WSTA226 adds the attended execute-gate wrapper for the cloudflared egress
allowlist path.

This is source support only.  No live packet-filter mutation was run.

## What Changed

New runner:

```text
workspace/public/src/scripts/server-distro/run_wsta226_cloudflared_egress_allowlist_execute_gate.py
```

Default mode is host-only.  The runner consumes the WSTA223 live-gate plan,
validates that the plan is still complete, and delegates to WSTA88 only to build
the default-off operator execute gate.

Optional live delegation requires:

```text
--execute-live-egress-allowlist
--allow-operator-live
--allow-native-reboot
--allow-public-live
--ack-packet-filter-mutation
--force-packet-filter-restore-proof
--force-cloudflared-egress-allowlist-proof
--force-control-plane-proof
--force-public-off-proof
--force-ttl-expiry-proof
--force-manual-stop-proof
--route-artifact-json <private route artifact>
--native-confirm-token <private token>
--public-confirm-token <private token>
```

The private route artifact schema is:

```text
schema=a90-wsta226-cloudflared-egress-route-v1
state=CLOUDFLARED_EGRESS_ROUTE_DERIVED_PRIVATE
dns4=[private values]
tls4=[private values]
route_values_private=true
route_values_logged=false
```

Public output records only DNS/TLS counts and redaction markers.

## Delegation Shape

WSTA226 does not implement a new live primitive.  It delegates to the already
gated WSTA88 -> WSTA80 -> WSTA58 -> WSTA55 -> WSTA45 -> WSTA43 -> WSTA42 path.
When live execution is enabled, WSTA226 adds the WSTA225 egress flags and the
private route values to the WSTA88 invocation.  Without live execution, it only
prepares the WSTA88 default-off gate.

## Safety

WSTA226 changed source and tests only.  It did not perform any device action,
boot flash, native reboot, Wi-Fi connect/association, DHCP, ping, public tunnel,
public smoke, packet-filter mutation, rootfs mutation, userdata write, LSM
profile load, or switch-root.

The new path remains default-off and explicit-gated.  Route values, public URL
values, tunnel credentials, Wi-Fi credentials, and tokens are not written to
public output.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta226_cloudflared_egress_allowlist_execute_gate.py \
  tests/test_server_distro_wsta226_cloudflared_egress_allowlist_execute_gate.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta226_cloudflared_egress_allowlist_execute_gate

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta223_cloudflared_egress_allowlist_live_gate_plan \
  tests.test_server_distro_wsta226_cloudflared_egress_allowlist_execute_gate \
  tests.test_server_distro_wsta88_persistent_operator_workflow

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest discover -s tests -p 'test_server_distro*.py'
```

Results:

```text
WSTA226 focused tests: 6 tests OK
WSTA223/WSTA226/WSTA88 focused tests: 19 tests OK
server-distro regression: 835 tests OK
```

## Next

The source path is ready for an attended live attempt only after a private route
artifact is produced from live device/runtime state.  The live run must remain
operator-supervised, keep route values private, and verify restore/public-off
before returning.
