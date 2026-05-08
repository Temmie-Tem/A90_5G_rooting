# A90 Native Init v170-v177 Host Test Harness Roadmap

Date: `2026-05-09`
Baseline: `A90 Linux init 0.9.59 (v159)`
Cycle target: Wi-Fi baseline refresh 전에 host-side 테스트 실행자와 관찰자를 분리하고, 기존 검증 스크립트를 공용 하네스 위로 단계적으로 올린다.

## Summary

v160-v169 cycle은 안정성 테스트를 개별 스크립트로 성공시켰다. 다음 병목은 테스트마다
반복되는 `cmdv1` 호출, private evidence writer, observer/longsoak 수집, report
생성 코드가 흩어져 있다는 점이다.

v170-v177 cycle은 기능 추가보다 **테스트 인프라 정리**가 목적이다. 핵심 구조는
공용 observer와 모듈형 test runner다.

```text
host supervisor
  ├─ DeviceClient: serial cmdv1/raw-control 호출 직렬화
  ├─ EvidenceStore: 0700/0600/no-follow 증거 저장
  ├─ Observer: read-only status/selftest/longsoak/storage/netservice 샘플
  └─ TestModule: prepare → run → cleanup → verify
```

## Guardrails

- USB ACM serial bridge는 rescue/control channel로 유지한다.
- serial command는 기본적으로 single-writer/lock으로 직렬화한다.
- observer는 read-only 명령만 실행한다.
- side effect는 test module에만 허용한다.
- 모든 side-effect module은 bounded duration, safe path, cleanup, rollback, final verify를 가져야 한다.
- host evidence writer는 private `0700/0600`과 symlink/no-follow 정책을 따른다.
- USB rebind, NCM setup, reboot, watchdog, fault injection, tracefs active writes는 explicit module gate 없이는 실행하지 않는다.

## Version Plan

### v170 — Harness Foundation

Goal:

- `scripts/revalidation/a90harness/` 공용 패키지를 만든다.
- device command client, private evidence writer, 공통 schema를 분리한다.

Scope:

- `a90harness/device.py`: `DeviceClient`, command lock, `cmdv1` wrapper.
- `a90harness/evidence.py`: private dir/file writer, JSON/Markdown helper.
- `a90harness/schema.py`: `CheckResult`, `CommandRecord`, `HarnessResult`.
- smoke CLI로 `version/status`를 호출해 evidence bundle을 만든다.

Acceptance:

- `python3 scripts/revalidation/native_test_supervisor.py smoke` PASS.
- evidence directory contains `manifest.json`, `summary.md`, command transcripts.
- no existing test script behavior changes.

### v171 — Observer API

Goal:

- 공용 read-only observer를 구현한다.

Scope:

- `a90harness/observer.py`
- commands: `version`, `status`, `selftest verbose`, `bootstatus`, `longsoak status verbose`, `storage`, `netservice status`.
- output: `observer.jsonl`, `observer-summary.json`.

Acceptance:

- 2-5분 bounded observer run PASS.
- serial command failures 0.
- observer can run without a test module.

### v172 — Module Runner

Goal:

- `prepare/run/cleanup/verify` 모듈 인터페이스와 supervisor runner를 고정한다.

Scope:

- `a90harness/module.py`
- `a90harness/runner.py`
- first module: read-only `kselftest-feasibility` wrapper.

Acceptance:

- `native_test_supervisor.py run kselftest-feasibility` PASS.
- observer and module evidence share one run directory.
- cleanup/verify execute even when module run fails.

### v173 — Storage/CPU Module Port

Goal:

- 기존 storage/CPU 부하 테스트를 supervisor 구조로 포팅한다.

Scope:

- module wrappers for `storage_iotest.py` and `cpu_mem_thermal_stability.py`.
- observer samples during module execution.

Acceptance:

- storage quick profile PASS under supervisor.
- CPU/memory/thermal smoke profile PASS under supervisor.
- existing standalone scripts remain usable.

### v174 — USB/NCM Module Port

Goal:

- 연결 재열거/네트워크 테스트를 supervisor가 안전하게 다루게 한다.

Scope:

- wrapper for `usb_recovery_validate.py`.
- NCM/TCP preflight wrapper that fails/skip clearly when host NCM is not configured.

Acceptance:

- USB recovery smoke PASS and final ACM-only.
- NCM module reports SKIP/DEFERRED if host NCM setup is unavailable.
- observer resynchronizes after USB rebind.

### v175 — Unified Evidence Bundle

Goal:

- 모든 supervisor run output layout을 표준화한다.

Scope:

- `manifest.json`
- `summary.md`
- `observer.jsonl`
- `commands/*.txt`
- `modules/<name>/*`
- optional copied child reports.

Acceptance:

- any module run has the same top-level schema.
- bundle writer keeps private/no-follow policy.
- report includes host git state, expected version, module result, observer result.

### v176 — Long-Run Supervisor

Goal:

- 자거나 출근할 때 돌릴 수 있는 long-run host supervisor mode를 만든다.

Scope:

- `native_test_supervisor.py observe --duration unlimited|N`.
- heartbeat and partial-report-safe shutdown.
- optional disconnect classifier integration.

Acceptance:

- bounded smoke run PASS.
- interrupt/timeout still writes partial manifest and summary.
- host/device command failures are distinguishable.

### v177 — Safety Gate / Dry-Run Policy

Goal:

- 위험하거나 환경 의존적인 module 실행 전 preflight/dry-run gate를 공통화한다.

Scope:

- module metadata: `requires_ncm`, `requires_reboot_ok`, `requires_usb_rebind`, `destructive`, `operator_confirm_required`.
- `native_test_supervisor.py list`, `plan`, `run --dry-run`.

Acceptance:

- dangerous or environment-dependent modules default to blocked/skip until explicit flag.
- dry-run prints required preconditions and exact reason.
- v178 Wi-Fi baseline refresh can reuse this gate.

## Completion Criteria

- v170-v177 each has plan/report pair or documented deferral.
- Existing standalone scripts keep working.
- Supervisor evidence output uses private/no-follow file handling.
- Observer is read-only by default.
- Module side effects are bounded and gated.
- Final v177 decides whether to run Wi-Fi baseline refresh on the new harness.

## Carry-Forward After v177

- v178 Wi-Fi Baseline Refresh on supervisor.
- v179 Network Exposure Hardening preflight on supervisor.
- Optional static helper tests only after module gate policy is in place.
