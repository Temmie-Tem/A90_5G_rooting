# Native Init V260 CNSS Zombie Postflight Report

## Summary

- Status: PASS for tooling, BLOCKED for another live CNSS retry
- Tool: `scripts/revalidation/wifi_cnss_zombie_audit.py`
- Outputs:
  - `tmp/wifi/v260-cnss-zombie-audit/`
  - `tmp/wifi/v260-runner-preflight-with-zombie/`
  - `tmp/wifi/v260-cnss-live-evidence-reclass-with-process-audit/`
- Device command type: read-only process/status inspection
- Daemon execution: none

## Finding

The current native session is healthy enough for shell commands, but it contains one CNSS target zombie:

```text
pid=5900 state=Zs name=cnss-daemon raw=[cnss-daemon]
```

`/proc/5900/status` confirms:

```text
Name: cnss-daemon
State: Z (zombie)
PPid: 1
Uid: 1000 1000 1000 1000
Gid: 1000 1000 1000 1000
Groups: 1010 3003 3005
```

This explains why `pidof cnss-daemon` returned rc=1 while the process still existed: the residue is a zombie under PID1, not a running daemon.

## Validation

Static:

```text
python3 -m py_compile scripts/revalidation/wifi_cnss_zombie_audit.py scripts/revalidation/wifi_cnss_start_only_runner.py scripts/revalidation/wifi_cnss_live_evidence_analyzer.py
git diff --check
```

Device read-only audit:

```text
python3 scripts/revalidation/wifi_cnss_zombie_audit.py --out-dir tmp/wifi/v260-cnss-zombie-audit
```

Result:

```text
decision: cnss-zombie-present
pass: False
reason: one or more CNSS target processes are zombies under PID1
```

Runner preflight:

```text
python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v260-runner-preflight-with-zombie preflight
```

Result:

```text
decision: start-only-blocked
pass: False
```

Analyzer reclassification:

```text
python3 scripts/revalidation/wifi_cnss_live_evidence_analyzer.py \
  --out-dir tmp/wifi/v260-cnss-live-evidence-reclass-with-process-audit \
  --post-processes tmp/wifi/v260-ps-o-pid-stat-comm.txt
```

Result:

```text
decision: cnss-start-only-evidence-incomplete
pass: False
FAIL post-cnss-process-clean: target_process_count=1 target_zombie_count=1
```

## Interpretation

- V257 still proved that the v10 helper can start, observe, stop, and reap its tracked child process.
- V260 invalidates the previous postflight sufficiency rule: `pidof` absence is not enough.
- Future live CNSS attempts must require both:
  - no running target daemon
  - no target zombie in `ps -A -o pid,stat,comm`

## Decision

- Do not run another live CNSS retry while PID `5900` remains as a zombie.
- The zombie cannot be killed directly; only PID1 can reap it, or a reboot clears it.
- Next defensible work is one of:
  - PID1 orphan/zombie reaper hardening in the next native boot image
  - explicit reboot/clean-state validation before QRTR/QMI probing
  - no-start property/perfd model work that does not rely on clean CNSS live state
