# Native Init Next Work List (2026-04-25)

이 문서는 `A90 Linux init 0.8.1 (v70)` 기준 이후 작업을 정리한 실행 목록이다.

현재 단계는 넓은 의미의 리버싱도 포함하지만, 중심은 더 이상 Android 전체를
분해하는 것이 아니다. Stock Android kernel과 Samsung vendor driver 위에서
우리의 작은 native userspace, shell, display HUD, input/menu, log/runtime 계층을
만드는 단계다.

따라서 후속 작업은 아래 원칙으로 진행한다.

- 필요한 하드웨어/커널 경로만 역추적한다.
- 셸은 실험 도구이자 운영 콘솔로 안정화한다.
- 화면 HUD는 부팅 상태를 보이게 만드는 최소 UI로 발전시킨다.
- 저장소와 로그는 복구 가능한 영역부터 사용한다.
- ADB는 보류하고 USB ACM serial을 기준 제어 채널로 유지한다.

---

## 모듈화 설계 기준

v80/v81 이후 모듈화는 단순히 파일을 작게 나누는 작업이 아니라, PID 1이
실패했을 때 원인을 좁히고 복구 가능한 부팅 경로를 유지하기 위한 구조화 작업이다.
분리 기준은 아래 네 가지로 고정한다.

- **부팅 순서**: `init_main`은 PID 1 부팅 흐름만 보여 주고, 세부 구현은 모듈에 둔다.
- **책임 영역**: log, timeline, storage, console, shell, display, input, network를 섞지 않는다.
- **장애 영향 범위**: boot-critical 계층부터 작게 분리하고, UI/network/service는 안정화 후 분리한다.
- **의존성 방향**: 하위 계층인 util/log/timeline이 HUD, shell, menu 같은 상위 계층을 호출하지 않게 한다.

참고 구조:

- Linux initramfs: rootfs의 `/init`이 PID 1로 실행되며 이후 부팅을 책임진다.
  - https://docs.kernel.org/6.2/filesystems/ramfs-rootfs-initramfs.html
- Android init: early mount/dev/proc 준비와 first/second stage 흐름을 나눈다.
  - https://android.googlesource.com/platform/system/core.git/+/1350207265745ad3e5ee26017a0f8cc14dc268b8/init/README.md
- Buildroot/BusyBox init: 임베디드 환경에서는 작은 init과 service/run 구조가 실용적이다.
  - https://buildroot.org/downloads/manual/manual.html
- USB gadget configfs: ACM/NCM은 gadget function/config 조합이므로 USB gadget 제어와 network 정책을 분리한다.
  - https://www.kernel.org/doc/html/latest/usb/gadget_configfs.html
- DRM/KMS dumb buffer: early graphics에는 저수준 KMS와 drawing/HUD/menu 계층 분리가 적합하다.
  - https://www.kernel.org/doc/html/v4.8/gpu/drm-kms.html

목표 모듈 경계:

```text
init_main
  -> util / log / timeline / dev / storage
  -> console / shell / cmdproto / run
  -> metrics / kms / draw / hud / input / menu
  -> usb_gadget / netservice
  -> optional helpers / BusyBox / dropbear
```

