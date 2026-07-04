# WSTA110 Service Launcher Chroot Live Proof

Date: 2026-07-05 02:35 KST

## Scope

WSTA110 proves the WSTA109 service-hardening assets inside the SD-backed Debian
chroot. This was a live device run, but it did not build or flash a boot image,
reboot native init, associate Wi-Fi, run DHCP, open a public tunnel, run public
smoke, mutate packet filters, touch userdata, or switch root.

## Source Changes

- Added `run_wsta110_service_launcher_chroot_proof.py`.
  - Default mode is fail-closed and device-inert.
  - Explicit live execution requires both `--execute-service-launcher-chroot-live`
    and `--allow-service-launcher-live`.
  - Reuses the existing SD image, clean/work image restore, D2 chroot/dropbear,
    and WSTA94 cleanup patterns.
  - Stages WSTA109 service users, `/usr/local/bin/a90-service-launch`,
    `/etc/a90-dpublic/service-hardening.json`, and stage markers into the chroot.
  - Runs `a90-service-launch dpublic-smoke-httpd ...` and verifies UID/GID,
    fail-closed launcher branches, public default-off, and `NoNewPrivs=1`.
- Hardened WSTA94 native stale cleanup.
  - Added a delayed loop detach recheck so transient `/dev/loop0` detach is not
    overclassified as a stale-loop blocker.
  - Kept the cleanup script below the cmdv1x argument-size failure observed during
    WSTA110 bring-up.

## Live Evidence

Command:

```text
python3 workspace/public/src/scripts/server-distro/run_wsta110_service_launcher_chroot_proof.py \
  --run-id wsta110-service-launcher-live-20260704T173234Z \
  --execute-service-launcher-chroot-live \
  --allow-service-launcher-live
```

Private result:

```text
workspace/private/runs/server-distro/wsta110-service-launcher-live-20260704T173234Z/wsta110_result.json
```

Result:

- Decision: `wsta110-service-launcher-chroot-live-pass`
- Debian chroot version observed: `12.14`
- Remote clean image SHA: `210fc1f92d4eb8bf291fb5b362154a29ca2b579a22a0a41cb1aaa89b5b6cb0dc`
- Remote work image restored to the same SHA before staging.
- Final selftest: `pass=12 warn=1 fail=0`

Launcher proof markers:

```text
A90WSTA110_PUBLIC_ENABLE_ABSENT=1
A90WSTA110_LAUNCHER_PRESENT=1
A90WSTA110_POLICY_PRESENT=1
A90WSTA110_SETPRIV_PRESENT=1
A90WSTA110_UNKNOWN_BLOCKED=1
A90WSTA110_COMMAND_REQUIRED_BLOCKED=1
a90_service_launcher_decision=exec
a90_service_launcher_service=dpublic-smoke-httpd
a90_service_launcher_user=a90www
a90_service_launcher_network_intent=bind-loopback-127.0.0.1:8080-only
a90_service_launcher_no_new_privs=1
child_uid=3901
child_gid=3901
child_user=a90www
child_group=a90www
child_no_new_privs=1
child_cap_eff=0000000000000000
A90WSTA110_PROC_UNMOUNTED=1
A90WSTA110_PROOF_DONE
```

Cleanup evidence:

- Service-probe `/proc` cleanup reported `A90WSTA110 proc_mount_absent=1`.
- Postcheck reported mount absent, loop node absent, and dropbear absent.
- A separate post-live diagnostic showed no `/dev/loop0` attachment; `pidof`
  exit code `1` for dropbear and smoke means both processes were absent.

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta94_packet_filter_live_gate.py \
  workspace/public/src/scripts/server-distro/run_wsta110_service_launcher_chroot_proof.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta94_packet_filter_live_gate \
  tests.test_server_distro_wsta110_service_launcher_chroot_proof

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_prepare_wsta3_sta_rootfs \
  $(find tests -maxdepth 1 -type f -name 'test_server_distro_wsta*.py' \
    -printf '%f\n' | sort -V | sed 's/^/tests./; s/\.py$//' | tr '\n' ' ')
```

Result:

- `24 tests OK`
- WSTA110 focused tests: `10 tests OK`
- Full server-distro WSTA regression: `365 tests OK`

## Notes

Bring-up caught three useful issues before the pass:

- A stale `/dev/loop0` attachment from an older WSTA image required delayed cleanup
  classification.
- The first delayed cleanup patch exceeded the cmdv1x argument-size envelope and was
  shortened.
- The chroot did not have `/proc` mounted, so `NoNewPrivs` was not observable until
  WSTA110 mounted `/proc` only for the proof and unmounted it before cleanup.

## Next

Fold WSTA110 into the operator-facing WSTA108/WSTA90 status so the hardening HUD no
longer reports the smoke-service launcher as unproven, then extend the same live proof
shape to the remaining service profiles.
