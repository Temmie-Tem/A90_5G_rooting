# v221 Host Vendor ELF / Library Evidence Closure

## Summary

v221 adds a host-side ELF/library evidence closure tool for `cnss-daemon` and
`cnss_diag`. It does not execute vendor daemons and does not issue live device
commands.

Result: PASS.

Final decision: `vendor-root-required`.

Reason: host-visible vendor root is required for ELF/library inspection.

This is an expected safe outcome. v221 narrowed the v218 blocker to a concrete
missing host input: a vendor root containing `bin/cnss-daemon` and
`bin/cnss_diag`.

## Changes

- Added `scripts/revalidation/wifi_vendor_elf_library_closure.py`.
- Added v221 plan:
  `docs/plans/NATIVE_INIT_V221_HOST_VENDOR_ELF_LIBRARY_EVIDENCE_PLAN_2026-05-13.md`.

## Scope

The tool consumes v210/v216/v218/v219/v220 manifests and writes:

- `tmp/wifi/v221-host-vendor-elf-library-evidence/manifest.json`
- `tmp/wifi/v221-host-vendor-elf-library-evidence/elf-dependencies.json`
- `tmp/wifi/v221-host-vendor-elf-library-evidence/summary.md`

It supports two modes:

- manifest-only without `--vendor-root`: expected decision `vendor-root-required`
- host vendor root with `--vendor-root`: parse ELF interpreter and library
  dependencies with `readelf`

## Static Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_vendor_elf_library_closure.py
```

Result: PASS.

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import wifi_vendor_elf_library_closure
wifi_vendor_elf_library_closure.validate_no_active_commands()
print('v221 command guard PASS')
PY
```

Result:

```text
v221 command guard PASS
```

## Manifest-Only Run

Command:

```bash
python3 scripts/revalidation/wifi_vendor_elf_library_closure.py \
  --v210-manifest tmp/wifi/v210-vendor-asset-classifier/manifest.json \
  --v216-manifest tmp/wifi/v216-service-replay-model/manifest.json \
  --v218-manifest tmp/wifi/v218-cnss-daemon-dryrun/manifest.json \
  --v218-native-manifest tmp/wifi/v218-cnss-daemon-dryrun-native/manifest.json \
  --v219-manifest tmp/wifi/v219-native-android-env-shim/manifest.json \
  --v220-manifest tmp/wifi/v220-bringup-gate-v2/manifest.json \
  --out-dir tmp/wifi/v221-host-vendor-elf-library-evidence
```

Result:

```text
PASS out_dir=/home/temmie/dev/A90_5G_rooting/tmp/wifi/v221-host-vendor-elf-library-evidence decision=vendor-root-required reason=host-visible vendor root is required for ELF/library inspection
```

## Evidence Summary

```text
decision: vendor-root-required
pass: True
vendor_root_status: not-provided
visible_vendor_paths_count: 47
```

Required host vendor paths:

| Service | Expected path | Capabilities |
| --- | --- | --- |
| `cnss-daemon` | `<vendor-root>/bin/cnss-daemon` | `NET_ADMIN` |
| `cnss_diag` | `<vendor-root>/bin/cnss_diag` | none |

Daemon inspection status:

| Service | Inspection | Vendor path |
| --- | --- | --- |
| `cnss-daemon` | `vendor-root-required` | `bin/cnss-daemon` |
| `cnss_diag` | `vendor-root-required` | `bin/cnss_diag` |

## Guardrails

- No live device commands.
- No daemon execution.
- No Android service start.
- No ICNSS sysfs/debugfs writes.
- No firmware path mutation.
- No rfkill write.
- No link-up.
- No scan/connect.
- No credential collection.

## Hashes

```text
a4492262ce7b942c86e24879995ce7f109a3aad9ee7a8441196ff69df1dedf5b  scripts/revalidation/wifi_vendor_elf_library_closure.py
6321d014884c090cb01dd8b4d7de5279bb2ac21dfb80167f6bf88e598b95ccde  docs/plans/NATIVE_INIT_V221_HOST_VENDOR_ELF_LIBRARY_EVIDENCE_PLAN_2026-05-13.md
b5071c9b2302ff0639337646869628b82c106f480e0b9d17bc717ca3b971cbfb  tmp/wifi/v221-host-vendor-elf-library-evidence/manifest.json
8541a089c19afe8014cb47c96c6a3e834573daf7d260c91150a97663bf32d878  tmp/wifi/v221-host-vendor-elf-library-evidence/elf-dependencies.json
f478fefca531d2ef63cab21082bedc72bceeaddd0fe1608bbd54cabc8bb7083e  tmp/wifi/v221-host-vendor-elf-library-evidence/summary.md
```

## Decision

Active Wi-Fi remains blocked. v221 did not approve CNSS daemon execution.

Before v223 recovery policy or any controlled CNSS start planning can be useful,
the project needs v222 to produce a host-visible vendor root or an equivalent
private evidence bundle that contains at least:

- `bin/cnss-daemon`
- `bin/cnss_diag`
- related `lib`/`lib64` vendor shared libraries

## Next

Replace the previous v222 recovery-policy slot with a vendor root export or
extraction plan. After that artifact exists, rerun v221 with `--vendor-root` and
only then continue to recovery/rollback policy hardening.