`v108 APP INPUTMON API`까지 실기 verified 완료했다. v106-v108은 UI/App Architecture split로 진행했고 ABOUT/changelog, displaytest/cutout, input monitor/layout UI를 각각 `a90_app_about.c/h`, `a90_app_displaytest.c/h`, `a90_app_inputmon.c/h`로 분리했다. v108 결과는
`docs/reports/NATIVE_INIT_V108_UI_APP_INPUTMON_2026-05-04.md`에 둔다. v107 결과는
`docs/reports/NATIVE_INIT_V107_UI_APP_DISPLAYTEST_2026-05-04.md`에 둔다. v106 결과는
`docs/reports/NATIVE_INIT_V106_UI_APP_ABOUT_2026-05-04.md`에 둔다. v105 결과는
`docs/reports/NATIVE_INIT_V105_SOAK_RC_2026-05-04.md`에 둔다. v104 결과는
`docs/reports/NATIVE_INIT_V104_WIFI_FEASIBILITY_2026-05-04.md`에 둔다. v103 결과는
`docs/reports/NATIVE_INIT_V103_WIFI_INVENTORY_2026-05-04.md`에 둔다. v102 결과는
`docs/reports/NATIVE_INIT_V102_DIAGNOSTICS_2026-05-03.md`에 둔다. v101 결과는
`docs/reports/NATIVE_INIT_V101_SERVICE_MANAGER_2026-05-03.md`에 둔다. v100 결과는
`docs/reports/NATIVE_INIT_V100_REMOTE_SHELL_2026-05-03.md`에 둔다. v99 결과는
`docs/reports/NATIVE_INIT_V99_BUSYBOX_USERLAND_2026-05-03.md`에 둔다. v98 결과는
`docs/reports/NATIVE_INIT_V98_HELPER_DEPLOY_2026-05-03.md`에 둔다. v97 결과는
`docs/reports/NATIVE_INIT_V97_SD_RUNTIME_ROOT_2026-05-03.md`에 둔다. v96 결과는
`docs/reports/NATIVE_INIT_V96_STRUCTURE_AUDIT_2026-05-03.md`에 둔다. v95 결과는
`docs/reports/NATIVE_INIT_V95_NETSERVICE_USB_API_2026-05-03.md`에 둔다. v94 결과는
`docs/reports/NATIVE_INIT_V94_BOOT_SELFTEST_API_2026-05-03.md`에 둔다.
v96-v105 장기 로드맵은
`docs/plans/NATIVE_INIT_LONG_TERM_ROADMAP_2026-05-03.md`를 기준으로 한다.
v103 상세 계획은
`docs/plans/NATIVE_INIT_V103_WIFI_INVENTORY_PLAN_2026-05-04.md`에 둔다.
v104 상세 계획은
`docs/plans/NATIVE_INIT_V104_WIFI_FEASIBILITY_PLAN_2026-05-04.md`에 둔다.
v105 상세 계획은
`docs/plans/NATIVE_INIT_V105_SOAK_RC_PLAN_2026-05-04.md`에 둔다.
v102 상세 계획은
`docs/plans/NATIVE_INIT_V102_DIAGNOSTICS_PLAN_2026-05-03.md`에 둔다. v101 상세 계획은
`docs/plans/NATIVE_INIT_V101_SERVICE_MANAGER_PLAN_2026-05-03.md`에 둔다. v100 상세 계획은
`docs/plans/NATIVE_INIT_V100_REMOTE_SHELL_PLAN_2026-05-03.md`에 둔다. v99 상세 계획은
`docs/plans/NATIVE_INIT_V99_BUSYBOX_USERLAND_PLAN_2026-05-03.md`에 둔다.
v96 상세 계획과 결과는
`docs/plans/NATIVE_INIT_V96_STRUCTURE_AUDIT_PLAN_2026-05-03.md`,
`docs/reports/NATIVE_INIT_V96_STRUCTURE_AUDIT_2026-05-03.md`에 둔다.
v97 상세 계획은
`docs/plans/NATIVE_INIT_V97_SD_RUNTIME_ROOT_PLAN_2026-05-03.md`에 둔다. v98 상세 계획과 결과는
`docs/plans/NATIVE_INIT_V98_HELPER_DEPLOY_PLAN_2026-05-03.md`,
`docs/reports/NATIVE_INIT_V98_HELPER_DEPLOY_2026-05-03.md`에 둔다.
v93 계획과 결과는
`docs/plans/NATIVE_INIT_V93_STORAGE_API_PLAN_2026-05-02.md`,
`docs/reports/NATIVE_INIT_V93_STORAGE_API_2026-05-02.md`에 둔다.
v92 계획과 결과는 `docs/plans/NATIVE_INIT_V92_SHELL_CONTROLLER_PLAN_2026-05-02.md`,
`docs/reports/NATIVE_INIT_V92_SHELL_CONTROLLER_API_2026-05-02.md`에 둔다.
shell/cmdproto 착수 지도와 실행 계획은 각각 `docs/reports/NATIVE_INIT_V83_CONSOLE_SHELL_CMDPROTO_DEPENDENCY_MAP_2026-04-29.md`,
`docs/plans/NATIVE_INIT_V84_SHELL_CMDPROTO_PLAN_2026-04-29.md`에 보존한다.

---

## 프로젝트 목표 재정의

현재 프로젝트의 목표는 `native Linux 진입 가능성 확인`이 아니라,
이미 확보한 진입점을 기반으로 **Android kernel 위에 작은 native Linux userspace를
직접 구성하는 것**이다.

목표 구조:

```text
Samsung bootloader
  -> stock Android Linux kernel
    -> custom static /init (PID 1)
      -> native runtime services
      -> serial shell
      -> KMS HUD/menu
      -> input/button control
      -> sysfs/proc/device map
      -> log/storage layer
      -> optional BusyBox/network/SSH
```

이 프로젝트에서 `서버처럼 사용한다`는 말은 처음부터 Debian 전체를 올린다는 뜻이 아니다.
우선 목표는 아래 조건을 만족하는 초소형 임베디드 Linux 콘솔이다.

- 부팅 진행과 실패 원인이 화면 또는 로그에 남는다.
- serial shell이 성공/실패를 신뢰 가능하게 보고한다.
- 외부 static binary를 실행하고 exit status를 확인할 수 있다.
- `/cache` 같은 안전한 저장소에 로그와 도구를 둘 수 있다.
- 파티션별 안전 등급을 구분해 Android/identity/security 영역을 실수로 덮어쓰지 않는다.
- 버튼만으로 최소한의 상태 확인과 recovery/poweroff 조작이 가능하다.
- 추후 USB network와 SSH/dropbear를 붙일 수 있는 runtime 구조를 가진다.

