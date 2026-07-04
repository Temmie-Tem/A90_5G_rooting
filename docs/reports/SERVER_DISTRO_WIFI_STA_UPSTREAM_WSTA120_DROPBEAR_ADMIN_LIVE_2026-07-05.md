# WSTA120 Dropbear Admin Live Pass

Date: 2026-07-05 04:44 KST

## Scope

WSTA120 runs the WSTA119 Dropbear admin model as a bounded private live gate on
the SD-backed Debian work image. It stages `a90admin`, starts Dropbear on the
USB/NCM admin bind, proves non-root SSH identity, proves root SSH rejection, and
cleans key material plus the chroot/loop runtime state.

This unit did not build or flash a boot image, reboot native init, associate
Wi-Fi, run DHCP, open a public tunnel, run public smoke, mutate packet filters,
touch userdata, or switch root.

## Changes

- Added `run_wsta120_dropbear_admin_live_gate.py`.
- Added `tests/test_server_distro_wsta120_dropbear_admin_live_gate.py`.
- The runner is inert by default and requires all explicit live acknowledgements:
  `--execute-dropbear-admin-live`, `--allow-dropbear-admin-live`,
  `--ack-admin-key-material`, and `--ack-root-login-negative-test`.
- The live flow avoids the temporary root-authorized-keys SSH path. It uploads a
  native stage script through `tcpctl_host.py install`, mounts the SD Debian work
  image through the existing WSTA94 path, stages `a90admin`, starts Dropbear with
  `-s -w -j -k`, probes SSH as `a90admin`, probes root SSH rejection, then runs
  cleanup and postcheck.
- The account exact-line checks use fixed-string grep (`grep -Fqx`) so the
  locked shadow entry `a90admin:*:...` is matched literally.
- Cleanup proof is split deliberately:
  - the WSTA120 admin cleanup proves admin key material was removed;
  - the common WSTA94 cleanup/postcheck proves final Dropbear, mount, and loop
    absence.

## Live Proof

Private result:

```text
workspace/private/runs/server-distro/wsta120-dropbear-admin-live-v6-20260705T044147KST/wsta120_result.json
```

Result:

- Decision: `wsta120-dropbear-admin-live-pass`
- Native init: `0.11.153` / `v3397-wsta-execute-gate-screen`
- Baseline selftest: `pass=12 warn=1 fail=0`
- Remote work image restored from clean image before the live stage.
- Admin stage script uploaded to the SD runtime path.
- Admin stage passed:
  - `/root/.ssh/authorized_keys` absent;
  - `a90admin` passwd/group/shadow lines present;
  - admin authorized keys present;
  - Dropbear present;
  - host key generated;
  - Dropbear command included `-s -w -j -k`;
  - Dropbear alive and listening on the USB/NCM admin bind.
- Admin SSH passed:
  - `A90WSTA120_ADMIN_UID=3903`
  - `A90WSTA120_ADMIN_GID=3903`
  - `A90WSTA120_ADMIN_USER=a90admin`
  - `A90WSTA120_ADMIN_GROUP=a90admin`
- Root SSH rejected:
  - root SSH return code: `255`
  - authentication failed with public-key-only root login disabled.
- Admin key cleanup passed for key material:
  - `admin_keys_absent=true`
- Common cleanup/postcheck passed:
  - shadow restored;
  - mount cleanup OK;
  - loop cleanup OK;
  - final Dropbear absent;
  - final mount absent;
  - final loop node absent.
- Final selftest: `pass=12 warn=1 fail=0`

All committed artifacts remain redacted. Private SSH key material and the
generated public key value remain under `workspace/private/`.

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta120_dropbear_admin_live_gate.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta120_dropbear_admin_live_gate
```

Result:

- WSTA120 focused tests: `8 tests OK`
- Full server-distro WSTA regression: `380 tests OK`
- Live WSTA120 gate: `wsta120-dropbear-admin-live-pass`
- Final standalone device selftest after the live run: `pass=12 warn=1 fail=0`
- The WSTA94 runner-error JSON printed during the full run is the expected
  exception-path fixture from that unit test; unittest completed OK.
- `git diff --check`: OK

## Next

WSTA120 proves the bounded Dropbear admin live path, but WSTA108/WSTA90 operator
status still needs to consume this private proof. The next bounded source unit
should fold the WSTA120 pass JSON into operator status, retiring the Dropbear
admin model/runtime blocker without generalizing to the tunnel or HUD service
profiles.
