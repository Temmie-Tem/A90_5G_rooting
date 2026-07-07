# S22+ EUD Phase-B TTY Delta Classifier (2026-07-08)

## Verdict

PASS / LIVE STILL INACTIVE.

This unit improves how the future reversible EUD enable run will be interpreted.
No EUD sysfs write, flash, reboot, partition write, module insertion, or
native-init candidate was executed.

## Change

`workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py`
now compares host serial paths before and after the enable window:

```text
tty_delta_after_enable
tty_delta_after_disable
host_new_serial_tty_hint
host_eud_or_new_tty_hint
```

The live return condition is now:

```text
enable restored to 0
AND
(
  host_eud_usb_hint
  OR a new host serial/TTY path appears after enable
)
```

This avoids the weak interpretation where EUD could expose a usable serial node
without a convenient `EUD` string in `lsusb`/dmesg, causing the helper to report
only a negative hint. It also avoids counting the existing Android `/dev/ttyACM0`
baseline as EUD evidence.

## Policy/Readiness Updates

The inert EUD Phase-B policy draft now includes the `new host serial/TTY path`
marker. The readiness auditor checks that marker through the helper plan and
includes a synthetic classifier self-test:

```text
before:        /dev/serial/by-id/android, /dev/ttyACM0
after_enable: /dev/serial/by-id/android, /dev/ttyACM0, /dev/ttyUSB0
after_disable:/dev/serial/by-id/android, /dev/ttyACM0
```

Expected result:

```text
enabled_delta.added = ["/dev/ttyUSB0"]
enabled_delta.new_tty_paths_detected = true
restored_delta.changed = false
```

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
TTY delta classifier self-test: pass
default EUD helper dry-run: fails closed at agents_exception missing EUD Phase-B markers
```

## Status

EUD Phase-B remains prepared but not live-authorized. The next live step still
requires explicit attended approval, active policy promotion, and the reversible
`enable=1` -> host USB/serial delta observation -> `enable=0` sequence.
