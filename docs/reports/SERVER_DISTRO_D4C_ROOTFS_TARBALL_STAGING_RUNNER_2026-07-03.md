# Server-Distro D4C Rootfs Tarball Staging Runner

- Date: `2026-07-03`
- Decision: `server-distro-d4c-rootfs-tarball-staging-runner-static`
- Device action: none
- Flash action: none
- Userdata action: none
- Runner: `workspace/public/src/scripts/server-distro/prepare_d4c_userdata_rootfs_tarball.py`
- Test: `tests/test_prepare_d4c_userdata_rootfs_tarball.py`

## Purpose

This runner prepares the rootfs input for the destructive D4C `userdata` appliance step without entering
the destructive step itself. It converts the clean D3 sysvinit rootfs directory into a deterministic,
SHA-pinned tarball, uploads that tarball to the native-init SD runtime path, and verifies the remote SHA.

The default target is:

```text
local rootfs=workspace/private/builds/server-distro/d3-sysvinit-usrmerge-20260703T101657Z-rootfs
remote tarball=/mnt/sdext/a90/runtime/a90-d4c-userdata-rootfs.tar
```

## Guardrails

- Requires resident v2321 before and after staging.
- Requires `selftest fail=0` before and after staging.
- Creates the tarball under `workspace/private/runs/server-distro/...`; private run artifacts stay out of
  commits.
- Uses `tar --format=gnu --sort=name --numeric-owner --owner=0 --group=0 --mtime=@0` so the future
  `userdata` extraction installs root-owned files even though the host rootfs staging tree is owned by the
  host user.
- Verifies the rootfs has `/sbin/init`, `/etc/debian_version`, `/etc/inittab`, and
  `/etc/a90-server-distro-stage`.
- Verifies the tarball contains the required init, Debian version, inittab, and stage-marker entries.
- Uploads only to `/mnt/sdext/a90/runtime/a90-d4c-userdata-rootfs.tar`.
- Verifies the remote SHA after upload.
- Does not flash.
- Does not call `userdata-appliance-format`.
- Does not call `switch-root-to-userdata`.
- Does not run `mkfs` or `mke2fs`.
- Does not mount, format, populate, or otherwise touch `userdata`.

## Validation

Static validation passed:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/prepare_d4c_userdata_rootfs_tarball.py \
  tests/test_prepare_d4c_userdata_rootfs_tarball.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_prepare_d4c_userdata_rootfs_tarball
```

Result:

```text
Ran 3 tests
OK
```

## Next Gate

The next bounded live prep is still non-destructive:

1. Run `prepare_d4c_userdata_rootfs_tarball.py` on clean resident v2321.
2. Confirm the resulting run JSON pins the local tarball SHA, remote tarball path, remote SHA, final v2321
   version, and final `selftest fail=0`.
3. Flash exact V3375 through `native_init_flash.py`.
4. Run candidate health, read-only `userdata-appliance-preflight`, and
   `userdata-appliance-formatter-probe` only.
5. Roll back to v2321 unless destructive D4C format starts immediately under the D4 runbook.

D4C format/populate remains disallowed until both the SD-staged rootfs tarball SHA and V3375 formatter
probe are live-proven.
