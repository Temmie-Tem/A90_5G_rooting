# Minimal Boot Status (2026-04-22)

Goal:
- converge from `317` active packages toward a minimal bootable Android set
- first target: `89`-package safer allowlist
- later target: `70-80` packages with additional high-risk trimming

Current status:
- Active packages (user 0): `92`
- `sys.boot_completed = 1`
- Allowlist size: `89`
- Remaining packages outside allowlist: `3`

Remaining extras outside allowlist:

```text
com.samsung.android.game.gos
com.samsung.android.themecenter
com.sec.android.sdhms
```

Observed behavior:
- `com.samsung.android.themecenter` failed with `DELETE_FAILED_INTERNAL_ERROR`
- `com.samsung.android.game.gos` and `com.sec.android.sdhms` previously returned `Success` in batch logs but still remain present in `pm list packages`

Key files:
- Allowlist: `docs/plans/MINIMAL_BOOT_ALLOWLIST_2026-04-22.txt`
- Delete candidates snapshot: `docs/plans/MINIMAL_BOOT_DELETE_CANDIDATES_2026-04-22.txt`
- Batch delete log: `docs/reports/MINIMAL_BOOT_DELETE_RUN_2026-04-22.log`
- Re-run after root log: `docs/reports/MINIMAL_BOOT_DELETE_RUN_AFTER_ROOT_2026-04-22.log`

## Incremental Trim Validation

Validated after bulk pass:

- Removed: `com.samsung.android.honeyboard`
- Reboot result: success
- `adb` reconnected normally
- `sys.boot_completed = 1`
- Active packages after reboot (user 0): `91`

Validated next:

- Removed for user 0: `com.google.android.documentsui`
- Reboot result: success
- `adb` reconnected normally
- `sys.boot_completed = 1`
- Active packages after reboot (user 0): `90`

Validated next:

- Attempted removal for user 0: `com.google.android.partnersetup`
- `pm uninstall --user 0` returned `Success`
- `cmd package dump` briefly showed `User 0 installed=false`
- After reboot, package was present again for `user 0`
- Net effect on package count: none

Counting note:
- Earlier broad counts based on `pm list packages` included system-known packages even when `installed=false` for user 0.
- Current minimal-boot tracking should use:
  - `cmd package list packages --user 0`

## Re-applied After Root

After the rooted patched AP booted successfully, the device returned to a near-stock user 0 package set.
The minimal allowlist was re-applied with these adjustments:

- keep `com.topjohnwu.magisk`
- do not keep `com.google.android.documentsui`

Re-application result:

- current packages before replay: `432`
- allowlist size: `89`
- delete candidates processed: `343`
- success: `342`
- failure: `1`
- failure detail: `com.samsung.android.themecenter` -> `DELETE_FAILED_INTERNAL_ERROR`

Post-replay state:

- `sys.boot_completed = 1`
- `su -v` returns `30.7:MAGISKSU`
- active packages (user 0): `92`
- extras outside allowlist:
  - `com.samsung.android.game.gos`
  - `com.samsung.android.themecenter`
  - `com.sec.android.sdhms`

## Extra Package Validation

### `com.samsung.android.game.gos`

- `pm uninstall --user 0` returned `Success`
- `cmd package dump` still showed `User 0 installed=true`
- after reboot, package remained present for `user 0`
- net effect: none

### Root-context uninstall retry

Retested with `su -c` for the remaining extras:

- `com.samsung.android.game.gos`
  - `su -c 'pm uninstall --user 0 ...'` returned `Success`
  - still showed `User 0 installed=true`
  - net effect: none
- `com.sec.android.sdhms`
  - `su -c 'pm uninstall --user 0 ...'` returned `Success`
  - still showed `User 0 installed=true`
  - net effect: none
- `com.samsung.android.themecenter`
  - `su -c 'pm uninstall --user 0 ...'` returned `DELETE_FAILED_INTERNAL_ERROR`
  - remained present for `user 0`

Conclusion:
- root shell does not make these three removable through package-manager uninstall on this build
