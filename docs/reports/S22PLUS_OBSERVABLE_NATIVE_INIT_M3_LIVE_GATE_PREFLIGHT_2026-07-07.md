# S22+ Observable Native-Init M3 Live Gate Preflight - 2026-07-07

## Scope

Prepared and dry-ran the guarded live gate for the M3 observable native-init
candidate. No live flash, Odin transfer, reboot, partition write, sysfs/configfs
write, module load, Magisk module install, or recovery action was performed.

## Added Helper

```text
workspace/public/src/scripts/revalidation/s22plus_m3_observable_live_gate.py
```

The helper is fail-closed:

- dry-run is the default;
- live mode requires `--live --ack S22PLUS-M3-OBSERVABLE-LIVE-GATE`;
- `AGENTS.md` must contain the exact M3 SHA-pinned exception;
- candidate AP must match the exact M3 AP hash and contain only
  `boot.img.lz4`;
- rollback APs must match the pinned Magisk boot-only AP and stock boot-only
  fallback AP;
- current Android must be a single `SM-S906N` / `g0q` / `S906NKSS7FYG8`
  device with boot completed and orange verified boot;
- the live path is attended: after candidate flash and bounded host-side
  observation, the operator must put the phone into download mode for rollback.

## AGENTS Update

Added a narrow M3 exception for exactly one attended boot-only live gate:

```text
candidate AP.tar.md5 SHA256=d588b84c231a53ba8447716af2f0bee6128f738634c951b8728fed662c17807e
candidate boot.img SHA256=583a748f045c1053b808ca5b337c66336d3838f3fa240fa5de8e4dbf3f819734
primary rollback Magisk AP.tar.md5 SHA256=d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
fallback rollback stock AP.tar.md5 SHA256=1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

It authorizes only the M3 direct PID1 candidate behavior already built in the
host report: kmsg/pmsg marker, 26 USB-first `.ko` insertions, minimal runtime
configfs `ncm.0` link-only gadget, and heartbeat park. It does not authorize
display/distro/M4 work or any non-boot partition.

## Dry-Run Command

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m3_observable_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m3_observable_live_gate.py
```

Private dry-run log:

```text
workspace/private/runs/s22plus_m3_observable_live_gate_20260706T180616Z/
```

## Dry-Run Result

PASS:

```text
agents_exception_missing=[]
m3_candidate_sha256=d588b84c231a53ba8447716af2f0bee6128f738634c951b8728fed662c17807e
m3_candidate_members=['boot.img.lz4']
magisk_boot_rollback_sha256=d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
magisk_boot_rollback_members=['boot.img.lz4']
stock_boot_fallback_sha256=1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
stock_boot_fallback_members=['boot.img.lz4']
android_preflight=model SM-S906N, device g0q, bootloader S906NKSS7FYG8, boot_completed 1, vbstate orange
magisk_root_preflight=uid 0 root context magisk
host_snapshot=collected
```

The helper also captured private host-side `ip`, `adb devices`, `odin4 -l`, and
host dmesg snapshot files for the dry-run baseline. They remain private because
they can contain device and host identifiers.

## Live Boundary

Live M3 is now gated but not executed. The live command shape is:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m3_observable_live_gate.py \
  --live \
  --ack S22PLUS-M3-OBSERVABLE-LIVE-GATE
```

Expected operator action during live:

1. Let the helper reboot Android to download mode and flash the M3 boot-only AP.
2. Watch the bounded host observation window for USB/NCM evidence.
3. Put the phone into download mode for rollback when prompted.
4. Let the helper flash the pinned Magisk boot-only rollback AP and verify
   rooted Android returns.

If rollback transfer fails and download mode remains visible, the helper may use
the pinned stock boot-only AP fallback.
