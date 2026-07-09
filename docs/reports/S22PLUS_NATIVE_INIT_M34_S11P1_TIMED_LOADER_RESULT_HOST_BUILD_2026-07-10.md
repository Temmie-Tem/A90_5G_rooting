# S22+ M34 S11P1 Timed Loader-Result Host Build

Date: 2026-07-10 KST / 2026-07-09 UTC  
Scope: host-only source/build unit; no flash, no reboot, no partition write

## Purpose

S11P0 live missed because its combined one-bit predicate did not enter the
true-action Download path. That left too much ambiguity: loader open/read
failure, `cmd-db.ko` attempt/rc failure, first later module failure, or a
`/proc/modules` observation artifact all collapsed into the same parked MISS.

S11P1 keeps the same isolated S9/S10C0 module recipe and does not touch
configfs, UDC, USB role, TypeC role, power rails, persistent mounts, block
devices, Android handoff, Magisk modules, or any non-boot partition. The only
semantic change from S11P0 is the observation channel: S11P1 always requests
`reboot(download)` after a bounded delay, and the delay encodes the loader/proc
outcome.

## Runtime Contract

```text
stage=S11P1
stage_number=22
version=0.13
module_load_probe=timed_first_failure_or_proc_modules_result
s11p1_timed_loader_result=1
timed_download_beacon=1
always_reboot_download=1
true_action=timed_reboot_download
false_action=timed_reboot_download
```

Delay model:

```text
6s    modules open/read failure
12s   cmd-db was not attempted
18s   cmd-db was attempted but rc was not accepted
20s+N first failing module index N
116s  no first failure, but watchdog module absent from /proc/modules
122s  watchdog visible, but cmd_db absent from /proc/modules
128s  watchdog and cmd_db visible in /proc/modules
```

The module list is still the pinned 89-module devlink-supplier closure. The
important early positions for S11P1 timing interpretation are:

```text
5   cmd-db.ko
21  qcom_wdt_core.ko
22  gh_virt_wdt.ko
```

## Host Build

Command:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_m34_runtime_gadget_split.py \
  --stages S11P1 \
  --force
```

Output:

```text
out_dir=workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_15
AP=workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_15/S11P1/odin4/AP.tar.md5
```

Hashes:

```text
AP.tar.md5               1bc209674aa6b496bcc4132eae4343c1311de06143164771994cc8b1df945b56
boot.img                 874c312b4ce1b95388c158a686f22e56d7a5278dd09cfab13c0c853ab688c61e
boot.img.lz4             cb4234a257a91b4b7b43343f97c1c9f90049a2daca59cc28f19da5159567605a
/init                    af4eb75a8bcdcbbe8bd4fe81e1100cbc34ef786c1c2e64b09b111582c727c3d1
module list              c07425f4c738b53822e9f6783a142a2b5eafd72a15bd34c06fb3b49357c8fe26
base Magisk boot         2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
no-change repack boot    2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

The AP tar contains exactly one member:

```text
boot.img.lz4
```

## Validation

Passed:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_s22plus_m34_runtime_gadget_split.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_s22plus_m34_runtime_gadget_split_build

Ran 5 tests in 0.025s
OK
```

Manifest checks:

```text
labels=['S11P1']
tar_members=['boot.img.lz4']
live_flash_authorized=false
auto_reboot=download-if-probe-true-or-s11p1-timed-always
requires_new_sha_pinned_agents_exception_before_flash=true
```

## Live Status

No S11P1 live gate was run. No Odin flash, reboot, partition write,
native-init candidate execution, or rollback was performed in this unit.

Before live use, add a fresh narrow `AGENTS.md` exception or equivalent checked
live gate pinning the exact S11P1 hashes above, requiring boot-only AP scope,
and preserving the current Magisk boot rollback rules.
