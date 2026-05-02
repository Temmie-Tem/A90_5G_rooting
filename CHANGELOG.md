# Changelog

## `0.8.25` (`v94`) - 2026-05-03

- Added `a90_selftest.c/h` for fast non-destructive boot selftest result tracking.
- Runs boot selftest after ACM gadget setup and before tty attach while keeping failures warn-only.
- Added `selftest [status|run|verbose]` and selftest summaries in `status` and `bootstatus`.
- Checks log, timeline, storage, metrics, KMS, input nodes, service registry, and ACM configfs state without USB rebind or mount mode changes.
- Verified v94 flash, `cmdv1 version/status`, `bootstatus`, `selftest`, `selftest verbose`, `selftest run`, `timeline`, `logcat`, `storage`, `mountsd status`, `statushud`, `autohud`, `screenmenu`, `hide`, and `netservice status`.

## `0.8.24` (`v93`) - 2026-05-02

- Added `a90_storage.c/h` for boot storage state, SD workspace probing, `/cache` fallback policy, and `storage`/`mountsd` command handlers.
- Replaced direct include-tree `boot_storage` access with storage status snapshots for HUD/status/menu call sites.
- Preserved Android layout, netservice, USB gadget, and recovery/reboot command behavior for v94+ separation.
- Fixed `mountsd ro/off/init` logpath recovery so remounting SD restores `/mnt/sdext/a90/logs/native-init.log`.
- Verified v93 flash, `cmdv1 version/status`, `storage`, `mountsd status/ro/rw/init/off`, `logpath`, `timeline`, `statushud`, `autohud`, `screenmenu`, `hide`, and `netservice status`.

## `0.8.23` (`v92`) - 2026-05-02

- Added `a90_shell.c/h` for command flags/types, last-result storage, protocol sequence allocation, command lookup, errno normalization, and result printing.
- Added `a90_controller.c/h` for serial hide-word detection and auto-menu / power-page busy policy.
- Updated v92 dispatch to use shell/controller APIs while preserving command handlers, command table entries, and command UX.
- Verified v92 flash, `cmdv1 version/status`, unknown and busy framed results, nonblocking `screenmenu`, menu-visible observation commands, power-page busy gate, `cpustress`, `autohud`, and `watchhud`.

## `0.8.22` (`v91`) - 2026-05-02

- Added `/bin/a90_cpustress` as a static ARM64 helper included in the boot ramdisk.
- Moved CPU stress worker forking out of PID1 for both the shell command and menu CPU stress app.
- Extended `a90_run` with process-group stop support so cancel/timeout can terminate helper worker trees.
- Preserved `cpustress [sec] [workers]` UX, menu CPU stress timing choices, nonblocking `screenmenu`, and storage/display behavior.
- Verified v91 flash, `cmdv1 version/status`, direct helper run, `cpustress 3 2`, q cancel, `statushud`, `autohud`, `watchhud`, `screenmenu`, `hide`, menu-visible busy gate, and physical-button CPU stress menu flow.

## `0.8.21` (`v90`) - 2026-05-02

- Added `a90_metrics.c/h` for battery, CPU, GPU, memory, power, uptime, and CPU frequency snapshot helpers.
- Removed metric/sysfs read ownership from `a90_hud.c/h` so HUD remains a renderer over metrics snapshots.
- Updated `status`, status HUD, and CPU stress screen callsites to use the shared metrics API.
- Preserved v89 menu control behavior, nonblocking `screenmenu`, storage, displaytest, and cutout calibration behavior.
- Verified v90 flash, `cmdv1 version/status`, `statushud`, `autohud`, `watchhud`, `screenmenu`, `hide`, SD storage, `cpustress`, `displaytest safe`, and `cutoutcal`.

## `0.8.20` (`v89`) - 2026-05-02

- Added `a90_menu.c/h` for menu page/action/app enums, item/page tables, menu state movement, action-to-app mapping, and CPU stress duration mapping.
- Changed `screenmenu`/`menu` into nonblocking background HUD menu show requests that return framed cmdv1 results immediately.
- Added formal `hide`, `hidemenu`, and `resume` commands for HUD menu hide requests.
- Extended auto-menu IPC from hide-only to show/hide while keeping `blindmenu` as the blocking rescue foreground path.
- Verified v89 flash, `cmdv1 version/status`, nonblocking `screenmenu`, menu-visible observability commands, `hide`, display/HUD regressions, and SD storage status.

## `0.8.19` (`v88`) - 2026-05-02