---

## 구현 범위와 비목표

현재 범위:

- custom `/init` 안정화
- shell/HUD/menu/log/runtime 구현
- 필요한 `/proc`, `/sys`, `/dev`, ioctl 경로 탐색
- safe storage와 boot recovery path 유지
- BusyBox 같은 static userland 검토
- USB serial 기반 운용

명시적 비목표:

- full POSIX shell 직접 구현
- Debian/Ubuntu 전체 배포판 즉시 포팅
- Android framework, Zygote, SurfaceFlinger 복구
- 커널 교체 또는 커널 드라이버 개발
- 카메라/모뎀/GPU 가속 같은 vendor userspace 의존 기능 지원
- `/efs`, RPMB, keymaster, modem 영역 쓰기

---

## 단계별 마일스톤

### M0. Native init 진입 확보 — 완료

- stock Android kernel 부팅
- custom static `/init` PID 1 실행
- USB ACM serial shell 확보
- KMS 화면 출력 확보
- 버튼 입력과 기본 sensor/sysfs 읽기 확보

### M1. 신뢰 가능한 native console

- shell return code 정밀화 — v40 완료
- command duration/result/errno 기록 — v40/v41 완료
- blocking command 취소 정책 통일 — v42 완료
- serial 반향/prompt 오염 방어

### M2. 관찰 가능한 boot/runtime

- `/cache/native-init.log` — v41 완료
- boot readiness timeline — v43 완료
- HUD boot progress/error 표시 — v44 완료
- safe storage/partition map 문서화 — v46 완료

### M3. 단독 운용 가능한 device UI

- 버튼 기반 on-screen menu — v47/v52 완료
- status/log/reboot/recovery/poweroff 조작 — v52 완료
- menu-active serial busy gate와 `hide` 요청 — v53 완료
- unsolicited `AT` serial noise filter — v59 완료
- serial 없이도 최소 복구 조작 가능 — 계속 검증

### M4. 작은 Linux userland

- static toybox 실행 — 완료
- `/cache/bin` 또는 ramdisk 기반 tool path — 완료
- process 실행, timeout, signal, zombie 회수 안정화 — 진행 중

### M5. 서버형 접근

- USB NCM probe — 완료
- USB NCM persistent link + IPv4/IPv6 ping + host→device netcat 검증 — 완료
- USB NCM 운영 helper + TCP nettest helper — 완료
- NCM TCP control helper — 완료
- TCP control host wrapper — 완료
- NCM + TCP control 5분 soak — 완료
- boot-time NCM/tcpctl netservice 정책 — v60 완료
- netservice stop/start software UDC reconnect recovery — v60 완료
- HUD CPU/GPU usage percent 표시 — v61 완료
- CPU stress usage gauge + `/dev/null`/`/dev/zero` guard — v62 완료
- 계층형 앱 메뉴 + CPU stress screen app — v63 완료
- TEST 부팅 화면을 custom boot splash로 교체 — v64 완료
- boot splash 잘림 방지 safe layout — v65 완료
- semantic version + ABOUT/changelog/credits app — v66 완료
- compact ABOUT typography + version별 changelog detail — v67 완료
- HUD log tail + expanded changelog history — v68 완료
- physical-button input gesture layout — v69 완료
- input monitor app + raw/gesture trace — v70 완료
- HUD/menu live log tail panel — v71 완료
- display test screen + framebuffer color fix — v72 완료
- cmdv1/A90P1 shell protocol + host wrapper — v73 완료
- cmdv1x length-prefixed argv encoding — v74 완료
- idle-timeout serial reattach log quieting — v75 완료
- AT fragment serial noise hardening — v76 완료
- display test multi-page app + cutout calibration — v77 완료
- ext4 SD workspace + `mountsd` storage manager — v78 완료
- boot-time SD health check + `/cache` fallback — v79 완료
- PID1 source layout split into include modules — v80 완료
- config/util true `.c/.h` base module extraction — v81 완료
- log/timeline true `.c/.h` API module extraction — v82 완료
- console true `.c/.h` API module extraction — v83 완료
- cmdproto true `.c/.h` API module extraction — v84 완료
- run/service true `.c/.h` API module extraction — v85 완료
- KMS/draw true `.c/.h` API module extraction — v86 완료
- input true `.c/.h` API module extraction — v87 완료
- HUD true `.c/.h` API module extraction — v88 완료
- menu control true `.c/.h` API module extraction + nonblocking `screenmenu` — v89 완료
- metrics true `.c/.h` API module extraction — v90 완료
- CPU stress external helper process separation — v91 완료
- shell/controller metadata and busy policy API extraction — v92 완료
- storage true `.c/.h` API module extraction — v93 완료
- boot selftest non-destructive module smoke test API — v94 완료
- netservice/USB gadget true `.c/.h` API module extraction — v95 완료
- structure audit/refactor debt cleanup — v96 완료
- SD runtime root promotion — v97 완료
- helper deployment/package manifest — v98 완료
- BusyBox static userland evaluation — v99 완료
- TCP shell/dropbear remote access prototype — v100 완료
- Minimal service manager command/view — v101 완료
- Diagnostics/log bundle command and host collector — v102 완료
- Wi-Fi read-only inventory — v103 완료
- Wi-Fi enablement feasibility — v104 완료, 현재 gate 결과 no-go/baseline-required
- long-run soak/recovery release candidate — v105 완료
- ABOUT/displaytest/input monitor UI app split — v106-v108 완료
- static dropbear SSH 또는 custom TCP shell

