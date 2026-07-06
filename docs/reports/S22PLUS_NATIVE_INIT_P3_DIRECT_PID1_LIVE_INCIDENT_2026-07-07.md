# S22+ Native-Init P3 Direct PID1 Live Incident

Date: 2026-07-07 KST

Target:
- Samsung Galaxy S22+ `SM-S906N` / `g0q`
- Build: `S906NKSS7FYG8`

## Scope

This was the first live transfer of the P3 direct native-init PID1 candidate
documented in:

```text
docs/reports/S22PLUS_NATIVE_INIT_P3_DIRECT_PID1_HOST_BUILD_2026-07-07.md
```

The live action used the SHA-pinned `AGENTS.md` P3 exception and wrote only the
boot AP member:

```text
candidate AP.tar.md5:
21838b4e64656cead9804f9034ed554bf6737a9666d07001d30ec66c01364d8b

candidate padded boot.img:
bb803901048a089b956d7657ed45496de7416a90c0a35872784b537d7167f2cb

AP member:
boot.img.lz4
```

Rollback prerequisites were present before live transfer:

```text
stock boot-only rollback AP.tar.md5:
1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e

full stock FYG8 firmware:
f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8
```

## Pre-Flash State

ADB reported a booted Android userspace before the P3 transfer:

```text
sys.boot_completed=1
ro.product.model=SM-S906N
ro.product.device=g0q
ro.boot.bootloader=S906NKSS7FYG8
ro.build.version.incremental=S906NKSS7FYG8
ro.boot.verifiedbootstate=orange
```

## Odin Transfer

Odin4 detected a Samsung download-mode endpoint and accepted the boot-only AP.

Transcript summary:

```text
Reboot into normal mode
Check file : workspace/private/outputs/s22plus_native_init/direct_p3_v0_1/odin4/AP.tar.md5
Setup Connection
initializeConnection
Receive PIT Info
success getpit
Upload Binaries
boot.img.lz4
100%
Close Connection
```

No non-boot Odin slot was supplied.

## Expected Result

P3 direct `/init` was expected to:

1. run as PID1,
2. emit `S22_NATIVE_INIT_DIRECT_P3` to `kmsg`,
3. dwell for approximately 15 seconds,
4. reboot to recovery,
5. allow TWRP `/proc/last_kmsg` collection,
6. then permit stock boot-only rollback.

## Observed Result

After Odin transfer, the host observed no USB recovery/device/download transport:

```text
ADB post-flash poll: no device rows for 90 seconds
Odin post-timeout list: no download-mode endpoint
lsusb post-timeout: no Samsung USB device visible
fixed ADB/Odin poll: no endpoint for 180 additional seconds
final ADB: no device rows
final Odin: no download-mode endpoint
final lsusb: no Samsung USB device visible
```

No `S22_NATIVE_INIT_DIRECT_P3` marker was collectable because recovery never
became available to the host.

Continuation check after the next operator turn:

```text
ADB: no device rows
Odin4 -l: no download-mode endpoint
lsusb: no Samsung USB device visible
additional fixed ADB/Odin poll: no endpoint for 60 seconds
```

The operator later reported the panel was in stock/general recovery rather than
TWRP. Host ADB saw a recovery-like endpoint, but it was unauthorized, matching
stock recovery behavior:

```text
ADB state: unauthorized
Odin: no download-mode endpoint at that moment
```

Because stock recovery ADB was unauthorized, the host could not collect
`/proc/last_kmsg`, pstore, or issue `adb reboot download` from recovery.

## Classification

FAIL: P3 live first-light was not proven.

The transfer itself succeeded, but the device did not return through the planned
automatic recovery observation path and did not expose ADB/Odin USB transport to
the host afterward.

Most likely current state:

- direct PID1 did not reach or complete the recovery reboot path, or
- recovery booted without host-visible USB, or
- the device is stuck/off/black-screen before USB gadget enumeration.

This incident does not prove that `/init` did not execute; it proves only that
the P3 proof marker was not collectable through the planned recovery path.

## Recovery Action

The operator physically entered download mode. Odin4 detected one Samsung
download-mode endpoint, so the P3 collect-and-rollback helper performed the
pinned stock boot-only rollback.

Rollback AP:

```text
workspace/private/outputs/s22plus_native_init/odin4_stock_rollback_short/AP.tar.md5
sha256: 1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

Helper:

```text
python3 workspace/public/src/scripts/revalidation/s22plus_p3_collect_and_rollback.py \
  --live \
  --ack S22PLUS-P3-COLLECT-AND-ROLLBACK
```

Result:

```text
rollback odin rc=0
android_boot_completed=1
```

Post-rollback Android validation:

```text
sys.boot_completed=1
ro.product.model=SM-S906N
ro.product.device=g0q
ro.product.name=g0qksx
ro.boot.bootloader=S906NKSS7FYG8
ro.build.version.incremental=S906NKSS7FYG8
ro.boot.verifiedbootstate=orange
ro.boot.boot_recovery=0
persist.sys.safemode=<empty>
shell uid=2000 context=u:r:shell:s0
su=NO_SU
```

Post-rollback forensic read attempts from stock Android shell:

```text
/proc/last_kmsg: not readable or absent
/sys/fs/pstore: Permission denied
/dev/block/by-name/boot: points to /dev/block/sda25
sha256sum /dev/block/by-name/boot: Permission denied
```

Interpretation: the device is recovered to booting stock-boot Android, but P3
first-light proof remains unavailable because the only recovery state reached
before rollback was stock/general recovery with unauthorized ADB, and stock
Android has no root after the stock boot rollback.

## Helper Added After The Incident

```text
workspace/public/src/scripts/revalidation/s22plus_p3_collect_and_rollback.py
```

Validation:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_p3_collect_and_rollback.py \
  workspace/public/src/scripts/revalidation/s22plus_p2_stock_boot_rollback_guard.py

python3 workspace/public/src/scripts/revalidation/s22plus_p3_collect_and_rollback.py --wait-sec 1
```

Dry-run result with no current host transport:

```text
no ADB/Odin transport visible; no action taken
rc=2
```

If recovery or Android ADB becomes visible, the helper collects selected
properties, `/proc/last_kmsg`, `/sys/fs/pstore`, and boot-surface hashes before
rebooting to download mode and delegating the pinned stock boot rollback to the
existing guarded rollback helper. If Odin download mode is already visible, it
delegates directly to the same pinned stock boot rollback helper.

## Stop Condition

The run is stopped before any additional candidate flash. Rollback is complete,
Android boots again, and P3 first-light remains unproven. The next S22+
native-init step must be host-only until a new deterministic boot artifact and a
new SHA-pinned `AGENTS.md` exception exist.
