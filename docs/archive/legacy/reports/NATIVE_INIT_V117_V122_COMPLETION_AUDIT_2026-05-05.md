# A90 Native Init v117-v122 Completion Audit

Date: 2026-05-05
Objective: `v117 부터 v122 까지 진행하자`

## Deliverables

The objective is complete only if all of the following are true:

1. v117 through v122 each have a committed implementation.
2. Each version has source, boot image artifact, report, and validation evidence.
3. v122 is the latest verified build in the main docs.
4. Real-device flash evidence exists for each version.
5. v122 Wi-Fi result answers whether active Wi-Fi work remains blocked.
6. The repository is left in a coherent state with no uncommitted required work.

## Prompt-to-Artifact Checklist

| requirement | evidence | status |
|---|---|---|
| v117 roadmap baseline | commit `30b02a2`, `docs/reports/NATIVE_INIT_V117_PID1_SLIM_ROADMAP_2026-05-05.md`, `stage3/linux_init/init_v117.c`, `stage3/boot_linux_v117.img` | PASS |
| v118 shell metadata cleanup | commit `9523e3c`, `docs/reports/NATIVE_INIT_V118_SHELL_META_API_2026-05-05.md`, `cmdmeta` validation | PASS |
| v119 menu routing cleanup | commit `3cb5cc1`, `docs/reports/NATIVE_INIT_V119_MENU_ROUTE_API_2026-05-05.md`, route helper/static/menu regression validation | PASS |
| v120 command group split | commit `0f95ba0`, `docs/reports/NATIVE_INIT_V120_COMMAND_GROUP_API_2026-05-05.md`, `cmdgroups` validation | PASS |
| v121 PID1 guard | commit `88285ce`, `docs/reports/NATIVE_INIT_V121_PID1_GUARD_2026-05-05.md`, `pid1guard pass=11 warn=0 fail=0` | PASS |
| v122 Wi-Fi refresh | commit `6e07199`, `docs/reports/NATIVE_INIT_V122_WIFI_REFRESH_2026-05-05.md`, `wifiinv refresh`, `wififeas refresh`, host collector | PASS |
| latest docs point to v122 | `README.md`, `docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md`, `docs/plans/NATIVE_INIT_NEXT_WORK_2026-04-25.md` show `A90 Linux init 0.9.22 (v122)` | PASS |
| current device is v122 | `a90ctl.py --json version` returned `A90 Linux init 0.9.22 (v122)` with `rc=0 status=ok` | PASS |
| boot/status health | `a90ctl.py status` returned `selftest: pass=11 warn=0 fail=0` and `pid1guard: pass=11 warn=0 fail=0` | PASS |
| Wi-Fi decision | v122 report concludes active Wi-Fi bring-up remains blocked due to missing WLAN/rfkill/module gates | PASS |

## Version Evidence

| version | build | commit | report | quick validation |
|---|---|---|---|---|
| v117 | `A90 Linux init 0.9.17 (v117)` | `30b02a2` | `docs/reports/NATIVE_INIT_V117_PID1_SLIM_ROADMAP_2026-05-05.md` | flash PASS, selftest PASS, 3-cycle soak PASS |
| v118 | `A90 Linux init 0.9.18 (v118)` | `9523e3c` | `docs/reports/NATIVE_INIT_V118_SHELL_META_API_2026-05-05.md` | `cmdmeta` PASS, unknown command framed result PASS, 3-cycle soak PASS |
| v119 | `A90 Linux init 0.9.19 (v119)` | `3cb5cc1` | `docs/reports/NATIVE_INIT_V119_MENU_ROUTE_API_2026-05-05.md` | menu/show/hide/display regression PASS, 3-cycle soak PASS |
| v120 | `A90 Linux init 0.9.20 (v120)` | `0f95ba0` | `docs/reports/NATIVE_INIT_V120_COMMAND_GROUP_API_2026-05-05.md` | `cmdgroups` PASS, representative groups PASS, 3-cycle soak PASS |
| v121 | `A90 Linux init 0.9.21 (v121)` | `88285ce` | `docs/reports/NATIVE_INIT_V121_PID1_GUARD_2026-05-05.md` | `pid1guard` PASS, `status`/`bootstatus` PASS, 3-cycle soak PASS |
| v122 | `A90 Linux init 0.9.22 (v122)` | `6e07199` | `docs/reports/NATIVE_INIT_V122_WIFI_REFRESH_2026-05-05.md` | `wifiinv refresh` PASS, `wififeas refresh` PASS, host collector PASS, 3-cycle soak PASS |

