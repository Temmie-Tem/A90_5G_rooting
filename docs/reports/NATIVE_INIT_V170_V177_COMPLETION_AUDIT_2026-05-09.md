# Native Init v170-v177 Host Harness Completion Audit (2026-05-09)

## Objective

User objective:

> v170~v177 까지 늘 하던 개발 루프로 진행하자

Concrete success criteria:

- v170-v177 each has a plan document.
- v170-v177 each has an implementation or explicit documented deferral.
- v170-v177 each has a validation report.
- Validation evidence exists for each claimed result.
- Host harness code passes static validation.
- Evidence output keeps private/no-follow policy.
- Observer remains read-only by default.
- Side-effect modules are bounded and gated.
- Final v177 decides that v178 Wi-Fi baseline refresh can proceed on the new harness.

## Prompt-To-Artifact Checklist

| Requirement | Artifact / Evidence | Result |
| --- | --- | --- |
| Cycle roadmap exists | `docs/plans/NATIVE_INIT_V170_V177_HARNESS_ROADMAP_2026-05-09.md` | PASS |
| v170 plan exists | `docs/plans/NATIVE_INIT_V170_HARNESS_FOUNDATION_PLAN_2026-05-09.md` | PASS |
| v170 report exists | `docs/reports/NATIVE_INIT_V170_HARNESS_FOUNDATION_2026-05-09.md` | PASS |
| v170 evidence exists | `tmp/soak/harness/v170-smoke-20260508T173932Z/manifest.json` pass=`True` | PASS |
| v170 commit exists | `0c109ac Validate v170 harness foundation` | PASS |
| v171 plan exists | `docs/plans/NATIVE_INIT_V171_OBSERVER_API_PLAN_2026-05-09.md` | PASS |
| v171 report exists | `docs/reports/NATIVE_INIT_V171_OBSERVER_API_2026-05-09.md` | PASS |
| v171 evidence exists | `tmp/soak/harness/v171-observer-20260508T174309Z/manifest.json` pass=`True`, samples=`21`, failures=`0` | PASS |
| v171 commit exists | `da67c55 Validate v171 observer API` | PASS |
| v172 plan exists | `docs/plans/NATIVE_INIT_V172_MODULE_RUNNER_PLAN_2026-05-09.md` | PASS |
| v172 report exists | `docs/reports/NATIVE_INIT_V172_MODULE_RUNNER_2026-05-09.md` | PASS |
| v172 evidence exists | `tmp/soak/harness/v172-kselftest-feasibility-20260508T175009Z/manifest.json` pass=`True`, module=`kselftest-feasibility`, observer failures=`0` | PASS |
| v172 commit exists | `dca09c6 Validate v172 module runner` | PASS |
| v173 plan exists | `docs/plans/NATIVE_INIT_V173_STORAGE_CPU_MODULES_PLAN_2026-05-09.md` | PASS |
| v173 report exists | `docs/reports/NATIVE_INIT_V173_STORAGE_CPU_MODULES_2026-05-09.md` | PASS |
| v173 CPU evidence exists | `tmp/soak/harness/v173-cpu-mem-thermal-20260508T175358Z/manifest.json` pass=`True`, skipped=`False` | PASS |
| v173 storage evidence exists | `tmp/soak/harness/v173-storage-io-20260508T175421Z/manifest.json` pass=`True`, skipped=`True` with NCM precondition reason | PASS |
| v173 commit exists | `5de231b Validate v173 storage cpu modules` | PASS |
| v174 plan exists | `docs/plans/NATIVE_INIT_V174_USB_NCM_MODULES_PLAN_2026-05-09.md` | PASS |
| v174 report exists | `docs/reports/NATIVE_INIT_V174_USB_NCM_MODULES_2026-05-09.md` | PASS |
| v174 USB evidence exists | `tmp/soak/harness/v174-usb-recovery-20260508T175639Z/manifest.json` pass=`True`, skipped=`False` | PASS |
| v174 NCM/TCP evidence exists | `tmp/soak/harness/v174-ncm-tcp-preflight-20260508T175654Z/manifest.json` pass=`True`, skipped=`True` with NCM precondition reason | PASS |
| v174 commit exists | `e00f199 Validate v174 usb ncm modules` | PASS |
| v175 plan exists | `docs/plans/NATIVE_INIT_V175_UNIFIED_EVIDENCE_BUNDLE_PLAN_2026-05-09.md` | PASS |
| v175 report exists | `docs/reports/NATIVE_INIT_V175_UNIFIED_EVIDENCE_BUNDLE_2026-05-09.md` | PASS |
| v175 evidence exists | `tmp/soak/harness/v175-bundle-20260508T175913Z/manifest.json` pass=`True`, schema=`a90-harness-v175` | PASS |
| v175 commit exists | `0a2ac4e Validate v175 evidence bundle` | PASS |
| v176 plan exists | `docs/plans/NATIVE_INIT_V176_LONG_RUN_SUPERVISOR_PLAN_2026-05-09.md` | PASS |
| v176 report exists | `docs/reports/NATIVE_INIT_V176_LONG_RUN_SUPERVISOR_2026-05-09.md` | PASS |
| v176 evidence exists | `tmp/soak/harness/v176-long-run-20260508T180122Z/manifest.json` pass=`True`, samples=`14`, failures=`0`, stop_reason=`max-cycles` | PASS |
| v176 commit exists | `c7e2827 Validate v176 long run supervisor` | PASS |
| v177 plan exists | `docs/plans/NATIVE_INIT_V177_SAFETY_GATE_PLAN_2026-05-09.md` | PASS |
| v177 report exists | `docs/reports/NATIVE_INIT_V177_SAFETY_GATE_2026-05-09.md` | PASS |
| v177 allowed-module evidence exists | `tmp/soak/harness/v177-gate-allowed-20260508T180349Z/manifest.json` pass=`True` | PASS |
| v177 gate block evidence exists | `native_test_supervisor.py run usb-recovery` returned rc=`2` without allow flags | PASS |
| v177 commit exists | `74f3b36 Validate v177 safety gate` | PASS |

## Validation Commands Replayed During Audit

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check

python3 scripts/revalidation/native_test_supervisor.py list
python3 scripts/revalidation/native_test_supervisor.py run usb-recovery
```

Observed:

- static validation: `PASS`
- `list`: NCM modules blocked by default, USB rebind module blocked by default
- `run usb-recovery`: rc=`2`, required flags `--allow-usb-rebind --assume-yes`

## Deferred / Weakly Verified Items

These are intentionally not treated as blocking failures because they are
documented deferrals with explicit preconditions:

- `storage-io` full I/O PASS was not rerun because host NCM `192.168.7.2` was not reachable.
  - Evidence: `v173-storage-io` structured SKIP.
  - Follow-up: configure host NCM and run `native_test_supervisor.py run storage-io --allow-ncm`.
- `ncm-tcp-preflight` full tcpctl PASS was not rerun because host NCM `192.168.7.2` was not reachable.
  - Evidence: `v174-ncm-tcp-preflight` structured SKIP.
  - Follow-up: configure host NCM and run `native_test_supervisor.py run ncm-tcp-preflight --allow-ncm`.

## Completion Decision

The v170-v177 host harness cycle meets the stated objective:

- Plan/report pairs exist for every version.
- Implementations are committed per version.
- Real evidence exists for each completed claim.
- Deferrals are explicit and gated.
- Static validation passes.
- v177 safety gate makes v178 Wi-Fi baseline refresh safer to run.

Next recommended work:

- v178 Wi-Fi Baseline Refresh on the supervisor.
