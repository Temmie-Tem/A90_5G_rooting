# S22+ Magisk Boot-Time Capture M1 Preflight - 2026-07-07

## Scope

Prepare a temporary Android-side Magisk boot-time capture capsule for the S22+
native-init observability pivot. This unit adds the guard helper and
authorization only; no live reboot, remote script installation, `/data` write,
or log collection was performed by this report.

Goal: improve on the post-boot snapshot by capturing earlier rooted Android
state from Magisk `post-fs-data.d` and `service.d` hooks.

## Boundary

Allowed in the upcoming live run:

- verify rooted `SM-S906N` / `g0q` / `S906NKSS7FYG8` Android;
- temporarily stage two scripts under `/data/local/tmp`;
- install exactly:
  - `/data/adb/post-fs-data.d/s22plus_boot_capture_m1.sh`
  - `/data/adb/service.d/s22plus_boot_capture_m1.sh`
- reboot Android normally;
- let the scripts write bounded text logs under
  `/data/adb/s22plus_boot_capture_m1/`;
- pull logs into `workspace/private/runs/`;
- delete the two hook scripts, staging files, and remote log directory.

Not allowed:

- Odin, partition write, boot/recovery/vbmeta flash;
- Magisk module installation;
- module load/unload;
- sysfs/configfs writes;
- service mutation;
- `multidisabler`, format-data, wipe, or any destructive `/data` action.

## Authorization Update

`AGENTS.md` now has a narrow 2026-07-07 S22+ Magisk boot-time capture M1
exception. It is data-only and scoped to the checked helper:

```text
workspace/public/src/scripts/revalidation/s22plus_magisk_boot_time_capture_m1.py
```

## Helper Behavior

The live helper:

1. verifies one rooted Android S22+ target;
2. generates deterministic `post-fs-data` and `service.d` scripts;
3. pushes them through `/data/local/tmp`;
4. copies them into `/data/adb/post-fs-data.d` and `/data/adb/service.d` with
   `0700` permissions;
5. reboots Android;
6. waits for Android and Magisk root to return;
7. pulls `/data/adb/s22plus_boot_capture_m1`;
8. cleans remote scripts, staging files, and remote logs.

The hook scripts read:

- identity props and boot status;
- `/proc/modules`;
- `modules.load`, `modules.dep`, and `modules.alias`;
- USB gadget/configfs tree and selected function values;
- network state;
- DRM/display/backlight state;
- pstore listing;
- dmesg key lines and full dmesg.

## Dry-Run Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_magisk_boot_time_capture_m1.py

python3 workspace/public/src/scripts/revalidation/s22plus_magisk_boot_time_capture_m1.py \
  --dry-run
```

Result:

```text
dry-run ok: rooted target verified
post_script_sha256=129472e86ae164181e82ad896e9b98d59a8f4251c4beffea7892ac9ef94f8645
service_script_sha256=d4497f881601c8775c7d4f798be0eca782b12ca81f0981f94a9d2ba8a82e7646
```

Private dry-run log:

```text
workspace/private/runs/s22plus_magisk_boot_time_capture_m1_20260706T173153Z/s22plus_magisk_boot_time_capture_m1.txt
```

## Next Live Command

```text
python3 workspace/public/src/scripts/revalidation/s22plus_magisk_boot_time_capture_m1.py \
  --live-run \
  --ack S22PLUS-MAGISK-BOOT-CAPTURE-M1
```

Expected result: Android reboots once, root returns, two stage logs are pulled
into a private run directory, and the remote capsule is removed.
