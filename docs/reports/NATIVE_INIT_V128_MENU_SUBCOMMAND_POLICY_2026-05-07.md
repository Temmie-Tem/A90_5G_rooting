# A90 Native Init v128 Menu Subcommand Policy

Date: 2026-05-07
Build: `A90 Linux init 0.9.28 (v128)`
Marker: `0.9.28 v128 MENU SUBCOMMAND POLICY`

## Summary

v128 preserves the v127 F023 mitigation and narrows the menu-visible relaxation
from command-name allowlist to explicit read-only subcommand policy. While the
screen menu is visible, status/query forms such as `mountsd status`, `diag
paths`, `selftest verbose`, `netservice status`, and `service status autohud`
can run through the serial bridge. Mutating forms such as `run`, `writefile`,
`mountsd rw`, `diag full`, `hudlog on`, `netservice start`, `rshell start`, and
`service start` remain blocked with `rc=-16 status=busy`.

v128 is a UX refinement, not a new security closure. F023 remains closed by
v127's deny-by-default menu busy gate.

## Changes

- Added `a90_controller_command_busy_reason_ex()` so v128 can evaluate `argc` /
  `argv` in addition to command flags and menu state.
- Kept the v127 `a90_controller_command_busy_reason()` wrapper for older include
  trees and compatibility.
- Added read-only subcommand policy for `selftest`, `pid1guard`, `helpers`,
  `mountsd`, `hudlog`, `diag`, `wifiinv`, `wififeas`, `netservice`, `rshell`,
  and `service`.
- Updated v128 shell dispatch to use the subcommand-aware controller API.
- Bumped version metadata to `0.9.28 (v128)` and added the changelog entry.

## Finding Coverage

| finding | result |
|---|---|
| F023 | Preserved mitigation: v127 closed the issue; v128 keeps side-effect commands blocked and only relaxes explicit read-only subcommands. |

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v128` | `1cda7cf557f4137765c18b573a47467b01066eb53e008fb775cbd4b0bd5cc945` |
| `stage3/ramdisk_v128.cpio` | `9bacd7a8761126fbca79905eefc85e039b1fdc7d3cad3362675666a6d6d9b4b2` |
| `stage3/boot_linux_v128.img` | `da1cd9e436ae734f991ef101775efe53ad72b53e84a73ea85a3b5f7ccf94e6a3` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.28 (v128)`, `A90v128`, and
  `0.9.28 v128 MENU SUBCOMMAND POLICY` — PASS.
- host-side controller policy harness — PASS.
- host Python `py_compile` for control/diagnostic scripts and
  `mkbootimg/gki/certify_bootimg.py` — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v128.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.28 (v128)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified.
- TWRP push and remote SHA256 verified.
- boot partition prefix SHA256 matched image SHA256.
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`.

### Runtime Checks

With `screenmenu` visible, allowed read-only commands returned `rc=0 status=ok`:

- `status`
- `storage`
- `timeline`
- `logpath`
- `selftest verbose`
- `pid1guard verbose`
- `helpers path a90_tcpctl`
- `mountsd status`
- `hudlog status`
- `diag paths`
- `wifiinv paths`
- `wififeas gate`
- `netservice status`
- `rshell audit`
- `service status autohud`

With `screenmenu` visible, mutating commands were blocked with `rc=-16 status=busy`:

- `run /bin/a90sleep 1`
- `mountsd rw`
- `diag full`
- `hudlog on`
- `netservice start`
- `rshell start`
- `service start tcpctl`
- `writefile /tmp/v128 x`
- `selftest verbose extra`
- `netservice status extra`

After `hide`:

- `run /bin/a90sleep 1` — PASS, `rc=0 status=ok`.
- `selftest verbose` — PASS, `pass=10 warn=1 fail=0`.
- `status` — PASS, reports `A90 Linux init 0.9.28 (v128)`.

## Notes

- v128 does not weaken the power-page gate; power menu state still uses the
  stricter v127 allowlist.
- v128 does not add authentication to the USB ACM root console or localhost
  bridge. F021 and F030 remain accepted trusted-lab-boundary issues.