---

## 현재 기준점

- 최신 확인 버전: `A90 Linux init 0.9.8 (v108)`
- 공식 버전: `0.9.8`
- build tag: `v108`
- creator: `made by temmie0214`
- 최신 verified 소스: `stage3/linux_init/init_v108.c` + `stage3/linux_init/v108/*.inc.c` + `stage3/linux_init/helpers/a90_cpustress.c` + `stage3/linux_init/helpers/a90_rshell.c` + `stage3/linux_init/a90_config.h` + `stage3/linux_init/a90_util.c/h` + `stage3/linux_init/a90_log.c/h` + `stage3/linux_init/a90_timeline.c/h` + `stage3/linux_init/a90_console.c/h` + `stage3/linux_init/a90_cmdproto.c/h` + `stage3/linux_init/a90_run.c/h` + `stage3/linux_init/a90_service.c/h` + `stage3/linux_init/a90_kms.c/h` + `stage3/linux_init/a90_draw.c/h` + `stage3/linux_init/a90_input.c/h` + `stage3/linux_init/a90_hud.c/h` + `stage3/linux_init/a90_menu.c/h` + `stage3/linux_init/a90_metrics.c/h` + `stage3/linux_init/a90_shell.c/h` + `stage3/linux_init/a90_controller.c/h` + `stage3/linux_init/a90_storage.c/h` + `stage3/linux_init/a90_selftest.c/h` + `stage3/linux_init/a90_usb_gadget.c/h` + `stage3/linux_init/a90_netservice.c/h` + `stage3/linux_init/a90_runtime.c/h` + `stage3/linux_init/a90_helper.c/h` + `stage3/linux_init/a90_userland.c/h` + `stage3/linux_init/a90_diag.c/h` + `stage3/linux_init/a90_wifiinv.c/h` + `stage3/linux_init/a90_wififeas.c/h` + `stage3/linux_init/a90_app_about.c/h` + `stage3/linux_init/a90_app_displaytest.c/h` + `stage3/linux_init/a90_app_inputmon.c/h`
- 최신 verified boot image: `stage3/boot_linux_v108.img`
- previous verified source-layout baseline: `stage3/linux_init/init_v80.c` + `stage3/linux_init/v80/*.inc.c`
- known-good fallback: `stage3/boot_linux_v48.img`
- 주 제어 채널: USB CDC ACM serial (`/dev/ttyGS0` ↔ `/dev/ttyACM0`)
- host bridge: `scripts/revalidation/serial_tcp_bridge.py --port 54321`
- 화면 상태: custom boot splash 약 2초 표시 후 상태 HUD/menu 자동 전환
- 버튼 상태: VOL+/VOL-/POWER 입력 확인
- 로그 상태: SD 정상 시 `/mnt/sdext/a90/logs/native-init.log`, fallback 시 `/cache/native-init.log` boot/command log 확인
- blocking 상태: `waitkey`/`readinput`/`watchhud`/`blindmenu` q/Ctrl-C 취소 확인
- timeline 상태: `timeline` 명령과 current native log replay 확인
- HUD 상태: `BOOT OK shell` summary 표시 확인
- run/log 상태: `/bin/a90sleep` q 취소와 recovery 왕복 log preservation 확인
- storage 상태: `/cache` safe write, ext4 SD workspace `/mnt/sdext/a90`, boot-time SD health check, critical partitions do-not-touch 기준 문서화
- screen menu 상태: 자동 메뉴, 버튼 조작, input gesture layout, input monitor, serial `hide`/busy gate 확인
- USB 상태: ACM-only gadget `04e8:6861` / host `cdc_acm` 기준 문서화
- USB reattach 상태: v48 `usbacmreset`와 외부 helper `off` 후 serial 복구 확인
- USB NCM 상태: host `cdc_ncm` + device `ncm0`, IPv4 ping, IPv6 link-local ping, host→device netcat 확인
- NCM 운영 helper 상태: host interface 자동 탐지, ping, static TCP nettest 양방향 payload 검증 완료
- TCP control 상태: NCM 위에서 `a90_tcpctl` ping/status/run/shutdown 검증 완료
- TCP wrapper 상태: `tcpctl_host.py smoke` launch/client/stop 자동 검증 완료
- TCP soak 상태: `tcpctl_host.py soak` 5분/30사이클 안정성 검증 완료
- serial noise 상태: unsolicited `AT` modem probe line 무시 확인
- boot netservice 상태: opt-in flag 기반 NCM/tcpctl 부팅 자동 시작과 rollback 검증 완료
- netservice 기본값: disabled. `/cache/native-init-netservice` flag가 있을 때만 자동 시작
- reconnect 상태: v60 `netservice stop/start` software UDC 재열거 후 NCM/TCP 복구 확인
- HUD metrics 상태: CPU/GPU 온도와 사용률 `%` 표시, `cpustress`로 CPU usage 상승 확인
- dev node 상태: `/dev/null`/`/dev/zero` boot-time char device guard 확인
- app menu 상태: APPS/MONITORING/TOOLS/LOGS/NETWORK/POWER 계층 메뉴와 CPU stress 시간 선택 확인
- boot splash 상태: `A90 NATIVE INIT` custom splash와 `display-splash` timeline 기록 확인
- splash layout 상태: v65에서 긴 문구/footer 잘림 방지 safe layout 적용
- about app 상태: `APPS / ABOUT`에 version, changelog 목록/상세, credits 추가
- menu gate 상태: 메뉴 표시 중 위험 명령 `[busy]` 차단, 관찰 명령 허용
- ADB 상태: 보류

