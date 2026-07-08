# S22+ M33 P25/P28 Branch Live Gate Source

Date: 2026-07-09 02:45 KST / 2026-07-08 17:45 UTC

## Verdict

SOURCE READY / POLICY INERT for both P25 and P28.

No live flash was performed. There is no active `AGENTS.md` authorization for
P25 or P28. Default execution for both helpers fail-closes before Android/device
preflight because the variant-specific policy markers and live tokens are absent
from `AGENTS.md`.

## Why These Two

P27 is already source-ready and is the next intended live boundary after P12
survived. These two helpers prepare both branches after a future P27 result:

- P27 fails: run P25 to separate SMMU/secure-buffer from HS PHY.
- P27 survives: run P28 to isolate DWC3 before ACM/configfs.

## Helpers

P25:

`workspace/public/src/scripts/revalidation/s22plus_m33_p25_wdt_prefix_park_live_gate.py`

P28:

`workspace/public/src/scripts/revalidation/s22plus_m33_p28_wdt_prefix_park_live_gate.py`

Both helpers keep the same fail-closed shape:

- `--offline-check`: verifies candidate AP, manifest, and rollback APs only.
- default run: requires active `AGENTS.md` markers before Android/device preflight.
- `--live`: requires a future active variant-specific live token.
- `--rollback-from-download`: requires a future active variant-specific rollback token.

No active token is present in `AGENTS.md` at this checkpoint.

## P25 Candidate

Candidate AP:

`workspace/private/outputs/s22plus_native_init/m33_wdt_prefix_park_matrix_v0_1/P25/odin4/AP.tar.md5`

Pinned hashes:

- AP.tar.md5: `1ae65c1d994137237f2227f95b86700f74d00791d6cfec53b1bcf245f0aa18d7`
- boot.img: `fd29255237b34df959102e11fa60bd654678fe3eda93c710dbf314e5485e6651`
- `/init`: `bc4a2667f13a3b34e9c11c06c7c4c7b5cf55df233009a8ce661982d7154b465e`
- module list: `72ccb5e52af731993d4d94670bcbba42a1f53e6254c59636e2df9efe0bea579b`
- generated source: `3e941075b4a466f30ab67f5976dcc3c890a414de2f266f061aa90a33897169be`
- preserved kernel: `bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff`
- base Magisk boot: `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

P25 boundary:

- module count: 29
- includes `arm_smmu.ko`
- excludes `phy-msm-snps-hs.ko`
- excludes `phy-msm-snps-eusb2.ko`
- excludes `usb_f_ss_mon_gadget.ko`
- excludes `dwc3-msm.ko`
- excludes `usb_f_ss_acm.ko`

## P28 Candidate

Candidate AP:

`workspace/private/outputs/s22plus_native_init/m33_wdt_prefix_park_matrix_v0_1/P28/odin4/AP.tar.md5`

Pinned hashes:

- AP.tar.md5: `4c76ef4df814356a7acfa9ce9a00c2fe003208ff8289c2874535e26b7e1c3f07`
- boot.img: `3bc59d6df58b5c7130e6ca531a6a6cd3a4d35e14ff7fd6667da72e2bd40e9e29`
- `/init`: `2ef661b9e5a1496674b6cc457c9b0e84c60ae7af01914c2403db602c6ebe84b1`
- module list: `ef57a00fbef4b9c89936b30fc5c001974fbe9c2ece590c6a6984cb4695318a8f`
- generated source: `8d752ade0ee5100b5f91cb7fb15c09d24652a97e03721fb8c4d784d1f419f289`
- preserved kernel: `bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff`
- base Magisk boot: `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

P28 boundary:

- module count: 44
- includes `arm_smmu.ko`
- includes `phy-msm-snps-hs.ko`
- includes `phy-msm-snps-eusb2.ko`
- includes `usb_f_ss_mon_gadget.ko`
- includes `dwc3-msm.ko`
- excludes `usb_f_ss_acm.ko`

## Shared Runtime Scope

Both helpers remain park-only:

- no reboot syscall
- no Download beacon
- no runtime USB/configfs/ACM setup
- no Android/Magisk handoff
- no persistent partition mount
- no block write
- no module binary injection into boot ramdisk
- boot AP must contain only `boot.img.lz4`

Both keep `phy-msm-ssusb-qmp.ko` and EUD excluded.

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m33_p25_wdt_prefix_park_live_gate.py \
  workspace/public/src/scripts/revalidation/s22plus_m33_p28_wdt_prefix_park_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest -q \
  tests/test_s22plus_m33_p25_wdt_prefix_park_live_gate.py \
  tests/test_s22plus_m33_p27_wdt_prefix_park_live_gate.py \
  tests/test_s22plus_m33_p28_wdt_prefix_park_live_gate.py \
  tests/test_s22plus_m33_wdt_prefix_park_build.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m33_p25_wdt_prefix_park_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m33_p28_wdt_prefix_park_live_gate.py \
  --offline-check
```

Results:

- `py_compile`: pass
- M33 P25/P27/P28/build tests: 17 passed
- P25 `--offline-check`: pass, no device action
- P28 `--offline-check`: pass, no device action
- P25 default run: fail-closed on missing `AGENTS.md` authorization markers
- P28 default run: fail-closed on missing `AGENTS.md` authorization markers

## Next Gate

The next actual live gate remains P27 unless the operator redirects. P25 and P28
are branch-ready artifacts only and require fresh SHA-pinned `AGENTS.md`
exceptions plus explicit operator approval before any flash.
