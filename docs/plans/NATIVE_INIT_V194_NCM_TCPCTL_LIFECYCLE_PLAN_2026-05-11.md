# v194 Plan: NCM/tcpctl Broker Lifecycle Automation

## Summary

v194 is a host-side lifecycle wrapper for the `A90B1` `ncm-tcpctl` backend. It
keeps the native-init device build unchanged and removes the manual step where
an operator starts `/cache/bin/a90_tcpctl listen ... max_clients=0` before broker
NCM validation.

## Scope

- Add a lifecycle validator that:
  - starts `tcpctl_host.py start` with authenticated tcpctl and `max_clients=0`;
  - waits for the `tcpctl: listening` readiness marker;
  - runs `a90_broker_concurrent_smoke.py --backend ncm-tcpctl` with absolute
    `run /cache/bin/toybox ...` commands;
  - stops the listener with `tcpctl_host.py stop` unless `--leave-running` is set;
  - writes private summary/report/transcript evidence.
- Add `--dry-run` so CI/local planning can verify the command plan without
  touching device USB/NCM state.

## Non-Goals

- Do not configure the host NCM interface; `ncm_host_setup.py` remains the host
  IP setup tool.
- Do not modify native-init PID1, Wi-Fi, or USB gadget policy.
- Do not replace `tcpctl_host.py`; the wrapper composes existing tested tools.

## Validation

```bash
python3 -m py_compile scripts/revalidation/a90_broker_ncm_lifecycle_check.py
python3 scripts/revalidation/a90_broker_ncm_lifecycle_check.py \
  --dry-run \
  --run-dir tmp/a90-v194-dry-run
```

Optional live validation when NCM is up:

```bash
python3 scripts/revalidation/a90_broker_ncm_lifecycle_check.py \
  --run-dir tmp/a90-v194-live
```

## Acceptance

- Dry-run evidence shows authenticated lifecycle commands and max-client-unlimited
  listener policy.
- Live run, when executed, must show `auth=required`, NCM broker smoke PASS, and
  tcpctl stop PASS.
