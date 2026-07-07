# S22+ Native-Init M12 M5-Floor Live Gate Preflight - 2026-07-07

## Verdict

M12 live-gate preflight passed. No live flash was run.

Codex added the SHA-pinned `AGENTS.md` M12 boot-only/Odin exception and the
guarded helper
`workspace/public/src/scripts/revalidation/s22plus_m12_m5_floor_live_gate.py`.
The helper verifies the exact M12 candidate, rollback APs, manifest safety,
`AGENTS.md` authorization text, Android/Magisk baseline stability, and current
boot hash before any live flash.

M12 deliberately has no reboot beacon and no ACM-triggered download command.
If the candidate parks or exposes ACM, rollback requires operator manual
download-mode entry followed by the helper's rollback-only mode.

## Candidate

```text
AP.tar.md5             deece127aa5c85dbf4937459fc528f2cfcd9926fb3556f26ffc9b10fbfe932cb
boot.img               f211e46c7153df31c458a907f4ac56fe4a3d160d8ded2a13a8e0e31af6f5106c
M12 /init              50ae525230680c495d3c40fc671cb88118e8bd473cef92873266142549a28002
M12 module list        c2e44f6f934542f8f7889ef09245294ee342c5ae03a0f6db9988b58b943ddc16
source                 5b43593a24b3b03a667f5515b8a558e40121b4da091efb56adf383ea50240392
base Magisk boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                 bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
vendor_ramdisk00       41b2481b779ff48863c300250dabf1b3dcc45c7f58fab421fcf6df1245145193
```

Rollback APs verified by the helper:

```text
Magisk boot-only rollback AP  d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot-only fallback AP   1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

## Helper Gates

Offline-check command:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m12_m5_floor_live_gate.py --offline-check
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
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m12_m5_floor_live_gate.py
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
module_list_path=/s22plus_m12_m5_floor.modules
module_list_files_injected_into_boot_ramdisk=1
module_files_injected_into_boot_ramdisk=0
configfs_runtime_gadget=ss_acm.0 only
udc_binding=a600000.dwc3 only; never dummy_udc.0
usb_role_force=attempt /sys/class/usb_role/*/role=device
block_device_writes=false
tar_members=["boot.img.lz4"]
```

M12 floor gates verified:

```text
subset_count=24
subset_bytes=391
m5_floor_common_count=24
m11_only_reference_count=24
m5_only_withheld_modules=usb_notifier_qcom.ko, qc_usb_audio.ko
order_source=M5 v0.4 order filtered to modules common with M11
explicit_blocklist_absent_from_final_subset=true
```

Runtime no-reboot gates verified:

```text
required_string=no_reboot_beacon=1
required_string=acm_cmd_status=1
required_string=S22_NATIVE_INIT_USB_ACM_M12 ACK status park
arm64 __NR_reboot=142 load absent from manifest objdump
```

Private run logs:

```text
workspace/private/runs/s22plus_m12_m5_floor_live_gate_20260707T135247Z/s22plus_m12_m5_floor_live_gate.txt
workspace/private/runs/s22plus_m12_m5_floor_live_gate_20260707T135247Z_01/s22plus_m12_m5_floor_live_gate.txt
```

## Live Contract

The next supervised live command is:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m12_m5_floor_live_gate.py --live --ack S22PLUS-M12-M5-FLOOR-LIVE-GATE
```

Rollback-only command after the operator manually enters download mode:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m12_m5_floor_live_gate.py --rollback-from-download --ack S22PLUS-M12-ROLLBACK-FROM-DOWNLOAD
```

Expected branch logic:

```text
ACM appears:
  target signal reached. Enter download mode manually, then run rollback-only.

No ACM, device visibly parks:
  M5-floor candidate survived; add M11-only substrate back in small groups.
  Enter download mode manually, then run rollback-only.

Bootloop / Odin endpoint appears:
  if Odin endpoint is already present, helper can rollback immediately; otherwise enter download mode manually and run rollback-only.

ADB returns:
  unexpected Android return. Helper attempts host-commanded rollback through download mode.
```

No live flash was executed in this preflight unit.
