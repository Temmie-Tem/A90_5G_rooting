# NATIVE_INIT V2510 — audio ACDB exec-linked own-process init_v3 block live

## Decision

`v2510-exec-linked-helper-reaches-init-v3-ret-minus-19-rollback-pass`

V2510 reran the V2508 exec-linked own-process ACDB GET helper through the checked
Android handoff, this time with `--from-native`.  The Android handoff completed,
the helper and ACDB dependency closure were staged, the helper executed, and V2321
rollback completed with final `selftest fail=0`.

The helper did **not** reach any `acdb_ioctl()` GET call.  It stopped at:

```json
{"event":"error","stage":"acdb_loader_init_v3","code":-19,"pid":3804,"tid":3804}
```

No raw ACDB payload was generated.

## Run metadata

Private run directory:

- `workspace/private/runs/audio/v2490-acdb-ownprocess-get-20260616-033836/`

Helper:

- `workspace/private/builds/audio/v2508-acdb-ownprocess-exec-linked-host-only/bin/a90_acdb_ownprocess_get_exec_linked_v2508`
- SHA256: `73c2ab686e2462e59c09c27b2f0e0d3ce8d84c2a3a814b0f787c3faba6bc1bda`
- staged remote name: `/data/local/tmp/a90-acdb-ownget/a90_acdb_ownprocess_get_v2489`

Runner identity still reports `V2490` because it is the inherited own-process
live runner.  This report records the operational iteration as V2510.

## What passed

The V2509 handoff invocation miss was corrected:

- `flash_android` included `--from-native`;
- Android boot and Magisk `su` root settle passed;
- remote setup under `/data/local/tmp/a90-acdb-ownget` passed;
- V2506 dependency closure pushed successfully:
  - `libaudcal.so`
  - `libdiag.so`
  - `libacdb-fts.so`
  - `libacdbrtac.so`
  - `libadiertac.so`
  - `libacdbloader.so`
- helper SHA on device matched the V2508 SHA;
- helper executed and returned rc file value `29`;
- artifact pull and cleanup passed;
- Android reboot-to-recovery and checked V2321 rollback passed.

Final health after rollback:

```text
A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)
selftest: pass=11 warn=1 fail=0
```

## ACDB result

Summary:

| Field | Value |
|---|---|
| classification | `init-v3-block` |
| helper rc file | `29` |
| error stage | `acdb_loader_init_v3` |
| error code | `-19` |
| acdb_ioctl rows | `0` |
| raw files | `0` |
| target 4916 count | `0` |
| rollback | passed to V2321 |

This is useful evidence: the exec-linked startup-load strategy moved past the
V2507 late-dlopen TLS wall and into the ACDB loader itself.  The current blocker
is now ACDB database initialization, not library loadability.

## Notable setup evidence

The live setup command showed `/vendor/etc/acdbdata` exists but listed only:

```text
adsp_avs_config.acdb
```

The operator RE note expects `acdb_loader_init_v3()` / `init_v4()` to discover
`.acdb` files by scanning the supplied ACDB directory.  Therefore `-19` is most
likely a path/content/environment initialization failure inside `libacdbloader`,
not a failure of the V2508 DT_NEEDED approach.

Do not infer that topology GET command IDs are wrong: none of those calls ran.

## Boundaries preserved

Preserved:

- no in-HAL injection;
- no wrapper-exec Magisk module;
- no HAL restart;
- no AudioTrack/playback;
- no native speaker write;
- no `/dev/msm_audio_cal` open/ioctl;
- no `0xC00461CB` calibration SET ioctl;
- no `acdb_ioctl()` write/replay path;
- no raw payload committed;
- checked rollback to V2321 ended with `selftest fail=0`.

## Validation

Post-run host checks:

```text
python3 workspace/public/src/scripts/revalidation/a90ctl.py --timeout 8 version
python3 workspace/public/src/scripts/revalidation/a90ctl.py --timeout 8 selftest
```

Both passed against V2321.

## Next unit

The next unit should be host-only first:

1. RE `libacdbloader.so` return path for `acdb_loader_init_v3()` / `init_v4()`
   returning `-19`.
2. Confirm whether the live Android-good ACDB path uses a different ACDB root,
   subdirectory, delta path, metadata path, or system property than
   `/vendor/etc/acdbdata`.
3. Inventory Android live ACDB file layout recursively under likely roots, but
   keep files private and commit only metadata.
4. Only then build the next helper variant, if needed, with a corrected ACDB path
   or required environment preflight.

Do not rerun the same helper unchanged.  The current blocker is deterministic
and inside `acdb_loader_init_v3`.
