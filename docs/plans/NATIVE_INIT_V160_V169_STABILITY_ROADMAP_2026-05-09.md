# A90 Native Init v160-v169 Stability Test Roadmap

Date: `2026-05-09`
Baseline: `A90 Linux init 0.9.59 (v159)`
Cycle target: Wi-Fi baseline refresh 전에 커널, PID1, SD runtime, USB/NCM, helper lifecycle 안정성 기준선을 만든다.

## Summary

v154-v159에서 커널 기능 inventory는 read-only로 정리됐다. 다음 단계는 Wi-Fi로 바로
넘어가기보다, 현재 native init runtime이 여러 부하 조건에서도 안정적인지 확인하는
테스트 인프라를 버전별로 쪼개서 구축하는 것이다.

이 사이클은 기능 확장보다 안정성 검증이 목적이다. 모든 테스트는 실패 원인 분리가
가능하도록 storage, network, process, thermal, USB, scheduler, filesystem, kernel
feasibility 순서로 작게 나눈다.

## Current Evidence

- v159 idle/monitoring longsoak 약 15.77시간 PASS.
- host cmdv1/serial command failures: 0.
- device longsoak samples: 3780, sequence/time/uptime monotonic.
- SD backend 정상, `/mnt/sdext/a90` writable.
- NCM link와 최신 `a90_tcpctl` smoke는 수동 보정 후 PASS.
- 남은 리스크는 active workload, multi-process, I/O pressure, USB recovery, network throughput/impairment이다.

## Guardrails

- USB ACM serial bridge는 항상 rescue/control channel로 유지한다.
- Wi-Fi enablement, rfkill write, module load/unload, firmware/vendor mutation 금지.
- raw block device, `/efs`, modem, key/security, bootloader, Android 파티션 write 금지.
- storage write test는 `/mnt/sdext/a90/test-*` 아래로만 제한한다.
- watchdog open, fault injection enable, tracefs active tracing은 별도 승인 전까지 금지한다.
- stress test는 항상 bounded duration, bounded output, free-space guard, q/Ctrl-C cancel 또는 host stop path를 가져야 한다.
- 모든 host evidence writer는 private `0700/0600`과 symlink/no-follow 정책을 따른다.

## External Test Families Used As References

- `fio`: sequential/random I/O, verify, direct/buffered I/O pattern 참고.
- `stress-ng`: CPU, VM, filesystem, kernel-interface stressor taxonomy 참고.
- Linux Test Project: kernel reliability/regression test 구조 참고. full LTP 실행은 보류.
- xfstests/fsx: filesystem exerciser와 regression 개념 참고. A90에서는 SD test dir 한정 mini exerciser로 축소.
- `iperf3`: TCP/UDP throughput 측정 방식 참고. A90에서는 static binary 또는 `a90_netpump` helper가 필요.
- kselftest: kernel code path별 userspace selftest 개념 참고. 안전한 subset feasibility부터 평가.
- rt-tests/cyclictest: wakeup latency baseline 측정 방식 참고.
- `tc netem`: host-side delay/loss/reorder impairment 참고. device 쪽 qdisc 변경은 보류.

Reference URLs:

- fio documentation: https://fio.readthedocs.io/en/master/fio_doc.html
- stress-ng upstream: https://github.com/ColinIanKing/stress-ng
- Linux Test Project documentation: https://linux-test-project.readthedocs.io/
- Linux kselftest documentation: https://docs.kernel.org/dev-tools/kselftest.html
- iperf3 documentation: https://software.es.net/iperf/
- Linux `tc` netlink specification: https://docs.kernel.org/netlink/specs/tc.html
- `tc-netem` manual: https://man7.org/linux/man-pages/man8/tc-netem.8.html
- rt-tests/cyclictest guide: https://wiki.linuxfoundation.org/realtime/documentation/howto/tools/cyclictest/start
- xfstests overview: https://kernel.googlesource.com/pub/scm/fs/ext2/xfstests-bld/+/HEAD/Documentation/what-is-xfstests.md

## Version Plan

### v160 — NCM/TCP Stability

Build: `A90 Linux init 0.9.60 (v160)`
Marker: `0.9.60 v160 NCM TCP STABILITY`

Goal:

- 현재 수동으로 진행 중인 NCM ping + token-authenticated `a90_tcpctl` soak를 공식 테스트 경로로 만든다.
- tcpctl helper version mismatch를 사전에 감지한다.
- host IP/interface 설정과 NCM/TCP evidence를 재현 가능하게 남긴다.

