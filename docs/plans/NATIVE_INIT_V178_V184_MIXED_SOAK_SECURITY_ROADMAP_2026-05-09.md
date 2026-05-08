# A90 Native Init v178-v184 Mixed Soak / Serverization Gate Roadmap

Date: `2026-05-09`
Baseline: `A90 Linux init 0.9.59 (v159)`
Cycle target: Wi-Fi 연결과 서버화 전에 host/device 장시간 혼합 안정성, 네트워크 노출 안전성,
증거 수집 신뢰성을 검증 가능한 기준으로 만든다.
Post-security baseline: F038-F044 host harness fixes through `fafa6d6`.

## Summary

v160-v169는 개별 안정성 축을 검증했고, v170-v177은 그 검증들을 공용 host
harness 위로 올렸다. 이후 F038-F044 보안 스캔에서 host validator/path
guard/replay/evidence 판정 문제가 확인되어 `0b8e9bc`, `c214478`, `952e572`,
`fafa6d6`로 패치했다. 따라서 v160-v177 결과는 역사적 baseline으로만 유지하고,
mixed-soak/serverization 판단은 post-security harness로 다시 만든 증거를
기준으로 삼는다.

다음 병목은 “패치된 harness 자체의 신뢰성 고정”, “장시간 실제 운영에 가까운
혼합 부하”, “Wi-Fi/server exposure 전 신뢰 기준”이다.

Wi-Fi를 연결하면 USB-local 실험 장비에서 무선 네트워크에 붙은 장비가 된다.
그 순간부터 고려 대상이 달라진다.

- 외부에서 도달 가능한 경로가 늘어난다.
- 인증, bind address, token, listener lifecycle, log privacy가 더 중요해진다.
- 장시간 운영 중 온도, 배터리, USB/NCM, SD, PID1 responsiveness가 흔들리면
  원격 복구가 어려워질 수 있다.
- “짧은 기능 테스트 PASS”만으로는 서버처럼 켜 두기 어렵다.

따라서 v178-v184는 Wi-Fi bring-up 자체가 아니라, Wi-Fi/serverization 전
**신뢰성 게이트**를 만드는 cycle로 둔다.

## Current Codebase Baseline

현재 host harness는 다음 기반을 이미 갖고 있다.

```text
native_test_supervisor.py
  ├─ MODULES: cpu/mem, kselftest feasibility, NCM/TCP, storage I/O, USB recovery
  ├─ DeviceClient: cmdv1 serial bridge 호출 single-writer lock
  ├─ EvidenceStore: 0700/0600 private output + no-follow writer
  ├─ Observer: read-only status/selftest/bootstatus/longsoak/storage/netservice samples
  ├─ TestModule: prepare -> run -> cleanup -> verify
  └─ Gate: requires_ncm / requires_usb_rebind / destructive / operator confirm
```

중요한 한계도 분명하다.

- F038-F044 이전에 만든 v160-v177 evidence는 보안 패치 전 host tooling으로
  생성된 것이므로 최종 readiness evidence로 승격하지 않는다.
- `ModuleRunner`는 현재 observer를 먼저 수행하고 module을 실행한다. 즉
  “부하 중 동시 관찰” 구조가 아니다.
- 모듈은 하나씩 실행된다. CPU, memory, NCM/TCP, storage를 일정 주기 또는
  seed-random으로 섞어 돌리는 scheduler가 없다.
- 장시간 failure를 serial timeout, NCM loss, device-side selftest failure,
  thermal warning, storage error로 분류하는 공용 classifier가 아직 없다.
- Wi-Fi/server exposure 전용 acceptance gate가 아직 없다.

## External Reference Notes

이 cycle은 외부 도구를 그대로 포팅하기보다, 검증 방식과 모델을 차용한다.

- Linux kselftest는 작은 userspace test, subset 실행, timeout, skip 가능한
  결과 모델을 중시한다. A90 harness도 `PASS/WARN/SKIP/FAIL/TIMEOUT`을
  명확히 기록한다.
  - Reference: https://www.kernel.org/doc/html/latest/dev-tools/kselftest.html
