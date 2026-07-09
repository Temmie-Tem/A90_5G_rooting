# S22+ M34 S8B1 Download-Beacon Probe Host Build (2026-07-09)

Host-only build. No S22+ live flash is authorized by this report.

## Purpose

S8B1 implements the first S8 observability probe after the S7A2 blind result.
It keeps the S7A2 module recipe fixed, loads the GENI I2C transport plus the
max77705/PDIC/altmode session-producer chain, then reads exactly one predicate:

```text
/sys/class/typec/port0 exists OR /sys/bus/i2c/devices/57-0066 exists
```

If the predicate is true, the candidate requests `reboot(download)` as a
host-visible 1-bit HIT. If the predicate remains false after a bounded poll, it
parks. S8B1 intentionally skips downstream configfs gadget creation, UDC bind,
`ssusb` role writes, TypeC role writes, FunctionFS, and stock composite setup so
the result isolates max77705/I2C reachability before the USB gadget path.

## Output

Output root:

```text
workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_8/
```

S8B1 AP path:

```text
workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_8/S8B1/odin4/AP.tar.md5
```

Hashes:

```text
S8B1 AP.tar.md5 SHA256: 0bf313cdf24a5f5babc3d0073a1e90686f1b734b6dafdfa548154ef3eac6c2c8
S8B1 padded boot.img SHA256: 4e599087f242fdf2ae6bee1465e0725b60057bad893b665a178bcf87b88b9a20
S8B1 /init SHA256: a1cbc9828a24a7e302bd569de93b4f41e2ceb159130ea373d2ea9c9572f5a20d
S8B1 module-list SHA256: c0c35e02fe61a3f6c18c221a9ae2cc1a54aafd38374117fa954dbfa675700998
base Magisk boot SHA256: 2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
template source SHA256: 35978182a80e0502a0aec89ec66e35ca378ebbb3b7c58c573ad0e8ff55cc248d
```

AP tar members:

```text
boot.img.lz4
```

## Static Contract

S8B1 runtime contract:

- direct PID1 native-init, no Android/Magisk handoff
- boot partition only artifact, constructed by MagiskBoot unpack/repack from
  the known-booting Magisk boot
- module count: 86
- module recipe: same GENI I2C plus max77705 session-producer closure as S7A2
- probe paths: `/sys/class/typec/port0`,
  `/sys/bus/i2c/devices/57-0066`
- true action: `reboot(download)`
- false action: park
- no configfs gadget setup, no UDC bind, no TypeC role-write discriminator, no
  FunctionFS, no stock composite
- no persistent partition mount and no block-device writes

Manifest safety still sets `live_flash_authorized=false` and
`requires_new_sha_pinned_agents_exception_before_flash=true`.

## Validation

Commands run:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/build_s22plus_m34_runtime_gadget_split.py --force
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests/test_s22plus_m34_runtime_gadget_split_build.py
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests/test_s22plus_m34_s7a_session_producer_live_gate.py tests/test_s22plus_m34_s7a2_geni_i2c_live_gate.py
```

Results:

```text
M34 v0.8 build: OK
runtime gadget split tests: Ran 5 tests, OK
S7A/S7A2 live-helper regression tests: Ran 20 tests, OK
```

The first build attempt also caught a host-side false-positive safety check:
`download_beacon=1` matched inside `no_download_beacon=1`. The forbidden string
gate now checks the space-delimited positive tokens instead, preserving the
intended guarantee that only S8B1 carries the download-beacon contract.

## Next Gate

Before any S8B1 live flash, add a fresh active `AGENTS.md` boot-only exception
pinning the exact S8B1 AP.tar.md5 SHA256, padded boot.img SHA256, `/init`
SHA256, module-list SHA256, rollback AP hashes, and one attended operator
approval. Without that exception, the artifact remains host-only.
