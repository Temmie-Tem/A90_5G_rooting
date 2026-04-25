# Changelog

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
