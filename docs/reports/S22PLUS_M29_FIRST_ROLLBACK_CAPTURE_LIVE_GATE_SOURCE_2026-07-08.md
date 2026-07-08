# S22+ M29 First-Rollback Capture Live Gate Source (2026-07-08)

## Verdict

SOURCE READY / HOST-ONLY VALIDATED / NO LIVE AUTHORIZATION.

M29 implements the operator steer in
`S22PLUS_M29_CAPTURE_AT_FIRST_ROLLBACK_BOOT_STEER_2026-07-08.md`: keep the
existing M28 dependency-complete `S24` candidate and M25 high-speed DTBO cap,
but capture retained evidence at the first post-candidate Android rollback boot
before stock-DTBO rollback can advance the `/proc/last_kmsg` window.

No flash, reboot, partition write, sysfs write, or device mutation was performed
for this source unit.

## Added Source

```text
workspace/public/src/scripts/revalidation/s22plus_m29_first_rollback_capture_live_gate.py
```

Helper SHA256:

```text
d8da7792f9ccc60a16358984636b29a3df27fac6b264f039354ea54770a18bb3
```

Test:

```text
tests/test_s22plus_m29_first_rollback_capture_live_gate.py
```

## Scope

M29 intentionally does not build a new boot candidate. It reuses the already
host-built M28 `S24` AP and the M25 DTBO high-speed cap:

```text
S24 AP.tar.md5 SHA256  c684f6a21bcc9aa50b066b447f4356958fe6d7bfed93edf0ac1b7dcaae8ce75f
S24 boot.img SHA256    a1459931001bfd6e17593dd329fc682f00ab61f4841b6543791f5349dd012cd0
S24 /init SHA256       5c04a2023b2b56ef98746da6f7168121b62d7859cee81c756b80d1a382c1964e
```

`F43` remains unauthorized. The new helper accepts only `S24`.

## Capture Order

The live path, when separately authorized, will:

1. Verify Android/Magisk baseline and stock DTBO.
2. Apply the M25 high-speed DTBO cap if needed.
3. Capture a pre-candidate retained-log baseline after the DTBO cap and before
   candidate `adb reboot download`.
4. Flash M28 `S24`.
5. If an Odin endpoint returns, flash Magisk boot rollback.
6. At the first post-candidate Android boot, immediately capture:
   - `/sys/fs/pstore/*`
   - `/proc/last_kmsg`
   - `/proc/reset_summary`
   - `/proc/reset_klog`
   - `/proc/reset_history`
   - `/proc/reset_tzlog`
   - reset-reason probe summary
7. Fingerprint first-capture `/proc/last_kmsg` and compare it with the
   pre-candidate baseline SHA256.
8. Only then restore stock DTBO.

The key ordering marker is:

```text
first-post-candidate-rollback-before-stock-dtbo-rollback
```

## Fail-Closed Policy

The helper has fresh M29 ack tokens:

```text
S22PLUS-M29-FIRST-ROLLBACK-CAPTURE-LIVE-GATE
S22PLUS-M29-FIRST-ROLLBACK-CAPTURE-ROLLBACK-FROM-DOWNLOAD
S22PLUS-M29-FIRST-ROLLBACK-CAPTURE-RESTORE-STOCK-DTBO
```

`AGENTS.md` does not currently authorize those tokens. Default execution fails
closed before touching the device.

Observed default command result:

```text
rc=1
AGENTS.md missing M29 first-rollback capture authorization markers
```

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m29_first_rollback_capture_live_gate.py \
  tests/test_s22plus_m29_first_rollback_capture_live_gate.py
```

Result: pass.

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_s22plus_m29_first_rollback_capture_live_gate
```

Result:

```text
Ran 7 tests in 0.011s
OK
```

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m29_first_rollback_capture_live_gate.py \
  --offline-check
```

Result:

```text
offline-check ok: M29 S24 capture gate artifacts verified; no device action
```

## Next Gate

Before live, promote a fresh narrow `AGENTS.md` exception for exactly this helper
SHA, exactly S24, the M25 DTBO cap AP, the Magisk boot rollback AP, and stock
DTBO rollback AP. The live result must treat any operator manual Download as
contamination and must not run `F43`.

