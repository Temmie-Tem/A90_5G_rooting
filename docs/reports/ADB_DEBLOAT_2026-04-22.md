# ADB Debloat Snapshot (2026-04-22)

Device: `SM-A908N`
Build: `samsung/r3qks/r3q:12/SP1A.210812.016/A908NKSU5EWA3:user/release-keys`

Policy:
- Kept: `SystemUI`, `Launcher`, `SetupWizard`, `Settings`, phone, Wi-Fi, core Knox/KG packages
- Method 1: `pm disable-user --user 0`
- Method 2: `pm uninstall --user 0`

Current counts:
- Disabled packages: `0`
- Active packages reported by `pm list packages`: `92`

## Originally Disabled Packages

All packages listed in this section were later removed from `user 0` successfully.

```text
com.google.android.apps.restore
com.google.android.apps.turbo
com.google.android.feedback
com.google.android.googlequicksearchbox
com.google.android.printservice.recommendation
com.google.ar.core
com.microsoft.appmanager
com.samsung.android.aircommandmanager
com.samsung.android.allshare.service.fileshare
com.samsung.android.allshare.service.mediashare
com.samsung.android.app.aodservice
com.samsung.android.app.appsedge
com.samsung.android.app.clipboardedge
com.samsung.android.app.cocktailbarservice
com.samsung.android.app.dofviewer
com.samsung.android.app.dressroom
com.samsung.android.app.earphonetypec
com.samsung.android.app.galaxyfinder
com.samsung.android.app.reminder
com.samsung.android.app.routines
com.samsung.android.app.settings.bixby
com.samsung.android.app.sharelive
com.samsung.android.app.simplesharing
com.samsung.android.app.soundpicker
com.samsung.android.app.taskedge
com.samsung.android.app.tips
com.samsung.android.app.updatecenter
com.samsung.android.app.watchmanagerstub
com.samsung.android.ardrawing
com.samsung.android.aremoji
com.samsung.android.arzone
com.samsung.android.bixby.agent
com.samsung.android.bixby.service
com.samsung.android.bixby.wakeup
com.samsung.android.bixbyvision.framework
com.samsung.android.cmfa.framework
com.samsung.android.easysetup
com.samsung.android.forest
com.samsung.android.game.gamehome
com.samsung.android.game.gametools
com.samsung.android.game.gos
com.samsung.android.kidsinstaller
com.samsung.android.livestickers
com.samsung.android.mdecservice
com.samsung.android.mdx
com.samsung.android.mdx.kit
com.samsung.android.mdx.quickboard
com.samsung.android.peripheral.framework
com.samsung.android.privateshare
com.samsung.android.samsungpass
com.samsung.android.samsungpassautofill
com.samsung.android.scloud
com.samsung.android.secsoundpicker
com.samsung.android.service.health
com.samsung.android.service.peoplestripe
com.samsung.android.service.stplatform
com.samsung.android.setting.multisound
com.samsung.android.smartmirroring
com.samsung.android.smartsuggestions
com.samsung.android.stickercenter
com.samsung.android.themestore
com.samsung.cmfa.AuthTouch
com.samsung.gamedriver.sm8150
com.samsung.systemui.bixby2
com.sec.android.app.dexonpc
com.sec.android.app.clockpackage
com.sec.android.app.myfiles
com.sec.android.app.samsungapps
com.sec.android.emergencylauncher
com.sec.android.easyMover.Agent
com.sec.android.gallery3d
```

## Uninstalled For User 0

`pm uninstall --user 0` returned `Success` for all of the following:

```text
com.google.android.youtube
com.google.android.gm
com.google.android.apps.maps
com.google.android.apps.tachyon
com.google.android.projection.gearhead
com.samsung.android.calendar
com.samsung.android.video
com.sec.android.QRreader
com.sec.android.app.fm
```

## Bulk Promotion To Uninstall

After staged testing, every package that had been left in `disabled-user` state was promoted to:

```bash
adb shell pm uninstall --user 0 <package>
```

Result:
- Remaining disabled packages: `0`
- Active packages: `349`

## Aggressive Removal Round

The following additional packages were removed from `user 0` successfully:

```text
com.sec.android.daemonapp
com.diotek.sec.lookup.dictionary
com.samsung.android.lool
com.kt.olleh.storefront
com.kt.serviceagent
com.ktpns.pa
com.ktshow.cs
com.kt.olleh.servicemenu
com.samsung.hidden.KT
com.samsung.kt114provider2
com.samsung.android.messaging
com.samsung.knox.securefolder
com.android.managedprovisioning
com.samsung.android.app.contacts
com.sec.android.widgetapp.easymodecontactswidget
com.android.cellbroadcastreceiver
com.android.cellbroadcastservice
com.android.chrome
com.sec.android.app.chromecustomizations
com.samsung.android.app.spage
com.samsung.android.mateagent
com.sec.android.app.camera
com.samsung.android.app.camera.sticker.facearavatar.preload
com.android.cameraextensions
com.samsung.android.camerasdkservice
com.samsung.android.cameraxservice
com.sec.factory.camera
com.sec.factory.cameralyzer
```

State after this round:
- `sys.boot_completed = 1`
- Active packages: `321`

## Google / Separation Removal Round

The following additional packages were removed from `user 0` successfully:

```text
com.android.vending
com.google.android.gms
com.google.android.gsf
com.samsung.android.appseparation
```

State after this round:
- `sys.boot_completed = 1`
- Active packages: `317`
- Confirmed absent from package list:
  - `com.android.vending`
  - `com.google.android.gms`
  - `com.google.android.gsf`
  - `com.samsung.android.appseparation`
  - `com.google.android.setupwizard` was kept
  - `com.android.managedprovisioning` had already been removed earlier
  - `com.samsung.android.bixbyvision.framework` had already been removed earlier

## Minimal Boot Bulk Delete

Using `docs/plans/MINIMAL_BOOT_ALLOWLIST_2026-04-22.txt` as the safer minimal boot target:

- current packages before bulk pass: `317`
- allowlist size: `89`
- bulk delete candidates computed: `228`

Bulk run result:
- processed: `227`
- success: `226`
- failure: `1`
- failure detail: `com.samsung.android.themecenter` -> `DELETE_FAILED_INTERNAL_ERROR`

Current state after the bulk pass:
- `sys.boot_completed = 1`
- active packages: `92`
- remaining packages outside allowlist:
  - `com.samsung.android.game.gos`
  - `com.samsung.android.themecenter`
  - `com.sec.android.sdhms`

## Restore

Re-enable a disabled package:

```bash
adb shell pm enable <package>
```

Restore a package removed only for user 0:

```bash
adb shell cmd package install-existing <package>
```

Check disabled packages:

```bash
adb shell pm list packages -d | sort
```