Scope:

- `tcpctl_host.py soak` 결과를 v160 report 형식으로 고정.
- `a90_tcpctl` expected usage/hash/version sanity check 추가 후보 검토.
- NCM ping, tcpctl ping/status/run, serial bridge recovery를 하나의 PASS/FAIL 결과로 정리.
- longsoak device recorder와 병행해 CPU/GPU/battery/memory trend를 같이 수집.

Acceptance:

- `NCM ping` 0% loss.
- `tcpctl ping/status/run` 반복 PASS.
- soak summary `failures: 0`.
- 종료 후 `version`, `status`, `selftest verbose`, `netservice status`, `longsoak status verbose` PASS.

### v161 — Storage I/O Integrity

Build: `A90 Linux init 0.9.61 (v161)`
Marker: `0.9.61 v161 STORAGE IO INTEGRITY`

Goal:

- SD runtime root가 random write/read/verify, rename, unlink, fsync 반복을 견디는지 확인한다.

Scope:

- `a90_iotest.c/h` 또는 host-controlled shell profile 추가 후보.
- test root: `/mnt/sdext/a90/test-io`.
- file size classes: `4K`, `64K`, `1M`, `16M`, optional `128M`.
- pseudo-random deterministic seed로 write 후 hash/verify.
- free-space low-watermark guard.
- `iotest [quick|soak|status|clean]` API 검토.

Acceptance:

- quick profile: random files write/read/hash PASS.
- rename/unlink/fsync PASS.
- test root 외부 write 없음.
- 실패 시 partial artifacts와 manifest가 남고 cleanup command가 동작한다.

### v162 — Process/Concurrency Stability

Build: `A90 Linux init 0.9.62 (v162)`
Marker: `0.9.62 v162 PROCESS CONCURRENCY`

Goal:

- PID1 run/service/reap 경계와 tcpctl multi-client command path가 동시성 조건에서 깨지지 않는지 확인한다.

Scope:

- short helper churn: `/cache/bin/toybox true`, `stat`, `echo`, `uptime` 반복 실행.
- parallel tcpctl clients with bounded max clients.
- `longsoak + autohud + tcpctl + cpustress short burst` 동시 실행.
- zombie/orphan scan through `/proc/*/status`.
- FD count and process count snapshots.

Acceptance:

- zombie count remains 0 for controlled test helpers.
- PID1 shell/cmdv1 stays responsive.
- busy gate blocks unsafe overlapping commands.
- helper exit/reap result is recorded.

### v163 — CPU/Memory/Thermal Stability

Build: `A90 Linux init 0.9.63 (v163)`
Marker: `0.9.63 v163 CPU MEM THERMAL`

Goal:

- CPU stress, memory pattern verify, and thermal/power trend를 묶어서 부하 중 안정성을 확인한다.

Scope:

- existing `/bin/a90_cpustress`를 반복 프로파일로 사용.
- bounded memory allocation/write/read verify helper 후보.
- load 중 serial/cmdv1/NCM 응답성 샘플링.
- thermal zone max, CPU/GPU temp, battery temp, power, mem used trend report.

Acceptance:

- no kernel panic, no PID1 hang, no helper zombie.
- temperature remains within documented safe test threshold.
- `status` and `longsoak` remain responsive under load.

### v164 — Scheduler/Latency Baseline

Build: `A90 Linux init 0.9.64 (v164)`
Marker: `0.9.64 v164 SCHED LATENCY`

Goal:

- cyclictest-style wakeup latency baseline을 native init 환경에서 측정한다.

Scope:

- `a90_latprobe` helper 후보: `clock_nanosleep` interval jitter min/max/p99.
- baseline idle, under tcpctl soak, under cpustress, under I/O profile 비교.
- no RT priority requirement by default; optional priority mode는 별도 opt-in.

Acceptance:

- latency report includes min/max/avg/p95/p99 and missed deadline count.
- test is bounded and does not require kernel config change.
- load condition metadata is recorded.

### v165 — USB Recovery Stability

Build: `A90 Linux init 0.9.65 (v165)`
Marker: `0.9.65 v165 USB RECOVERY`

Goal:

- USB UDC re-enumeration, ACM bridge recovery, NCM host interface recovery, tcpctl recovery 시간을 측정한다.

Scope:

