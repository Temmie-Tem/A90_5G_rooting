# S22+ M20 Floor-Split Host Build (2026-07-08)

## Verdict

HOST-ONLY BUILD PASS. No live flash was executed or authorized.

The S22+ is currently back on the rooted Magisk Android baseline after the
operator-reported bootloop/manual-download event:

- `ro.product.model=SM-S906N`
- `ro.product.device=g0q`
- `ro.build.display.id=AP3A.240905.015.A2.S906NKSS7FYG8`
- `sys.boot_completed=1`
- `ro.boot.verifiedbootstate=orange`
- `ro.boot.boot_recovery=0`
- Magisk root available
- current boot SHA256:
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

M20 splits the M19 C000 floor before any module work is retried.

## Artifacts

Builder:

`workspace/public/src/scripts/revalidation/build_s22plus_m20_floor_split.py`

Sources:

- `workspace/public/src/native-init/s22plus_init_raw_reboot_m20a.S`
- `workspace/public/src/native-init/s22plus_init_m20_floor_split.c`

Private output root:

`workspace/private/outputs/s22plus_native_init/m20_floor_split_v0_1`

All variants are boot-only Odin APs with a single `boot.img.lz4` member and
`live_flash_authorized=false`.

| Variant | Purpose | AP.tar.md5 SHA256 | boot.img SHA256 |
| --- | --- | --- | --- |
| `M20A_RAW` | first-action raw `reboot(download)` positive control | `795e071107fdd7011a5acdc48ca7415273e5f2a3e19af45386702617292021fc` | `4fada63c986abc774e2a41eebc590f0635f1f1dcc8a207baa8d02cbfeb20eeb5` |
| `M20B_MINFS` | minimal `dev/proc/sys/run` setup, then `reboot(download)`, no kmsg write | `939f1b2a1c009c0a85ddc85e6c6e7a36b0ba1fadb19c7c20bacbd99b1323dc28` | `b1cc15ae17bf9607947a0819a0e530d6ada3867550c03f841e92f27c1116d46f` |
| `M20C_KMSG` | minimal fs setup, `/dev/kmsg` marker, then `reboot(download)` | `fd7b14f1fa13490c5fe724c2afa9a723f0707859d3ad4a6809e3c00e8093981d` | `fe7b8a38b4ca5b5c92f6a94423bba130263b5ba91f7a7de1c110ccc107a2f363` |

## Safety Gates

Build-time gates passed:

- base Magisk boot SHA matched
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`.
- `magiskboot` no-change repack was byte-identical to the base boot image.
- original Magisk `/init` SHA matched the pinned expected value.
- patched ramdisk replacement was limited to `/init` and extracted replacement
  matched the compiled init.
- patched boot retained the original kernel.
- AP tar member list was exactly `boot.img.lz4`.
- Odin invalid-device parse gate parsed each AP and failed only on the fake USB
  path.
- ELF checks found no `PT_INTERP`; binaries are AArch64.
- Disassembly checks found `svc` and arm64 `__NR_reboot` (`142`).
- Forbidden strings for module/configfs/ACM/gadget paths were absent.

Variant-specific gates:

- `M20A_RAW` is raw assembly: no libc, no fs setup, no marker write.
- `M20B_MINFS` contains `kmsg_emit=0` and does not contain `/dev/kmsg` or
  `phase=kmsg`.
- `M20C_KMSG` contains `/dev/kmsg`, `phase=kmsg`, and `kmsg_emit=1`.

## Future Live Order

Do not flash any M20 artifact without a fresh SHA-pinned `AGENTS.md` exception
and a guarded live helper.

If live proceeds, run exactly one step at a time:

1. `M20A_RAW` first, to re-establish raw `reboot(download)` as a positive
   control under the current operator/manual-download timing.
2. `M20B_MINFS` only if M20A is operator-clean.
3. `M20C_KMSG` only if M20B is operator-clean.

Do not return to C129 or wider M19 module prefixes until the C000 floor is
localized.

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_s22plus_m20_floor_split.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_m20_floor_split.py \
  --force

tar tf workspace/private/outputs/s22plus_native_init/m20_floor_split_v0_1/M20A_RAW/odin4/AP.tar.md5
tar tf workspace/private/outputs/s22plus_native_init/m20_floor_split_v0_1/M20B_MINFS/odin4/AP.tar.md5
tar tf workspace/private/outputs/s22plus_native_init/m20_floor_split_v0_1/M20C_KMSG/odin4/AP.tar.md5

strings -a workspace/private/outputs/s22plus_native_init/m20_floor_split_v0_1/M20B_MINFS/build/s22plus_init_m20b_minfs \
  | rg '/dev/kmsg|phase=kmsg|kmsg_emit=1|S22_NATIVE_INIT_M20B|kmsg_emit=0|reboot_request=download'

strings -a workspace/private/outputs/s22plus_native_init/m20_floor_split_v0_1/M20C_KMSG/build/s22plus_init_m20c_kmsg \
  | rg '/dev/kmsg|phase=kmsg|kmsg_emit=1|S22_NATIVE_INIT_M20C|reboot_request=download'
```

Result:

- Build: pass.
- Static validation: pass.
- Device action: none.
