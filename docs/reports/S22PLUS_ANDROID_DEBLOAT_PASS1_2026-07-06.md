# S22+ Android Debloat Pass 1 - 2026-07-06

## Scope

First reversible debloat pass on the rooted Samsung S22+ `SM-S906N` / `g0q`
running `S906NKSS7FYG8`.

Method: user-0 package removal / disable only. This run did not delete APKs from
system partitions and did not modify boot, recovery, vbmeta, vendor_boot, super,
userdata, EFS, modem, RPMB, keymaster, or bootloader partitions.

Core packages intentionally left installed: Settings, One UI launcher, SystemUI,
Play services, Play Store, WebView, Samsung keyboard, camera, gallery, dialer,
phone, and Magisk.

## Pre-State

```text
sys.boot_completed=1
ro.build.version.incremental=S906NKSS7FYG8
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
```

## Removed For User 0

These packages returned `Success` from:

```text
cmd package uninstall --user 0 <package>
```

Packages:

```text
skplanet.musicmate
com.skt.nugu.apollo
kr.co.captv.pooqV2
com.google.android.apps.youtube.music
com.samsung.android.app.tips
com.google.android.apps.tachyon
com.google.android.projection.gearhead
com.google.android.apps.bard
com.microsoft.appmanager
com.samsung.android.app.spage
com.samsung.android.bixby.agent
com.samsung.android.bixby.wakeup
com.samsung.android.bixbyvision.framework
com.samsung.android.game.gamehome
com.samsung.android.game.gametools
com.samsung.android.aremoji
com.samsung.android.aremojieditor
com.sec.android.mimage.avatarstickers
com.samsung.android.app.camera.sticker.facearavatar.preload
com.sec.android.autodoodle.service
com.samsung.android.app.dressroom
com.samsung.android.app.dofviewer
com.samsung.android.visionintelligence
com.samsung.android.app.sharelive
com.samsung.android.app.reminder
com.samsung.android.scloud
com.samsung.knox.securefolder
com.sec.android.easyMover
com.sec.android.easyMover.Agent
com.samsung.android.smartswitchassistant
com.samsung.android.kidsinstaller
com.samsung.android.app.parentalcare
com.samsung.android.dynamiclock
com.samsung.android.forest
com.samsung.android.app.watchmanagerstub
com.skt.hpsagree
com.skt.hps20client
com.skt.t_smart_charge
com.sktelecom.minit
com.skt.skaf.OA00412131
com.skt.skaf.A000Z00040
com.skt.skaf.OA00018282
com.skt.skaf.OA00199800
```

## Disabled

`com.samsung.android.game.gos` reported `Success` from uninstall, but still
appeared installed for user 0. It was then disabled:

```text
pm disable-user --user 0 com.samsung.android.game.gos
Package com.samsung.android.game.gos new state: disabled-user
```

Final `dumpsys package` state:

```text
enabled=3
```

## Post-State

Android and root remained healthy:

```text
sys.boot_completed=1
ro.build.version.incremental=S906NKSS7FYG8
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
```

Core package checks:

```text
ok:com.android.settings
ok:com.sec.android.app.launcher
ok:com.android.systemui
ok:com.google.android.gms
ok:com.android.vending
ok:com.google.android.webview
ok:com.samsung.android.honeyboard
ok:com.sec.android.app.camera
ok:com.sec.android.gallery3d
ok:com.samsung.android.dialer
ok:com.android.phone
ok:com.topjohnwu.magisk
```

Remaining third-party package list after pass 1:

```text
com.sec.android.app.popupcalculator
com.google.android.apps.photos
com.sec.android.app.sbrowser
com.skt.tmap.ku
com.topjohnwu.magisk
```

## Restore

Most packages can be restored without reflashing:

```text
cmd package install-existing --user 0 <package>
```

For GOS:

```text
pm enable --user 0 com.samsung.android.game.gos
```

If a package is not restorable by `install-existing`, reinstall it from Galaxy
Store, Play Store, or the original firmware package.

