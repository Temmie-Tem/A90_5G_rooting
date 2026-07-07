# S22+ Sec Debug MID M18 Capture Gate Source (2026-07-08)

## Scope

Host-only source/gate work. No device action, no reboot, no flash, and no
partition write.

This replaces the older DTBO/ramoops M18 capture assumption with the live-proven
Samsung `sec_debug` / DEBUG LEVEL MID retained-console path. The intended live
unit is boot-only: flash the pinned M18 boot AP, observe, restore boot, then
collect `/proc/last_kmsg`.

## Added Helper

`workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py`

Modes:

- `--offline-check`: verify pinned M18 and rollback boot APs plus inert policy
  draft; no device action.
- `--print-plan`: print the attended operator command sequence; no device
  action.
- default dry-run: once policy is active, verify Android/root, current boot hash,
  and sec_debug MID before live flashing.
- `--live`: once policy is active, flash M18 boot only, observe ACM/ADB/Odin/no
  transport, rollback boot if possible, and collect retained evidence.
- `--rollback-boot-from-download`: attended rollback and `/proc/last_kmsg`
  collection after the operator manually enters Download mode.

## Required Pinned Artifacts

```text
M18 AP.tar.md5            9382f91bf2cd3235410368ca08208b9343d8584da48c29b25c46a931b1f42805
M18 boot.img              a99a09fa062d1aaa848a41037c649a43abc983f177714dfc24c39d0df4d84083
M18 base Magisk boot      2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
M18 init                  e73f39f7cc6f3a70e62ab2837b9e2d23422e2b6a5747e94f77bafcf0443baa40
M18 module list           153921f2cd886e31a5989ba589f6e5058fda4cc8eb6eb196e843293f8fae8e78
M18 source                29e0a4a9771aacbef24106f3b838d0731cbe294ae0cf064bf14e4256face7dfd
Magisk rollback AP        d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock boot fallback AP    1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

All APs must contain exactly `boot.img.lz4`.

Ack tokens reserved by the helper:

```text
S22PLUS-SECDEBUG-M18-CAPTURE-LIVE-GATE
S22PLUS-SECDEBUG-M18-ROLLBACK-BOOT-FROM-DOWNLOAD
DEBUG_LEVEL_MID_SET_BY_OPERATOR
```

## Positive-Control Carryover

The preceding sec_debug/MID sysrq live proof retained the panic in
`/proc/last_kmsg`. The operator also visually confirmed the phone displayed the
Samsung kernel panic screen with `Panic Msg : sysrq triggered crash`. That
screen observation matches the retained `/proc/last_kmsg` evidence and supports
using the same Samsung channel for native-init fault capture.

## Validation

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py \
  --print-plan

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py
```

Results:

```text
py_compile: pass
offline-check: pass; no device action
print-plan: pass; no device action
default execution: rc=1, blocked before Android/device action because AGENTS.md
  has no active sec_debug M18 capture exception
```

## Next Gate

To execute live, promote a narrow SHA-pinned `AGENTS.md` exception for this
helper only, run an active dry-run, then run the attended live command. If M18
shows a panic/upload screen or no rollback transport, the operator must enter
Download mode manually and run the rollback mode.
