# S22+ M33 P27 Watchdog Prefix-Park Live Gate Preflight

Date: 2026-07-09 02:51 KST / 2026-07-08 17:51 UTC

## Verdict

PASS: M33 P27 live gate is prepared and dry-run verified.

No live flash has been performed by this preflight. The operator gave pre-live
approval, and `AGENTS.md` now contains a one-shot SHA-pinned boot-only M33 P27
exception.

## Candidate

Helper:

`workspace/public/src/scripts/revalidation/s22plus_m33_p27_wdt_prefix_park_live_gate.py`

Live ack:

`S22PLUS-M33-P27-WDT-PREFIX-PARK-LIVE-GATE`

Rollback-from-Download ack:

`S22PLUS-M33-P27-WDT-PREFIX-PARK-ROLLBACK-FROM-DOWNLOAD`

Candidate AP:

`workspace/private/outputs/s22plus_native_init/m33_wdt_prefix_park_matrix_v0_1/P27/odin4/AP.tar.md5`

Pinned hashes:

- AP.tar.md5: `9110e793f5cc812c856dedf35aaa4cc2f2c692f8561bba9dbe10c7b1e8a29371`
- boot.img: `16efd35b4bb340b2c8d5d5b99e3e3d3e19d4c01a60e87f6ed3cf60acc90386ea`
- `/init`: `4ce13d65264c2e887aadeefe66c812e4079340b14745bfb277b37a9fde7e8785`
- module list: `11f8ccac67944d689d327d0157eb2f504e794d205df91c480506a3247d9c830e`
- generated source: `b57c37678ec5b145d3b1c6208c6ee685ba40401512115e08e4f92afa63627f33`
- preserved kernel: `bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff`
- base Magisk boot: `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

## Scope

M33 P27 is a park-only discriminator:

- boot partition only
- direct freestanding PID1
- watchdog-managed prefix closure
- includes SMMU and HS/eUSB2 PHY module loading
- excludes DWC3
- excludes ACM
- excludes QMP and EUD
- no reboot syscall
- no Download beacon
- no runtime USB/configfs/ACM
- no Android/Magisk handoff
- no persistent partition mount
- no block write
- no module binary injection into boot ramdisk

Module closure count: 40.

Interpretation:

- P27 survives: SMMU + HS/eUSB2 PHY loading is not the M32 no-ACM/bootloop
  boundary; continue to P28/DWC3.
- P27 fails: run P25 next to separate SMMU/secure-buffer from HS PHY.
- PMIC/RDX abnormal reset before the observation window is fail for this
  boundary.

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m33_p27_wdt_prefix_park_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest -q \
  tests/test_s22plus_m33_p27_wdt_prefix_park_live_gate.py \
  tests/test_s22plus_m33_wdt_prefix_park_build.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m33_p27_wdt_prefix_park_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m33_p27_wdt_prefix_park_live_gate.py
```

Results:

- `py_compile`: pass
- M33 P27 live/build tests: 9 passed
- `--offline-check`: pass, no device action
- dry-run: pass
- `agents_exception_missing=[]`
- Android identity: `SM-S906N/g0q/S906NKSS7FYG8`
- ADB serial: `<S22_SERIAL_REDACTED>`
- vbstate: `orange`
- Android boot complete: `1`
- bootanim: `stopped`
- Magisk root: `uid=0(root) ... context=u:r:magisk:s0`
- Android stability: 4 samples OK
- current boot partition SHA256:
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

Dry-run log:

`workspace/private/runs/s22plus_m33_p27_wdt_prefix_park_live_gate_20260708T175107Z_01/s22plus_m33_p27_wdt_prefix_park_live_gate.txt`

## Next Command

Approved live command:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m33_p27_wdt_prefix_park_live_gate.py \
  --live --ack S22PLUS-M33-P27-WDT-PREFIX-PARK-LIVE-GATE
```

Expected operator action:

- Do not press physical keys during the 90 second observation window.
- If the candidate survives, the helper will ask for manual Download mode for
  rollback.
- If RDX/PMIC abnormal reset or bootloop occurs first, enter Download mode when
  the helper asks and use the same rollback path.
