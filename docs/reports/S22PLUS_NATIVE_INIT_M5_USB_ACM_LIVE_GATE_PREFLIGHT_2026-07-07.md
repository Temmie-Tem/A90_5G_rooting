# S22+ Native-Init M5 USB-ACM Live Gate Preflight - 2026-07-07

## Scope

Host-side preflight for the M5 USB-ACM live gate. No live flash was run, no
device partition was written, and no reboot was requested in this unit.

This preflight now targets M5 v0.4 freestanding, not the earlier glibc-static
v0.3 candidate. The change removes glibc static PID1 startup as a confound
before testing the USB module/configfs chain.

## Helper

```text
workspace/public/src/scripts/revalidation/s22plus_m5_usb_acm_live_gate.py
```

Live ack token:

```text
S22PLUS-M5-USB-ACM-LIVE-GATE
```

Rollback-only ack token:

```text
S22PLUS-M5-ROLLBACK-FROM-DOWNLOAD
```

Latest dry-run private log:

```text
workspace/private/runs/s22plus_m5_usb_acm_live_gate_20260706T213744Z/s22plus_m5_usb_acm_live_gate.txt
```

## Pinned Candidate

```text
AP.tar.md5                  5bce15dede8bcd84b8ead1a7f6db6b09135d38637c983d06965930c40a00159f
boot.img                    3f4e9a514549a2cad2475ef7ef745dfc7e832c910cf1cca25ec4654c9c5522a1
base Magisk boot            2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel                      bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
M5 /init                    596e4198bbdfece9eb1c227acd19cdca1934a440a544fe43cfdf79976a4fc594
module bundle manifest      1c22c93496e03a7df6dd74959511797b6d033b74361d3d3733d7be8269a5fa05
```

The candidate AP contains exactly:

```text
boot.img.lz4
```

Manifest safety requires:

```text
runtime=freestanding-raw-syscall
glibc_static_startup=false
host_commanded_reboot_download=true
boot_only=true
block_device_writes=false
persistent_partition_mount=false
```

## Rollback Payloads

```text
Magisk boot-only AP          d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot-only fallback AP  1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

Both rollback APs are verified as single-member `boot.img.lz4` packages.

## Dry-Run Result

The strengthened dry-run passed. It verifies the candidate hashes, rollback
hashes, `AGENTS.md` exception, manifest safety, Android identity, current
Magisk/root baseline, current boot hash, and Android stability before live.

Recent stability evidence from the dry-run:

```text
android_stability_result=ok samples=4
current_boot_hash=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
boot_completed=1
bootanim=stopped
Magisk root available
```

The helper also records the current Android ACM baseline:

```text
path=/dev/ttyACM0
vendor=04e8
product=6860
model=SAMSUNG_Android
driver=cdc_acm
```

M5 live success is keyed on the M5-specific ACM identity or banner, not on
plain `/dev/ttyACM*` existence:

```text
vendor=04e8
product=685d
serial=S22M5ACM0001
S22_NATIVE_INIT_USB_ACM_M5 READY
```

If the M5 ACM appears, the helper writes `download\n`, waits for
`S22_NATIVE_INIT_USB_ACM_M5 ACK download`, then waits for Odin/download mode
and rolls back to the pinned Magisk boot-only AP. If ACM does not appear, or
ACM proof appears but download mode does not, rollback requires manual
download-mode entry plus `--rollback-from-download`.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/build_s22plus_inplace_m5_usb_acm.py \
  workspace/public/src/scripts/revalidation/s22plus_m5_usb_acm_live_gate.py
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m5_usb_acm_live_gate.py
git diff --check
```

All passed.

## Next

The next live command, if supervised, is:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m5_usb_acm_live_gate.py --live --ack S22PLUS-M5-USB-ACM-LIVE-GATE
```

If the phone is already in download mode and only rollback is needed:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m5_usb_acm_live_gate.py --rollback-from-download --ack S22PLUS-M5-ROLLBACK-FROM-DOWNLOAD
```

Do not run this unattended.
