# Native Init V1643 Bootloader / PMIC Artifact Acquisition Plan

## Summary

- Cycle: `V1643`
- Type: host-only bootloader / PMIC artifact acquisition plan
- Decision: `v1643-read-only-bootloader-pmic-artifact-plan-ready`
- Result: PASS
- Reason: V1642 leaves the suspected SDX50M main-rail owner outside AP kernel source; the next safe step is read-only artifact metadata, not a live PMIC/GPIO/GDSC write.

## Inputs

- `docs/reports/ESOC_NATURAL_PATH_MDM2AP_OBSERVATION_CONTRACT_2026-06-02.md`: `True`
- `docs/reports/ESOC_PON_SOURCE_ANALYSIS_2026-06-02.md`: `True`
- `docs/reports/ESOC_DTB_PARITY_2026-06-02.md`: `True`
- `docs/reports/NATIVE_INIT_V1638_NATURAL_PATH_MDM2AP_IRQ_SUMMARY_HANDOFF_2026-06-02.md`: `True`
- `docs/reports/NATIVE_INIT_V1642_SDX_POWER_OWNER_CLASSIFIER_2026-06-02.md`: `True`

## Checks

- `required_reports_present`: `True`
- `v1638_one_run_handoff_present`: `True`
- `v1642_external_owner_gap_present`: `True`
- `candidate_partition_policy_defined`: `True`
- `sensitive_exclusions_defined`: `True`
- `metadata_only_report_mode`: `True`
- `no_binary_commit_policy`: `True`
- `no_live_write_gate`: `True`

## Acquisition Policy

- Primary bootloader / PMIC-control candidates: `xbl`, `xblbak`, `abl`, `ablbak`, `aop`, `aopbak`, `devcfg`, `devcfgbak`, `tz`, `tzbak`, `hyp`, `hypbak`, `keymaster`, `keymasterbak`, `cmnlib`, `cmnlibbak`, `cmnlib64`, `cmnlib64bak`, `qupfw`, `qupfwbak`.
- Context-only firmware candidates: `modem`, `NON-HLOS`, `bluetooth`, `dsp`. These may explain SDX firmware expectations, but do not justify Wi-Fi HAL or connect work.
- Sensitive / identity-bearing exclusions: `userdata`, `metadata`, `persist`, `efs`, `modemst1`, `modemst2`, `fsg`, `fsc`, `keystore`, `sec_efs`. These are not needed for the SDX50M power-owner question.
- Repository policy: do not commit raw proprietary bootloader, firmware, partition dumps, `.img`, `.bin`, `.mbn`, `.elf`, `.tar`, `.lz4`, or `.md5` artifacts.
- Evidence policy: collect partition name, resolved block path, byte size, SHA256, and bounded token-filtered strings only; store any raw dump outside git under private `tmp/` storage if a later gate explicitly needs it.
- Token filter for bounded strings: `sdx`, `sdx50`, `sdxprairie`, `pmic`, `pm8150`, `pm8150l`, `pmxprairie`, `pon`, `ps_hold`, `mdm`, `mhi`, `pcie`, `gpio`, `ap2mdm`, `mdm2ap`, `vdd_modem`.

## Proposed V1644 Read-only Live Gate

If selected, V1644 should only read metadata and hashes from existing block devices:

```sh
toybox ls -l /dev/block/by-name 2>&1

for p in xbl xblbak abl ablbak aop aopbak devcfg devcfgbak tz tzbak hyp hypbak keymaster keymasterbak cmnlib cmnlibbak cmnlib64 cmnlib64bak qupfw qupfwbak modem NON-HLOS bluetooth dsp; do
  if [ -e /dev/block/by-name/$p ]; then
    printf 'PART %s\n' "$p"
    toybox ls -l /dev/block/by-name/$p
    toybox blockdev --getsize64 /dev/block/by-name/$p 2>&1
    toybox sha256sum /dev/block/by-name/$p 2>&1
  fi
done
```

The live gate must not dump full partition contents by default. If a later explicit gate needs a private dump, it must write under a private, ignored `tmp/` path with `umask 077`, record SHA256/size in the report, and keep the binary out of git.

## Current Local Artifact Scan

- Bounded local bootloader / PMIC artifact hits: `0`

## Interpretation

V1638 already performed the one natural-path observation run and later V1642 found no AP-native safe write target. Re-running natural-path timing variants or jumping to PMIC/GPIO/GDSC mutation would violate the current stop condition. The only defensible next move is to close the missing artifact gap with read-only partition metadata and, if necessary, private non-git dumps for offline analysis.

## Hard Stops

No forced RC1 enumerate, pci-msm case write, fake ONLINE/system-info spoof, PMIC/GPIO/GDSC/regulator write, eSoC notify/`BOOT_DONE`, PCI rescan, platform bind/unbind, Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, external ping, boot image write, or partition write is part of V1643.

## Next

V1644 may be a read-only live partition metadata/hash capture if the device is available. It should produce a private evidence bundle and a report that either identifies a concrete bootloader/PMIC owner artifact for offline analysis or explicitly hands off the remaining evidence gap.
