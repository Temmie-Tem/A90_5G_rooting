# S22+ Native-Init M7 USB-Subset Live Gate Preflight - 2026-07-07

## Verdict

PASS: M7 live gate helper and SHA-pinned `AGENTS.md` exceptions are prepared,
and the no-flash dry-run passed against the current rooted Android/Magisk
baseline.

No live flash was run.

## Added

```text
workspace/public/src/scripts/revalidation/s22plus_m7_usb_subset_live_gate.py
```

## Pinned Candidate

```text
AP.tar.md5             be0e1e34ec9452a14b7cfac66cc7ac57a0b29e92343945c35c1f836282563c4d
boot.img               7e58de4cfbf50eabef73f62ed1c30a1b4bc83089307cca083c304b9a9b360206
M7 /init               530ff86247270c5a48db22f009e5f659d4403643a90486842938200c8192514d
M7 subset list         b630d318d1a95f596cbd97699d04d2bf60a53e634f35c00bbabc8000fb3315b7
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                 bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
vendor_ramdisk00       41b2481b779ff48863c300250dabf1b3dcc45c7f58fab421fcf6df1245145193
```

Rollback APs verified by the helper:

```text
Magisk boot-only rollback  d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot-only fallback   1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

## Helper Gates

The helper verifies:

```text
single AP member                     boot.img.lz4
target identity                      SM-S906N/g0q/S906NKSS7FYG8
current Android baseline             boot_completed=1, Magisk root, orange verified boot
current boot hash                    2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
M7 subset count                      53
M7 dependency closure                 54
M7 subset bytes                      802
M7 subset runtime buffer             8192
watchdog modules in final subset      0
blocked closure entry                 qc_usb_audio.ko
module binary injection               false
boot ramdisk module-list files         1
```

The live ack token is:

```text
S22PLUS-M7-USB-SUBSET-LIVE-GATE
```

Rollback-only ack token:

```text
S22PLUS-M7-ROLLBACK-FROM-DOWNLOAD
```

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m7_usb_subset_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m7_usb_subset_live_gate.py --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m7_usb_subset_live_gate.py

git diff --check
```

Results:

```text
offline-check ok: M7 candidate and rollback APs verified; no device action
dry-run ok: M7 candidate, rollback APs, AGENTS exception, Android stability, and boot hash verified
```

## Next

The next supervised live command is:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m7_usb_subset_live_gate.py \
  --live \
  --ack S22PLUS-M7-USB-SUBSET-LIVE-GATE
```

Expected discriminator: if watchdog/full-recovery replay caused the M6 loop, M7
should stop fast-looping and either park or expose ACM. If no ACM appears,
manual download-mode rollback remains the required recovery path.
