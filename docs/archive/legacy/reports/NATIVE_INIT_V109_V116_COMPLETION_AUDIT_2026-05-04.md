# Native Init v109-v116 Completion Audit

Date: `2026-05-04`
Scope: v109 through v116 implementation cycle
Latest verified build: `A90 Linux init 0.9.16 (v116)`
Latest commit at audit start: `7da255a Add v116 diagnostics bundle`

## Summary

The v109-v116 implementation cycle is complete.

This audit did not create a new boot image or build tag. It verifies that the v109-v116 roadmap completion criteria are covered by actual commits, reports, latest-version documentation, local artifacts, and live device version evidence.

Next work should open a new cycle from the v116 baseline, starting with v117 planning.

## Roadmap Criteria

The roadmap completion criteria were:

1. Latest verified build reaches `A90 Linux init 0.9.16 (v116)`.
2. README, project status, versioning, task queue, and next-work docs point to v116.
3. Every version v109-v116 has a report and commit.
4. Real-device flash validation is recorded for every boot image version unless explicitly documentation-only.
5. Physical/manual-only validation gaps are explicitly recorded, not implied as complete.

## Audit Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Latest verified build is v116 | `README.md`, `docs/README.md`, `docs/overview/PROJECT_STATUS.md`, `docs/overview/VERSIONING.md`, and task queue all reference `A90 Linux init 0.9.16 (v116)` / `stage3/boot_linux_v116.img` | PASS |
| Device is currently v116 | `python3 scripts/revalidation/a90ctl.py version` returned `A90 Linux init 0.9.16 (v116)` with `rc=0/status=ok` | PASS |
| v116 source exists | `stage3/linux_init/init_v116.c` and `stage3/linux_init/v116/` exist | PASS |
| v116 artifacts exist | `stage3/linux_init/init_v116`, `stage3/ramdisk_v116.cpio`, and `stage3/boot_linux_v116.img` exist locally | PASS |
| v116 report records artifact hashes | `docs/reports/NATIVE_INIT_V116_DIAG_BUNDLE_2026-05-04.md` includes hashes for init, ramdisk, boot image, `a90_cpustress`, and `a90_rshell` | PASS |
| v109-v116 reports exist | Reports for v109, v110, v111, v112, v113, v114, v115, and v116 exist under `docs/reports/` | PASS |
| v109-v116 commits exist | `git log` contains commits `cf7b924`, `d5c98cf`, `f453a8e`, `f9ae60e`, `efa20ed`, `4581852`, `001145a`, `7da255a` | PASS |
| Real-device flash validation recorded | Each v109-v116 report includes a flash command, boot partition prefix SHA/PASS, and post-boot `cmdv1 version/status` verification | PASS |
| Soak/regression validation recorded | v109-v110 quick soak, v111 10-cycle soak, v112 service/NCM checks, v113-v116 soak or equivalent regression checks are recorded | PASS |
| Manual/physical gaps are not hidden | Reports explicitly distinguish opt-in USB/NCM/rshell checks and rollback behavior; no unrecorded manual-only success claim was found in this cycle audit | PASS |
| Working tree clean at audit start | `git status --short` returned empty before this audit report was written | PASS |

## Version Evidence Table

| Version | Commit | Report | Key validation evidence |
|---|---|---|---|
| v109 | `cf7b924 Add v109 structure audit baseline` | `NATIVE_INIT_V109_STRUCTURE_AUDIT_2026-05-04.md` | real-device flash PASS, `cmdv1 version/status` PASS, 3-cycle quick soak PASS |
| v110 | `d5c98cf Add v110 app controller cleanup` | `NATIVE_INIT_V110_APP_CONTROLLER_CLEANUP_2026-05-04.md` | real-device flash PASS, controller busy gate PASS, 3-cycle quick soak PASS |
| v111 | `f453a8e Add v111 extended soak RC` | `NATIVE_INIT_V111_EXTENDED_SOAK_RC_2026-05-04.md` | real-device flash PASS, 10-cycle extended soak PASS, final service/selftest PASS |
| v112 | `f9ae60e Add v112 USB service soak` | `NATIVE_INIT_V112_USB_SERVICE_SOAK_2026-05-04.md` | real-device flash PASS, NCM ping PASS, tcpctl host checks PASS, ACM rollback PASS |
| v113 | `efa20ed Add v113 runtime package layout` | `NATIVE_INIT_V113_RUNTIME_PACKAGE_LAYOUT_2026-05-04.md` | real-device flash PASS, runtime package paths PASS, 3-cycle quick soak PASS |
| v114 | `4581852 Add v114 helper deploy visibility` | `NATIVE_INIT_V114_HELPER_DEPLOY_2026-05-04.md` | real-device flash PASS, helpers manifest/plan PASS, helpers verify PASS, 3-cycle quick soak PASS |
| v115 | `001145a Add v115 remote shell hardening` | `NATIVE_INIT_V115_RSHELL_HARDENING_2026-05-04.md` | real-device flash PASS, `rshell audit` PASS, invalid-token rejection PASS, NCM smoke/rollback PASS |
| v116 | `7da255a Add v116 diagnostics bundle` | `NATIVE_INIT_V116_DIAG_BUNDLE_2026-05-04.md` | real-device flash PASS, `diag full` PASS, `diag bundle` PASS, host `diag_collect.py` PASS, 3-cycle soak PASS |

## Current v116 Artifact Hashes

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v116` | `423769cc2eea841306dca2d14411384967bb3afe50ea00353574fd9bd7e91c35` |
| `stage3/ramdisk_v116.cpio` | `0ce1218c3e01e19c9d77909b3cc3968fad77f1584323d0da9063f4d30346b3a3` |
| `stage3/boot_linux_v116.img` | `6c7a320973a417abc4f423dadd0e2a0ee6420eb3a739cdd9eb2549ba24069e8f` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |

## Audit Commands

Representative commands used during the audit:

```bash
git status --short
git log --oneline -12
for v in 109 110 111 112 113 114 115 116; do ls docs/reports/NATIVE_INIT_V${v}_*_2026-05-04.md; done
sha256sum stage3/linux_init/init_v116 stage3/ramdisk_v116.cpio stage3/boot_linux_v116.img stage3/linux_init/helpers/a90_cpustress stage3/linux_init/helpers/a90_rshell
python3 scripts/revalidation/a90ctl.py version
```

Static validation after writing this audit should still run:

```bash
git diff --check
python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/native_init_flash.py scripts/revalidation/diag_collect.py scripts/revalidation/rshell_host.py scripts/revalidation/native_soak_validate.py scripts/revalidation/ncm_host_setup.py
```

## Conclusion

The v109-v116 cycle is closed with no uncovered completion criterion found.

The next recommended item is `v117 planning`: choose the next cycle theme and guardrails from the v116 baseline before implementing new features.