- `netservice stop/start` repeated soak.
- ACM-only rollback verification.
- host-side interface detection, IP assignment, ping, tcpctl smoke.
- optional manual physical unplug/replug checklist.

Acceptance:

- repeated software reconnect cycles PASS.
- bridge recovers after each cycle.
- final state is ACM-only unless test explicitly leaves NCM running.

### v166 — Network Throughput / Impairment

Build: `A90 Linux init 0.9.66 (v166)`
Marker: `0.9.66 v166 NETWORK THROUGHPUT`

Goal:

- stability-oriented throughput and degraded-network behavior를 확인한다.

Scope:

- `a90_netpump` helper 또는 static `iperf3` feasibility 검토.
- host-to-device and device-to-host TCP throughput.
- long-running small-payload and large-payload streams.
- host-side `tc netem` delay/loss/reorder profile는 optional/manual, device network qdisc mutation은 보류.

Acceptance:

- throughput report includes direction, duration, bytes, MB/s, errors, reconnect state.
- impairment profile is clearly marked and reversible.
- no network-facing auth/bind policy regression.

### v167 — Filesystem Exerciser Mini

Build: `A90 Linux init 0.9.67 (v167)`
Marker: `0.9.67 v167 FS EXERCISER MINI`

Goal:

- xfstests/fsx style filesystem operation fuzz를 SD test directory 안에서 제한적으로 수행한다.

Scope:

- random operation sequence: create, write, read, truncate, rename, unlink, fsync.
- deterministic seed and operation log.
- manifest-based replay/verify subset.
- strictly no raw block access.

Acceptance:

- operation log can reproduce a failure window.
- all paths are under `/mnt/sdext/a90/test-fsx`.
- cleanup command removes only test-owned files.

### v168 — Kernel Selftest Feasibility

Build: `A90 Linux init 0.9.68 (v168)`
Marker: `0.9.68 v168 KSELFTEST FEASIBILITY`

Goal:

- mainline kselftest/LTP 중 A90 native init에서 안전하게 차용 가능한 userspace subset이 있는지 평가한다.

Scope:

- no full LTP/kselftest run.
- static build feasibility and dependency inventory.
- safe candidates: timers, basic procfs/sysfs readers, net smoke, filesystem non-destructive probes.
- skip/hard-block candidates: hotplug, module insertion, fault injection, watchdog, raw device mutation.

Acceptance:

- feasibility report with candidate/blocked/unknown lists.
- no kernel mutation performed.
- next implementation candidates are bounded helper tests only.

### v169 — Fault/Debug Feasibility

Build: `A90 Linux init 0.9.69 (v169)`
Marker: `0.9.69 v169 FAULT DEBUG FEASIBILITY`

Goal:

- fault-injection, usbmon, tracefs active mode, pstore crash/reboot style tests를 실제 실행하기 전에 안전 조건을 문서화한다.

Scope:

- read-only inventory of debugfs/tracefs/fault-injection/usbmon availability.
- no fault injection enable.
- no active tracing by default.
- no LKDTM/crash trigger.
- pstore reboot preservation test는 별도 explicit plan으로 분리.

Acceptance:

- each debug/fault facility has status: unavailable, read-only-only, opt-in-safe-candidate, or blocked.
- blocked items include exact reason and required recovery preconditions.
- Wi-Fi/network exposure work can proceed with known debug fallback options.

## Recommended Execution Order

1. Complete the current NCM/TCP manual soak and write it up as v160 evidence.
2. Implement storage I/O integrity before heavier CPU/memory stress.
3. Run process/concurrency after storage and NCM paths are stable.
4. Run CPU/memory/thermal before scheduler latency, so latency baselines can compare idle vs loaded.
5. Run USB recovery after NCM/TCP and process lifecycle paths are stable.
6. Keep v166-v169 more exploratory; stop if any security scan or real-device stability issue appears.

## Completion Criteria

- Each version v160-v169 has a plan/report pair or a documented reason for being deferred.
- Every version that changes boot image is real-device flash verified before README promotion.
- Every stress helper has bounded duration, bounded output, cleanup, and safe path constraints.
- Longsoak or equivalent sensor logging is active during storage, network, CPU, and USB stability tests.
- The final v169 result decides whether to enter Wi-Fi baseline refresh as v170+.

## Carry-Forward After v169

- Wi-Fi baseline refresh.
- Network exposure hardening before any non-USB-local control path.
- Optional static `fio`, `iperf3`, `stress-ng`, or kselftest subset only if custom helper coverage is insufficient.