- `stress-ng`는 stressor class, sequential/parallel, pause/backoff, metrics
  개념을 제공한다. A90에서는 전체 포팅보다 phase/duty-cycle scheduler 설계
  참고로 사용한다.
  - Reference: https://manpages.debian.org/testing/stress-ng/stress-ng.1.en.html
- `fio`는 `runtime`, `time_based`, verify/checksum, steady-state 개념이 SD
  I/O 장기검증에 적합하다. A90에서는 기존 `storage_iotest.py`를 먼저 확장한다.
  - Reference: https://fio.readthedocs.io/en/master/fio_doc.html
- `iperf3`는 interval report, JSON output, parallel/reverse/bidirectional
  network test 모델이 좋다. A90에서는 기존 `tcpctl_host.py`/ping/NCM 경로를
  먼저 scheduler workload로 묶고, throughput helper는 후순위로 둔다.
  - Reference: https://software.es.net/iperf/invoking.html
- NIST WLAN/IoT guidance는 무선 네트워크가 설계, 설정, 모니터링, lifecycle
  전체의 보안 문제라는 점을 강조한다. A90에서는 Wi-Fi 연결 전 exposure
  inventory, listener policy, logging/privacy, recovery를 gate로 만든다.
  - Reference: https://csrc.nist.gov/pubs/sp/800/153/final
  - Reference: https://www.nist.gov/publications/iot-device-cybersecurity-guidance-federal-government-establishing-iot-device

## Target Architecture

```text
host mixed-soak supervisor
  ├─ RunConfig
  │   ├─ duration: 1h / 8h / 24h / unlimited
  │   ├─ profile: idle / balanced / network-heavy / storage-heavy / thermal-guarded
  │   ├─ seed: deterministic random schedule
  │   └─ gates: allow-ncm / allow-usb-rebind / assume-yes
  ├─ ObserverLoop
  │   ├─ read-only cmdv1 samples
  │   ├─ host ping / optional NCM samples
  │   └─ heartbeat + partial-report-safe output
  ├─ WorkloadScheduler
  │   ├─ phase schedule: idle -> low -> medium -> spike -> cooldown
  │   ├─ seed-random workload choice
  │   └─ resource conflict avoidance
  ├─ ResourceLockManager
  │   ├─ serial
  │   ├─ ncm
  │   ├─ storage
  │   ├─ cpu
  │   ├─ memory
  │   └─ usb-rebind
  ├─ WorkloadModules
  │   ├─ cpu duty-cycle
  │   ├─ bounded memory verify
  │   ├─ tcpctl ping/status/run
  │   ├─ host ping
  │   ├─ SD write/read/hash/sync
  │   └─ idle/cooldown
  ├─ FailureClassifier
  │   ├─ serial-timeout
  │   ├─ ncm-loss
  │   ├─ device-selftest-fail
  │   ├─ thermal-warning
  │   ├─ storage-error
  │   └─ policy-blocked
  └─ EvidenceBundle
      ├─ schedule.json
      ├─ observer.jsonl
      ├─ workload-events.jsonl
      ├─ failures.jsonl
      ├─ heartbeat.json
      ├─ manifest.json
      └─ summary.md
```

## Safety Policy

Default policy:

- Read-only observer always allowed.
- CPU/memory/storage/NCM workloads are bounded and profile-controlled.
- NCM workloads require `--allow-ncm`.
- USB rebind/recovery workloads require `--allow-usb-rebind --assume-yes`.
- Wi-Fi enablement, rfkill writes, module load/unload, firmware mutation, partition
  writes, watchdog open, active tracing, reboot loops are out of scope.
- Remote shell/listener widening is out of scope until v184 gate passes.

Abort/cooldown policy:

- Thermal threshold breach: stop active workload, enter cooldown, keep observer alive.
- Serial bridge loss: classify and retry observer after backoff, do not start new
  side-effect workloads until recovered.