상세 상태 문서:

- `docs/reports/NATIVE_INIT_V82_LOG_TIMELINE_2026-04-29.md`
- `docs/reports/NATIVE_INIT_V81_CONFIG_UTIL_2026-04-29.md`
- `docs/reports/NATIVE_INIT_V80_SOURCE_MODULES_2026-04-29.md`
- `docs/reports/NATIVE_INIT_V79_BOOT_STORAGE_2026-04-29.md`
- `docs/reports/NATIVE_INIT_V78_SD_WORKSPACE_2026-04-29.md`
- `docs/reports/NATIVE_INIT_V77_DISPLAY_TEST_PAGES_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V76_AT_FRAGMENT_FILTER_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V75_QUIET_IDLE_REATTACH_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V74_CMDV1X_ARG_ENCODING_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V73_CMDV1_PROTOCOL_2026-04-27.md`
- `docs/reports/NATIVE_INIT_V45_RUN_LOG_2026-04-25.md`
- `docs/reports/NATIVE_INIT_STORAGE_MAP_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V47_SCREEN_MENU_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V48_USB_REATTACH_NCM_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V53_MENU_BUSY_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V54_NCM_LINK_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V55_NCM_OPS_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V56_TCPCTL_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V57_TCPCTL_HOST_WRAPPER_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V58_TCPCTL_SOAK_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V59_AT_NOISE_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V60_NETSERVICE_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V60_RECONNECT_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V61_CPU_GPU_USAGE_2026-04-26.md`
- `docs/reports/NATIVE_INIT_V62_CPUSTRESS_2026-04-26.md`
- `docs/reports/NATIVE_INIT_USB_GADGET_MAP_2026-04-25.md`
- `docs/reports/NATIVE_INIT_USERLAND_CANDIDATES_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V44_HUD_BOOT_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V43_TIMELINE_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V42_CANCEL_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V41_LOGGING_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V40_BUILD_2026-04-25.md`
- `docs/reports/NATIVE_INIT_V39_STATUS_2026-04-25.md`

---

## P0. 운영 안정성

### 1. Shell return code 정밀화

목표:

- `[done]`이 단순히 command dispatch 완료가 아니라 실제 성공에 가깝게 보이도록 한다.
- 실패한 내부 syscall, mount, file open, ioctl, exec 결과를 command result에 반영한다.

현재 상태:

- `init_v40`에서 1차 구현 및 실기 검증 완료
- 상세 기록: `docs/reports/NATIVE_INIT_V40_BUILD_2026-04-25.md`
- `/cache/native-init.log`는 `init_v41`에서 구현 및 실기 검증 완료

대상:

- display 명령
- mount 명령
- file 명령
- input 명령
- process 실행 명령

작업:

- legacy `cmd_*` 함수 중 `void` 계열을 `int` 반환으로 단계 전환
- 실패 시 `errno` 보존
- `last`가 실제 실패 원인을 더 잘 보여주도록 정리
- unknown command, usage error, syscall error를 구분

검증:

- 존재하지 않는 파일 `cat`
- 잘못된 mount source
- 잘못된 display color
- 없는 executable `run`
- 정상 명령과 실패 명령의 `[done]`/`[err]` 차이 확인

### 2. 파일 로그 추가

목표:

- serial이 끊기거나 화면이 멈춘 것처럼 보여도 부팅 진행과 명령 결과를 나중에 확인한다.

우선 저장 위치:

- 1순위: `/cache/native-init.log`
- 2순위: `/tmp/native-init.log`

기록 항목:

- boot step
- version
- mount 결과
- display init 결과
- serial attach 결과
- command start/end
- result code
- `errno`
- duration

주의:

