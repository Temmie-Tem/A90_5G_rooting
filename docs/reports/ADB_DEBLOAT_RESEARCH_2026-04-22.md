# ADB Debloat Research (2026-04-22)

Target device: `SM-A908N`
Build: `A908NKSU5EWA3` / Android 12 / One UI 4.x

Goal:
- Keep the device stable for boot, USB debugging, Wi-Fi, remote/server-like use.
- Distinguish between packages that are safe to remove, safer to only disable, and risky to touch.

Method:
- Local package inventory from `adb shell pm list packages`
- Official Android documentation for provisioning, permissions, network stack, and document handling
- Official Samsung support/Knox documentation for Samsung-specific features
- Package-name-based inference only when no primary source clearly maps the package name

Important:
- `KG STATE: Prenormal` is currently relevant on this device, so packages related to device lock/security/compliance are treated conservatively.
- "Safe to remove" below means "not needed for boot/basic server use", not "no user-visible feature loss."

## 1. Keep: core boot, setup, permission, network, and control plane

These should be treated as non-removable for your current goal.

### Provisioning / setup / UI

- `com.google.android.setupwizard`
- `com.sec.android.app.SecSetupWizard`
- `com.sec.android.app.setupwizardlegalprovider`
- `com.android.systemui`
- `com.sec.android.app.launcher`
- `com.android.settings`
- `com.android.settings.intelligence`

Reason:
- Android provisioning state depends on Setup Wizard and provisioning flags.
- Your device has already shown Setup Wizard breakage before.

Sources:
- AOSP Setup Wizard helper checks `DEVICE_PROVISIONED` and `USER_SETUP_COMPLETE`.
- AOSP Provision app sets those values and disables itself when setup is completed.

### Permission / install / file access

- `com.google.android.permissioncontroller`
- `com.google.android.packageinstaller`
- `com.google.android.documentsui`

Reason:
- PermissionController is an Android Mainline module that handles runtime permission UI, logic, and roles.
- DocumentsUI controls document/file access flows for components that use document permissions.

Sources:
- AOSP PermissionController module docs
- AOSP DocumentsUI module docs

### Telephony / connectivity / Wi-Fi

- `com.android.phone`
- `com.android.server.telecom`
- `com.android.providers.telephony`
- `com.android.carrierconfig`
- `com.google.android.networkstack`
- `com.google.android.networkstack.permissionconfig`
- `com.google.android.captiveportallogin`
- `com.android.networkstack.tethering.inprocess`
- `com.samsung.android.networkstack`
- `com.samsung.android.networkstack.tethering.overlay`
- `com.samsung.android.networkstack.tethering.inprocess.overlay`
- `com.android.wifi.resources`
- `com.samsung.android.wifi.resources`
- `com.samsung.android.wifi.softap.resources`

Reason:
- Network Stack is a Mainline module for IP provisioning and captive portal handling.
- These packages directly affect Wi-Fi, DHCP, and connectivity behavior.

Sources:
- AOSP Network Stack module docs

### Security / lock state / compliance

- `com.samsung.android.kgclient`
- `com.samsung.android.knox.attestation`
- `com.samsung.android.sm.devicesecurity`
- `com.samsung.android.fmm`
- `com.samsung.klmsagent`
- `com.sec.enterprise.knox.cloudmdm.smdms`
- `com.samsung.knox.securefolder`

Reason:
- `kgclient` is strongly associated with Knox Guard state on Samsung devices.
- Knox Guard officially restricts binary flashing and other capabilities on locked devices.
- `Find My Mobile` is an official Samsung security and remote recovery feature.
- `Secure Folder` is a Knox-backed isolation feature.

Sources:
- Samsung Knox Guard admin docs
- Samsung Find My Mobile support docs
- Samsung Secure Folder support docs

## 2. High-confidence removable for server-only use

These are not required for boot/basic remote operation. For a server-like phone, they are reasonable removal or disable targets.

### Bixby family

