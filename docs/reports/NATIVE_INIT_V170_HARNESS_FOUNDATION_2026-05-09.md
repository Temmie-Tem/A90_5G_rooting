# Native Init v170 Harness Foundation Report (2026-05-09)

## Result

- status: PASS
- label: `v170 Harness Foundation`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- device build was not bumped for this host-side tooling step.
- objective: add shared host-side device client, private evidence writer, result schema, and supervisor smoke CLI.

## Implemented

- Added `scripts/revalidation/a90harness/device.py`.
- Added `scripts/revalidation/a90harness/evidence.py`.
- Added `scripts/revalidation/a90harness/schema.py`.
- Added `scripts/revalidation/native_test_supervisor.py`.
- Added `docs/plans/NATIVE_INIT_V170_V177_HARNESS_ROADMAP_2026-05-09.md`.
- Added `docs/plans/NATIVE_INIT_V170_HARNESS_FOUNDATION_PLAN_2026-05-09.md`.

## Evidence Path

```text
tmp/soak/harness/v170-smoke-20260508T173932Z/
```

Primary files:

```text
tmp/soak/harness/v170-smoke-20260508T173932Z/manifest.json
tmp/soak/harness/v170-smoke-20260508T173932Z/summary.md
tmp/soak/harness/v170-smoke-20260508T173932Z/commands/version.txt
tmp/soak/harness/v170-smoke-20260508T173932Z/commands/status.txt
```

## Smoke Summary

```text
result: PASS
expect_version: A90 Linux init 0.9.59 (v159)
version_matches: True
failed_checks: 0
failed_commands: 0
commands: 2
duration: 0.837s
```

## Checks

| Check | Result |
|---|---|
| `version` command | PASS |
| expected version string | PASS |
| `status` command | PASS |
| `status` contains selftest summary | PASS |

## Static Validation

```text
python3 -m py_compile scripts/revalidation/native_test_supervisor.py scripts/revalidation/a90harness/*.py
git diff --check
```

Result: PASS.

## Notes

- v170 does not replace existing standalone validators.
- Evidence output uses private `0700/0600` helpers and no-follow destination checks.
- The only device commands in this smoke were `version` and `status`; no device mutation was performed.

## Next

- v171 Observer API.
