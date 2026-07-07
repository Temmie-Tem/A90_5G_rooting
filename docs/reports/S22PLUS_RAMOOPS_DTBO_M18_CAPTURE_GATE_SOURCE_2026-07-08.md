# S22+ Ramoops DTBO + M18 Capture Gate Source (2026-07-08)

## Scope

Host-only source/gate work. No device action, no reboot, no flash, and no
partition write.

This follows the M18 bootloop observation and the DTBO ramoops target correction.
The point is to prepare the attended capture run without weakening the current
boot-only safety contract.

## Added helper

`workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m18_capture_live_gate.py`

Modes:

- `--offline-check`: verify all AP packages and manifests; no device action; does
  not require an `AGENTS.md` live exception.
- default dry-run: verify packages, then require the future SHA-pinned
  `AGENTS.md` exception before touching Android state.
- `--live`: once separately authorized, intended flow is patched DTBO flash,
  Android/root return, M18 boot flash, host observation, Magisk boot rollback,
  pstore collection, and stock DTBO restore.
- `--rollback-boot-from-download`: attended recovery mode if M18 loops and the
  operator manually enters download mode.
- `--restore-dtbo-from-download` / `--restore-dtbo-from-android`: explicit stock
  DTBO restore paths.

## Required pinned artifacts

```text
dtbo candidate AP.tar.md5 4f82663a7c2175a41760ec099c0f662dd04b8932a5ae82ba46b3ecb401a14a00
dtbo rollback AP.tar.md5  6f397421bee84f4ea0c80a8519be0f6f6af84119794970e8a1faaa05f261caaa
patched raw dtbo          1c90b54577cbb42e029818a0c4248e85ec3a0e40903b0887648d6556355c85ab
stock raw dtbo            97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c
M18 AP.tar.md5            9382f91bf2cd3235410368ca08208b9343d8584da48c29b25c46a931b1f42805
M18 boot.img              a99a09fa062d1aaa848a41037c649a43abc983f177714dfc24c39d0df4d84083
M18 base Magisk boot      2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
Magisk rollback AP        d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot fallback AP    1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

Required tar members:

```text
DTBO APs: dtbo.img.lz4
M18/boot rollback APs: boot.img.lz4
```

Ack tokens reserved by the helper:

```text
S22PLUS-RAMOOPS-DTBO-M18-CAPTURE-LIVE-GATE
S22PLUS-RAMOOPS-M18-ROLLBACK-BOOT-FROM-DOWNLOAD
S22PLUS-RAMOOPS-RESTORE-STOCK-DTBO
```

## Validation

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m18_capture_live_gate.py

python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m18_capture_live_gate.py \
  --offline-check

python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m18_capture_live_gate.py
```

Results:

```text
py_compile: pass
offline-check: pass; verified DTBO/M18 candidates and rollback APs; no device action
default dry-run: blocked before Android/device action because AGENTS.md has no
  ramoops DTBO + M18 capture authorization markers; rc=1
```

The dry-run blocker is intentional. The current contract still does not
authorize `dtbo` flashing or M18 live flashing.

## Next gate

Before any live capture attempt, add a narrow SHA-pinned `AGENTS.md` exception
covering exactly this capture gate and the hashes/tokens above. The exception
must explicitly accept that the patched DTBO does not match its stock AVB hash
descriptor and therefore depends on the already proven disabled-vbmeta/orange
state, or on a separate signing design.

Do not run `--live`, `--rollback-boot-from-download`, or any DTBO restore mode
until that exception exists and the operator is actively attending the device.
