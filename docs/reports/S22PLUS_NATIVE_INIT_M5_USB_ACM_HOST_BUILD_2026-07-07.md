# S22+ Native-Init M5 USB-ACM Host Build - 2026-07-07

## Scope

Host-only build of the S22+ M5 USB-ACM control-channel candidate. No live
flash was run, no device partition was written, and no reboot was requested.

This refresh supersedes the earlier glibc-static M5 v0.3 candidate. `GOAL.md`
pre-registered the bootloop triage risk: glibc static PID1 startup is still a
confound on this device. M5 v0.4 therefore uses a freestanding raw-syscall
runtime matching the M4T2/M4T3 runtime shape already proven by live behavior.

## Inputs

```text
source   workspace/public/src/native-init/s22plus_init_usb_acm_m5_freestanding.c
builder  workspace/public/src/scripts/revalidation/build_s22plus_inplace_m5_usb_acm.py
modules  workspace/private/inputs/s22plus_module_bundles/FYG8_usb_first_m2
base     workspace/private/outputs/s22plus_magisk_root_boot_only/boot.img
```

The builder starts from the known-booting Magisk boot image, proves a no-change
`magiskboot unpack/repack` is byte-identical, replaces only ramdisk `/init`,
injects the measured 26-module USB-first bundle under `/lib/modules/s22plus-m5`,
and emits a boot-only Odin AP containing exactly `boot.img.lz4`.

## Runtime

M5 v0.4 is not linked through glibc:

```text
aarch64-linux-gnu-gcc -nostdlib -static -ffreestanding -fno-builtin \
  -fno-stack-protector -Os -Wall -Wextra -Werror -Wl,-e,_start
```

The built `/init` is an AArch64 `EXEC` static binary with no program
interpreter in `readelf -l`. The marker includes:

```text
S22_NATIVE_INIT_USB_ACM_M5 version=0.4 runtime=freestanding raw_syscalls=1
```

## Native Init Behavior

The candidate uses direct syscalls to mount `/proc`, `/sys`, `/dev`, `/run`,
and `/config`; create minimal character nodes; emit kmsg markers; `finit_module`
the 26 FYG8 USB-first modules; create a configfs `ss_acm.0` gadget; retry UDC
binding; write `S22_NATIVE_INIT_USB_ACM_M5 READY` to `/dev/ttyGS0`; accept
`download`, `reboot-download`, or `S22M5_DOWNLOAD`; and call
`reboot(..., "download")` only after a recognized host ACM command.

It does not start Android or Magisk, mount persistent partitions, write block
devices, touch watchdog, install modules outside the ramdisk bundle, or
auto-reboot on a timer.

## Built Artifact

```text
output      workspace/private/outputs/s22plus_native_init/inplace_m5_usb_acm_v0_4_freestanding
AP.tar.md5  workspace/private/outputs/s22plus_native_init/inplace_m5_usb_acm_v0_4_freestanding/odin4/AP.tar.md5
member      boot.img.lz4
```

Hashes:

```text
AP.tar.md5                  5bce15dede8bcd84b8ead1a7f6db6b09135d38637c983d06965930c40a00159f
AP.tar                      2b59f03ef607f7279fcacb336e8c556b6b1571b7bcebd8fa52e9f8fac4424812
boot.img                    3f4e9a514549a2cad2475ef7ef745dfc7e832c910cf1cca25ec4654c9c5522a1
boot.img.lz4                3f9f45ca6c76f6a34f72c253817330d8506b1beb23d28f60f853f3bf7333e6f5
base Magisk boot            2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                      bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
M5 /init                    596e4198bbdfece9eb1c227acd19cdca1934a440a544fe43cfdf79976a4fc594
source                      20f97dc64169a0c245f80caec731a257270f76757d72fef0755f8ed11e941b5a
module bundle manifest      1c22c93496e03a7df6dd74959511797b6d033b74361d3d3733d7be8269a5fa05
ramdisk after               0bfdc4a5dd13b4054e3c0b5543918be68e1434c6c60508ed7cf5705fb701ad10
```

Sizes:

```text
AP.tar.md5                  100669481
boot.img                    100663296
boot.img.lz4                100663699
M5 /init                    66144
module bundle total         2854024
ramdisk before              1492480
ramdisk after               4217572
```

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_s22plus_inplace_m5_usb_acm.py \
  workspace/public/src/scripts/revalidation/s22plus_m5_usb_acm_live_gate.py
aarch64-linux-gnu-gcc -nostdlib -static -ffreestanding -fno-builtin \
  -fno-stack-protector -Os -Wall -Wextra -Werror -Wl,-e,_start \
  -o /tmp/s22plus_m5_freestanding_test \
  workspace/public/src/native-init/s22plus_init_usb_acm_m5_freestanding.c
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_inplace_m5_usb_acm.py --force
tar -tf workspace/private/outputs/s22plus_native_init/inplace_m5_usb_acm_v0_4_freestanding/odin4/AP.tar.md5
git diff --check
```

All passed. The builder also verified the base boot size, patched boot size,
single tar member, module count and hashes, first inserted module extraction
hash, unchanged kernel hash, byte-identical no-change repack, and Odin
invalid-device parse gate.

## Safety State

This is still host-build evidence only. A live test must use the SHA-pinned M5
helper and `AGENTS.md` exception for the v0.4 AP above. Rollback remains the
pinned Magisk boot-only AP first, with stock boot-only AP fallback only if
operator-selected.