- Added `a90_hud.c/h` for boot splash line storage/rendering, status HUD rendering, status snapshot reads, and log tail panel rendering.
- Replaced direct include-tree HUD drawing helpers with `a90_hud_*` calls while keeping the visual layout stable.
- Kept `screenmenu`, `blindmenu`, app routing, displaytest, cutoutcal, and inputmonitor logic in the v88 include tree.
- Added a small storage-status bridge so HUD rendering does not directly depend on the include-tree `boot_storage` static state.
- Verified v88 flash, `cmdv1 version/status`, `statushud`, `autohud 2`, `watchhud 1 2`, `displaytest safe`, `storage`, `mountsd status`, and screenmenu cancel.

## `0.8.18` (`v87`) - 2026-04-30

- Added `a90_input.c/h` for physical button context open/close, key wait, gesture wait, gesture decoder helpers, and menu-action mapping.
- Removed inline `key_wait_context`, key wait, and gesture decoder implementation from the v87 include tree.
- Preserved menu/HUD/displaytest behavior while moving input decoding behind APIs.
- Changed boot summary time from truncated integer seconds to rounded 0.1s display.
- Local build, boot image generation, marker checks, static checks, TWRP flash, and post-boot regression checks passed.

## `0.8.17` (`v86`) - 2026-04-30

- Added `a90_kms.c/h` for DRM/KMS dumb-buffer state, frame begin/present, framebuffer info, and probe output.
- Added `a90_draw.c/h` for framebuffer clear/rect/text/text-fit/outline/test-pattern primitives.
- Removed direct `kms_state` and `struct kms_display_state` ownership from the v86 include tree.
- Preserved HUD/menu/input/displaytest behavior while moving low-level KMS/draw code behind APIs.
- Verified v86 flash, `cmdv1 version/status`, `kmsprobe`, `kmssolid`, `kmsframe`, `statushud`, `displaytest`, `cutoutcal`, `autohud`, and q cancel for `screenmenu`/`inputmonitor`.

## `0.8.16` (`v85`) - 2026-04-30

- Added `a90_run.c/h` for shared fork/exec/wait/timeout/cancel/reap/stop process handling.
- Added `a90_service.c/h` for static PID registry of `autohud`, `tcpctl`, and `adbd`.
- Moved `run`, `runandroid`, netservice helper execution, `tcpctl`, and `adbd` lifecycle paths onto the shared APIs.
- Preserved netservice policy, shell dispatch, storage, KMS/HUD/menu, and cpustress worker behavior.
- Verified v85 flash, `cmdv1 version/status`, run/runandroid, cpustress/watchhud/autohud/stophud, adbd start/stop, netservice start/stop, and q cancel regressions.

## `0.8.15` (`v84`) - 2026-04-30

- Added `a90_cmdproto.c/h` as the owner of `cmdv1/cmdv1x` protocol helpers.
- Moved `A90P1` begin/end frame formatting and protocol status mapping behind cmdproto APIs.
- Moved `cmdv1x` length-prefixed hex argv decode behind cmdproto APIs.
- Kept shell command table, busy gate, last result, and dispatch ownership unchanged for a narrow protocol split.
- Verified v84 flash, `cmdv1` ok/unknown/busy/error statuses, `cmdv1x` whitespace/malformed paths, storage/display regressions, and run/cpustress/watchhud q cancel.

## `0.8.14` (`v83`) - 2026-04-29

- Added `a90_console.c/h` as the owner of USB ACM console fd state.
- Moved attach, reattach, readline, write/printf, stdio dup, and cancel polling behind console APIs.
- Kept shell dispatch and `cmdv1`/`cmdv1x` behavior unchanged for a safer first console split.
- Added on-device `0.8.14 v83 CONSOLE API` changelog detail.
- Verified v83 flash, `cmdv1 version/status`, storage/log/timeline/display regressions, run/cpustress/watchhud, q cancel, `reattach`, and `usbacmreset`.

## `0.8.13` (`v82`) - 2026-04-29

- Added `a90_log.c/h` for native log path/state and file output.
- Added `a90_timeline.c/h` for boot timeline storage, replay, probe, summary, and read-only entry access.
- Removed direct include-tree access to native log/timeline arrays and paths.
- Preserved console, shell, storage, display, and netservice behavior while moving log/timeline into real API modules.
- Added on-device `0.8.13 v82 LOG TIMELINE API` changelog detail.
- Verified v82 flash, SD log path, timeline/bootstatus/logpath, storage, displaytest safe, and autohud restart.

## `0.8.12` (`v81`) - 2026-04-29

- Added `a90_config.h` for shared version/path/constant definitions.
- Added `a90_util.c/h` as the first real compiled base module.
- Moved common file/string/time/errno helpers out of PID1 include modules.
- Preserved v80 behavior while starting true `.c/.h` API extraction.
- Added on-device `0.8.12 v81` changelog detail.
- Verified v81 flash, SD storage path, shell commands, HUD/display, timeline, and autohud restart.

## `0.8.11` (`v80`) - 2026-04-29