- NCM loss: stop NCM workloads, keep serial observer if available.
- Storage write/hash failure: stop storage workloads, keep read-only observer.
- Repeated selftest failure: mark run FAIL, keep evidence collection if safe.

## Version Plan

### v178 — Post-Security Harness Baseline

Goal:

- F038-F044 패치 이후 host harness가 다시 신뢰 가능한 evidence producer인지
  검증한다.

Scope:

- 세부 계획: `docs/plans/NATIVE_INIT_V178_POST_SECURITY_BASELINE_PLAN_2026-05-09.md`
- local security rescan F001-F044 `FAIL=0` 유지.
- storage/fs path safety negative tests.
- unauthenticated tcpctl transcript rejection fixture.
- short real-device observer smoke.
- SD/NCM smoke는 가능한 환경에서만 수행하고, 불가 시 structured `SKIP/DEFERRED`
  로 남긴다.

Acceptance:

- post-security local scan has `FAIL=0`.
- negative tests fail before device contact.
- observer heartbeat/sample counters are valid.
- v179 mixed-soak scheduler foundation으로 넘어갈 수 있는 baseline report가 남는다.

### v179 — Mixed Soak Scheduler Foundation

Goal:

- `native_test_supervisor.py mixed-soak` 명령을 추가한다.

Scope:

- `a90harness/scheduler.py`
- schedule model: `phase`, `workload`, `start/end`, `resource_locks`, `seed`.
- `--dry-run`은 실제 부하 없이 전체 일정과 gate 요구사항을 출력한다.
- observer를 workload와 동시에 실행한다.

Acceptance:

- 2-5분 smoke mixed-soak PASS.
- `schedule.json`, `workload-events.jsonl`, `observer.jsonl`, `summary.md` 생성.
- seed가 같으면 같은 schedule이 나온다.

### v180 — CPU/Memory Workload Profiles

Goal:

- CPU와 memory 부하를 low/medium/spike/cooldown profile로 실행한다.

Scope:

- 기존 `/bin/a90_cpustress`와 `cpu_mem_thermal_stability.py`를 workload adapter로 연결.
- memory workload는 bounded tmpfs/file allocation, pattern write, SHA-256 verify로
  시작한다.
- 첫 단계에서는 full memory pressure나 OOM 유도 금지.

Acceptance:

- `balanced` profile에서 CPU usage 상승과 cooldown 복귀가 observer에 기록된다.
- memory verify mismatch 0.
- PID1 responsiveness와 controlled zombie count 회귀 없음.

### v181 — NCM/TCP + Storage Workload Integration

Goal:

- NCM/TCP와 SD I/O workload를 mixed scheduler에 편입한다.

Scope:

- `tcpctl_host.py ping/status/run` workload adapter.
- host ping workload.
- `storage_iotest.py` bounded write/read/hash/sync workload adapter.
- NCM missing 상태는 structured SKIP으로 기록한다.

Acceptance:

- `--allow-ncm` 없이는 network/storage NCM workload가 blocked/skip된다.
- NCM configured 상태에서 1h mixed run PASS.
- storage cleanup and final verify PASS.

### v182 — Failure Classifier + Recovery Policy

Goal:

- 장시간 run 중 발생한 실패를 운영 판단 가능한 분류로 남긴다.

Scope:

- `a90harness/failure.py`
- serial disconnect, bridge timeout, NCM loss, device command rc/status failure,
  thermal warning, storage mismatch, policy gate block 분류.
- partial report가 실패 원인과 마지막 정상 sample을 포함한다.

Acceptance:

- artificial blocked workload가 `policy-blocked`로 기록된다.
- NCM 없는 상태의 network workload가 FAIL이 아니라 환경 SKIP/DEFERRED로 기록된다.
- interrupt 후에도 bundle이 유효하다.

### v183 — 8h Pilot Mixed Soak

Goal:

- 잠깐 돌리는 smoke가 아니라 실제 운영 시간대에 가까운 8시간 pilot run을 수행한다.

Scope:

- profile: `balanced`.
- observer interval: 15-60초.
- workload mix: idle/cpu/memory/tcp/status/storage/cooldown.
- USB rebind workload는 기본 제외.

