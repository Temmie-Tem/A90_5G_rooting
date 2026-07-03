# Server-Distro D4C Userdata Format And Populate

- Date: `2026-07-03`
- Decision: `server-distro-d4c-userdata-format-populate-live-pass`
- Candidate used: `A90 Linux init 0.11.138 (v3381-server-distro-journaled-formatter)`
- Candidate boot image: `workspace/private/inputs/boot_images/boot_linux_v3381_server_distro_journaled_formatter.img`
- Candidate SHA256: `c99be26deb3ca872de444e1f34ab602938a68381fe84c338bf29ead7ed9f1c4f`
- Source tarball: `/mnt/sdext/a90/runtime/a90-d4c-userdata-rootfs.tar`
- Source tarball SHA256: `0875b8bd6e58298f644735e5d7ee12c0286e3057a7744b05064fc34829412603`
- Final device state: V3381 still live for D4D handoff

## Result

D4C passed: `userdata` was formatted as journaled ext4 and populated with the staged Debian appliance
rootfs.

This is the first destructive D4 step. Android `/data` contents were disposed by formatting the
`userdata` partition. The write target was limited to the sysfs `PARTNAME=userdata` target that was
freshly re-derived in the same V3381 session.

D4D `switch-root-to-userdata` has not yet run.

## Preconditions

```text
D4A report=docs/reports/SERVER_DISTRO_D4A_USERDATA_PREFLIGHT_2026-07-03.md
D4B health report=docs/reports/NATIVE_INIT_V3374_SERVER_DISTRO_D4B_CANDIDATE_HEALTH_LIVE_2026-07-03.md
D4C rootfs staged report=docs/reports/SERVER_DISTRO_D4C_ROOTFS_TARBALL_STAGING_LIVE_2026-07-03.md
D4C e2fsprogs toolroot report=docs/reports/SERVER_DISTRO_D4C_E2FSPROGS_TOOLROOT_STAGING_2026-07-03.md
V3381 journaled formatter live report=docs/reports/NATIVE_INIT_V3382_SERVER_DISTRO_D4C_JOURNALED_FORMATTER_LIVE_PASS_2026-07-03.md
rollback_v2321_sha=ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb
fallback_v2237_sha=b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f
fallback_v48_sha=1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042
twrp_recovery_img_sha=b1ef377a52ec8ab43b49a5fcc7a0b27e8efff91bf2d8cccdc565ecadadcc646c
```

## Candidate Flash And Health

V3381 was flashed through `native_init_flash.py` for the destructive D4C session:

```text
local_sha256=c99be26deb3ca872de444e1f34ab602938a68381fe84c338bf29ead7ed9f1c4f
remote_sha256=c99be26deb3ca872de444e1f34ab602938a68381fe84c338bf29ead7ed9f1c4f
boot_readback_sha256=c99be26deb3ca872de444e1f34ab602938a68381fe84c338bf29ead7ed9f1c4f
candidate_version=A90 Linux init 0.11.138 (v3381-server-distro-journaled-formatter)
candidate_status_selftest=pass=12 warn=1 fail=0
candidate_explicit_selftest=pass=12 warn=1 fail=0
candidate_flash_total_sec=67.442
```

## Fresh Same-Session Preflight

The first preflight attempt hit the auto-menu busy gate, then `--hide-on-busy` retried successfully.
These values were used for the format command in the same candidate boot:

```text
target.source=partname-scan
target.devname=sda33
target.sysname=sda33
target.dev=259:17
target.sectors=231577432
target.size_bytes=118567645184
target.ro=0
target.mounted=0
target.node=/dev/block/a90-userdata
target.node_exists=0
target.byname_exists=0
target.byname_matches=0
preflight=ok format_allowed=0 node_materialized=0
```

## Rootfs Tarball Gate

The staged rootfs tarball was rechecked on-device before formatting:

```text
0875b8bd6e58298f644735e5d7ee12c0286e3057a7744b05064fc34829412603  /mnt/sdext/a90/runtime/a90-d4c-userdata-rootfs.tar
size_bytes=268349440
```

## Format

