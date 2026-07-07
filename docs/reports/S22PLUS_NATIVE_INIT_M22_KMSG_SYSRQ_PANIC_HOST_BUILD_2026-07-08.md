# S22+ M22 Kmsg Sysrq Panic Host Build (2026-07-08)

## Verdict

HOST-ONLY BUILD PASS. No flash, reboot, Odin live action, or device write was
run for this unit.

M22 is the retained-console positive control after the DTBO+M13 no-hit. It is
not another passive park candidate. If later live-authorized with patched DTBO
ramoops enabled, it writes an early marker to `/dev/kmsg`, enables sysrq, then
writes `c` to `/proc/sysrq-trigger` so the kernel crash path should force the
marker into console-ramoops / retained last-kmsg. If sysrq returns or fails, it
falls back to `reboot(..., "download")` for recovery.

Live flashing is not authorized by this report.

## Candidate

Source:

`workspace/public/src/native-init/s22plus_init_kmsg_sysrq_panic_m22.c`

Builder:

`workspace/public/src/scripts/revalidation/build_s22plus_m22_kmsg_sysrq_panic.py`

Private output:

`workspace/private/outputs/s22plus_native_init/m22_kmsg_sysrq_panic_v0_1`

Runtime shape:

```text
freestanding direct PID1
no libc / PT_INTERP
minimal /dev + /proc + /sys setup
write /dev/kmsg marker
write /proc/sys/kernel/sysrq = 1
write /proc/sysrq-trigger = c
fallback nanosleep(250ms) -> reboot(download) -> wfe park
no module load
no configfs / USB role force / UDC binding
no Android or Magisk handoff
```

## Hashes

```text
source              a48818067b6b79578bdc6cd0e327d9e7c316b10bca1be7d838605c7d7e0e6444
base_boot           2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
nochange_repack     2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
original_magisk_init 383670a7ba3a6a4b79e5f3467e1da4b66a5df66a9b356ab9f70916854dd6b468
kernel              bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
init                2b711b0fccf6cdd9b4c9beb5ba2f1a095d4e873b42bd03a02eb4655106873831
boot_img            c79bbe1fb1cee7d7e3c70ff4c249d6e0359760e203cc0bebb1c71d6cc0518802
boot_img_lz4        b54b41079bb902a13045d4a78897e5e3ffc6c5ae3315dc0db356fb29775b1d28
AP.tar.md5          77c17e9d3fb62319823499e0e8e7fcd485cd180dd730e40d9c2a8112308c4852
```

AP member list:

```text
boot.img.lz4
```

## Static Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_s22plus_m22_kmsg_sysrq_panic.py

aarch64-linux-gnu-gcc -std=gnu11 -Wall -Wextra -Werror -Os \
  -ffreestanding -fno-builtin -fno-stack-protector -nostdlib -static \
  -Wl,--build-id=none -Wl,-e,_start -Wl,-z,noexecstack \
  -o /tmp/s22plus_m22_init_check \
  workspace/public/src/native-init/s22plus_init_kmsg_sysrq_panic_m22.c

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_m22_kmsg_sysrq_panic.py \
  --force
```

Results:

- `py_compile`: pass.
- Standalone M22 `/init` compile: pass.
- M22 `/init` ELF: AArch64 executable, statically linked, no interpreter.
- Final stripped `/init` size: 2272 bytes.
- Required strings present:
  `S22_NATIVE_INIT_M22_KMSG_SYSRQ_PANIC`, `/dev/kmsg`,
  `/proc/sys/kernel/sysrq`, `/proc/sysrq-trigger`, `sysrq_trigger=c`,
  `phase=kmsg-before-sysrq`, `phase=sysrq-trigger-about-to-write`,
  `phase=sysrq-returned`, and `download`.
- Forbidden strings absent: dynamic loader/libc, `/lib/modules`,
  `finit_module`, module lists, `ttyGS0`, `ss_acm.0`, `usb_gadget`, and
  `/config`.
- Disassembly loads the expected arm64 syscall numbers: `mknodat=33`,
  `mkdirat=34`, `mount=40`, `openat=56`, `close=57`, `write=64`,
  `nanosleep=101`, and `reboot=142`.
- Final `/init` contains 11 `svc #0` instructions.
- Magiskboot no-change repack is byte-identical to the rooted Magisk base boot.
- Patched boot remains boot-partition sized and changes only through the
  intended ramdisk `/init` replacement path.
- Odin parse gate with an intentionally invalid device parsed the AP and failed
  only on the nonexistent USB path.

## Safety State

The manifest records:

```text
boot_only=true
host_only_build=true
live_flash_authorized=false
requires_new_sha_pinned_agents_exception_before_flash=true
requires_ramoops_dtbo_enabled_before_flash=true
base_is_known_booting_magisk_boot=true
module_insertions=false
module_binary_injection=false
configfs_runtime_gadget=false
udc_binding=false
usb_role_force=false
block_device_writes=false
kmsg_marker_write=true
procfs_writes=["/proc/sys/kernel/sysrq", "/proc/sysrq-trigger"]
intentional_kernel_crash=sysrq-trigger-c
fallback_reboot=download
```

## Future Live Interpretation

M22 should only be considered after a fresh SHA-pinned `AGENTS.md` exception
that combines the already-proven patched-DTBO status enable step with this
boot-only candidate.

Expected interpretations:

- PASS: with patched DTBO enabled, post-rollback pstore or retained last-kmsg
  contains the M22 marker and/or sysrq crash evidence.
- SYSRQ RETURNED: marker reached `/dev/kmsg`, but sysrq did not crash; fallback
  download may still recover the device, but retained-console proof is weaker.
- NO MARKER: retained console is still not useful on this path. Stop blind
  native-init candidates and move to EUD/UART.

## Next

Do not flash M22 from this report. The next unit, if selected, must add a
guarded M22+DTBO live helper and a fresh one-shot `AGENTS.md` exception with the
hashes above, explicit intentional-crash wording, stock-DTBO restore, Magisk
boot rollback, and fail-closed default dry-run.
