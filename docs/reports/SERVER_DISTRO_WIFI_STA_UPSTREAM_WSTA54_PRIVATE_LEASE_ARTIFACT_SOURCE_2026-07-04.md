# WSTA54 Private Lease Artifact Source

- Date: 2026-07-04
- Scope: host-only private lease artifact generator
- Device action: none
- Flash: none
- Public exposure: none
- Decision: `wsta54-private-lease-artifact-source-pass`

## Summary

WSTA54 implements the host-only rung after WSTA53:

- `workspace/public/src/scripts/server-distro/run_wsta54_private_lease_artifact.py`

The runner consumes a WSTA53 pass result from `workspace/private`, revalidates the
WSTA52/WSTA53 fail-closed contract, and materializes two private run artifacts:

```text
wsta54_private_lease.json
wsta54_redacted_lease_marker.json
```

It does not touch the device and does not authorize live public exposure.  The
private lease carries an opaque lease id only in the private artifact; the result
and marker expose only `lease_id_present=true` and `lease_id_value_redacted=true`.

## Contract

Input requirements:

```text
wsta53 decision == wsta53-persistent-exposure-plan-pass
wsta54_private_artifact_ready == true
future_live_allowed == false
ttl_sec > 0
ttl_sec <= 14400
operator_ack_credentialed_wifi == true
operator_ack_public_exposure == true
native_confirm_token_source == private
public_confirm_token_source == private
public_url_storage == workspace/private-only
```

Output policy:

```text
private_run_dir_required=true
default_state=public-off
state=ARMED_PRIVATE_LEASE
renewal_requires_host_gate=true
boot_autostart_without_valid_private_lease=false
wsta54_live_allowed=false
wsta55_explicit_live_gate_required=true
public_url_value_logged=false
secret_values_logged=0
```

The WSTA54 artifact records WSTA55 live gates as deferred.  WSTA55 must still
recheck bridge health, resident health, WSTA45 preflight, recent scan-green state,
public smoke, TTL expiry, cleanup, post selftest, and WSTA48 redaction.

## CLI Smoke

WSTA53 source input was created under a private smoke run:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/server-distro/run_wsta53_persistent_exposure_plan.py \
  --run-dir workspace/private/runs/server-distro/wsta54-smoke/wsta53 \
  --ttl-sec 1800 \
  --ack-credentialed-wifi \
  --ack-public-exposure \
  --native-confirm-token-source private \
  --public-confirm-token-source private
```

Result: `decision=wsta53-persistent-exposure-plan-pass`.

WSTA54 consumed that private result:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/server-distro/run_wsta54_private_lease_artifact.py \
  --run-dir workspace/private/runs/server-distro/wsta54-smoke/wsta54 \
  --wsta53-result-json workspace/private/runs/server-distro/wsta54-smoke/wsta53/wsta53_result.json
```

Result:

```text
decision=wsta54-private-lease-artifact-pass
gate_decision=ok
state=ARMED_PRIVATE_LEASE
ttl_sec=1800
lease_id_present=true
lease_id_value_redacted=true
wsta55_explicit_live_gate_required=true
```

## Safety

- No device command ran.
- No boot image was built or flashed.
- No native reboot, Wi-Fi association, DHCP, public tunnel, public smoke request,
  userdata format/populate, switch-root, or external service action ran.
- The runner rejects non-private run directories and non-private WSTA53 result paths.
- WSTA54 rejects WSTA53 results with forbidden nested fields or live-safety flag drift.
- No raw public URL, confirm-token value, Wi-Fi credential, network address, routing
  value, or device serial is committed.

## Validation

Focused tests:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta54_private_lease_artifact \
  tests.test_server_distro_wsta53_persistent_exposure_plan \
  tests.test_server_distro_wsta52_persistent_exposure_design
```

Result: `Ran 21 tests ... OK`

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta54_private_lease_artifact.py
git diff --check
```

Result: pass

## Next

WSTA55 can be designed as the first live persistent-lease proof: start a short
lease through the existing WSTA45/WSTA43/WSTA42 path, prove public smoke, force
TTL expiry, prove cleanup, run WSTA48 redacted aggregation, and confirm post-run
`selftest fail=0`.