The destructive format command used the fresh preflight identity:

```text
userdata-appliance-format SERVER-DISTRO-D4-USERDATA-APPLIANCE sda33 259:17 231577432
```

Device output proved the same target and journaled ext4 result:

```text
format-ready-check target.devname=sda33 target.dev=259:17 target.sectors=231577432 target.mounted=0
mke2fs_sha=92721c9a402ba8015ec6321acffaac187ce32fd2772a54690b46dfe94b8f6589 expected_sha_match=1
dumpe2fs_sha=6e22ed6668e336a891621de3e18b8915e56545351c20c06bafb6682ac1de9aae expected_sha_match=1
tune2fs_sha=f4bd3a7e56772236ec0dd8f6a4c5fa2b9dfa52cf70d2af0fa1eb50cfeafa34ad expected_sha_match=1
node=created path=/dev/block/a90-userdata dev=259:17
e2fs-toolroot-node=created path=/mnt/sdext/a90/runtime/d4c-format-toolroot/dev/block/a90-userdata dev=259:17
format=begin formatter=e2fsprogs-mkfs.ext4 target=/dev/block/a90-userdata label=A90D4ROOT
Creating journal (131072 blocks): done
format=ext4-magic-ok magic=53ef offset=1080
Filesystem features: has_journal ext_attr resize_inode dir_index filetype extent 64bit flex_bg sparse_super large_file huge_file dir_nlink extra_isize metadata_csum
Total journal size: 512M
format=has-journal-ok feature_compat=0x0000003c has_journal=1
format=done formatter=e2fsprogs-mkfs.ext4 node=/dev/block/a90-userdata label=A90D4ROOT has_journal=1
rc=0 status=ok
```

## Populate

The populate command rechecked the source tarball SHA, mounted the new userdata filesystem, extracted
the rootfs, verified `/sbin/init`, and wrote the appliance marker:

```text
userdata-appliance-populate SERVER-DISTRO-D4-USERDATA-APPLIANCE /mnt/sdext/a90/runtime/a90-d4c-userdata-rootfs.tar 0875b8bd6e58298f644735e5d7ee12c0286e3057a7744b05064fc34829412603
sha=0875b8bd6e58298f644735e5d7ee12c0286e3057a7744b05064fc34829412603 expected_sha_match=1
populate-ready-check target.devname=sda33 target.dev=259:17 target.sectors=231577432 target.mounted=0
node=exists-ok path=/dev/block/a90-userdata dev=259:17
rootfs=mounted root=/mnt/a90-userdata-root node=/dev/block/a90-userdata
populate=begin source=/mnt/sdext/a90/runtime/a90-d4c-userdata-rootfs.tar root=/mnt/a90-userdata-root
appliance_init=ok path=/mnt/a90-userdata-root/sbin/init mode=755
marker=written path=/mnt/a90-userdata-root/etc/a90-appliance-stage value=userdata=appliance-root
populate=done root=/mnt/a90-userdata-root marker=userdata=appliance-root
rc=0 status=ok
```

## Post-D4C Verification

```text
post_status_selftest=pass=12 warn=1 fail=0
post_explicit_selftest=pass=12 warn=1 fail=0
marker_readback=userdata=appliance-root
/mnt/a90-userdata-root/sbin/init mode=0755 size=68448
/dev/block/a90-userdata on /mnt/a90-userdata-root type ext4 (rw,seclabel,relatime,i_version,stripe=128,data=ordered)
```

## Safety Boundary

- `userdata` was intentionally formatted and populated.
- No forbidden partition was written.
- No `switch-root-to-userdata` was run in this D4C unit.
- No public tunnel or external exposure was opened.
- The boot image was not rolled back at the end of this unit because V3381 remains live for the
  immediate D4D handoff proof; v2321 rollback remains available through `native_init_flash.py`.

## Next

Run D4D `switch-root-to-userdata SERVER-DISTRO-D4-USERDATA-APPLIANCE userdata=appliance-root`, then
prove Debian PID1/local USB networking/root filesystem identity. Keep a timed recovery/rollback path
ready for the first handoff proof.
