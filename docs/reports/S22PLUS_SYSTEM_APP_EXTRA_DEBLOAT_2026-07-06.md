# S22+ extra system-app debloat after A90 comparison

Date: 2026-07-06

Device:
- Samsung Galaxy S22+ `SM-S906N` / `g0q`
- Build: `S906NKSS7FYG8`
- Root: Magisk 30.7

Scope:
- Continue cleanup from the proven `154` package safe boundary.
- User-0 package-manager uninstall only.
- No partition writes.
- A90 minimal allowlist used as a comparison source.
- Known-bad pass4 set excluded from all persistent-removal batches.

## Starting State

```text
sys.boot_completed=1
persist.sys.safemode=
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
user-0 packages: 154
disabled packages: 0
outside A90 allowlist: 77
```

Known-bad pass4 set retained:

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

## Batch 1: Wi-Fi / Tethering Optional Resources

Log:

```text
/tmp/s22_extra_debloat_batch1_20260706T142552Z.log
processed: 14
success: 14
failure: 0
```

Removed:

```text
com.android.pacprocessor
com.android.wifi.dialog
com.google.android.networkstack.tethering
com.google.android.networkstack.tethering.overlay
com.samsung.android.networkstack.tethering.overlay
com.samsung.android.wifi.ai
com.samsung.android.wifi.decrease.scan.interval.resources
com.samsung.android.wifi.h2e.resources
com.samsung.android.wifi.increase.scan.interval.resources
com.samsung.android.wifi.p2paware.resources
com.samsung.android.wifi.resources.wifilock
com.samsung.android.wifi.softapdun.resources
com.samsung.android.wifi.softapsixghz.resources
com.samsung.android.wifi.softapwpathree.resources
```

Reboot validation:

```text
boot_completed_after=4s
sys.boot_completed=1
persist.sys.safemode=
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
user-0 packages: 140
disabled packages: 0
wifi status command: Wi-Fi enabled, not connected
```

## Batch 2: Resource / Overlay / Misc Optional Packages

Log:

```text
/tmp/s22_extra_debloat_batch2_20260706T142658Z.log
processed: 13
success: 13
failure: 0
```

Removed:

```text
android.auto_generated_rro_product__
com.android.credentialmanager
com.google.android.appsearch.apk
com.google.android.overlay.gmsconfig.common
com.google.android.overlay.modules.captiveportallogin.forframework
com.google.android.overlay.modules.cellbroadcastreceiver
com.google.android.overlay.modules.cellbroadcastservice
com.google.android.overlay.modules.documentsui
com.google.android.overlay.modules.ext.services
com.google.android.overlay.modules.modulemetadata.forframework
com.google.android.server.deviceconfig.resources
com.qti.snapdragon.qdcm_ff
com.samsung.android.uwb.resources.mccmncregulation
```

Reboot validation:

```text
boot_completed_after=6s
sys.boot_completed=1
persist.sys.safemode=
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
user-0 packages: 127
disabled packages: 0
```

## Batch 3: Policy / Misc Services

Log:

```text
/tmp/s22_extra_debloat_batch3_20260706T142842Z.log
processed: 5
success: 5
failure: 0
```

Removed:

```text
com.android.intentresolver
com.android.ons
com.android.rkpdapp
com.samsung.android.scpm
com.samsung.android.sdm.config
```

Reboot validation:

```text
boot_completed_after=3s
sys.boot_completed=1
persist.sys.safemode=
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
user-0 packages: 122
disabled packages: 0
```

## Batch 4: Navigation Overlay Packages

Log:

```text
/tmp/s22_extra_debloat_batch4_20260706T143030Z.log
processed: 6
success: 6
failure: 0
```

Removed:

```text
com.android.internal.systemui.navbar.gestural
com.android.internal.systemui.navbar.threebutton
com.android.internal.systemui.navbar.transparent
com.samsung.internal.systemui.navbar.gestural_no_hint
com.samsung.internal.systemui.navbar.sec_gestural
com.samsung.internal.systemui.navbar.sec_gestural_no_hint
```

Reboot validation:

```text
boot_completed_after=5s
sys.boot_completed=1
persist.sys.safemode=
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
user-0 packages: 116
disabled packages: 0
screencap: /tmp/s22_batch4_screen.png captured successfully
```

The lock screen rendered after the reboot.

## Batch 5: Stubborn Package Retry

Log:

```text
/tmp/s22_extra_debloat_batch5_20260706T143155Z.log
processed: 2
success: 2
failure: 0
```

Attempted:

```text
com.samsung.android.game.gos
com.sec.android.sdhms
```

Immediate result:

```text
user-0 packages: 115
com.samsung.android.game.gos: still present
com.sec.android.sdhms: missing immediately
root: OK
```

Reboot result:

```text
boot_completed_after=5s
sys.boot_completed=1
persist.sys.safemode=
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
user-0 packages: 116
com.samsung.android.game.gos: present
com.sec.android.sdhms: present
```

Interpretation:
- `SDHMS` still restores across reboot.
- `GOS` still remains present.
- This retry did not produce a persistent package-count reduction.

## Final State

```text
sys.boot_completed=1
build=S906NKSS7FYG8
persist.sys.safemode=
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
user-0 packages: 116
disabled packages: 0
outside A90 allowlist: 40
known-bad pass4 packages still installed: 13
```

Core package check passed for:

```text
com.android.settings
com.sec.android.app.launcher
com.android.systemui
com.google.android.gms
com.android.vending
com.google.android.webview
com.google.android.gsf
com.google.android.packageinstaller
com.google.android.permissioncontroller
com.google.android.networkstack
com.samsung.android.networkstack
com.android.phone
com.android.server.telecom
com.sec.imsservice
com.android.providers.telephony
com.topjohnwu.magisk
```

Remaining outside the A90 allowlist:

```text
com.android.bluetooth
com.android.cameraextensions
com.android.mtp
com.android.phone.auto_generated_characteristics_rro
com.android.providers.telephony.auto_generated_characteristics_rro
com.android.uwb.resources
com.android.vending
com.google.android.connectivity.resources
com.google.android.documentsui
com.google.android.gms
com.google.android.gsf
com.google.android.providers.media.module
com.google.android.sdksandbox
com.knox.vpn.proxyhandler
com.osp.app.signin
com.qualcomm.location
com.qualcomm.qti.gpudrivers.taro.api31
com.qualcomm.qti.services.systemhelper
com.samsung.advp.imssettings
com.samsung.android.app.telephonyui.esimclient
com.samsung.android.game.gos
com.samsung.android.kmxservice
com.samsung.android.knox.app.networkfilter
com.samsung.android.knox.er
com.samsung.android.knox.kfbp
com.samsung.android.knox.knnr
com.samsung.android.knox.sandbox
com.samsung.android.mdm
com.samsung.android.nfc.resources.korea
com.samsung.android.providers.factory
com.samsung.android.rampart
com.samsung.android.ssiframework
com.samsung.android.themecenter
com.samsung.android.wallpaper.res
com.samsung.ipservice
com.sec.android.sdhms
com.sec.enterprise.knox.cloudmdm.smdms
com.skms.android.agent
com.skp.seio
com.skt.prod.dialer
```

## Result

The device is now at a new reboot-validated `116` package boundary.

The remaining packages are mostly:
- known-bad pass4 packages,
- Google Store/Play services packages that restore across reboot,
- protected Knox/Samsung packages,
- phone/IMS/media/connectivity packages that are higher risk to remove,
- GPU/Qualcomm support packages.

Further reduction should use one-package or two-package probes only, with reboot
validation after each probe.
