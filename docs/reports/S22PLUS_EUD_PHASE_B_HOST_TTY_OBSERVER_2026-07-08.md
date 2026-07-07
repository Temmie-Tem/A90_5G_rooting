# S22+ EUD Phase-B Host TTY Observer Hardening (2026-07-08)

## Verdict

PASS / LIVE STILL INACTIVE.

This unit strengthened the EUD Phase-B reversible enable helper before any live
`enable=1` run. No EUD sysfs write, flash, reboot, partition write, module
insertion, or native-init candidate was executed.

## Change

`workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py`
now records richer host-side USB/serial state for every `before`,
`after_enable`, and `after_disable` snapshot:

```text
lsusb
lsusb -t
dmesg tail
/dev/ttyUSB*
/dev/ttyACM*
/dev/serial/by-id/*
/dev/serial/by-path/*
udevadm properties for ttyUSB*/ttyACM*
```

The private summary now carries:

```text
host_eud_usb_hint
host_serial_tty_hint
host_tty_paths
```

This matters because the live gate is not only asking whether the EUD hub
enumerates, but whether it gives us the practical A90-style serial path. The
future live result can compare `before.host_tty_paths` against
`after_enable.host_tty_paths` and identify a new EUD TTY instead of confusing it
with the existing Android ADB/MTP ACM node.

## Policy/Readiness Updates

The inert policy draft now includes `host serial/TTY` evidence alongside host
`lsusb` and dmesg. The readiness auditor checks that marker and verifies the
printed operator plan mentions the serial/TTY snapshot.

Files changed:

```text
docs/operations/S22PLUS_EUD_PHASE_B_ENABLE_AGENTS_EXCEPTION_DRAFT_2026-07-08.md
workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py
workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_readiness_audit.py
```

## Read-Only Snapshot

The validation run with `--include-read-only-check` executed the new host TTY
snapshot path without writes. It found the current baseline Android serial
interface:

```text
host_eud_usb_hint=false
host_serial_tty_hint=true
host_tty_paths includes:
  /dev/ttyACM0
  /dev/serial/by-id/usb-SAMSUNG_SAMSUNG_Android_<REDACTED_SERIAL>-if01
```

Interpretation: `/dev/ttyACM0` is the existing Android-side ACM path, not proof
of EUD. A future live EUD pass should look for a new Qualcomm/EUD USB hint or a
new serial path after `enable=1`, then confirm it disappears or returns to
baseline after `enable=0`.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_readiness_audit.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py \
  --print-plan

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_readiness_audit.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_readiness_audit.py \
  --include-read-only-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_readiness_audit.py \
  --expect-agents-active --no-default-dryrun-check
```

Results:

```text
py_compile: pass
offline-check: pass
print-plan: pass
inactive readiness audit: pass
read-only included readiness audit: pass
active-policy negative check: expected failure against inactive AGENTS.md
default EUD helper dry-run: fails closed at agents_exception missing EUD Phase-B markers
```

## Status

EUD Phase-B remains prepared but not live-authorized. The next live step still
requires explicit attended approval, active policy promotion, and the reversible
`enable=1` -> host USB/serial observation -> `enable=0` sequence.
