# Native Init Post-v105 Discussion Notes

Date: `2026-05-04`
Baseline: `A90 Linux init 0.9.5 (v105)`

## 목적

이 문서는 v105 verified 이후 대화에서 나온 질문과 판단을 다음 계획 수립용 메모로 고정한다.
현재 Codex memory는 이 환경에서 직접 갱신하지 않고, repo 문서를 계획의 source of truth로 둔다.

## 질문별 정리

### 1. v105 이후 다음으로 무엇을 해야 하는가

- v105 quick soak는 통과했지만, stable baseline으로 삼으려면 선택적 확장 검증이 남아 있다.
- 우선 후보는 새 기능보다 `extended soak / recovery validation`이다.
- 검증 후보:
  - 30~60분 idle soak, HUD hidden/visible 상태 비교
  - USB 물리 unplug/replug 후 ACM bridge 복구
  - NCM opt-in: `netservice start` → host ping/tcpctl/rshell smoke → `netservice stop`
  - native init ↔ TWRP ↔ native init 왕복
  - cleanup retention: `v105` latest, `v104` rollback, `v48` known-good

### 2. shell / serial 쪽 개선 필요성

- PID1 shell 자체를 갈아엎을 필요는 없다.
- 개선 가치는 운영 안정성/관측성에 있다.
- 후보:
  - bridge 상태 표시: waiting ACM, connected, client closed, serial disconnected
  - transcript 정리: prompt/echo가 섞인 raw serial 로그를 host에서 더 깔끔히 저장
  - command별 기본 timeout: `diag`, `wifiinv full`, `cpustress`, `soak` 등
  - busy 자동회복 정책: `--hide-on-busy` 적용 범위 일관화
  - serial noise 통계: AT fragment 무시 횟수를 `diag`/`status`에 노출
  - single-client bridge 정책: 기존 client 종료/새 client 거부/상태 출력 명확화

### 3. 모듈화 / 합체 / 기능 분리 / 최적화

- 현재 가장 큰 구조 부채는 UI/app include tree다.
- 확인된 큰 코드 덩어리:
  - `stage3/linux_init/v105/40_menu_apps.inc.c` 약 3767 lines
  - `stage3/linux_init/v105/80_shell_dispatch.inc.c` 약 1118 lines
  - `stage3/linux_init/v105/70_storage_android_net.inc.c` 약 1079 lines
- 1차 분리 추천:
  - `a90_app_about.c/h`: ABOUT, version, changelog 목록/상세
  - 이유: 상태 의존성이 낮고 화면 출력 중심이라 리스크가 작다.
- 2차 후보:
  - `a90_app_displaytest.c/h`: displaytest color/font/safe/layout, cutoutcal
  - `a90_app_inputmon.c/h`: inputmonitor, waitgesture, input layout 표시
- 나중 후보:
  - CPU stress app, service/network app
  - 이유: run/service/netservice와 얽혀 있어 먼저 떼면 리스크가 크다.
- 합치지 말아야 할 모듈:
  - `a90_storage` + `a90_runtime`: mount/probe와 workspace contract는 분리 유지
  - `a90_diag` + `a90_selftest`: report와 pass/warn/fail 판정은 분리 유지
  - `a90_usb_gadget` + `a90_netservice`: USB primitive와 network policy는 분리 유지
  - `a90_hud` + `a90_metrics`: 표시와 sysfs snapshot은 분리 유지

### 4. 커널에서 활용 가능한데 아직 덜 쓴 기능

- read-only snapshot 기준으로 커널은 여러 인터페이스를 노출한다.
- 우선순위 높은 후보:
  - `pstore`/ramoops: panic/reboot 직전 로그 보존
  - `tracefs`/`debugfs`: boot latency, scheduler, IRQ, thermal 분석
  - `cgroup`/`cpuset`: `rshell`, `tcpctl`, `cpustress` 서비스 격리
  - `watchdog`: hang 자동 복구. 단, opt-in 필요
  - `zram`: userland 확대 시 메모리 여유 확보
  - `loop-control`/`device-mapper`: SD 위 rootfs image, rollback 가능한 userland sandbox
  - `tun`: user-space network tunnel
  - `uinput`/`uhid`: remote input/test input injection
  - `hw_random`/`msm-rng`: token/SSH/TLS 난수 품질 개선
  - `devfreq`/`hwmon`/`thermal`: governor/throttling 진단 강화
- 후순위 또는 vendor 의존 후보:
  - camera/video4linux/sound/nfc/fingerprint/npu
  - binder/hwbinder/vndbinder/ashmem/ion
  - Wi-Fi/`ieee80211`: v104 gate 기준 bring-up 금지 유지

### 5. 문서화 / 메모리 처리

- 현재 환경에서는 memory 갱신이 아니라 repo 문서화가 안전하다.
- 이 문서를 다음 planning entrypoint로 사용한다.
- 다음 계획 문서 작성 시 먼저 확인할 문서:
  - `docs/reports/NATIVE_INIT_V105_SOAK_RC_2026-05-04.md`
  - `docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md`
  - `docs/plans/NATIVE_INIT_POST_V105_DISCUSSION_NOTES_2026-05-04.md`

## 다음 사이클 후보

### 후보 A: v106 UI App Split 1

- 목표: `a90_app_about.c/h`로 ABOUT/changelog 화면을 분리한다.
- 성격: 구조 개선, 기능 변화 없음.
- 장점: 가장 큰 UI 부채를 낮은 리스크로 줄인다.
- 검증: `screenmenu`, ABOUT/changelog navigation, `version`, `status`, `autohud`, quick soak.

### 후보 B: v106 Serial Ops Hardening

- 목표: bridge/a90ctl/busy/timeout/transcript 운영성을 개선한다.
- 성격: host tooling 중심, device 변경 최소.
- 장점: 플래시/검증 루프 실수를 줄인다.
- 검증: bridge reconnect, busy retry, command timeout matrix, transcript diff.

### 후보 C: v106 Kernel Capability Inventory

- 목표: `kernelcap` read-only command와 host collector로 커널 기능 후보를 분류한다.
- 성격: 탐색/계획 기반 강화.
- 장점: pstore/watchdog/cgroup/tracefs/zram/loop/tun/uinput 등 다음 기능 선정 근거를 만든다.
- 검증: `/proc/filesystems`, `/proc/misc`, `/sys/class`, `/sys/fs` snapshot, safe/risky/vendor-dependent 분류.

## 현재 추천

다음 구현 버전으로는 `v106 UI App Split 1`을 추천한다.
이유는 가장 큰 코드 부채가 `40_menu_apps.inc.c`이고, ABOUT/changelog는 낮은 리스크로 분리 가능한 독립 UI이기 때문이다.
다만 운영 실수 감소가 더 급하면 `Serial Ops Hardening`, 커널 기능 탐색을 우선하고 싶으면 `Kernel Capability Inventory`를 선택한다.
