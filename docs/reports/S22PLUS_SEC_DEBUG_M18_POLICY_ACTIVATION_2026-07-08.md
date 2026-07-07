# S22+ Sec Debug MID M18 Policy Activation (2026-07-08)

## Verdict

PASS. The sec_debug/MID M18 capture policy is active and dry-run verified.

No live flash, reboot, or partition write occurred in this policy activation
unit.

## Policy Scope

`AGENTS.md` now contains a narrow one-shot exception for:

- helper:
  `workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py`
- live ack:
  `S22PLUS-SECDEBUG-M18-CAPTURE-LIVE-GATE`
- rollback ack:
  `S22PLUS-SECDEBUG-M18-ROLLBACK-BOOT-FROM-DOWNLOAD`
- debug-level confirmation:
  `DEBUG_LEVEL_MID_SET_BY_OPERATOR`

The exception authorizes only the pinned M18 boot AP and pinned boot rollback
APs. It explicitly excludes DTBO, vendor_boot, vbmeta, recovery, BL, CP, CSC,
super, userdata, persist, EFS, sec_efs, RPMB, keymaster, modem, bootloader, raw
host `dd`, fastboot, Magisk modules, format data, additional candidates, kernel
rebuilds, and A90 actions.

## Pinned Artifacts

```text
M18 AP.tar.md5            9382f91bf2cd3235410368ca08208b9343d8584da48c29b25c46a931b1f42805
M18 boot.img              a99a09fa062d1aaa848a41037c649a43abc983f177714dfc24c39d0df4d84083
M18 base Magisk boot      2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
M18 marker                S22_NATIVE_INIT_USB_ACM_M18_FULL
Magisk rollback AP        d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot fallback AP    1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

## Validation

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py \
  --offline-check

git diff --check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py
```

Results:

```text
py_compile: pass
offline-check: pass
git diff --check: pass
active dry-run: pass
```

Active dry-run verified:

```text
M18 candidate and rollback AP hashes: OK
AGENTS exception: present
Android/root stability: OK
current boot hash: known Magisk baseline
sec_debug DEBUG LEVEL: MID
```

Private dry-run log, not committed:

```text
workspace/private/runs/s22plus_sec_debug_m18_capture_20260707T213348Z/s22plus_sec_debug_m18_capture_live_gate.txt
```

## Next

Run the attended live command. If the phone lands in Samsung panic/upload or no
rollback transport appears, enter Download mode manually and run the rollback
mode.
