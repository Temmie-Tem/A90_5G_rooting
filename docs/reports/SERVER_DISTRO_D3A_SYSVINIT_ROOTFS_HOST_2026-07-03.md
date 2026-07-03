# Server Distro Endgame - D3A Sysvinit Rootfs Host Prep

- Date: 2026-07-03 KST / 2026-07-03 UTC
- Unit: D3A host-only sysvinit rootfs/image preparation.
- Design: `docs/plans/NATIVE_INIT_SERVER_DISTRO_ENDGAME_DESIGN_2026-06-30.md`
- Charter: `GOAL.md` D3 design decision, operator-resolved 2026-07-03.
- Decision: `server-distro-d3a-sysvinit-rootfs-host-pass`
- Device action: none. No flash, no hot-reload, no mount on device, no `switch_root`, no format,
  no `userdata` touch.

## Scope

D3A implements the host-only half of the operator-resolved D3 plan:

- init system: `sysvinit-core`
- observation path: dropbear started by sysvinit's firstboot path
- recovery path: mandatory bounded unconditional auto-reboot scheduled as firstboot's first action
- marker: Debian-side D3 marker containing Debian version and PID1 identity fields

Private artifacts are under `workspace/private/builds/server-distro/` and are not committed.

## Implementation

Added:

`workspace/public/src/scripts/server-distro/prepare_d3_sysvinit_rootfs.py`

The script runs under `fakeroot`, so it can build an ext4 image with root ownership and device-node
metadata without requiring sudo. It:

1. Creates a private arm64 apt state using the Debian archive keyring already present in the base
   rootfs.
2. Downloads the minimal sysv package set.
3. Copies the D1/D2 base rootfs under fakeroot.
4. Extracts the sysv packages into the D3 rootfs.
5. Installs an explicit `/etc/inittab` with `si::sysinit:/etc/a90-d3-firstboot`.
6. Installs `/etc/a90-d3-firstboot`, which schedules the mandatory auto-reboot before networking,
   reasserts the USB-local NCM interface, writes `A90D3_MARKER`, generates a temporary dropbear host
   key if needed, and starts key-only dropbear only if the later live runner has staged
   `root/.ssh/authorized_keys`.
7. Builds a 2 GiB ext4 image labeled `A90D3ROOT`.

## Private Artifact

- Private summary:
  `workspace/private/builds/server-distro/d3-sysvinit-20260703T080236Z-summary.json`
- D3 rootfs:
  `workspace/private/builds/server-distro/d3-sysvinit-20260703T080236Z-rootfs`
- D3 image:
  `workspace/private/builds/server-distro/d3-sysvinit-20260703T080236Z.img`
- D3 image SHA-256:
  `2ee61172116be7578fddbfcbe491c1c29e3e4c7cf485376191019417c69880c3`
- Intended device path for the later live unit:
  `/mnt/sdext/a90/runtime/debian-bookworm-arm64-d3-sysvinit.img`
- Mandatory auto-reboot window: `120s`

Downloaded package set:

| Package | Version | SHA-256 |
| --- | --- | --- |
| `initscripts` | `3.06-4` | `a83b40eb46250597d315531cdf82d774227cc1c9b03966737de08602a6af02ef` |
| `insserv` | `1.24.0-1` | `3647a9c6780fec32fbd7ddb7f1ecd149074793516ecaf7b4b80de2691d17a83d` |
| `startpar` | `0.65-1+b1` | `e07d6db20b9f5da6a4329b8c32da50213c31f1e1eec58d161b4ad8c1f5a677db` |
| `sysv-rc` | `3.06-4` | `4afe3c6c8a46b290554a07ed613aff4a394f0c18a2ad7c6444261043f98faa90` |
| `sysvinit-core` | `3.06-4` | `59bedbd7fd5d6e918bb485f10571fe4bd48468f13dc6c629ab4e6d8d4ebe87dd` |

## Static Validation

Script/unit tests:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/prepare_d3_sysvinit_rootfs.py tests/test_server_distro_d3_sysvinit_rootfs.py`
- `PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_server_distro_d3_sysvinit_rootfs`
  - `Ran 3 tests ... OK`

Image inspection via `debugfs`:

- `/sbin/init` exists, mode `0755`, uid/gid `0:0`.
- `/dev/null` is a character device with major/minor `1:3`.
- `/etc/inittab` contains `si::sysinit:/etc/a90-d3-firstboot`.
- `/etc/a90-d3-firstboot` schedules the `120s` auto-reboot before NCM reassertion and dropbear start.
- `/root/.ssh/authorized_keys` is absent from the image; D3 live must stage a per-run temporary key
  before handoff.

## Safety Result

- Host-only; no device command was run for D3A.
- No boot image was built or flashed.
- No rollback was needed.
- No public tunnel exposure.
- No credentials or keys are included in the D3 image.
- `userdata` remains untouched.

## Next

Proceed to D3B: stage the private D3 image to SD, stage a per-run temporary SSH key into the mounted
image, and run the checked native-init `switch_root` handoff. The live unit must observe the Debian
marker over SSH and then wait for the mandatory auto-reboot back to resident v2321 with
`selftest fail=0`.
