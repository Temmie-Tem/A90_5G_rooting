# S22+ Android 116-package checkpoint

Date: 2026-07-06

Device:
- Samsung Galaxy S22+ `SM-S906N` / `g0q`
- Build: `S906NKSS7FYG8`
- Root: Magisk 30.7

Scope:
- Record the current reboot-validated Android user-0 package state as the S22+
  package cleanup checkpoint.
- Package-manager state only.
- No partition writes.
- No device identifiers recorded.

## Checkpoint Summary

```text
sys.boot_completed=1
build=S906NKSS7FYG8
persist.sys.safemode=
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
user-0 packages: 116
disabled packages: 0
known-bad pass4 packages still installed: 13
outside A90 allowlist: 40
```

The exact package allowlist is stored in:

```text
docs/plans/S22PLUS_ANDROID_116_PACKAGE_ALLOWLIST_2026-07-06.txt
```

## Why This Is A Checkpoint

This state has survived multiple reboot validations:

```text
154-package safe boundary: reboot OK
140-package boundary: reboot OK
127-package boundary: reboot OK
122-package boundary: reboot OK
116-package boundary: reboot OK
```

The previous unsafe boundary is also known:

```text
141-package pass4 batch: forced Samsung safe mode, factory reset required
```

Therefore `116` is the current S22+ Android package checkpoint, but only because
the known-bad pass4 packages were retained and the later reductions avoided that
batch.

## Core Package Check

Core package presence was verified:

```text
ok:com.android.settings
ok:com.sec.android.app.launcher
ok:com.android.systemui
ok:com.google.android.gms
ok:com.android.vending
ok:com.google.android.webview
ok:com.google.android.gsf
ok:com.google.android.packageinstaller
ok:com.google.android.permissioncontroller
ok:com.google.android.networkstack
ok:com.samsung.android.networkstack
ok:com.android.phone
ok:com.android.server.telecom
ok:com.sec.imsservice
ok:com.android.providers.telephony
ok:com.topjohnwu.magisk
```

## Known-Bad Pass4 Set Retained

These packages are intentionally still installed:

```text
com.android.bluetooth
com.android.cameraextensions
com.android.mtp
com.android.uwb.resources
com.google.android.documentsui
com.qualcomm.location
com.samsung.android.app.telephonyui.esimclient
com.samsung.android.nfc.resources.korea
com.samsung.android.providers.factory
com.samsung.android.wallpaper.res
com.skms.android.agent
com.skp.seio
com.skt.prod.dialer
```

Do not remove this set as a batch again.

## Reapply Method

To reapply this checkpoint after factory reset or package-state loss:

```bash
adb shell cmd package list packages --user 0 | sed 's/^package://' | sort > /tmp/s22_current.txt
comm -23 /tmp/s22_current.txt docs/plans/S22PLUS_ANDROID_116_PACKAGE_ALLOWLIST_2026-07-06.txt > /tmp/s22_delete_to_116.txt
while read -r p; do
  adb shell cmd package uninstall --user 0 "$p"
done < /tmp/s22_delete_to_116.txt
```

Then reboot and validate:

```bash
adb reboot
adb wait-for-device
adb shell 'getprop sys.boot_completed; getprop persist.sys.safemode; su -c id; cmd package list packages --user 0 | wc -l'
```

Expected post-reboot result:

```text
sys.boot_completed=1
persist.sys.safemode=
root OK
user-0 packages: 116
disabled packages: 0
```

## Restore

Any user-0 package removed by package-manager cleanup can usually be restored
without reflashing:

```bash
adb shell cmd package install-existing --user 0 <package>
```

If the package was disabled instead:

```bash
adb shell pm enable --user 0 <package>
```

## Current Guidance

Treat this as the Android-side S22+ package checkpoint.

Further reductions should be:
- one package or two packages per batch,
- followed by a reboot validation,
- documented as a new checkpoint only after `sys.boot_completed=1`, no forced
  safe mode, root OK, and core packages present.
