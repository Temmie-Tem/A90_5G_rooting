# A90 v182 Failure Classifier + Recovery Policy Report

Date: `2026-05-09`
Device build under test: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v182` host harness, not a native-init boot image
Plan: `docs/plans/NATIVE_INIT_V182_FAILURE_CLASSIFIER_PLAN_2026-05-09.md`
Roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

Result: `PASS`

v182 adds a mixed-soak failure classifier and partial-bundle interrupt handling.
This does not unblock v181 full NCM/TCP + storage validation; host NCM setup is
still required for that gate. It does make current deferred states explicit and
machine-readable.

## Implementation

- Added `scripts/revalidation/a90harness/failure.py`.
- `a90harness/scheduler.py` now writes `failure-classification.json`.
- `mixed-soak-result.json` now includes `classification_path`,
  `classification_summary`, `interrupted`, and `stop_reason`.
- `a90harness/observer.py` accepts a stop event so interrupted scheduler runs can
  stop the observer and finalize a bundle.
- `native_test_supervisor.py` includes classification fields in mixed summaries.

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

Results:

- Python compile: `PASS`
- diff whitespace: `PASS`

Policy-blocked classification:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 20 \
  --observer-interval 5 \
  --seed 182 \
  --workload ncm-tcp-preflight \
  --run-dir tmp/soak/harness/v182-policy-blocked-20260509-050457
```

Result:

- run: `PASS`
- classifier kind: `policy-blocked`
- severity: `deferred`
- evidence: `tmp/soak/harness/v182-policy-blocked-20260509-050457/`

NCM-missing classification:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 20 \
  --observer-interval 5 \
  --seed 182 \
  --workload ncm-tcp-preflight \
  --allow-ncm \
  --run-dir tmp/soak/harness/v182-ncm-missing-20260509-050519
```

Result:

- run: `PASS`
- classifier kind: `env-ncm-missing`
- severity: `deferred`
- evidence: `tmp/soak/harness/v182-ncm-missing-20260509-050519/`

Interrupt bundle:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 120 \
  --observer-interval 5 \
  --seed 182 \
  --workload ncm-tcp-preflight \
  --workload storage-io \
  --run-dir tmp/soak/harness/v182-interrupt-20260509-050613
# Ctrl-C during scheduler wait
```

Result:

- run exits `FAIL` as expected for operator interrupt.
- `manifest.json`: present
- `failure-classification.json`: present
- `summary.md`: present
- `bundle-index.json`: present
- classifier kinds: `policy-blocked`, `operator-interrupt`
- last good observer sample: present
- evidence: `tmp/soak/harness/v182-interrupt-20260509-050613/`

## Result

v182 classifier foundation is accepted. v181 full NCM/TCP + storage remains the
next blocking gate before v183 8h pilot and v184 24h+ readiness runs.
