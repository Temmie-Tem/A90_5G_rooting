# S22+ Native-Init M10A1 Stat-Dev Reboot Live Gate Preflight - 2026-07-07

## Verdict

M10A1 live gate preflight passed. No live flash was run.

Codex added the SHA-pinned `AGENTS.md` M10A1 boot-only/Odin exception and the
guarded helper
`workspace/public/src/scripts/revalidation/s22plus_m10a1_stat_dev_reboot_live_gate.py`.
The helper verifies the exact M10A1 candidate, rollback APs, manifest safety,
`AGENTS.md` authorization text, Android/Magisk baseline stability, and current
boot hash before any live flash.

The helper also fixes the M10A interpretation trap: a later Odin endpoint is
logged as manually ambiguous and must not be treated as automatic self-download
proof unless the operator confirms no manual download-mode entry occurred.

## Candidate

```text
AP.tar.md5             68a7f1f5b336a32d882e7cdde73f299815d689b6885b724a6b6c7672bdda00bf
boot.img               2fe6b3270f7d493f677f126594061eea33d22de7abe98dc2210fe8050961ecb2
M10A1 /init            477583121c6c29f5eb31866c034352abb2f03c8fe97ec71e2f63ecbddd6f1642
source                 a60b66ec5d07f93bb9e29ac96c342e57621815630c29f31653b104e19f7ff86b
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
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m10a1_stat_dev_reboot_live_gate.py --offline-check
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
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m10a1_stat_dev_reboot_live_gate.py
```

Result:

```text
dry-run ok
agents_exception_missing=[]
android_stability_result=ok samples=4
current_boot_hash matches 2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
host Odin endpoint absent during dry-run snapshot
manual_download_ambiguity_policy=later Odin endpoint is not automatic proof without operator confirmation
```

Manifest safety verified:

```text
boot_only=true
host_only_build=true
live_flash_authorized=false
requires_new_sha_pinned_agents_exception_before_flash=true
intended_syscall_count=2
intended_syscalls=["newfstatat", "reboot"]
first_runtime_side_effect=newfstatat-/dev-readonly
vfs_setup=newfstatat-dev-readonly-only
vfs_mutation=false
mkdirat=false
marker_write=false
kmsg_write=false
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
workspace/private/runs/s22plus_m10a1_stat_dev_reboot_live_gate_20260707T121426Z/s22plus_m10a1_stat_dev_reboot_live_gate.txt
workspace/private/runs/s22plus_m10a1_stat_dev_reboot_live_gate_20260707T121432Z/s22plus_m10a1_stat_dev_reboot_live_gate.txt
```

## Live Contract

The next supervised live command is:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m10a1_stat_dev_reboot_live_gate.py --live --ack S22PLUS-M10A1-STAT-DEV-REBOOT-LIVE-GATE
```

Rollback-only command if the candidate does not return to download mode and the
operator manually enters download mode:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m10a1_stat_dev_reboot_live_gate.py --rollback-from-download --ack S22PLUS-M10A1-ROLLBACK-FROM-DOWNLOAD
```

Expected branch logic:

```text
original Odin endpoint disconnects, later Odin endpoint appears, operator confirms no manual entry:
  read-only pathname lookup/VFS access is survivable before reboot.
  M10A failure points at mkdir mutation or directory-create path.

original Odin endpoint disconnects, later Odin endpoint appears, operator manually entered download:
  rollback succeeds, but result is ambiguous/manual and not automatic proof.

no later Odin endpoint / bootloop:
  enter download mode manually, run rollback-only command, and treat pathname VFS access itself as suspect.
```

No live flash was executed in this preflight unit.