- `com.samsung.android.app.settings.bixby`
- `com.samsung.android.bixby.agent`
- `com.samsung.android.bixby.service`
- `com.samsung.android.bixby.wakeup`
- `com.samsung.android.bixbyvision.framework`
- `com.samsung.systemui.bixby2`

Reason:
- Samsung documents Bixby as assistant/voice/vision/routine features, not a boot requirement.

### Games / AR / stickers / themes / store

- `com.samsung.android.game.gamehome`
- `com.samsung.android.game.gametools`
- `com.samsung.android.game.gos`
- `com.samsung.gamedriver.sm8150`
- `com.samsung.android.aremoji`
- `com.samsung.android.ardrawing`
- `com.samsung.android.arzone`
- `com.samsung.android.livestickers`
- `com.samsung.android.stickercenter`
- `com.samsung.android.app.dressroom`
- `com.samsung.android.app.dofviewer`
- `com.sec.android.app.samsungapps`
- `com.samsung.android.themestore`
- `com.samsung.android.themecenter`

Reason:
- User-facing enhancement features only.
- Not part of Android provisioning, connectivity, or remote administration.

### Sharing / ecosystem / DeX / companion features

- `com.samsung.android.app.sharelive`
- `com.samsung.android.app.simplesharing`
- `com.samsung.android.privateshare`
- `com.samsung.android.allshare.service.fileshare`
- `com.samsung.android.allshare.service.mediashare`
- `com.samsung.android.smartmirroring`
- `com.sec.android.app.dexonpc`
- `com.samsung.android.mdecservice`
- `com.samsung.android.mdx`
- `com.samsung.android.mdx.kit`
- `com.samsung.android.mdx.quickboard`
- `com.samsung.android.app.watchmanagerstub`

Reason:
- Samsung support material maps these to file sharing, mirroring, PC/Desktop integration, or companion-device workflows.
- Not needed for headless/server use.

### Samsung account convenience / cloud / autofill

- `com.samsung.android.samsungpass`
- `com.samsung.android.samsungpassautofill`
- `com.samsung.android.scloud`

Reason:
- Samsung Pass is biometric login/autofill.
- Samsung Cloud is sync/backup.
- Useful to users, not required for a server-like target.

### Miscellaneous user features

- `com.samsung.android.app.tips`
- `com.samsung.android.forest`
- `com.samsung.android.app.reminder`
- `com.samsung.android.app.routines`
- `com.samsung.android.app.aodservice`
- `com.samsung.android.app.soundpicker`
- `com.samsung.android.secsoundpicker`
- `com.samsung.android.setting.multisound`
- `com.samsung.android.smartsuggestions`
- `com.samsung.android.aircommandmanager`
- `com.samsung.android.kidsinstaller`

Reason:
- Samsung documents AOD, Modes and Routines, and similar items as optional UX features.
- Not tied to boot completion or network bring-up.

### Google consumer apps

- `com.google.android.youtube`
- `com.google.android.gm`
- `com.google.android.apps.maps`
- `com.google.android.apps.tachyon`
- `com.google.android.projection.gearhead`

Reason:
- Consumer apps only; not system-critical for your target use case.

## 3. Safer to disable first, not permanently remove first

These can often be disabled safely, but removing them is more likely to create rough edges or future maintenance problems.

### File and media management

- `com.sec.android.app.myfiles`
- `com.sec.android.gallery3d`
- `com.sec.android.app.clockpackage`

Reason:
- Samsung support documents these as user apps, so they are not boot-critical.
- However, they are still the default local file browser, media viewer, and alarm/clock stack.
- For a server device, removal is possible, but disable or staged removal is safer.

### Google support modules and optional adjuncts

- `com.google.android.tts`
- `com.google.android.apps.carrier.carrierwifi`
- `com.google.android.gms.location.history`
- `com.google.android.apps.restore`
- `com.google.android.apps.turbo`
- `com.google.android.feedback`
- `com.microsoft.appmanager`

