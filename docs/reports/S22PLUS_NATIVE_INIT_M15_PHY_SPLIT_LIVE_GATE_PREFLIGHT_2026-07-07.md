# S22+ Native-Init M15 PHY-Split Live-Gate Preflight - 2026-07-07

## Verdict

PASS: M15 live-gate preflight is ready.

No live flash was executed. The helper verified the exact M15 candidate,
rollback APs, SHA-pinned `AGENTS.md` authorization, Android/Magisk baseline
stability, and current boot hash in dry-run mode.

## Candidate

```text
AP.tar.md5       16a4d526bbc0cb09bc63d61f4743d17dddb26c34047127fe610b1f677bddced2
boot.img         adaee20d490748aa1be555cdc7aa6828b9bc553185355a60183bd722119b5812
M15 /init        5897fee141921dffc2848fb3eb3515a9b2d75d41e0c286448c4f0add06ab8558
M15 module list  f3afe268a05c47492107227b224185c65f7757c004806c4c24d23231bd19e217
source           ac57cb1ece2dcc65bf5a8cbfc3fa0a077b006c757a4615298ee00d115b1fdd13
base boot        2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel           bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
```

M15 module payload:

```text
phy-msm-ssusb-qmp.ko
phy-msm-snps-eusb2.ko
```

The AP contains exactly one Odin member:

```text
boot.img.lz4
```

## Helper

```text
workspace/public/src/scripts/revalidation/s22plus_m15_phy_split_live_gate.py
```

Ack tokens:

```text
live                 S22PLUS-M15-PHY-SPLIT-LIVE-GATE
rollback-from-download S22PLUS-M15-ROLLBACK-FROM-DOWNLOAD
```

Live is gated by:

```text
exact M15 AP SHA
exact M15 boot.img SHA
exact Magisk base boot SHA
exact kernel SHA
exact M15 /init SHA
exact M15 module-list SHA
exact M15 source SHA
exact Magisk rollback AP SHA
exact stock fallback AP SHA
AGENTS.md exception markers
Android/Magisk baseline availability
current boot hash == base boot hash
explicit --live --ack token
```

## Preflight Runs

Offline check:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m15_phy_split_live_gate.py --offline-check
```

Result:

```text
offline-check ok: M15 candidate and rollback APs verified; no device action
```

Private log:

```text
workspace/private/runs/s22plus_m15_phy_split_live_gate_20260707T150103Z/s22plus_m15_phy_split_live_gate.txt
```

Dry-run:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m15_phy_split_live_gate.py
```

Result:

```text
dry-run ok: M15 candidate, rollback APs, AGENTS exception, Android stability, and boot hash verified
```

Private log:

```text
workspace/private/runs/s22plus_m15_phy_split_live_gate_20260707T150109Z/s22plus_m15_phy_split_live_gate.txt
```

## Boundaries

The preflight did not:

```text
flash M15
reboot the device
enter download mode
write any partition
load modules on device
install a Magisk module
touch recovery, vendor_boot, vbmeta, dtbo, BL, CP, CSC, super, userdata, EFS, RPMB, keymaster, modem, or A90
```

## Live Command

The attended live command, if the operator wants to run it next:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m15_phy_split_live_gate.py \
  --live --ack S22PLUS-M15-PHY-SPLIT-LIVE-GATE
```

If M15 parks or exposes ACM, it has no reboot/download command path by design.
Rollback then requires manual download-mode entry followed by:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m15_phy_split_live_gate.py \
  --rollback-from-download --ack S22PLUS-M15-ROLLBACK-FROM-DOWNLOAD
```

## Expected Interpretation

```text
M15 loops:
  The loop is at or below the PHY-side module load or finit_module path.

M15 parks/no ACM:
  The two PHY-side modules are tolerated. Next add dwc3-msm.ko alone.

M15 exposes ACM:
  Unexpected but positive; preserve the transcript and roll back manually.
```
