# S22+ SysDump Package Restore (2026-07-08)

## Verdict

PACKAGE-STATE FIX PASS.

The physical `*#9900#` SysDump route failed because the required Samsung
ServiceMode packages had been removed from user 0 during debloat. Restoring the
packages with Android's package manager made the SysDump / CPDebugLevel UI
visible again.

No flash, reboot, partition write, procfs/sysfs write, sysrq trigger, Odin
transfer, Magisk module install, or native-init candidate action was performed.
This was a user-0 package-manager state correction only.

## Root Cause

The dialer and telephony path were still alive:

```text
default dialer role holder: com.samsung.android.dialer
DIAL intent resolves to:   com.samsung.android.dialer/.DialtactsActivity
telephony packages alive:  com.android.phone, com.sec.phone,
                           com.samsung.android.app.telephonyui,
                           com.skt.prod.dialer
```

The missing part was the Samsung ServiceMode stack:

```text
com.sec.android.app.servicemodeapp  installed=false for user 0
com.sec.android.RilServiceModeApp   installed=false for user 0
com.sec.android.app.parser          installed=false for user 0
```

Those packages were present as system APKs, so they could be restored without
reflashing:

```text
/system/priv-app/serviceModeApp_FB/serviceModeApp_FB.apk
/system/priv-app/ModemServiceMode/ModemServiceMode.apk
/system/app/DRParser/DRParser.apk
```

## Action

Commands run:

```bash
adb shell 'cmd package install-existing --user 0 com.sec.android.app.servicemodeapp'
adb shell 'cmd package install-existing --user 0 com.sec.android.RilServiceModeApp'
adb shell 'cmd package install-existing --user 0 com.sec.android.app.parser'
```

Results:

```text
Package com.sec.android.app.servicemodeapp installed for user: 0
Package com.sec.android.RilServiceModeApp installed for user: 0
Package com.sec.android.app.parser installed for user: 0
```

## Live Verification

Current package state:

```text
user-0 package count: 119

com.sec.android.app.servicemodeapp
  codePath=/system/priv-app/serviceModeApp_FB
  appId=1000 / sharedUser=android.uid.system
  User 0: installed=true hidden=false stopped=false notLaunched=false enabled=0

com.sec.android.RilServiceModeApp
  codePath=/system/priv-app/ModemServiceMode
  appId=1001 / sharedUser=android.uid.phone
  User 0: installed=true hidden=false stopped=true notLaunched=true enabled=0

com.sec.android.app.parser
  codePath=/system/app/DRParser
  appId=1000 / sharedUser=android.uid.system
  User 0: installed=true hidden=false stopped=false notLaunched=false enabled=0
```

Operator observation:

```text
physical dialer *#9900# now opens the Samsung SysDump / CPDebugLevel UI
```

ADB window/activity state agreed with the visible UI:

```text
visible task:   com.sec.android.app.servicemodeapp
focused window: com.sec.android.app.servicemodeapp/.CPDebugLevel
SysDump window: com.sec.android.app.servicemodeapp/.SysDump
```

A follow-up read-only sec_debug probe passed after the UI appeared:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_mid_sysrq_gate.py \
  --read-only-probe
```

Private run, not committed:

```text
workspace/private/runs/s22plus_sec_debug_mid_sysrq_20260707T210024Z
```

Public result:

```text
mode                  read-only-probe
writes_performed      false
reboots_performed     false
flashes_performed     false
sysrq_triggered       false
debug_level decimal   20300
debug_level hex       0x4f4c
debug_level ascii_le  LO
likely_low_code       true
```

## Interpretation

The earlier negative ADB route probe remains valid: shell/root cannot directly
open SysDump on this build. The practical route is the physical dialer code
`*#9900#`, and that route requires the three ServiceMode/DRParser packages above
to be installed for user 0.

The panic gate remains parked because `debug_level` still decodes as LOW after
the package restore. The next action is operator-side UI selection of DEBUG
LEVEL MID if available, followed by another `--read-only-probe`. Do not run the
intentional sysrq panic path while the decoded value is still LOW.

## Follow-Up State

Added the package overlay:

```text
docs/plans/S22PLUS_ANDROID_DEBUG_CHANNEL_REQUIRED_PACKAGES_2026-07-08.txt
```

Use it on top of the historical 116-package Android checkpoint while the S22+
observability path depends on Samsung SysDump, ServiceMode, or sec_debug MID.