Reason:
- These look optional for basic server use, but some participate in restore, Wi-Fi offload/carrier integration, voice features, or vendor support.
- Best handled by disable-first testing.

### Samsung migration and onboarding helpers

- `com.samsung.android.easysetup`
- `com.samsung.android.smartswitchassistant`
- `com.sec.android.easyMover.Agent`

Reason:
- Samsung documents Smart Switch as a migration tool, not a runtime necessity.
- Still, some onboarding/update flows may reference these packages.
- Disable first; remove only after longer observation.

### Edge and secondary UI surfaces

- `com.samsung.android.app.appsedge`
- `com.samsung.android.app.clipboardedge`
- `com.samsung.android.app.cocktailbarservice`
- `com.samsung.android.app.taskedge`
- `com.samsung.android.service.peoplestripe`
- `com.sec.android.emergencylauncher`

Reason:
- These are not needed for server use.
- However, `Emergency Launcher` affects fallback UI in emergency situations, so treat it as optional rather than "always remove."

## 4. Keep unless you deliberately give up the related safety feature

These are not boot-critical in the narrow sense, but deleting them gives up useful recovery or security behavior.

- `com.samsung.android.fmm`
  Keep if you want Find My Mobile / remote location/lock features.
- `com.samsung.knox.securefolder`
  Keep if you want Knox-isolated storage/apps.
- `com.sec.android.emergencymode.service`
- `com.sec.android.provider.emergencymode`
  Keep if emergency mode matters.

## 5. Current recommendation for your device

### Good candidates to keep removed/disabled

These already align with the research and are low-risk for your current goal:

- Bixby packages
- AR/sticker/game/theme/store packages
- Samsung Pass / Samsung Cloud
- Samsung DeX / MDE / sharing packages
- Reminder / Routines / Tips / AOD / Smart Suggestions
- YouTube / Gmail / Maps / Meet / Android Auto / Samsung Calendar / Samsung Video / FM / QR Reader

### Do not touch further right now

- SetupWizard / SystemUI / Launcher
- PermissionController / PackageInstaller / DocumentsUI
- Phone / Telecom / Telephony / Network Stack / Captive Portal Login
- `kgclient`, Knox Guard/attestation-related packages
- `fmm`

### If you want to continue trimming

Proceed in this order:

1. Disable first:
   - `com.sec.android.app.myfiles`
   - `com.sec.android.gallery3d`
   - `com.sec.android.app.clockpackage`
   - `com.google.android.tts`
   - `com.google.android.apps.carrier.carrierwifi`
   - `com.google.android.gms.location.history`
   - `com.samsung.android.smartswitchassistant`
   - `com.sec.android.easyMover.Agent`

2. Reboot and validate:
   - boot completion
   - Wi-Fi reconnect
   - ADB
   - Settings app
   - Downloads/file picking if you still need on-device management

3. Only then consider uninstalling for user 0.

## 6. Remaining System-App Analysis After Aggressive Debloat

State observed after the later aggressive rounds:
- Active package count: `317`
- Major remaining memory consumers are no longer consumer apps, but core services and a smaller set of Samsung/Android system apps.

### Best remaining candidates if your goal is memory reduction

These are the most meaningful remaining non-core targets by observed PSS or obvious optional function.

- `com.samsung.android.honeyboard`
  - Very large memory user
  - Remove only if you are comfortable with ADB, external keyboard, or no on-device text entry
- `com.android.bluetooth`
  - Safe if you do not need Bluetooth at all
- `com.android.nfc`
  - Safe if you do not need NFC
- `com.sec.android.desktopmode.uiservice`
  - DeX/desktop-mode related
- `com.samsung.android.net.wifi.wifiguider`
  - Samsung Wi-Fi assistance UI, not the Wi-Fi stack itself
- `com.sec.android.diagmonagent`
  - Diagnostics/telemetry style component
- `com.samsung.android.tadownloader`
  - Samsung update/download helper style component
- `com.samsung.android.dynamiclock`
  - Dynamic lock screen content
