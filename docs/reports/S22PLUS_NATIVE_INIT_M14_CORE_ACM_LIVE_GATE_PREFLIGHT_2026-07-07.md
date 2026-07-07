# S22+ Native-Init M14 Core-ACM Live Gate Preflight - 2026-07-07

## Verdict

M14 live-gate preflight passed. No live flash was run.

Codex added the SHA-pinned `AGENTS.md` M14 boot-only/Odin exception and the
guarded helper
`workspace/public/src/scripts/revalidation/s22plus_m14_core_acm_live_gate.py`.
The helper verifies the exact M14 candidate, rollback APs, manifest safety,
`AGENTS.md` authorization text, Android/Magisk baseline stability, and current
boot hash before any live flash.

M14 deliberately has no reboot beacon and no ACM-triggered download command.
If the candidate parks or exposes ACM, rollback requires operator manual
download-mode entry followed by the helper's rollback-only mode.

## Candidate

```text
AP.tar.md5             080fedea35c111020f68b5fb64eb260402dbc45ac4398e282523c94bf9a8922b
boot.img               dee741af20fb3dbcd347c2fa4d45099018f54f577ddf7ae64ac3dca4a357c2e4
M14 /init              0a144b2ddde32d78b4dfe051e009f5275f2e67c8276b0fa2d1a61e3280b7eed4
M14 module list        5b52cd5c1ae26d0bf24e7654b27f254ee478673c9313afdb955a0ec4fcf35f7c
source                 8acc0bfff03ec3adbde160a7ad6975be4154c8a219e8e59ebe1a6d8b1a19b8a7
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                 bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
```

Rollback APs verified by the helper:

```text
Magisk boot-only rollback AP  d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot-only fallback AP   1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

M14 module list verified by the helper:

```text
phy-msm-ssusb-qmp.ko
phy-msm-snps-eusb2.ko
dwc3-msm.ko
usb_f_ss_acm.ko
```

## Helper Gates

Offline-check command:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m14_core_acm_live_gate.py --offline-check
```

Result:

```text
offline-check ok
device_action=0
agents_exception_checked=0
android_checked=0
```

Default dry-run command:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m14_core_acm_live_gate.py
```

Result:

```text
dry-run ok
agents_exception_missing=[]
android_stability_result=ok samples=4
current_boot_hash matches 2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
host Odin endpoint absent during dry-run snapshot
```

Manifest safety verified:

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
module_binary_injection=false
module_list_path=/s22plus_m14_core_acm.modules
module_files_injected_into_boot_ramdisk=0
module_list_files_injected_into_boot_ramdisk=1
configfs_runtime_gadget=ss_acm.0 only
udc_binding=a600000.dwc3 only; never dummy_udc.0
usb_role_force=attempt /sys/class/usb_role/*/role=device
block_device_writes=false
tar_members=["boot.img.lz4"]
```

Runtime module gates verified:

```text
required_string=module_group=core_acm
required_string=module_count=4
required_string=module_list=boot_ramdisk_core_acm
required_string=no_reboot_beacon=1
required_string=acm_cmd_status=1
required_string=S22_NATIVE_INIT_USB_ACM_M14 ACK status park
module_subset_count=4
arm64 __NR_reboot=142 load absent from manifest objdump
arm64 __NR_finit_module=273 load present in manifest objdump
forbidden strings absent from stripped /init: download, modules.load, modules.load.recovery, /vendor_dlkm, ld-linux, libc.so
```

Private run logs:

```text
workspace/private/runs/s22plus_m14_core_acm_live_gate_20260707T144359Z/s22plus_m14_core_acm_live_gate.txt
workspace/private/runs/s22plus_m14_core_acm_live_gate_20260707T144410Z/s22plus_m14_core_acm_live_gate.txt
```

## Live Contract

The next supervised live command is:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m14_core_acm_live_gate.py --live --ack S22PLUS-M14-CORE-ACM-LIVE-GATE
```

Rollback-only command after the operator manually enters download mode:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m14_core_acm_live_gate.py --rollback-from-download --ack S22PLUS-M14-ROLLBACK-FROM-DOWNLOAD
```

Expected branch logic:

```text
ACM appears:
  target signal reached. Enter download mode manually, then run rollback-only.

No ACM, device visibly parks:
  the core USB/ACM add-back is tolerated. Enter download mode manually, roll
  back, then add the next dependency group instead of changing configfs.

Bootloop / Odin endpoint appears:
  if Odin endpoint is already present, helper can rollback immediately; otherwise
  enter download mode manually and run rollback-only. Next unit bisects inside
  the four-module core group or the finit path.

ADB returns:
  unexpected Android return. Helper attempts host-commanded rollback through
  download mode.
```

No live flash was executed in this preflight unit.
