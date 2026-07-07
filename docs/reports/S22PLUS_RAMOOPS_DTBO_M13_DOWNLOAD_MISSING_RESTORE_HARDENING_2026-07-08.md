# S22+ Ramoops DTBO + M13 Download-Missing Restore Hardening (2026-07-08)

## Scope

Host-only safety hardening before activating the DTBO+M13 live gate. No device
action, no reboot, no flash, and no partition write.

## Finding

The DTBO+M13 helper already restored stock DTBO if the M13 Odin flash failed
after an endpoint was acquired. One earlier failure boundary was weaker:

1. patched DTBO flash succeeds;
2. Android/root returns and live `ramoops_region/status=okay` is verified;
3. helper reboots Android to Download mode for the M13 boot flash;
4. Odin endpoint does not appear inside the bounded wait.

Before this hardening, that path returned immediately with a message that
patched-DTBO restore "may be needed". That preserved fail-closed behavior, but
left cleanup to a manual follow-up even when a second bounded Odin wait might
still catch the device and restore stock DTBO.

## Change

`workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m13_capture_live_gate.py`
now calls `restore_stock_dtbo_after_m13_download_missing()` when the M13
candidate Download endpoint is missing. The helper:

- logs `m13_candidate_download_missing_attempting_dtbo_restore=1`;
- attempts the existing stock-DTBO restore path from Download mode;
- logs the restore return code or exception;
- returns nonzero after cleanup (`12` on successful stock-DTBO restore), so the
  M13 capture is still reported as failed even if cleanup succeeds;
- prints the manual `--restore-dtbo-from-download` instruction if auto-restore
  cannot start.

This does not authorize any new partition, artifact, token, or live path.

## Validation

Commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m13_capture_live_gate.py \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m13_capture_readiness_audit.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m13_capture_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m13_capture_readiness_audit.py
```

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m13_capture_live_gate.py
```

Results:

```text
py_compile: pass
offline-check: pass; no device action
readiness_audit: pass; agents.complete=false, draft.complete=true
default helper execution: rc=1, blocked before Android/device action because
  AGENTS.md lacks the active DTBO+M13 authorization markers
```

Current live policy remains inert until the draft is promoted into `AGENTS.md`
and active-policy readiness plus default dry-run pass.
