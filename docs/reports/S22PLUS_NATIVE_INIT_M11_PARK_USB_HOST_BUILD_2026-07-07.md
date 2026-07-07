# S22+ Native-Init M11 Park USB Host Build - 2026-07-07

## Verdict

M11 host-only build passed. No live flash was run.

M11 implements the operator pivot away from the unreliable reboot-download
beacon. It keeps the M7 freestanding PID1/configfs/ACM shape, removes the
candidate reboot syscall path, derives a 48-module park-based USB/platform/
Max77705 subset, and parks forever. The intended live signal is visible
park-vs-loop plus host ACM enumeration, not self-download.

## Artifacts

```text
source                 workspace/public/src/native-init/s22plus_init_usb_acm_m11_park_usb.c
builder                workspace/public/src/scripts/revalidation/build_s22plus_inplace_m11_park_usb.py
output                 workspace/private/outputs/s22plus_native_init/inplace_m11_park_usb_v0_1
AP.tar.md5             8b4a4fa6db3bc0b2bf5e4fd1fccf4b671fd2fbd7fbbcc08542c3be816a3f5d43
boot.img               32f2667c31f05d967529031630e5b004cf5238120ffc6ec7089dcc40a3352a3f
M11 /init              234ded5b6172a3470825a1c616e6537c3de4b2274d8c26525386f8e85d5e8d7e
M11 module list        c254be05c91199c4f69380f0488de13c7b2cde987594bc1c5d0a6657a0e8eb58
source                 ff92af817cd4564b6fd811484540e8a217ff19bbe445839981ce7818498561f6
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                 bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
vendor ramdisk         41b2481b779ff48863c300250dabf1b3dcc45c7f58fab421fcf6df1245145193
```

AP tar contents:

```text
boot.img.lz4
```

## M11 Runtime

Safety flags from the manifest:

```text
boot_only=true
host_only_build=true
live_flash_authorized=false
requires_new_sha_pinned_agents_exception_before_flash=true
runtime=freestanding-raw-syscall
auto_reboot=false
reboot_syscall=false
host_commanded_reboot_download=false
observation_model=park-vs-loop plus host ACM enumeration; no reboot beacon
construction=magiskboot unpack/repack; replace ramdisk /init only
module_binary_injection=false
module_list_path=/s22plus_m11_park_usb.modules
module_list_files_injected_into_boot_ramdisk=1
module_files_injected_into_boot_ramdisk=0
udc_binding=a600000.dwc3 only; never dummy_udc.0
usb_role_force=attempt /sys/class/usb_role/*/role=device
configfs_runtime_gadget=ss_acm.0 only
block_device_writes=false
persistent_partition_mount=false
```

Required strings present in the stripped `/init`:

```text
S22_NATIVE_INIT_USB_ACM_M11
version=0.1
runtime=freestanding
raw_syscalls=1
/s22plus_m11_park_usb.modules
module_list=boot_ramdisk_park_usb
watchdog_blocklist=1
no_reboot_beacon=1
acm_cmd_status=1
module_source=stock_vendor_boot_ramdisk
module_injection=list_only
a600000.dwc3
role_force=device
ss_acm.0
ttyGS0
S22M11ACM0001
S22_NATIVE_INIT_USB_ACM_M11 READY
S22_NATIVE_INIT_USB_ACM_M11 ACK status park
```

Forbidden runtime properties verified:

```text
program interpreter absent
download string absent from stripped /init
arm64 __NR_reboot=142 load absent from objdump
modules.load.recovery string absent from stripped /init
/vendor_dlkm string absent from stripped /init
s22plus-m5 string absent from stripped /init
```

## Module Subset

M11 derives a 53-module dependency closure from M11 USB/platform/Max77705 seeds,
then blocks reset-prone/debug/audio entries. Final injected text list:

```text
subset_count=48
subset_bytes=738
dependency_closure_count=53
blocked_from_closure=abc.ko, icc-debug.ko, minidump.ko, qc_usb_audio.ko, sec_debug.ko
```

First entries:

```text
clk-rpmh.ko
gcc-waipio.ko
icc-rpmh.ko
qcom_ipc_logging.ko
rpmh-regulator.ko
clk-dummy.ko
clk-qcom.ko
cmd-db.ko
debug-regulator.ko
gdsc-regulator.ko
```

Tail entries:

```text
sps_drv.ko
switch_class.ko
common_muic.ko
vbus_notifier.ko
usb_typec_manager.ko
if_cb_manager.ko
pdic_notifier_module.ko
mfd_max77705.ko
pdic_max77705.ko
spu_verify.ko
```

## Validation

Commands run:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/build_s22plus_inplace_m11_park_usb.py
aarch64-linux-gnu-gcc -fsyntax-only -nostdlib -static -ffreestanding -fno-builtin -fno-stack-protector -Os -Wall -Wextra -Werror workspace/public/src/native-init/s22plus_init_usb_acm_m11_park_usb.c
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/build_s22plus_inplace_m11_park_usb.py --force
tar -tf workspace/private/outputs/s22plus_native_init/inplace_m11_park_usb_v0_1/odin4/AP.tar.md5
strings -a workspace/private/outputs/s22plus_native_init/inplace_m11_park_usb_v0_1/build/s22plus_init_usb_acm_m11
aarch64-linux-gnu-objdump -d workspace/private/outputs/s22plus_native_init/inplace_m11_park_usb_v0_1/build/s22plus_init_usb_acm_m11
```

Build gates confirmed:

```text
no-change MagiskBoot repack byte-identical to base boot
patched kernel hash preserved
ramdisk replaced entry init mode 750
added module-list entry s22plus_m11_park_usb.modules mode 640
AP tar member list exactly ["boot.img.lz4"]
vendor .ko count 441
modules.load.recovery count 446
modules.dep count 441
dwc3_msm softdep line present
```

## Live Status

No live flash is authorized by this host-build unit. The next unit, if selected,
must add a fresh SHA-pinned `AGENTS.md` exception and a guarded M11 live helper.
Rollback for M11 should assume manual download-mode entry if the device parks
with no Android transport, because M11 deliberately has no reboot beacon.
