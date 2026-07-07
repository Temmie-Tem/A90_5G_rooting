# S22+ Native-Init M8 Timed-Download Live Gate Preflight - 2026-07-07

## Verdict

PASS: the M8 timed-download live gate is source-prepared and passed both
host-only `--offline-check` and default no-flash dry-run.

No live flash was run. The next command is live-capable only with the explicit
M8 ack token and operator supervision.

## Helper

```text
workspace/public/src/scripts/revalidation/s22plus_m8_timed_download_live_gate.py
```

Ack tokens:

```text
live                  S22PLUS-M8-TIMED-DOWNLOAD-LIVE-GATE
rollback-only          S22PLUS-M8-ROLLBACK-FROM-DOWNLOAD
```

The helper verifies the SHA-pinned M8 AP/manifest and rollback APs before any
device action. In live mode it waits for the original candidate Odin endpoint
to disconnect before accepting a later Odin endpoint as M8 self-download proof.

## Candidate Pins

```text
AP.tar.md5             59433518e7bea2d16f5efb62ee226c190f6a3af8673336310a2ef0fff7bee36b
boot.img               3c10c9232b8579b552d791d24e65b7b4dd8ec3625941766894a08725a7abae52
M8 /init               5c8591023d0ad801155535e9b535993fb3122c4d3e4c86139d36a819ee72c3b2
M8 delta batch         6831a24ac12ddf0bfdb9b5695dcd3aada7f200aa4a998864874c207efa31bc9d
base boot              2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                 bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
vendor ramdisk         41b2481b779ff48863c300250dabf1b3dcc45c7f58fab421fcf6df1245145193
```

Rollback pins:

```text
Magisk boot-only AP     d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot-only AP      1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

All APs are single-member `boot.img.lz4` Odin archives.

## Gate Semantics

M8 success is not ACM. The only positive live proof is:

```text
candidate AP flashed
original Odin endpoint disconnected
later Odin endpoint appeared within bounded wait
rollback AP flashed
Android/root baseline returned
```

If the candidate does not self-return to download mode, the operator must enter
download mode manually and use:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m8_timed_download_live_gate.py \
  --rollback-from-download --ack S22PLUS-M8-ROLLBACK-FROM-DOWNLOAD
```

## Validation

Commands run:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m8_timed_download_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m8_timed_download_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m8_timed_download_live_gate.py
```

Private run logs:

```text
workspace/private/runs/s22plus_m8_timed_download_live_gate_20260707T103611Z/s22plus_m8_timed_download_live_gate.txt
workspace/private/runs/s22plus_m8_timed_download_live_gate_20260707T103619Z/s22plus_m8_timed_download_live_gate.txt
```

Offline-check result:

```text
M8 candidate and rollback APs verified
device_action=0
agents_exception_checked=0
android_checked=0
```

Default dry-run result:

```text
agents_exception_missing=[]
android_stability_result=ok samples=4
current_boot_hash=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
odin_l_rc=0
```

Manifest gates checked by the helper:

```text
boot_only=true
live_flash_authorized=false
module_binary_injection=false
module_files_injected_into_boot_ramdisk=0
module_list_files_injected_into_boot_ramdisk=1
batch_count=18
batch_bytes=255
m7_only_count=36
m7_overlap_with_m5_count=17
m5_only_not_in_m7_count=9
tar_members=["boot.img.lz4"]
nochange_repack_boot == base_boot
```

## Next

The supervised live command is prepared but not executed:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m8_timed_download_live_gate.py \
  --live --ack S22PLUS-M8-TIMED-DOWNLOAD-LIVE-GATE
```

Expected branch interpretation:

- self-download observed: native PID1 survived the first 18 M7-only modules;
  continue with the later M7-only delta or USB/configfs path.
- no self-download / bootloop: culprit is in or before the first 18-module M8
  batch; manually enter download mode and rollback.