- `/cache` mount 실패 시 `/tmp`로 fallback
- 로그 파일이 너무 커지지 않도록 단순 rotation 또는 truncate 정책 필요
- `/data`, `/efs`, modem 관련 영역은 로그 대상으로 쓰지 않음

현재 상태:

- `init_v41`에서 구현 및 실기 검증 완료
- 상세 기록: `docs/reports/NATIVE_INIT_V41_LOGGING_2026-04-25.md`
- `logpath`, `logcat` 명령 추가
- `/sys/class/block/<name>/dev` 기반 동적 block node 생성으로 `sda28`, `sda31` major/minor 변동 대응
- recovery 왕복 후 로그 보존 재확인은 별도 항목으로 남김

검증:

- 부팅 후 `cat /cache/native-init.log`
- 고의 실패 명령 실행 후 로그에 실패 원인 기록 여부 확인
- recovery 재부팅 후 로그 보존 여부 확인

### 3. Blocking command 취소 정책 통일

목표:

- 오래 기다리는 명령에서 shell을 잃지 않도록 한다.

대상:

- `watchhud`
- `waitkey`
- `readinput`
- `blindmenu`
- `run`

정책:

- `q`: 정상 취소
- `Ctrl-C`: 강제 취소
- timeout 옵션: 선택적 지원

현재 상태:

- `init_v42`에서 공통 cancel helper 구현 및 실기 검증 완료
- 상세 기록: `docs/reports/NATIVE_INIT_V42_CANCEL_2026-04-25.md`
- `q`/`Ctrl-C`는 `-ECANCELED` (`errno=125`)로 `last`와 log에 남김
- 실기 검증 완료:
  - `waitkey`
  - `readinput`
  - `watchhud`
  - `blindmenu`
- `run`/`runandroid` cancelable child wait는 구현됐지만, 안전한 long-running static test binary가 없어 실기 cancel은 보류

검증:

- 각 blocking 명령에서 `q`로 prompt 복귀 — 부분 완료
- `Ctrl-C` 입력 후 prompt 복귀 — `waitkey` 완료
- 취소 후 `status`, `last`, `help`가 정상 동작 — 완료

---

## P1. 필요한 역추적 목록

### 1. Boot readiness timeline

목표:

- native init 기준으로 커널 리소스가 언제 준비되는지 단계표를 만든다.

현재 상태:

- `init_v43`에서 자동 기록 및 실기 검증 완료
- 상세 기록: `docs/reports/NATIVE_INIT_V43_TIMELINE_2026-04-25.md`
- `timeline` shell 명령 추가
- `/cache` mount 전 초기 timeline은 `/cache` 선택 후 log에 replay

확인 항목:

- `/proc` mount 시점
- `/sys` mount 시점
- `/dev` 또는 수동 device node 생성 시점
- `/cache` mount 시점
- USB gadget configfs 준비 시점
- `/dev/ttyGS0` attach 시점
- DRM/KMS open 가능 시점
- input event node 준비 시점
- power/thermal sysfs 준비 시점

출력 형태:

- boot log
- `status`
- 별도 report 문서

### 2. Display pipeline

목표:

- 현재 HUD 출력이 왜 안정적으로 보이는지, 어떤 부분이 아직 불안정한지 분리한다.

확인 항목:

- DRM card 번호
- connector id
- encoder/crtc id
- mode 정보
- dumb framebuffer 생성/매핑
- `SETCRTC` 성공 조건
- page flip 실패 원인
- backlight sysfs 경로
- blank/unblank 경로
- 화면 회전/좌표계
- punch-hole/cutout 안전 영역

참고 후보:

- TWRP recovery ramdisk의 display 초기화 방식
- kernel DRM sysfs
- 기존 `kmsprobe`, `drminfo`, `fbinfo` 출력

검증:

- custom boot splash
- debug TEST pattern
- HUD
- 단색 출력
- 작은 글자 출력
- 화면 꺼짐/켜짐
- 밝기 변경

### 3. Input/event map

목표:

- 물리 버튼과 event node 관계를 고정한다.

현재 확인:

- `event0`: `qpnp_pon`, POWER/VOLDOWN
- `event3`: `gpio_keys`, VOLUP

추가 확인:

- long press 이벤트
- key release 이벤트
- repeat 이벤트
- recovery/TWRP에서 같은 event map 유지 여부
- 터치 event node 존재 여부

검증:

- `inputinfo`
- `inputcaps`
- `readinput`
- `waitkey`
- 화면 메뉴에서 선택 이동/확정

### 4. Power, battery, thermal units

목표:

- HUD에 표시되는 전력/온도/배터리 값의 단위와 신뢰도를 확정한다.

확인 항목:

- battery capacity
- battery status
- battery temp unit
- voltage unit
- `power_now`
- `power_avg`
- CPU thermal zone
- GPU thermal zone
- throttling 관련 sysfs

주의:

- Samsung vendor sysfs는 표준 단위와 다를 수 있다.
- 전력 표시는 확정 전까지 `W?`처럼 불확실성을 표시한다.

