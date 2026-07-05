# WSTA205 WSTA204 Live Transaction Bundle

Date: 2026-07-05 18:18 KST

## Verdict

WSTA205 adds a host-only single transaction bundle for the future attended
WSTA200/WSTA198 live path.  It consumes the private WSTA204 live-result
verifier, re-runs WSTA204 from the same WSTA203 audit, compares a
token-independent stable verifier view, and emits a private executable script
that will later run the current handoff and immediately verify the result.

Result: PASS.

Current bundle state:

```text
LIVE_TRANSACTION_BUNDLE_READY_TOKEN_REQUIRED_DEFAULT_OFF
```

The transaction bundle is structurally ready, but immediate live execution
remains false because the private `A90_PRIVATE_WSTA161_LOAD_TOKEN` environment
variable was not present in this host-only proof.

## Source Changes

- Added
  `workspace/public/src/scripts/server-distro/run_wsta205_wsta204_live_transaction_bundle.py`.
- Added focused tests in
  `tests/test_server_distro_wsta205_wsta204_live_transaction_bundle.py`.

## Proof

Run:

```text
workspace/private/runs/server-distro/wsta205-wsta204-live-transaction-bundle-20260705T181808KST/
```

Decision:

```text
wsta205-wsta204-live-transaction-bundle-source-pass
```

Input:

```text
workspace/private/runs/server-distro/wsta204-wsta198-live-result-verifier-20260705T181121KST/wsta204_wsta198_live_result_verifier.json
```

Generated private artifacts:

```text
workspace/private/runs/server-distro/wsta205-wsta204-live-transaction-bundle-20260705T181808KST/wsta205_result.json
workspace/private/runs/server-distro/wsta205-wsta204-live-transaction-bundle-20260705T181808KST/wsta205_wsta204_live_transaction_bundle.json
workspace/private/runs/server-distro/wsta205-wsta204-live-transaction-bundle-20260705T181808KST/wsta205_run_wsta200_and_verify.sh
workspace/private/runs/server-distro/wsta205-wsta204-live-transaction-bundle-20260705T181808KST/wsta205_wsta204_live_transaction_bundle.md
workspace/private/runs/server-distro/wsta205-wsta204-live-transaction-bundle-20260705T181808KST/wsta204-recheck/wsta204_result.json
```

Key checks:

```text
verifier_valid=true
wsta204_recheck_valid=true
verifier_stable_view_match=true
live_transaction_bundle_valid=true
ready_for_transaction_execution=true
ready_for_immediate_live_execute=false
private_token_env_present=false
private_token_matches_wsta161=false
```

## Transaction Contract

The generated private script will:

1. require `A90_PRIVATE_WSTA161_LOAD_TOKEN`,
2. re-run WSTA204 source preflight and require token-ready state,
3. execute the existing private WSTA200 handoff wrapper,
4. extract the resulting private WSTA198 `wsta198_result.json`,
5. run WSTA204 verify mode on that result, and
6. require `wsta204-wsta198-live-result-verify-pass`.

WSTA205 only emits the script.  It does not run the script.

## Safety Boundary

This proof did not flash, reboot, contact the device, connect Wi-Fi, run DHCP,
open a public tunnel, mutate packet filters, write userdata, switch root,
execute the generated transaction script, execute the WSTA200 handoff shell,
run WSTA198 live, supply the WSTA161 token to the device, run native health,
load a seccomp filter, or enforce seccomp.

## Validation

- `py_compile`:
  - `run_wsta205_wsta204_live_transaction_bundle.py`
  - `test_server_distro_wsta205_wsta204_live_transaction_bundle.py`
- Focused WSTA205 tests: `7 tests OK`.
- WSTA205 proof run: pass.
- Full server-distro regression: `762 tests OK`.

## Next

Export the private token deliberately, re-run WSTA202/WSTA203/WSTA204/WSTA205
to token-ready default-off states, then run the generated private WSTA205
transaction script under supervision.
