# S22+ EUD Phase-B Policy Activation (2026-07-08)

## Verdict

ACTIVE POLICY / DRY-RUN PASS / LIVE NEXT.

After explicit operator live approval, the inert EUD Phase-B exception was
promoted into `AGENTS.md`.

## Active Scope

The active exception authorizes only:

```text
helper: workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py
ack:    S22PLUS-EUD-PHASE-B-ENABLE-LIVE-GATE
target: SM-S906N/g0q/S906NKSS7FYG8
write:  /sys/module/eud/parameters/enable = 1 exactly once
observe: host lsusb, dmesg, host serial/TTY and TTY delta
restore:/sys/module/eud/parameters/enable = 0 before exit
```

It does not authorize flash, reboot, partition writes, native-init boot
candidates, module insertion, additional sysfs writes, Magisk modules, or any
A90 action.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_readiness_audit.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_readiness_audit.py \
  --expect-agents-active --no-default-dryrun-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py \
  --read-only-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py
```

Results:

```text
py_compile: pass
active readiness: pass, agents.complete=true
read-only check: pass, enable=0, ttyEUD0=1
active dry-run: pass
git diff --check: pass
```

The first active readiness attempt failed because the promoted `AGENTS.md` text
used backticks around `lsusb`, so the exact marker `host lsusb` was missing.
The policy text was corrected and the active readiness rerun passed.

## Status

Live reversible enable is now authorized and preflighted. The next command is:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py \
  --live --ack S22PLUS-EUD-PHASE-B-ENABLE-LIVE-GATE
```