- Split the native init PID1 source into include-based functional modules.
- Kept one static `/init` binary and one translation unit to avoid behavior drift.
- Preserved v79 boot storage/runtime behavior while making future helper extraction safer.
- Added on-device `0.8.11 v80` changelog detail.
- Local build and boot image generation passed; device flash validation is pending.

## `0.8.10` (`v79`) - 2026-04-29

- Added boot-time SD health check before the main HUD starts.
- Verifies `/dev/block/mmcblk0p1`, expected ext4 UUID `c6c81408-f453-11e7-b42a-23a2c89f58bc`, `/mnt/sdext/a90` identity marker, and read/write probe.
- Promotes `/mnt/sdext/a90` to the main runtime storage when SD validation passes.
- Falls back to `/cache` when SD is missing, changed, unmountable, or not writable.
- Shows SD probe progress on the boot splash and persistent SD warning text on the HUD when fallback is active.
- Added `storage` command and `status` storage lines for bridge-side verification.
- Added on-device `0.8.10 v79` changelog detail.

## `0.8.9` (`v78`) - 2026-04-29

- Promoted the SD-card work into its own feature version after the v77 display/cutout baseline.
- Added `mountsd [status|ro|rw|off|init]` for the ext4 SD workspace at `/mnt/sdext/a90`.
- Standardized `/mnt/sdext/a90/{bin,logs,tmp,rootfs,images,backups}` as the safer experiment workspace.
- Integrated SD mount state and free-space reporting into `status`.
- Added on-device `0.8.9 v78` changelog detail.
- Verified SD card ext4 formatting, workspace init, rw write/sync, ro remount, off/remount, and status reporting.

## `0.8.8` (`v77`) - 2026-04-27

- Split `TOOLS / DISPLAY TEST` into four pages: color/pixel, font/wrap, safe-area/cutout, and HUD/menu preview.
- Added `displaytest [0-3|colors|font|safe|layout]` for direct bridge validation.
- Added VOL+/VOL- page navigation for the display test app, with POWER returning to the menu.
- Added `cutoutcal [x y size]` plus `TOOLS > CUTOUT CAL` for camera-hole alignment.
- Reworked the safe/cutout page into a calibration reference around the real punch-hole area.
- Added on-device `0.8.8 v77` changelog detail.
- Verified v77 boot, `cutoutcal`, and all four displaytest pages with `rc=0`, `status=ok`.

## `0.8.7` (`v76`) - 2026-04-27

- Added a short AT serial fragment filter for `A`, `T`, `AT`, `ATA`, and `ATAT`-style probe fragments.
- Kept the existing full `AT...` probe filter for lines such as `AT+GCAP`.
- Prevented these fragments from becoming `unknown command` shell errors.
- Added on-device `0.8.7 v76` changelog detail.
- Verified v76 boot, raw fragment injection, normal `version`, and `cmdv1x` whitespace argument path.

## `0.8.6` (`v75`) - 2026-04-27

- Increased idle serial console reattach interval from 10 seconds to 60 seconds.
- Suppressed successful `idle-timeout` reattach request/ok logs so live LOG TAIL stays readable.
- Kept idle reattach failure logs and manual/non-idle reattach logs visible.
- Added on-device `0.8.6 v75` changelog detail.
- Verified v75 boot via native flash script, `cmdv1 version/status`, 70+ second idle log check, and manual `reattach` log check.

## `0.8.5` (`v74`) - 2026-04-27

- Added `cmdv1x <len:hex-utf8-arg>...` to preserve whitespace and special-character arguments inside framed shell calls.
- Kept the legacy `cmdv1 <command> [args...]` path for simple argv.
- Updated `a90ctl.py` to auto-select legacy `cmdv1` or encoded `cmdv1x`.
- Shared argv parsing/encoding across NCM, netservice reconnect, and TCP control host tools.
- Added on-device `0.8.5 v74` changelog detail.
- Verified v74 boot and `a90ctl.py echo "hello world"` with `rc=0`, `status=ok`.

## `0.8.4` (`v73`) - 2026-04-27

- Added `cmdv1 <command> [args...]` one-shot shell protocol wrapper.
- Added `A90P1 BEGIN` and `A90P1 END` records with `seq`, `cmd`, `argc`, `flags`, `rc`, `errno`, `duration_ms`, and `status`.
- Framed `unknown` and `busy` outcomes for safer automation.
- Added `scripts/revalidation/a90ctl.py` host wrapper with text/JSON output and busy-hide retry.
- Added on-device `0.8.4 v73` changelog detail.
- Verified v73 boot via native flash script and bridge `cmdv1`/`a90ctl` checks.

## `0.8.3` (`v72`) - 2026-04-27

