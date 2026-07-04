# WSTA109 Service Hardening Rootfs Source Pass

Date: 2026-07-05 02:15 KST

## Scope

WSTA109 converts the WSTA90 service-hardening blocking item into source-level rootfs
staging. This is host/source work only. No device action, native reboot, Wi-Fi connect,
DHCP, public tunnel, public smoke, packet-filter mutation, userdata action,
switch-root, or boot flash ran.

## Changes

- Added service identity staging to `prepare_wsta3_sta_rootfs.py`.
  - Adds deterministic non-root service users/groups: `a90www`, `a90tunnel`,
    `a90admin`, and `a90hud`.
  - Keeps `wsta-native-uplink-helper` as an explicit root/native-boundary service.
  - Fails closed if a target account already exists with conflicting UID/GID fields.
- Added `/usr/local/bin/a90-service-launch`.
  - Requires `setpriv`.
  - Uses `setpriv --no-new-privs --reuid <user> --regid <group> --init-groups`.
  - Blocks missing service, unknown service, missing command, and missing `setpriv`.
- Added `/etc/a90-dpublic/service-hardening.json`.
  - Records service user/group/UID/GID, network intent, no-new-privs, and empty
    ambient/bounding capability sets.
- Added service-hardening stage markers to `/etc/a90-server-distro-stage`.
- Updated WSTA90 wording so the previous "users/groups not staged" blocker is now
  represented as source-staged but live-proof pending.

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py \
  workspace/public/src/scripts/server-distro/run_wsta90_service_hardening_manifest.py \
  workspace/public/src/scripts/server-distro/run_wsta108_operator_server_status.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_prepare_wsta3_sta_rootfs \
  tests.test_server_distro_wsta90_service_hardening_manifest \
  tests.test_server_distro_wsta108_operator_server_status

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  $(find workspace/public/src/scripts/server-distro -maxdepth 1 -type f \
    \( -name 'run_wsta*.py' -o -name 'prepare_wsta3_sta_rootfs.py' \) | sort -V)

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_prepare_wsta3_sta_rootfs \
  $(find tests -maxdepth 1 -type f -name 'test_server_distro_wsta*.py' \
    -printf '%f\n' | sort -V | sed 's/^/tests./; s/\.py$//' | tr '\n' ' ')
```

Result:

- Focused WSTA90/108 + WSTA3 rootfs regression passed: `43 tests OK`.
- Focused WSTA/rootfs public workflow regression passed: `79 tests OK`.
- Full server-distro WSTA regression passed: `354 tests OK`.

Notes:

- A default private `prepare_wsta3_sta_rootfs.py --immediate-snapshot-only --no-tarball
  --no-sta-tool-install --no-packet-filter-tool-install` attempt stopped before service
  staging on the existing STA-tool precondition. That run is not used as WSTA109 pass
  evidence; it confirms only that the older WSTA3 fail-closed precondition still fires
  before later rootfs staging when tools are missing.

## Next

The next bounded unit should prove the staged launcher against an applied private
rootfs: run `a90-service-launch dpublic-smoke-httpd ...` under chroot with `setpriv`,
verify UID/GID/no-new-privs from inside the launched process, and keep public exposure
off.
