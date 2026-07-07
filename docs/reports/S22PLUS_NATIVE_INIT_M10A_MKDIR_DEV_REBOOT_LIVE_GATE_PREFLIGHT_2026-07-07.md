# S22+ Native-Init M10A Mkdir-Dev Reboot Live Gate Preflight - 2026-07-07

## Verdict

M10A live gate preflight passed. No live flash was run.

Codex added the SHA-pinned `AGENTS.md` M10A boot-only/Odin exceptions and the
guarded helper
`workspace/public/src/scripts/revalidation/s22plus_m10a_mkdir_dev_reboot_live_gate.py`.
The helper verifies the exact M10A candidate, rollback APs, manifest safety,
`AGENTS.md` authorization text, Android/Magisk baseline stability, and current
boot hash before any live flash. Its default self-download observation window
is 150 seconds, reflecting the M9A delayed-download result.

## Candidate

```text
AP.tar.md5             d71c8c82d2703892802228dd61ded561a9b4f90c678db15452014f2477170105
boot.img               c62fce5e444bad47e2b934f6e9e82bc731058a0c9494629f0eb9044ff92e8b24
M10A /init             8f954dfcd5d5887f8c1659e7e658617561627d9c7fecc518972a795ac20422b3
source                 c12b710f93b957313ad1018de40ebe2dec53883c5de6d018c9d5577b1a426cf0
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                 bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
runtime                freestanding-c-raw-syscall
```

Rollback APs verified by the helper:

```text
Magisk boot-only rollback AP  d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot-only fallback AP   1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

## Helper Gates

Offline-check command:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m10a_mkdir_dev_reboot_live_gate.py --offline-check
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
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m10a_mkdir_dev_reboot_live_gate.py
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
intended_syscall_count=2
intended_syscalls=["mkdirat", "reboot"]
first_runtime_side_effect=mkdirat-/dev-0755
marker_write=false
kmsg_write=false
vfs_setup=mkdirat-dev-only
mknodat=false
mounts=false
sleep_before_reboot=false
module_insertions=false
module_binary_injection=false
module_files_injected_into_boot_ramdisk=0
module_list_files_injected_into_boot_ramdisk=0
configfs_runtime_gadget=false
udc_binding=false
usb_role_force=false
block_device_writes=false
tar_members=["boot.img.lz4"]
```

Private run logs:

```text
workspace/private/runs/s22plus_m10a_mkdir_dev_reboot_live_gate_20260707T115148Z/s22plus_m10a_mkdir_dev_reboot_live_gate.txt
workspace/private/runs/s22plus_m10a_mkdir_dev_reboot_live_gate_20260707T115148Z_01/s22plus_m10a_mkdir_dev_reboot_live_gate.txt
```

## Live Contract

The next supervised live command is:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m10a_mkdir_dev_reboot_live_gate.py --live --ack S22PLUS-M10A-MKDIR-DEV-REBOOT-LIVE-GATE
```

Expected branch logic:

```text
original Odin endpoint disconnects, later Odin endpoint appears within 150 s:
  mkdirat("/dev") and basic pathname VFS access are survivable before reboot.
  Roll back immediately through the helper and add the next single side effect.

no later Odin endpoint / bootloop:
  Enter download mode manually, then run:
  PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m10a_mkdir_dev_reboot_live_gate.py --rollback-from-download --ack S22PLUS-M10A-ROLLBACK-FROM-DOWNLOAD
  Treat the first VFS syscall or pathname access as the failing boundary.
```

No live flash was executed in this preflight unit.
