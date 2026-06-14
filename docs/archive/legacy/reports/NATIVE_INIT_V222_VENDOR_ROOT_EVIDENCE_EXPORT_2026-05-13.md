# v222 Report: Vendor Root Evidence Export / Extraction

## Summary

v222 implements the host-side vendor root evidence export tool and runs the
safe plan-only path.

- script: `scripts/revalidation/wifi_vendor_root_evidence_export.py`
- plan: `docs/plans/NATIVE_INIT_V222_VENDOR_ROOT_EVIDENCE_EXPORT_PLAN_2026-05-13.md`
- output: `tmp/wifi/v222-vendor-root-evidence-export`
- result: PASS
- decision: `export-source-required`
- reason: `source vendor root is required for export`

This is an expected safe result when no host-visible vendor root has been
provided. It does not close the v221 vendor evidence blocker yet.

## What Was Implemented

`wifi_vendor_root_evidence_export.py` now supports:

- default plan-only run with no live device commands;
- `--source-vendor-root <path>` export mode;
- private evidence output using the shared `EvidenceStore`;
- no-follow destination file writes for copied vendor files;
- source root validation that rejects missing, symlinked, or non-directory roots;
- required path extraction from v221 evidence with fallback to:
  - `bin/cnss-daemon`
  - `bin/cnss_diag`
- allowlisted export of:
  - required CNSS binaries;
  - `lib/**`;
  - `lib64/**`;
  - small context rc/config files;
- source symlink handling only when the target resolves inside the source vendor
  root;
- copy count and total byte caps;
- `manifest.json`, `export-plan.json`, and `summary.md` output.

## Guardrails

The v222 tool does not:

- run live device commands by default;
- dump partitions;
- write to the device;
- execute copied vendor binaries;
- copy Wi-Fi credential paths;
- follow destination symlinks;
- create group/world-readable evidence output;
- perform rfkill, link-up, scan, connect, DHCP, or daemon start operations.

## Validation

Static validation:

```bash
python3 -m py_compile scripts/revalidation/wifi_vendor_root_evidence_export.py

python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import wifi_vendor_root_evidence_export
wifi_vendor_root_evidence_export.validate_no_active_commands()
print('v222 command guard PASS')
PY

git diff --check
```

Result:

```text
v222 command guard PASS
```

Plan-only run:

```bash
python3 scripts/revalidation/wifi_vendor_root_evidence_export.py \
  --v210-manifest tmp/wifi/v210-vendor-asset-classifier/manifest.json \
  --v221-manifest tmp/wifi/v221-host-vendor-elf-library-evidence/manifest.json \
  --out-dir tmp/wifi/v222-vendor-root-evidence-export
```

Result:

```text
PASS out_dir=/home/temmie/dev/A90_5G_rooting/tmp/wifi/v222-vendor-root-evidence-export decision=export-source-required reason=source vendor root is required for export
```

Manifest assertion:

```text
export-source-required True source vendor root is required for export
source_root_status not-provided
required ['bin/cnss-daemon', 'bin/cnss_diag']
```

Synthetic source-root export smoke test:

```text
PASS out_dir=/home/temmie/dev/A90_5G_rooting/tmp/wifi/v222-vendor-root-evidence-export decision=vendor-root-ready reason=minimal vendor root evidence is ready for v221 rerun
vendor-root-ready True 5 2
v222 synthetic export PASS
```

The final retained output was regenerated as plan-only
`export-source-required` after the synthetic smoke test.

## Output Files

```text
tmp/wifi/v222-vendor-root-evidence-export/manifest.json
tmp/wifi/v222-vendor-root-evidence-export/export-plan.json
tmp/wifi/v222-vendor-root-evidence-export/summary.md
```

File modes:

```text
600 tmp/wifi/v222-vendor-root-evidence-export/export-plan.json
600 tmp/wifi/v222-vendor-root-evidence-export/manifest.json
600 tmp/wifi/v222-vendor-root-evidence-export/summary.md
```

Required vendor paths:

| service | expected host path |
| --- | --- |
| cnss-daemon | `<vendor-root>/bin/cnss-daemon` |
| cnss_diag | `<vendor-root>/bin/cnss_diag` |

## Artifact Hashes

```text
2bf91d4ebc5ad3c310f772bb304c0deda7e830047c06601508d3bfe6709f67d0  scripts/revalidation/wifi_vendor_root_evidence_export.py
ab800bbf928f35e845e44f44cec2f4dab908bbdccaa70d7ec8d9c059588dddd0  docs/plans/NATIVE_INIT_V222_VENDOR_ROOT_EVIDENCE_EXPORT_PLAN_2026-05-13.md
9f30b72f6556487906218b714b830a6c799256df88fff4b2467eefbd93a6f1c3  tmp/wifi/v222-vendor-root-evidence-export/manifest.json
4058899daa70dbcee2dd5c12f4203f40b41fb27d9c76b8f8f43f270efa2ab19d  tmp/wifi/v222-vendor-root-evidence-export/export-plan.json
0d95e65efca155652fb003f21c620399c0f74d6b892dd194700b3e6dc42a7fbe  tmp/wifi/v222-vendor-root-evidence-export/summary.md
```

## Interpretation

v222 is complete as a host-side safe export tool, but the Wi-Fi prerequisite
chain remains blocked until a source vendor root is supplied and v222 is rerun
with `--source-vendor-root`.

Next operator action:

```bash
python3 scripts/revalidation/wifi_vendor_root_evidence_export.py \
  --source-vendor-root <vendor-root> \
  --out-dir tmp/wifi/v222-vendor-root-evidence-export
```

If that returns `vendor-root-ready`, rerun v221:

```bash
python3 scripts/revalidation/wifi_vendor_elf_library_closure.py \
  --vendor-root tmp/wifi/v222-vendor-root-evidence-export/vendor-root \
  --out-dir tmp/wifi/v221-host-vendor-elf-library-evidence-rerun
```

## Next

- Do not proceed to active Wi-Fi.
- Keep daemon execution blocked.
- Either collect a host-visible vendor root and rerun v222/v221, or continue to
  v223 recovery/rollback policy hardening while explicitly preserving the vendor
  root blocker.
