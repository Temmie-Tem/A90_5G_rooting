# Server Distro Endgame - D0 Device-Live Read-Only Inventory

- Date: 2026-07-03 KST / 2026-07-02 UTC
- Unit: D0 track A, device-live read-only inventory.
- Design: `docs/plans/NATIVE_INIT_SERVER_DISTRO_ENDGAME_DESIGN_2026-06-30.md`
- Charter: `docs/plans/NATIVE_INIT_SERVER_DISTRO_D0_INVENTORY_CHARTER_2026-07-01.md`
- Decision: `server-distro-d0-device-live-read-only-inventory-pass`
- Device action: read-only serial observations only. No flash, no mount change, no format, no `/data`
  mount, no boot/userdata write.
- End state: resident stayed `v2321-usb-clean-identity-rodata`; final standalone
  `selftest pass=11 warn=1 fail=0`.

## Scope

D0's host-staging half was already complete in
`docs/reports/SERVER_DISTRO_D0_HOST_STAGING_2026-07-01.md`. This unit completed the remaining
device-live half: sizing the SD staging target, identifying `userdata` without touching it,
checking native-init writable mounts, and checking the on-device tools D1 can rely on.

Raw command output is private only:

`workspace/private/runs/server-distro/d0-device-live-20260702T200338Z/`

The committed report contains only the redacted classification needed for D1 planning.

## Implementation

Added a reusable host-side collector:

`workspace/public/src/scripts/server-distro/collect_d0_device_inventory.py`

The collector runs the pre-vetted read-only command set from the D0 charter through the native-init
serial bridge and writes:

- `inventory_private.json`: raw command output and health transcripts, private only.
- `inventory_public_summary.json`: redacted classification summary, private run dir.

It refuses to proceed unless the resident device is v2321 and baseline selftest is `fail=0`, then
checks final v2321/selftest again after the observations.

## Inventory Result

| Item | Result | D1/D-public implication |
| --- | --- | --- |
| SD mount | `/mnt/sdext`, ext4, rw | D1 rootfs image should land on SD, not userdata. |
| SD capacity/free | `61,408,048` KiB total, `52,881,516` KiB free | The staged 2 GiB Debian image fits with large margin. |
| `userdata` identity | `/dev/block/sda33`, `PARTNAME=userdata`, `110.42 GiB` | Identified only. D0 did not mount or format it. |
| writable native-init mounts | `/`, `/tmp`, `/cache`, `/mnt/sdext`, `/config` | `/mnt/sdext` is the preferred D1 rootfs image mount/storage target. |
| ext4 support | present (`CONFIG_EXT4_FS=y`, `/proc/filesystems` has ext4) | SD ext4 loop image is feasible. |
| loop support | kernel/proc-devices present (`CONFIG_BLK_DEV_LOOP=y`, loop block major present) | `/dev/loop*` nodes are absent; D1 must materialize runtime loop nodes or prove `mount -o loop` handles them. |
| busybox applets | `losetup`, `mount`, `chroot`, `switch_root`, `tar`, `unshare` present; `mkfs.ext4` absent | D1 has required chroot/mount tools. D0/D1 do not need mkfs. |
| TUN | `CONFIG_TUN=y`, `/dev/net/tun` absent | D-public must materialize `/dev/net/tun` before tunnel-client use. Cloudflared HTTP tunnel may not need TUN; WG does. |
| namespaces/seccomp | `CONFIG_NAMESPACES=y`, `CONFIG_NET_NS=y`, `CONFIG_UTS_NS=y`, `CONFIG_SECCOMP=y`, `CONFIG_SECCOMP_FILTER=y`; `CONFIG_VETH=n`, `CONFIG_OVERLAY_FS=n` | seccomp is available; network namespace is available; veth/overlay are not available for later containment designs. |
| RAM/CPU | `5375.9 MiB`, `8` CPUs | Enough for the Debian chroot MVP. |

Host-staged artifact check from the collector:

- Debian rootfs image:
  `workspace/private/builds/server-distro/debian-bookworm-arm64-20260701-024412.img`,
  `2,147,483,648` bytes,
  SHA-256 `210fc1f92d4eb8bf291fb5b362154a29ca2b579a22a0a41cb1aaa89b5b6cb0dc`.
- Rootfs tree marker present; root password locked in the stage marker and root shadow entry.
- `cloudflared-linux-arm64` staged, `36,980,327` bytes,
  SHA-256 `59816ce9b16db71f5bc2a86d59b3632a96c8c3ee934bde2bc8641ee83a6070eb`.

## Safety Result

- No boot image was built or flashed.
- No rollback flash was needed because resident v2321 was maintained throughout.
- No partition was written.
- `userdata` was identified through `/sys/class/block/*/uevent` (`PARTNAME=userdata`) because
  `/dev/block/by-name` is absent in this native-init environment.
- Final standalone health:
  - `version`: `v2321-usb-clean-identity-rodata`
  - `selftest`: `pass=11 warn=1 fail=0`

## Validation

Host validation:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/collect_d0_device_inventory.py tests/test_server_distro_d0_inventory.py`
- `PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_server_distro_d0_inventory`
  - `Ran 2 tests ... OK`
- `git diff --check`

Device validation:

- Preflight bridge was reachable.
- Baseline `version/status/selftest` passed before inventory.
- The collector ran the D0 read-only command set and wrote private evidence.
- Collector final v2321/selftest checks passed.
- A separate post-run `a90ctl.py selftest` also passed with `fail=0`.

## D1 Readiness

D1 is unblocked as a non-destructive SD-backed chroot MVP:

1. Copy or stage the already-built 2 GiB Debian ext4 image to `/mnt/sdext`.
2. Materialize runtime loop nodes if `losetup`/`mount -o loop` cannot proceed with the current
   `/dev` state.
3. Mount the image read/write in the D1 unit, `chroot`, and run a static/known binary first.
4. Keep `userdata` untouched; D4 is the only later unit that may reformat `userdata`, and it needs a
   separate explicit gate.