Acceptance:

- host/device evidence correlation PASS.
- serial command failures 0 또는 원인 분류 완료.
- thermal runaway 없음.
- battery/charging/power trend 기록.
- final `selftest verbose`, `storage`, `netservice status`, `longsoak status verbose` PASS.

### v184 — 24h+ Serverization Readiness Gate

Goal:

- Wi-Fi baseline refresh와 서버화 검토를 허용할지 결정하는 최종 안정성 gate를 만든다.

Scope:

- 24시간 이상 mixed run.
- optional `unlimited` mode는 operator interrupt까지 partial-report-safe로 유지.
- final report: PASS/WARN/FAIL, blocker, Wi-Fi/serverization go/no-go.

Acceptance:

- 24h run에서 uncontrolled zombie 0.
- evidence bundle complete.
- observer heartbeat monotonic.
- storage/log path stable.
- NCM/TCP workload failures가 없거나 분류/복구 가능.
- Wi-Fi/serverization 다음 단계로 넘어갈 명확한 go/no-go 판정이 나온다.

## Profiles

### `idle`

- Observer only.
- 목적: host sleep 방지, USB ACM 장시간 유지, device baseline drift 확인.

### `balanced`

- 대부분 idle/low.
- 주기적으로 CPU/memory/TCP/storage 짧은 부하.
- 목적: 24h 기본 운영 신뢰성.

### `network-heavy`

- NCM/TCP ping/status/run 비중을 높인다.
- storage는 낮은 빈도.
- 목적: Wi-Fi/network-facing 전 control path 내구성.

### `storage-heavy`

- SD write/read/hash/sync 비중을 높인다.
- CPU/memory는 낮은 빈도.
- 목적: SD runtime root와 log storage 안정성.

### `thermal-guarded`

- 온도/전력 기준에 따라 자동 cooldown.
- 목적: 장시간 고온/충전 상태에서 runaway 방지.

## Evidence Requirements

Every mixed-soak run must produce:

- `manifest.json`: version, git state, host metadata, duration, profile, seed.
- `schedule.json`: planned workload timeline.
- `observer.jsonl`: read-only samples.
- `workload-events.jsonl`: start/end/rc/status/duration for every workload.
- `failures.jsonl`: classified failures and recovery actions.
- `heartbeat.json`: last cycle, elapsed, active workload, observer status.
- `summary.md`: human-readable result.
- child module reports copied through private/no-follow evidence helpers only.

## Wi-Fi / Serverization Gate Criteria

Wi-Fi baseline refresh can resume only when:

- v178 post-security harness baseline passes;
- mixed-soak foundation smoke passes;
- at least one 1h NCM/TCP/storage mixed run passes or is explicitly deferred with
  environmental reason;
- 8h pilot run has no unclassified failures;
- security scan has no open high-risk listener/auth findings;
- USB ACM rescue remains available after all tests;
- network exposure policy still defaults to disabled/USB-local unless explicitly enabled.

Server-style remote access can be considered only after:

- 24h+ mixed run is PASS or WARN-only with understood causes;
- authentication/token policy is documented and tested;
- bind address policy is documented and tested;
- log/evidence privacy remains owner-only;
- recovery path without Wi-Fi is preserved.

## Explicit Non-Goals

- No Wi-Fi bring-up in v178-v184.
- No rfkill writes.
- No kernel module load/unload.
- No firmware/vendor mutation.
- No public all-interface listener.
- No ADB revival.
- No watchdog open/kick tests.
- No destructive partition or SD format tests.

## Open Decisions

- Whether v184 requires a full 24h run before Wi-Fi baseline refresh, or whether an
  8h PASS plus explicit operator approval is enough for the next read-only Wi-Fi pass.
- Whether memory workload should remain host-driven/tmpfs-based or get a small
  `/bin/a90_memstress` helper after v180.
- Whether NCM throughput should use current `tcpctl` payload checks first or add a
  dedicated iperf-like helper later.