- `com.samsung.android.rubin.app`
  - Samsung personalization/continuity style component

### Good candidates if your goal is package-count reduction, not major RAM savings

These likely remove many packages with low runtime impact.

- `com.android.dreams.basic`
- `com.android.dreams.phototable`
- `com.android.egg`
- `com.android.traceur`
- `com.android.wallpaper.livepicker`
- `com.android.wallpaperbackup`
- `com.android.wallpapercropper`
- `com.android.htmlviewer`
- `com.android.bookmarkprovider`
- `com.android.providers.partnerbookmarks`
- `com.android.bips`
- `com.android.printspooler`
- `com.android.hotwordenrollment.okgoogle`
- `com.android.hotwordenrollment.xgoogle`
- Theme packs:
  - `com.android.theme.color.*`
  - `com.android.theme.icon.*`
  - `com.android.theme.icon_pack.*`
- Display cutout emulations:
  - `com.android.internal.display.cutout.emulation.*`

### Still not recommended to remove

- `com.google.android.setupwizard`
- `com.sec.android.app.SecSetupWizard`
- `com.android.systemui`
- `com.sec.android.app.launcher`
- `com.android.settings`
- `com.google.android.permissioncontroller`
- `com.google.android.packageinstaller`
- `com.google.android.documentsui`
- Telephony / IMS / Wi-Fi stack / network stack packages
- `com.samsung.android.kgclient`
- `com.samsung.android.knox.attestation`
- `com.samsung.android.fmm`

### Practical note

At this stage, "system app" is too broad to be useful.
The remaining set splits into:

1. truly core packages
2. optional runtime services with real memory cost
3. overlays/resources that mostly only reduce package count

If the next goal is:
- lower RAM: target `Honeyboard`, `Bluetooth`, `NFC`, `DesktopMode`, `WiFiGuider`, diagnostics/personalization helpers
- lower package count: target theme packs, dreams, wallpaper helpers, traceur, htmlviewer, print services

## Sources

- AOSP Provision / setup completion:
  - https://android.googlesource.com/platform/packages/apps/Provision/%2B/master/src/com/android/provision/DefaultActivity.java
  - https://android.googlesource.com/platform/frameworks/opt/setupwizard/%2B/56a1911/library/main/src/com/android/setupwizardlib/util/WizardManagerHelper.java
- AOSP Mainline modules:
  - https://source.android.com/docs/core/architecture/modular-system/permissioncontroller
  - https://source.android.com/docs/core/architecture/modular-system/networking
  - https://source.android.com/docs/core/ota/modular-system/documentsui
- Samsung Knox / security:
  - https://docs.samsungknox.com/admin/knox-guard
  - https://docs.samsungknox.com/admin/knox-guard/get-started/get-started-with-knox-guard/
- Samsung support pages:
  - Bixby: https://www.samsung.com/us/support/owners/app/Bixby
  - Bixby voice wake-up: https://www.samsung.com/us/support/answer/ANS10001415/
  - Always On Display: https://www.samsung.com/us/support/answer/ANS00062001/
  - Samsung DeX: https://www.samsung.com/us/support/answer/ANS10002880/
  - Modes and Routines: https://www.samsung.com/us/support/answer/ANS10002538/
  - Samsung Cloud: https://www.samsung.com/us/support/owners/app/samsung-cloud/
  - Smart Switch: https://www.samsung.com/us/support/answer/ANS10001345/
  - Find My Mobile: https://www.samsung.com/my/support/apps-services/what-is-find-my-mobile/
  - Secure Folder: https://www.samsung.com/us/support/answer/ANS10001401/
  - My Files: https://www.samsung.com/uk/support/mobile-devices/how-to-use-my-files/
  - Gallery: https://www.samsung.com/us/support/answer/ANS00079026/
  - Clock/Calendar: https://www.samsung.com/us/support/answer/ANS00089064/
  - Emergency mode: https://www.samsung.com/us/support/answer/ANS10001579/