검증:

- 충전기 연결/해제 전후 값 변화
- 화면 켜짐/꺼짐 전후 값 변화
- HUD refresh 반영 여부

### 5. Safe storage map

목표:

- native init에서 안전하게 읽고 쓸 수 있는 저장소를 구분한다.

현재 상태:

- `docs/reports/NATIVE_INIT_STORAGE_MAP_2026-04-25.md`로 v46 기준 1차 문서화 완료
- `/cache`는 persistent safe write로 사용
- `userdata`는 대용량 후보지만 Android FBE/user data와 엮여 있어 별도 의사결정 전까지 보류
- `efs`, `sec_efs`, modem, persist, key/security, vbmeta, bootloader 계열은 do-not-touch

후보:

- `/cache`
- `/tmp`
- `/mnt/system` read-only
- `/metadata` read-only 탐색 후보

금지 또는 주의:

- `/efs`
- modem 관련 파티션
- RPMB/keymaster/keystore 관련 영역
- `/data` 암호화 영역
- bootloader/vbmeta 계열

검증:

- `/proc/partitions`
- `/proc/mounts`
- `stat`
- `mountsystem ro`
- `/cache` write/read/sync

### 6. USB gadget map

목표:

- 현재 안정적인 ACM serial을 기준으로, 추후 네트워크/ADB 가능성을 판단할 자료를 만든다.

현재 상태:

- `docs/reports/NATIVE_INIT_USB_GADGET_MAP_2026-04-25.md`로 1차 문서화 완료
- 현재 active gadget은 ACM-only
- host descriptor는 CDC ACM control/data 2-interface만 노출
- ADB는 FunctionFS `ep0 only`/`adbd` zombie 문제가 blocker
- USB networking은 ACM rescue channel 유지 후 두 번째 function으로 probe 예정

확인 항목:

- configfs gadget path
- UDC name
- ACM function 설정
- host enumeration 상태
- FunctionFS ADB endpoint 생성 실패 조건
- RNDIS/NCM function 사용 가능성

현재 판단:

- ADB보다 ACM serial이 안정적이다.
- 추후 네트워크가 필요하면 ADB 복구보다 RNDIS/NCM + 작은 server가 더 현실적일 수 있다.

---

## P1. Shell 기능 개선 목록

### 1. 명령 help 정리

목표:

- `help` 출력이 너무 길어져도 읽을 수 있게 그룹화한다.

그룹 후보:

- core
- files
- mounts
- display
- input
- sensors
- process
- power
- debug

검증:

- `help`
- `help display`
- `help input`

### 2. 명령 parser 개선

목표:

- 실험에 필요한 최소 수준의 인자 처리를 안정화한다.

후보:

- quote 처리
- escaped space
- empty argument
- usage error 메시지 통일

비목표:

- full POSIX shell 구현
- pipe/redirection
- shell script language

### 3. File utility 보강

목표:

- device에서 직접 정보를 수집하기 쉽게 한다.

후보 명령:

- `readlink`
- `hexdump`
- `grep` 또는 단순 `findtext`
- `find`
- `tree` 제한 버전
- `tail`
- `log`

주의:

- 복잡한 BusyBox 재구현으로 흐르지 않게 한다.
- 필요한 것부터 작게 추가한다.

### 4. Process 실행 안정화

목표:

- 외부 static binary를 실험적으로 실행할 수 있게 한다.

작업:

- `run` timeout
- exit status 표시
- signal 종료 표시
- stdout/stderr 처리 정책
- child zombie 회수

검증:

- 정상 static binary
- 없는 binary
- crash binary
- 장시간 sleep binary

---

## P1. 화면/HUD/Menu

### 1. HUD 정보 레이아웃 안정화

목표:

- punch-hole, edge clipping, 색상 대비 문제를 피한다.

작업:

- safe margin 상수화
- font scale 정책 정리
- 상단 상태 위치 고정
- 하단 help text clipping 방지
- black-on-black 방지

검증:

- 검은 배경
- 밝은 배경
- 충전기 연결/해제
- 화면 회전 없이 1080x2400 기준 유지

### 2. Boot screen sequence

목표:

- 부팅 후 사용자가 “멈춘 것인지 진행 중인지” 알 수 있게 한다.

현재:

- v70 custom boot splash 약 2초
- HUD/menu 자동 전환

추가 후보:

- boot step progress text
- serial ready 표시
- cache/log ready 표시
- error 발생 시 붉은 상태줄

### 3. On-screen menu

목표:

- serial 없이도 최소 조작을 가능하게 한다.

현재 상태:

- `init_v47`에서 `menu`/`screenmenu` 화면 메뉴 초안 구현
- `RESUME`, `STATUS`, `LOG`, `RECOVERY`, `REBOOT`, `POWEROFF` 항목 제공
- q cancel 후 autohud 복구 확인
- 실제 버튼 이동/선택과 위험 동작은 수동 검증 대기

후보 메뉴:

