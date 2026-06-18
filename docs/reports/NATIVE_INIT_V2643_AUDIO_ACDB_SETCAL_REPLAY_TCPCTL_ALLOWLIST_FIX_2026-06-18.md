# NATIVE_INIT V2643 — ACDB SET-cal replay tcpctl allowlist fix

Date: 2026-06-18

## Scope

Host-only fix for the final V2639 rerun setup failure. After staged scripts were
moved to an allowed root, the replay still could not start because every V2636
ACDB replay artifact was planned under `/cache/a90-acdb-setcal-replay-v2636/`,
and `tcpctl_host install` refused that dedicated runtime directory.

## Change

- Add the narrow prefix `/cache/a90-acdb-setcal-replay-` to
  `tcpctl_host.INSTALL_ALLOWED_PREFIXES`.
- Keep the existing path safety checks: absolute paths only, safe characters only,
  no `..`, and no broad `/cache/` allow.
- Extend `tests/test_tcpctl_host.py` to cover the V2636 replay helper path.

## Safety

No device action was run in this fix. The new prefix is scoped to ACDB SET-cal
replay runtime directories and does not permit vendor/system/partition paths.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/tcpctl_host.py tests/test_tcpctl_host.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_tcpctl_host -v`
- `git diff --check`

## Next Unit

Run exactly one V2639 live rerun. Stop if another setup-level blocker appears;
do not continue blind-retrying.
