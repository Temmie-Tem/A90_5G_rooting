# A90 Native Init v120 Command Group API

Date: 2026-05-05
Build: `A90 Linux init 0.9.20 (v120)`
Marker: `0.9.20 v120 COMMAND GROUP API`

## Summary

v120 adds command group metadata to the shell command table. This is a low-risk split step: handler bodies and the shell loop stay in the include tree, but commands now have a stable group taxonomy for future handler/file separation and audits.

## Changes

- Added `enum a90_shell_command_group` and group stats APIs to `a90_shell.c/h`.
- Added a `group` field to `struct shell_command`.
- Annotated the v120 command table with groups: core, filesystem, storage, display, input, menu, process, service, network, android, power.
- Added read-only `cmdgroups [verbose]` command.
- Updated `cmdmeta verbose` to include command group labels.
- Added About/changelog entry `0.9.20 v120 COMMAND GROUP API`.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v120` | `efd7ec0769a79c751d03b4e8dee45f306b5e8b68be4b7257d43fd43d9260db48` |
| `stage3/ramdisk_v120.cpio` | `63d95f84438210c788a9ef3cf2e2e10cd321fb8710a67d7fe60ae01a2373c173` |
| `stage3/boot_linux_v120.img` | `bb228cf9d7fedb0223b86ed9955ad79b937163fd36cd7054b0c0f59df4ea8cd7` |
| `tmp/soak/v120-quick-soak.txt` | `9923ce04943bf5f1fe26585f53000023527f0eb19de4a61f728d55e774ab1243` |
| `tmp/soak/v120-cmdgroups-verbose.txt` | `28a2f5982b254f5adbc42f66683a79ee3557dd6ef410581bebaba754e723e915` |
| `tmp/soak/v120-cmdmeta-verbose.txt` | `64d4994f75ab73f3aa550d56d66960584912370082884a3a4131fa5c0d7ce4e8` |

## Validation

### Static

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS
- `strings` marker check for `A90 Linux init 0.9.20 (v120)`, `A90v120`, `0.9.20 v120 COMMAND GROUP API`, `cmdgroups` — PASS
- `git diff --check` — PASS
- host Python `py_compile` for flash/control scripts — PASS
- v120 command table group annotations present — PASS (`81` `A90_CMD_GROUP_*` hits)

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v120.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.20 (v120)" \
  --verify-protocol auto
```

Result: PASS

Evidence:

- local image marker and SHA256 verified
- TWRP push and remote SHA256 verified
- boot partition prefix SHA256 matched image SHA256
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`

### Runtime Regression

- `cmdgroups` — PASS (`total=81 core=15 filesystem=13 storage=8 display=15 input=7 menu=6 process=2 service=4 network=4 android=4 power=3`)
- `cmdgroups verbose` — PASS, inventory written to `tmp/soak/v120-cmdgroups-verbose.txt`
- `cmdmeta verbose` — PASS, group labels included
- storage group: `storage`, `runtime`, `helpers status`, `userland status` — PASS
- network group: `netservice status`, `wifiinv summary`, `wififeas gate` — PASS
- service group: `service list` — PASS
- core group: `selftest verbose` — PASS (`pass=11 warn=0 fail=0`)
- menu/display: `screenmenu`, menu-visible `status`, `hide` — PASS
- `native_soak_validate.py --cycles 3 --sleep 2` — PASS (`cycles=3 commands=14`)

## Next

Proceed to v121 `PID1 GUARD`:

- add read-only process/boot guard checks,
- surface guard summary through shell/status/diag if safe,
- warn-only, never block shell/HUD entry.
