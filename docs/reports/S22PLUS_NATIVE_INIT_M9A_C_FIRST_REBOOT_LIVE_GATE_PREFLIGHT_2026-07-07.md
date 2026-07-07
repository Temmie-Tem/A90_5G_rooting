# S22+ Native-Init M9A C First-Reboot Live Gate Preflight - 2026-07-07

## Verdict

M9A live gate preflight passed. No live flash was run.

Codex added the SHA-pinned `AGENTS.md` M9A boot-only/Odin exceptions and the
guarded helper
`workspace/public/src/scripts/revalidation/s22plus_m9a_c_first_reboot_live_gate.py`.
The helper now verifies the exact M9A candidate, rollback APs, manifest safety,
`AGENTS.md` authorization text, Android/Magisk baseline stability, and current
boot hash before any live flash.

## Candidate

```text
AP.tar.md5             c953f74fe7e3cdc226ebd3e1f0bac2142ee39e14483d87022714ae98e336d6b1
boot.img               4c998680a1ccdbd5017053d7da58858ab818fc0644f08ef5bb0fc5d0dcc2d981
M9A /init              46dfc4ecf92457260484d38360c70c0a45a1b7aead3a5cac567ec21ab2c7d97f
source                 6248617a4d2fe077768aef1324937659d33a0c93a453d0ecf9cd8cc3d3ec34a8
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
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m9a_c_first_reboot_live_gate.py --offline-check
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
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m9a_c_first_reboot_live_gate.py
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
intended_syscall_count=1
intended_syscalls=["reboot"]
marker_write=false
kmsg_write=false
vfs_setup=false
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
workspace/private/runs/s22plus_m9a_c_first_reboot_live_gate_20260707T113335Z/s22plus_m9a_c_first_reboot_live_gate.txt
workspace/private/runs/s22plus_m9a_c_first_reboot_live_gate_20260707T113335Z_01/s22plus_m9a_c_first_reboot_live_gate.txt
```

## Live Contract

The next supervised live command is:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m9a_c_first_reboot_live_gate.py --live --ack S22PLUS-M9A-C-FIRST-REBOOT-LIVE-GATE
```

Expected branch logic:

```text
original Odin endpoint disconnects, later Odin endpoint appears:
  M9A freestanding C entry, build-id/.eh_frame metadata, stack/helper path, and
  immediate reboot("download") syscall are viable.
  Roll back immediately through the helper and split M8A side effects next.

no later Odin endpoint / bootloop:
  Enter download mode manually, then run:
  PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m9a_c_first_reboot_live_gate.py --rollback-from-download --ack S22PLUS-M9A-ROLLBACK-FROM-DOWNLOAD
  Treat the failure as C entry/compiler metadata/stack-helper path until proved otherwise.
```

No live flash was executed in this preflight unit.
