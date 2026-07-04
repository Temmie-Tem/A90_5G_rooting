# WSTA123 Operator Status Cloudflared Model Source Pass

Date: 2026-07-05 05:05 KST

## Scope

WSTA123 folds the WSTA122 `cloudflared-quick-tunnel` source model into the
WSTA108 operator server status bundle. This is a host-only status overlay. It
does not start cloudflared, open a public tunnel, treat the model as a runtime
proof, or weaken any explicit live gate.

This unit did not run a device action, build or flash a boot image, reboot
native init, associate Wi-Fi, run DHCP, open a public tunnel, run public smoke,
mutate packet filters, touch userdata, or switch root.

## Changes

- Added optional WSTA108 input `--wsta122-cloudflared-model-json`.
- Imported and revalidated the WSTA122 model with
  `run_wsta122_cloudflared_service_model.validate_model()`.
- Added compact status field `hardening.cloudflared_model`.
- Fail closed if the supplied WSTA122 proof is non-pass, missing checks, or
  fails recomputed model validation.
- Added markdown lines for cloudflared model presence, target user, default-off
  state, and launcher hardening requirement.
- Kept runtime gaps explicit: `cloudflared_live_proven=false`, and
  `cloudflared-quick-tunnel` remains in remaining launcher/syscall proof
  profiles.

## Source Proof

Private output:

```text
workspace/private/runs/server-distro/wsta123-operator-status-cloudflared-model-20260705T050452KST/wsta108_operator_server_status.json
```

Result:

- Decision: `wsta108-operator-server-status-source-pass`
- Server state: `SERVER_PROFILE_READY_DEFAULT_OFF`
- Public state: `PUBLIC_OFF`
- Cloudflared model supplied: true
- Cloudflared model defined: true
- Cloudflared model state: `CLOUDFLARED_SERVICE_MODEL_SOURCE_DEFINED`
- Cloudflared target user: `a90tunnel`, UID/GID `3902/3902`
- Cloudflared default public off: true
- Cloudflared launcher hardening required: true
- Cloudflared live proven: false
- Remaining launcher profiles include `cloudflared-quick-tunnel`
- Remaining syscall profiles include `cloudflared-quick-tunnel`
- Public URL value logged: false
- Secret values logged: `0`

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta108_operator_server_status.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta108_operator_server_status

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  discover -s tests -p 'test_server_distro_wsta*.py'
```

Result:

- WSTA108 focused tests: `25 tests OK`
- Full server-distro WSTA regression: `394 tests OK`
- The WSTA94 runner-error JSON printed during the full run is the expected
  exception-path fixture from that unit test; unittest completed OK.
- `git diff --check`: OK

## Next

WSTA123 retires only the cloudflared source-model gap. The next bounded unit
should prove the cloudflared runtime profile privately through
`a90-service-launch`: process UID/GID `3902/3902`, no-new-privs, zero effective
capabilities, outbound-only behavior, private URL artifact handling, cleanup,
and a cloudflared syscall trace before any always-on/seccomp claim.
