# WSTA45 Appliance Operator Wrapper Source

- Date: 2026-07-04
- Scope: host-only source/productization update
- Device action: none
- Flash: none
- Public exposure: none
- Decision: `wsta45-appliance-operator-wrapper-source-pass`

## What Changed

WSTA45 turns the WSTA44 default-off profile into an operator-facing host entrypoint
without weakening the WSTA43 live gates.

Added:

- `workspace/public/src/scripts/server-distro/run_wsta45_appliance_operator.py`

The wrapper has two modes:

- `preflight` (default): host-only menu/profile contract validation, no device action.
- `publish`: delegates to WSTA43 only when every operator gate is explicit:
  `--use-native-uplink-profile`, `--allow-operator-live`, `--allow-native-reboot`,
  `--allow-public-live`, `--ack-credentialed-wifi`, `--ack-public-exposure`, native
  confirm token, and public confirm token.

The wrapper blocks WSTA43 passthrough from supplying or overriding gate flags.  Gate
flags must be supplied at the WSTA45 layer, then WSTA45 passes WSTA43 a profile-enabled
nested configuration.

## Profile Consumption

WSTA42 now has an optional `--use-native-uplink-profile` path:

- stages `/usr/local/bin/a90-dpublic-native-uplink-profile` into the Debian chroot;
- creates the private `/etc/a90-dpublic/native-uplink-enable` gate during confirmed
  autoconnect only;
- calls `a90-dpublic-native-uplink-profile autoconnect-confirmed` instead of the direct
  native uplink client;
- requires both the native client pass markers and the profile markers
  (`native-uplink-profile-autoconnect-pass`, public default off, secret hygiene);
- restores/removes the staged profile helper and enable file during cleanup.

WSTA43 now forwards `--use-native-uplink-profile` into WSTA42.  WSTA45 always enables
that nested profile path in publish mode.

The Debian-side profile now also records:

- `native_uplink_profile_public_runner=wsta43`
- `native_uplink_profile_operator_wrapper=wsta45`

## Safety

- Default WSTA45 execution does not touch the device.
- No boot image was built or flashed.
- No Wi-Fi association, DHCP, public tunnel, public URL fetch, or external service
  exposure ran in this unit.
- Confirm tokens and public URLs remain redacted; the local preflight output records
  only boolean gate state and source-contract markers.

## Validation

Focused tests:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_dpublic_smoke_helpers \
  tests.test_server_distro_wsta42_native_uplink_dpublic_tunnel \
  tests.test_server_distro_wsta43_orchestrated_native_uplink_dpublic \
  tests.test_server_distro_wsta45_appliance_operator
```

Result: `Ran 32 tests ... OK`

Syntax:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta42_native_uplink_dpublic_tunnel.py \
  workspace/public/src/scripts/server-distro/run_wsta43_orchestrated_native_uplink_dpublic.py \
  workspace/public/src/scripts/server-distro/run_wsta45_appliance_operator.py
```

Result: pass

```text
sh -n workspace/public/src/scripts/server-distro/a90_dpublic_native_uplink_profile.sh
```

Result: pass

Default CLI preflight:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/server-distro/run_wsta45_appliance_operator.py \
  --run-dir workspace/private/runs/server-distro/wsta45-source-preflight-check \
  --print-full-json
```

Result: `decision=wsta45-appliance-operator-preflight-pass`, `profile_contract_ok=true`,
`native_reboot=false`, `wifi_connect=false`, `public_tunnel=false`.

```text
git diff --check
```

Result: pass

## Next

WSTA46 can be the explicit WSTA45 publish live gate: run the new wrapper in `publish`
mode with the same native reboot, credentialed Wi-Fi, public exposure, and confirm-token
acks that WSTA43 required.  That should be a deliberate live/public action, not a
default continuation.