## Artifact Hashes

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v117` | `eed37baf7dd63ac5703ec8a0f6bc9f5c668cebcb29cf237d43942a2b0a73dcca` |
| `stage3/ramdisk_v117.cpio` | `765b0ad1f9a6b27106f244266faab36659a460b98cbf0438995c015df9c76a63` |
| `stage3/boot_linux_v117.img` | `dcd8d4cfcb729a3c9ebfed0eee9a141675492600de5742087476fc96beb683bc` |
| `stage3/linux_init/init_v118` | `291106ab7d477714b41966d232a5036013880a2d9b27f9df6927542de4f7779a` |
| `stage3/ramdisk_v118.cpio` | `3680d035cdfc9fe2cbeb8d93952de1881ebdcb7ff3e2f1701e36075fa2bf0bcc` |
| `stage3/boot_linux_v118.img` | `e76353265c58af0e606b2d22d3eb5e2bfd7b4a6793a8892540f3e37331610972` |
| `stage3/linux_init/init_v119` | `0994d7817f82e6f41d3d8bdf6cbc32d22a30cb541501a0358ffa53117b9cf220` |
| `stage3/ramdisk_v119.cpio` | `0b2bed4591a07bbdb4f8fa8f25fa1d512963be7ad08b82d066af345f95576e94` |
| `stage3/boot_linux_v119.img` | `409759a4aa83d89c492cb62d328f9047db2d0b29731d6925c65595d444643969` |
| `stage3/linux_init/init_v120` | `efd7ec0769a79c751d03b4e8dee45f306b5e8b68be4b7257d43fd43d9260db48` |
| `stage3/ramdisk_v120.cpio` | `63d95f84438210c788a9ef3cf2e2e10cd321fb8710a67d7fe60ae01a2373c173` |
| `stage3/boot_linux_v120.img` | `bb228cf9d7fedb0223b86ed9955ad79b937163fd36cd7054b0c0f59df4ea8cd7` |
| `stage3/linux_init/init_v121` | `6a22eb714e21ec3cc2c5a3cdeae6d67b5c6b74a09d7935346a23cf2410d411f0` |
| `stage3/ramdisk_v121.cpio` | `8ea7de80913c42070e0e6365d2866bb31329fa7c1e7bec8972454c862b4d1cca` |
| `stage3/boot_linux_v121.img` | `34760cd69b4adca766c5bf7f498269be267e626cf72cdc870a12efd40c694e91` |
| `stage3/linux_init/init_v122` | `4c9a8f366077ae03d68ed6705183b39abe88eeff32f77a9c7af0952752a679a8` |
| `stage3/ramdisk_v122.cpio` | `094d78ff8b57e5f07f7cc5b8b64713571bc8afb289741ee38cf591d666ec2c10` |
| `stage3/boot_linux_v122.img` | `010670c139b54e2a17c6a34c617f1a0b0f86334313fa87d45c8c1ed432867bf8` |

## Current Device Check

Latest live device check after v122:

- `version`: `A90 Linux init 0.9.22 (v122)`, `rc=0`, `status=ok`
- `status`: `selftest: pass=11 warn=0 fail=0`, `pid1guard: pass=11 warn=0 fail=0`
- storage: SD backend `/mnt/sdext/a90`, fallback `no`, writable `yes`
- netservice: disabled by default, tcpctl stopped

## Wi-Fi Carry-Forward

v122 does not authorize active Wi-Fi bring-up. It confirms:

- default native state remains `relation=unchanged-native-default`
- mounted-system state shows Android-side candidates only
- no `wlan*` interface
- no Wi-Fi rfkill
- no WLAN/CNSS/QCA module evidence

Next Wi-Fi work should remain read-only unless a separate controlled probe plan defines exact commands, rollback criteria, and no-mutating gates.

## Audit Verdict

All v117-v122 requirements are implemented, verified, documented, and committed. No missing or weakly verified requirement was found for the stated objective.
