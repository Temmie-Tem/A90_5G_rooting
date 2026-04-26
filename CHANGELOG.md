# Changelog

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