- status
- refresh
- mount system ro
- reboot recovery
- poweroff
- show log
- start serial hint

입력:

- VOLUP: move up
- VOLDOWN: move down
- POWER: select

검증:

- 각 버튼 1회 입력
- 길게 누르기
- prompt와 menu mode 전환

---

## P2. 네트워크와 외부 도구

### 1. BusyBox/toolbox류 도구 검토

목표:

- 모든 유틸을 직접 구현하지 않고, 필요한 static userland를 가져올 수 있는지 판단한다.

확인:

- static ARM64 BusyBox 실행 가능 여부
- 라이선스/배포 방식
- `/cache/bin` 또는 ramdisk 탑재 방식
- `PATH` 정책

주의:

- core shell 안정화 전에는 도구 추가가 문제를 가릴 수 있다.

현재 상태:

- V49로 승격해 진행 중이다.
- 후보 리포트: `docs/reports/NATIVE_INIT_USERLAND_CANDIDATES_2026-04-25.md`
- 1차 방향은 boot ramdisk 포함이 아니라 `/cache/bin`에 static ARM64 multi-call binary를 올리고 `run /cache/bin/<tool> <applet>` 형태로 명시 실행하는 것이다.
- host build prerequisite 설치 후 `scripts/revalidation/build_static_toybox.sh`로 `toybox 0.8.13` static ARM64 빌드가 성공했다.
- 산출물은 `external_tools/userland/bin/toybox-aarch64-static-0.8.13`이며 SHA256은 `92a0917579c76fec965578ac242afbf7dedc4428297fb90f4c9caf7f538a718c`다.
- TWRP ADB로 `/cache/bin/toybox` 배치 후 native init에서 주요 applet 실기 실행을 확인했다.
- `ifconfig -a`, `route -n`, `netcat --help`가 동작하므로 USB networking probe의 userland 기반은 확보됐다.

### 2. 네트워크

목표:

- 장기적으로 일반 Linux 서버처럼 접근할 수 있는 경로를 검토한다.

후보:

- USB RNDIS/NCM
- static telnetd
- static dropbear SSH
- host bridge 기반 custom RPC

현 판단:

- 당장은 serial bridge가 가장 단순하고 안정적이다.
- SSH/server화는 log, process, storage가 안정화된 뒤 검토한다.

### 3. ADB 재검토

목표:

- 현재 보류한 ADB를 나중에 다시 판단할 근거를 남긴다.

현재 문제:

- `adbd` zombie
- FunctionFS `ep0`만 생성
- `ep1`/`ep2` 미생성
- Android property service, SELinux context, bionic/apex 환경 부재

재검토 조건:

- FunctionFS endpoint 생성 흐름 이해
- 필요한 property/socket/context 최소셋 확인
- ADB가 serial/RNDIS보다 가치가 큰지 재판단

---

## 당장 다음 실행 순서

상세 실행 큐는 `docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md`를 따른다.

1. v106-v108 UI/App Architecture split 완료 감사와 변경분 커밋
2. optional extended soak/reconnect 범위는 별도 수동 작업으로 분리
3. Wi-Fi bring-up은 v104 gate 결과에 따라 계속 보류
4. post-v108 후보 선정과 v109 계획
   - v106: `docs/plans/NATIVE_INIT_V106_UI_APP_ABOUT_PLAN_2026-05-04.md`
   - v107: `docs/plans/NATIVE_INIT_V107_UI_APP_DISPLAYTEST_PLAN_2026-05-04.md`
   - v108: `docs/plans/NATIVE_INIT_V108_UI_APP_INPUTMON_PLAN_2026-05-04.md`

---

## 당장 하지 않을 것

- Android framework 전체 복구
- SELinux/property service 전체 재구현
- 커널 교체
- EFS/modem/keymaster/RPMB 영역 쓰기
- full POSIX shell 구현
- package manager 만들기
- ADB를 최우선 과제로 되돌리기

---

## 완료 기준

단기 완료 기준:

- serial shell이 실패/성공을 신뢰할 수 있게 보고한다.
- 부팅 로그가 `/cache` 또는 `/tmp`에 남는다.
- 화면 HUD가 진행 상태와 에러를 표시한다.
- 버튼만으로 최소 메뉴를 조작할 수 있다.

중기 완료 기준:

- native init 환경이 “부팅되는 실험”이 아니라 “반복 운용 가능한 최소 Linux 콘솔”이 된다.
- 디스플레이, 입력, 센서, 저장소, USB의 안전 사용 범위가 문서화된다.
- 추가 userland 도구나 네트워크를 올릴 기반이 생긴다.

## V109-V116 다음 사이클

- roadmap: `docs/plans/NATIVE_INIT_V109_V116_ROADMAP_2026-05-04.md`
- starting point: `A90 Linux init 0.9.8 (v108)`
- first item: v109 post-v108 structure audit
- cycle goal: structure cleanup, extended soak, USB/service/runtime hardening, diagnostics bundle improvement