- Added `TOOLS / DISPLAY TEST` plus `displaytest` for color/font/wrap/safe-area/cutout checks.
- Split the display-test top guide into `TOP LEFT SLOT`, `PUNCH HOLE`, and `TOP RIGHT SLOT`.
- Widened the main display-test safe-area grid.
- Fixed framebuffer color packing for `DRM_FORMAT_XBGR8888` so RGB labels match displayed colors.
- Added on-device `0.8.3 v72` changelog detail.
- Verified v72 boot via native flash script and bridge `version`/`status`/`displaytest`.

## `0.8.2` (`v71`) - 2026-04-27

- Added a shared framebuffer log-tail panel renderer.
- Kept the hidden HUD `LOG TAIL` view while reusing the same renderer.
- Added live log-tail display to the visible auto HUD menu spare area.
- Added live log-tail display to manual `screenmenu` when vertical space is available.
- Added title-to-log spacing for the live log tail panel.
- Increased log-tail row limits for HUD/menu views.
- Reduced log-tail body text size and wrapped long lines across rows.
- Relaxed the auto-menu busy gate so normal serial commands can run outside the POWER menu.
- Added basic log coloring for failure, cancel/noise, input/menu, and boot/timeline lines.
- Reduced manual screen menu scale for long changelog pages to avoid clipping.
- Verified v71 boot via native flash script and bridge `version`/`status`/`screenmenu`.

## `0.8.1` (`v70`) - 2026-04-26

- Added `TOOLS / INPUT MONITOR` for button-event debugging.
- Added `inputmonitor [events]` to print raw `DOWN`/`UP`/`REPEAT` events.
- Logged per-event gap time, hold duration, decoded gesture, and menu action.
- Split monitor rows into readable title/detail lines and color-coded event types.
- Added a large decoded-input panel for click/double/long/combo classification.
- Changed three-button input monitor exit to trigger immediately on all-buttons-down.
- Restored the HUD unconditionally after `inputmonitor` exits.
- Reused the same gesture decoder path as `waitgesture`.
- Verified v70 boot via native flash script and bridge `version`/`status`/`inputlayout`.

## `0.8.0` (`v69`) - 2026-04-26

- Added an input gesture layout for the three physical buttons.
- Added `inputlayout` to print the active button map.
- Added `waitgesture [count]` to debug single, double, long, and combo input.
- Updated `screenmenu` and `blindmenu` to use gesture actions.
- Reserved `POWER` long press for safety instead of binding it to a destructive action.

## `0.7.5` (`v68`) - 2026-04-26

- Added HUD log tail display when the menu is hidden.
- Expanded on-device changelog history through early native init milestones.
- Added detail screens for older changelog entries.

## `0.7.4` (`v67`) - 2026-04-26

- Reduced ABOUT/version/changelog text scale for the tall A90 display.
- Changed `APPS / ABOUT / CHANGELOG` into a version list.
- Added per-version detail screens for recent native init milestones.
- Preserved `made by temmie0214` and semantic version/build-tag display.
- Verified on device with bridge `version`, `status`, and `timeline`.

## `0.7.3` (`v66`) - 2026-04-26

- Added official semantic version display: `A90 Linux init 0.7.3 (v66)`.
- Added creator display: `made by temmie0214`.
- Added `APPS / ABOUT` menu with `VERSION`, `CHANGELOG`, and `CREDITS` screens.
- Added versioning policy document.
- Updated `version` and `status` output to include creator/version metadata.

## `0.7.2` (`v65`) - 2026-04-26

- Fixed custom boot splash clipping by reducing scale, widening safe margins, shortening rows, and fitting footer text.
- Verified bridge `version`, `status`, and `timeline` on-device.

## `0.7.1` (`v64`) - 2026-04-26

- Replaced the boot-time `TEST` debug pattern with a custom `A90 NATIVE INIT` splash.
- Added `display-splash` timeline logging.

## `0.7.0` (`v63`) - 2026-04-26

- Added hierarchical app menu structure.
- Added CPU stress screen app with selectable 5/10/30/60 second durations.
- Kept LOG/NETWORK/CPU STRESS screens persistent until a button is pressed.

## `0.6.0` (`v62`) - 2026-04-26

- Added CPU stress helper for CPU usage gauge validation.
- Added boot-time `/dev/null` and `/dev/zero` char node guard.

## Earlier Milestones

- `0.5.0` (`v60`): opt-in USB NCM/tcpctl netservice and reconnect validation.
- `0.4.0` (`v55`): NCM setup helper and bidirectional TCP validation foundation.
- `0.3.0` (`v53`): screen menu polish, menu busy gate, and flash auto-hide handling.
- `0.2.0` (`v40`~`v45`): shell return codes, file logging, timeline, HUD boot summary, and cancel handling.
- `0.1.0`: native init PID 1 entry, USB ACM serial shell, KMS display, and input probing.
