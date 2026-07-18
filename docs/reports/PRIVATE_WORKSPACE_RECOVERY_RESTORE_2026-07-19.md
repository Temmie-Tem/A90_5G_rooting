# Private Workspace Recovery Restore

Date: 2026-07-19 KST

Scope: host-only restoration and validation of ignored `workspace/private`
data after the exact Git history was restored under `android-native-init-lab`.
No device was contacted, enumerated, rebooted, transferred to, or flashed.

## Source

The canonical source view was
`A90_codex_claude_private_named_recovery_20260717_v31_new_exact` from the
preserved Windows recovery volume. Its own final audit records:

- 470 exact recovered unique SHA-256 objects;
- 771 `best_available` paths;
- 771 `latest_observed` paths;
- 468 latest-observed paths without their historical exact bytes;
- 408 dispositions as deterministically rebuildable intermediates;
- 27 dispositions as downloadable replacements;
- one replaceable container;
- 41 superseded historical SHA variants; and
- 22 exact historical objects that require a new external original.

The 22-item boundary remains unresolved and was not represented as recovered.
The source audit reports that local carving and reconstruction were exhausted
for those objects.

## Restore Procedure

The restored Git checkout initially contained only the tracked private
directory skeleton. Before copying:

- the source `best_available` file count and manifest selection both equaled
  771;
- the 771 source files passed complete manifest SHA-256 verification;
- the source contained no symlinks; and
- no source file path collided with an existing checkout file.

The 771 paths were merged with `rsync --ignore-existing` and hardlink
preservation. Two additional canonical exact inputs recorded by
`additional_exact_artifacts.tsv` were independently hash-verified and merged:

- the recovered FYG8 `vendor_ramdisk00` input; and
- the deterministic post-overwrite `a90_usbnet` helper reconstruction.

The separate 1,149,446,245-byte exact M34 recovery archive has no canonical
workspace path. It remains preserved on the recovery volume and was not
duplicated into the active checkout.

All 773 restored canonical files passed SHA-256 verification from their final
checkout paths. NTFS projected all recovered files as mode `0755`, so the
active private tree was normalized to user-only access: directories `0700`,
data files `0600`, and ELF/shebang executables `0700`. Content hashes were
unchanged.

The final recovery reports, disposition ledger, manifest, summary, and exact
reconstruction provenance were copied to the ignored local path
`workspace/private/recovery/2026-07-18-final/` with user-only permissions.

## Frontier Readiness

The active R4W1-B design needs the historical M4T2 carrier to be exactly
reproducible rather than permanently stored as a promoted candidate. The
checked M4T2 builder was rerun from the restored checkout and recovered private
inputs. It reproduced:

- raw `/init` SHA-256
  `b8371e3ac671ff71e9be752b8ff1087a4f20811c871a43ca8e698eee47783d12`;
- raw boot SHA-256
  `8103bce76fb3e41d71b64735a64d2f2f29431a44ea1c9a85dc0bc151d71afd15`;
- `boot.img.lz4` SHA-256
  `8db75e0cce8a8bea69c05e7747f4690fed19e51ddbc0f81dc06e1f4621be6265`;
- AP tar SHA-256
  `c07bd72a5f84af41ca7fa5006120d357f25a0a51a9eefa806b7030a79e69086f`;
  and
- `AP.tar.md5` SHA-256
  `66d7f24b348702f58efbe1945b0d2751052ed27f6ce1f6fc4e5da63f3a585b24`.

The no-change Magisk base repack was byte-identical. The restored stock FYG8
`vendor_boot`, known Magisk boot, and MagiskBoot matched their pinned hashes.
The pinned Odin4 binary was found outside the repository and matched SHA-256
`6754aa54f2abe6e99ece32414cd34c8b23b28dbddde537a33203036813637c3b`.

The reproduction output remained under `/tmp`; only its metadata was retained
under the ignored private recovery validation directory. It is not a promoted
R4W1-B candidate and creates no live authorization.

## Result

The active checkout now contains every canonical private file available in the
final recovery view plus both additional exact canonical inputs. The known
22-object external-original boundary remains explicit. Current R4W1-B host
work can resume from exact reproduced carrier and required-input identities.

Verdict:

`PASS_PRIVATE_WORKSPACE_RECOVERY_RESTORED_AND_R4W1B_CARRIER_REPRODUCED_HOST_ONLY`
