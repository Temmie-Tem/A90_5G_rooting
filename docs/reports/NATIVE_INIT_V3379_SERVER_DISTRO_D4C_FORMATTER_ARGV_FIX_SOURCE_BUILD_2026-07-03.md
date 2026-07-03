# Native Init V3379 Server-Distro D4C Formatter Argv Fix Source Build

- Cycle: `V3379`
- Decision: `v3379-server-distro-d4c-userdata-formatter-argv-fix-source-build`
- Init: `A90 Linux init 0.11.137 (v3379-server-distro-userdata-formatter-argv-fix)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3379_server_distro_userdata_formatter_argv_fix.img`
- Boot SHA256: `a58c07bca01c74ba97653a7cd3d3681788674fa8a6eb912a4fe64a84fb42112e`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3368_hot_reload_autohud.img`

## Change

- Keeps the device-supported BusyBox syntax: `mke2fs -F -L A90D4PROBE <probe-image> <KBYTES>`.
- Fixes the V3377 live failure by reserving a final NULL terminator in the formatter-probe argv array after `<probe-image>` and `<KBYTES>`.
- Keeps the probe non-destructive: it writes only an approved SD-runtime regular file, checks the ext superblock magic, unlinks the probe file, and reports `userdata_touched=0`.
- Keeps the D4B command surface: `userdata-appliance-preflight`, `userdata-appliance-format`, `userdata-appliance-populate`, and `switch-root-to-userdata`.
- All D4 commands require `SERVER-DISTRO-D4-USERDATA-APPLIANCE`; mutating commands re-derive sysfs `PARTNAME=userdata` and compare host-pinned `devname`, `dev`, and `sectors` before touching storage.
- The surface does not rely on `/dev/block/by-name/userdata`; it materializes `/dev/block/a90-userdata` from verified `MAJOR:MINOR` only after target identity passes.
- Fixes the destructive format path to remove unsupported BusyBox `-t ext4`: `busybox mke2fs -F -L A90D4ROOT /dev/block/a90-userdata`.
- Populate accepts only SHA-pinned source tarballs under `/mnt/sdext/a90/runtime/`, mounts userdata at `/mnt/a90-userdata-root`, extracts the rootfs, verifies `/sbin/init`, and writes `userdata=appliance-root`.
- `switch-root-to-userdata` verifies the appliance marker, prepares/moves `/proc`, `/sys`, and `/dev`, then execs BusyBox `switch_root` so userdata Debian init becomes PID1.
- This is a D4C entry-prep source-build/static gate. D4C format/populate still requires live formatter-probe pass, rootfs tarball staging, fresh same-session preflight, and rollback readiness.

## Static Validation Contract

- Boot image strings must contain the V3379 identity, all five D4 command names, `SERVER-DISTRO-D4-USERDATA-APPLIANCE`, `A90D4`, `/sys/class/block`, `PARTNAME=`, `userdata`, `/dev/block/a90-userdata`, `/mnt/a90-userdata-root`, and the formatter-probe/format/populate/switch markers.
- Source contract must show command table registration with `CMD_DANGEROUS` on mutating D4 commands and `CMD_DANGEROUS | CMD_NO_DONE` on `switch-root-to-userdata`.
- Live contract before destructive D4C: flash only through `native_init_flash.py`, prove candidate health, run device-side `userdata-appliance-preflight` plus `userdata-appliance-formatter-probe`, and roll back to v2321 unless the destructive D4C unit starts immediately under the same controlled plan.

## Validation

Static tests passed:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_native_init_boot_v3379_server_distro_userdata_formatter_argv_fix.py \
  tests/test_build_native_init_boot_v3379_server_distro_userdata_formatter_argv_fix.py \
  tests/test_build_native_init_boot_v3377_server_distro_userdata_formatter_fix.py \
  tests/test_build_native_init_boot_v3375_server_distro_userdata_formatter_probe.py \
  tests/test_build_native_init_boot_v3373_server_distro_userdata_appliance.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_build_native_init_boot_v3379_server_distro_userdata_formatter_argv_fix \
  tests.test_build_native_init_boot_v3377_server_distro_userdata_formatter_fix \
  tests.test_build_native_init_boot_v3375_server_distro_userdata_formatter_probe \
  tests.test_build_native_init_boot_v3373_server_distro_userdata_appliance
```

Result:

```text
Ran 16 tests
OK
```

Build passed:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_native_init_boot_v3379_server_distro_userdata_formatter_argv_fix.py
```

Post-build checks:

```text
init_sha256=c6b8e498ac6fde11b0ac61ef34bb0a995930dd816e0a6dd5af7207b5442b547e
boot_sha256=a58c07bca01c74ba97653a7cd3d3681788674fa8a6eb912a4fe64a84fb42112e
init_file=ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped
boot_file=Android bootimg
```

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `server-distro-d4c-formatter-argv-fix`.
