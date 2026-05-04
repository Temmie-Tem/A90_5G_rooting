# Native Init Task Queue (2026-04-25)

이 문서는 `A90 Linux init 0.9.12 (v112)` verified 이후 바로 실행할 작업 큐다.
큰 방향은 “보이는 부팅 → 복구 가능한 로그 → 단독 조작 → 작은 userland → USB networking” 순서다.

## 현재 고정 기준점

- latest verified build: `A90 Linux init 0.9.12 (v112)`
- official version: `0.9.12`
- build tag: `v112`
- creator: `made by temmie0214`
- latest verified source: `stage3/linux_init/init_v112.c` + `stage3/linux_init/v112/*.inc.c` + `stage3/linux_init/helpers/a90_cpustress.c` + `stage3/linux_init/helpers/a90_rshell.c` + `stage3/linux_init/a90_config.h` + `stage3/linux_init/a90_util.c/h` + `stage3/linux_init/a90_log.c/h` + `stage3/linux_init/a90_timeline.c/h` + `stage3/linux_init/a90_console.c/h` + `stage3/linux_init/a90_cmdproto.c/h` + `stage3/linux_init/a90_run.c/h` + `stage3/linux_init/a90_service.c/h` + `stage3/linux_init/a90_kms.c/h` + `stage3/linux_init/a90_draw.c/h` + `stage3/linux_init/a90_input.c/h` + `stage3/linux_init/a90_hud.c/h` + `stage3/linux_init/a90_menu.c/h` + `stage3/linux_init/a90_metrics.c/h` + `stage3/linux_init/a90_shell.c/h` + `stage3/linux_init/a90_controller.c/h` + `stage3/linux_init/a90_storage.c/h` + `stage3/linux_init/a90_selftest.c/h` + `stage3/linux_init/a90_usb_gadget.c/h` + `stage3/linux_init/a90_netservice.c/h` + `stage3/linux_init/a90_runtime.c/h` + `stage3/linux_init/a90_helper.c/h` + `stage3/linux_init/a90_userland.c/h` + `stage3/linux_init/a90_diag.c/h` + `stage3/linux_init/a90_wifiinv.c/h` + `stage3/linux_init/a90_wififeas.c/h` + `stage3/linux_init/a90_app_about.c/h` + `stage3/linux_init/a90_app_displaytest.c/h` + `stage3/linux_init/a90_app_inputmon.c/h`
- latest verified boot image: `stage3/boot_linux_v112.img`
- previous verified source-layout baseline: `stage3/linux_init/init_v80.c` + `stage3/linux_init/v80/*.inc.c`
- known-good fallback: `stage3/boot_linux_v48.img`
- local artifact retention: `v112` latest, `v111` rollback, `v48` known-good만 보존하고 나머지 ignored stage3 산출물은 정리 가능
- control channel: USB ACM serial bridge
- log: SD 정상 시 `/mnt/sdext/a90/logs/native-init.log`, fallback 시 `/cache/native-init.log`
- verified:
  - shell result/errno/duration
  - boot/command file log
  - blocking command q/Ctrl-C cancel
  - boot readiness timeline
  - HUD boot summary
  - `run` cancel helper
  - recovery log preservation
  - safe storage/partition map
  - screen menu draft
  - screen menu polished TUI
  - menu-active serial busy gate
  - USB gadget map
  - USB reattach / NCM probe
  - USB NCM persistent link + IPv6 netcat
  - KMS HUD
  - VOL+/VOL-/POWER input
  - hierarchical app menu
  - custom boot splash
  - ABOUT/versioning/changelog metadata
  - compact ABOUT/changelog detail screens
  - HUD log tail
  - physical-button input gesture layout
  - input monitor app / raw gesture trace
  - HUD/menu live log tail panel
  - display test screen for color/font/wrap/grid/cutout checks
  - cmdv1/A90P1 shell protocol + a90ctl host wrapper
  - config/util/log/timeline compiled API modules
  - console fd/attach/readline/cancel compiled API module
  - cmdproto frame/decode compiled API module
  - run/service lifecycle compiled API modules
  - KMS/draw framebuffer compiled API modules
  - input/HUD/menu/metrics compiled API modules
  - CPU stress external helper process separation
  - shell/controller metadata and busy policy compiled API modules
  - storage/selftest/USB/netservice/runtime compiled API modules

## 실행 큐

### V43. Boot Readiness Timeline — 완료

목표:

- 부팅 중 리소스가 언제 준비되는지 자동 기록한다.
- 화면/serial이 없어도 `/cache/native-init.log`로 원인을 추적할 수 있게 한다.

구현:

- boot step enum 또는 helper 추가
- 각 단계의 monotonic timestamp 기록
- `timeline` shell 명령 추가
- `/cache/native-init.log`에 동일 정보 기록

검증:

- `timeline` — PASS
- `logcat` replay — PASS
- `status` — PASS
- recovery 왕복 후 `/cache/native-init.log` 보존 확인은 별도 항목으로 유지

### V44. HUD Boot Progress/Error — 완료

목표:

- 부팅 화면에서 현재 단계와 마지막 에러를 직접 보이게 한다.

구현:

- boot timeline 정보를 HUD 상단/하단에 요약 표시
- 마지막 command result 또는 boot error를 짧게 표시
- 실패 시 검은 화면/정지처럼 보이지 않도록 error card 표시

검증:

- 정상 부팅 HUD에 `BOOT OK` 또는 현재 step 표시 — PASS
- `bootstatus`, `status`, `statushud`, `autohud 2` — PASS
- 고의 실패 가능한 display/sysfs 명령 후 HUD 복구 확인 — 보류

### V45. Log Preservation + Run Cancel Test — 완료

목표:

- `/cache/native-init.log`가 recovery 왕복 후 보존되는지 확인한다.
- `run` cancelable child wait를 실기 검증한다.

구현/준비:

- `/cache/bin` 또는 ramdisk에 안전한 static helper 준비
- long-running helper 실행 후 q/Ctrl-C cancel 확인
- recovery 재부팅 후 `cat /cache/native-init.log` 확인

검증:

- `run /bin/a90sleep 30` + q — PASS
- `last` — PASS
- `logcat` — PASS
- TWRP 왕복 후 log 보존 — PASS

### V46. Safe Storage / Partition Map Report — 완료

목표:

- 쓰기 가능한 안전 영역과 건드리면 안 되는 영역을 명확히 분리한다.

확인:

- `/cache`
- `/tmp`
- `/mnt/system` read-only
- `/data`는 보류
- `/efs`, modem, RPMB, keymaster 계열은 금지

산출:

- `docs/reports/NATIVE_INIT_STORAGE_MAP_2026-04-25.md`

결론:

- `/cache`는 native init log와 작은 도구를 둘 수 있는 1차 persistent safe write 영역
- `userdata`는 약 110 GiB 대용량 후보지만 Android FBE/user data와 엮여 있어 별도 백업/포맷 계획 전까지 보류
- `efs`, `sec_efs`, modem, persist, key/security, vbmeta, bootloader 계열은 do-not-touch
- block major/minor는 부팅마다 달라질 수 있으므로 by-name 또는 `/sys/class/block/<name>/dev` 기준으로 식별

### V47. On-screen Menu Draft — 완료

목표:

- serial 없이도 화면과 버튼만으로 최소 조작이 가능하게 한다.

구현:

- KMS 기반 screen menu 표시
- VOL+/VOL-/POWER 선택
- status/log/recovery/reboot/poweroff 우선
- `blindmenu`는 serial-only fallback으로 유지

검증:

- `menu` 화면 진입 — PASS
- q cancel 후 autohud 복구 — PASS
- 실제 버튼 이동/선택 — 수동 확인 대기
- recovery/reboot/poweroff 위험 동작 — 수동 확인 대기

산출:

- `docs/reports/NATIVE_INIT_V47_SCREEN_MENU_2026-04-25.md`

### V48. USB Gadget Map Report — 완료

목표:

- 현재 USB ACM serial 제어 채널을 기준점으로 고정한다.
- ADB와 USB networking 후보를 분리해 다음 실험 순서를 정한다.

확인:

- device-side configfs 구성은 `g1` + `acm.usb0` + `a600000.dwc3`
- host-side descriptor는 `04e8:6861`, CDC ACM control/data 2-interface
- host driver는 `cdc_acm`, 노드는 `/dev/ttyACM0`
- ADB는 `ffs.adb`/FunctionFS 경로가 있으나 `adbd` zombie와 `ep0 only`가 blocker
- USB networking은 ACM rescue channel 유지 후 두 번째 function으로 추가하는 방향

산출:

- `docs/reports/NATIVE_INIT_USB_GADGET_MAP_2026-04-25.md`

### V49. Toybox / Static Userland Candidate Review — 완료

목표:

- 모든 유틸을 native init 안에 재구현하지 않고, static ARM64 multi-call binary를 붙일 수 있는지 판단한다.
- USB networking probe 전에 `ip`/`ifconfig`/`route`/`nc`/`ps`/`dmesg`/`grep`/`tail` 계열 도구 확보 가능성을 확인한다.

확인:

- `run <path> [args...]`는 이미 static helper 실행, exit status, q/Ctrl-C cancel을 지원한다.
- 현재 `run` PATH는 `/cache:/cache/bin:/bin:/system/bin`이라 `/cache/bin` 기반 실험과 맞다.
- host build prerequisite 설치 후 `toybox 0.8.13` static ARM64 빌드가 성공했다.
- artifact는 `external_tools/userland/bin/toybox-aarch64-static-0.8.13`에 생성된다.
- artifact SHA256은 `92a0917579c76fec965578ac242afbf7dedc4428297fb90f4c9caf7f538a718c`다.
- `INTERP` segment와 dynamic section이 없어 static ELF 기준은 통과했다.
- 과거 `busybox-static:arm64` apt 확보 실패 기록이 있다.
- BusyBox는 GPLv2 배포 의무를 고려해야 하고, toybox는 Android 계열과 라이선스 측면에서 비교 후보가 된다.

산출:

- `docs/reports/NATIVE_INIT_USERLAND_CANDIDATES_2026-04-25.md`

실기 결과:

- `/cache/bin/toybox` 배치 완료
- SHA256 일치: `92a0917579c76fec965578ac242afbf7dedc4428297fb90f4c9caf7f538a718c`
- PASS:
  - `--help`
  - `uname -a`
  - `ls /proc`
  - `ps -A`
  - `ps -ef`
  - `dmesg --help`
  - `dmesg -s 1024`
  - `hexdump -C /proc/version`
  - `ifconfig -a`
  - `route -n`
  - `ip` usage
  - `netcat --help`
- 주의:
  - `ps` 단독은 `rc=1`; `ps -A`/`ps -ef` 사용
  - `netcat -h`는 `rc=1`; `netcat --help` 사용
  - `ip addr`/`ip link`는 interface를 출력하지만 `No such device`와 `rc=1`; USB network 추가 후 재확인

### V50. USB Reattach / NCM Probe — 완료

목표:

- USB gadget rebind 후 serial console이 stale fd에 묶이는 문제를 해결한다.
- ACM rescue channel을 유지한 상태에서 NCM function이 실제 host/device interface를 만드는지 확인한다.

구현:

- `init_v48`에서 `read_line()`을 `poll()` 기반으로 바꾸고 console reattach를 추가했다.
- `reattach`, `usbacmreset` 명령을 추가했다.
- `startadbd`/`stopadbd` rebind 뒤 console reattach를 호출한다.
- `serial_tcp_bridge.py`는 USB 재열거 시 serial device identity 변화를 감지해 fd를 다시 연다.
- `a90_usbnet` helper는 `status|ncm|rndis|probe-ncm|probe-rndis|off`를 제공한다.

실기 결과:

- `stage3/boot_linux_v48.img` 플래시 완료
- `version` → `A90 Linux init v48` 확인
- `usbacmreset` 후 serial console reattached 확인
- `run /cache/bin/a90_usbnet off` 후 약 3초 내 bridge `version` 복구 확인
- `probe-ncm` 중 host:
  - phone device에 `cdc_acm` + `cdc_ncm` composite interface 표시
  - `enx26eaa7b343d7` / `enx425f6b65a0cb` 형태 NCM interface 생성 확인
- `probe-ncm` 중 device:
  - toybox `ifconfig -a`에서 `ncm0` 확인
- rollback 후 ACM-only와 `version` 복구 확인

산출:

- `docs/reports/NATIVE_INIT_V48_USB_REATTACH_NCM_2026-04-25.md`

### V51~V52. HUD/Menu TUI Polish — 완료

목표:

- 부팅 후 TEST 화면에서 상태 화면과 버튼 메뉴로 자연스럽게 넘어간다.
- 화면 상단에 배터리, 전력, CPU/GPU 온도, 메모리, load를 읽기 쉽게 표시한다.
- VOL+/VOL-/POWER 조작 힌트와 메뉴 항목을 실기에서 보기 좋은 위치로 배치한다.

실기 결과:

- `A90 INIT BOOT OK CONSOLE`
- `BAT 100% FUL PWR ...`
- `CPU ... GPU ...`
- `MEM ... LOAD ...`
- `HIDE MENU`, `STATUS`, `LOG`, `RECOVERY`, `REBOOT`, `POWEROFF`
- footer `A90V52 UP ...`

### V53. Menu Busy Gate + Flash Auto-hide — 완료

목표:

- 화면 메뉴가 떠 있을 때 serial shell과 버튼 UI가 동시에 위험 명령을 실행하지 않게 한다.
- automation은 hang 대신 `[busy]`를 보고 `hide` 후 재시도할 수 있게 한다.

구현:

- `init_v53`에서 menu active state와 hide request를 `/tmp` 파일로 공유
- 메뉴 active 중 위험/장시간 명령은 `[busy]`로 즉시 차단
- `version`, `status`, `timeline`, `logcat` 등 관찰 명령은 허용
- `native_init_flash.py --from-native`는 `[busy]`를 보면 `hide` 후 `recovery` 재시도

실기 결과:

- `stage3/boot_linux_v53.img` SHA256 `44cb9ebb3cc65ab0b3316afe69592c8b7fa7a05a96c872dfd2a4f9f884d98046`
- local image SHA256, remote SHA256, boot partition prefix SHA256 일치
- `echo busytest` → `[busy] auto menu active; send hide/q or select HIDE MENU`
- `hide` 후 `echo afterhide` → `[done] echo`

산출:

- `docs/reports/NATIVE_INIT_V53_MENU_BUSY_2026-04-25.md`

### V54. NCM Persistent Link Validation — 완료

목표:

- ACM serial을 유지한 채 USB NCM persistent mode를 켠다.
- host `cdc_ncm` interface와 device `ncm0`가 동시에 살아 있는지 확인한다.
- NCM 위에서 실제 L3/TCP 통신이 가능한지 확인한다.

실기 결과:

- host: `04e8:6861` composite에 `cdc_acm` + `cdc_ncm` 동시 표시
- host interface: `enx6e0617d3b2a3`
- device helper: `f1 -> acm.usb0`, `f2 -> ncm.usb0`, `ncm.ifname: ncm0`
- device `ncm0`: `192.168.7.2/24`, `fe80::f83d:4bff:fe0f:b583/64`
- host `enx6e0617d3b2a3`: `192.168.7.1/24`
- IPv4 ping `192.168.7.2`: 3/3 PASS, 0% packet loss
- IPv6 link-local ping은 응답 확인
- host → device TCP:
  - host `nc -6 ... 2323`
  - device `/cache/bin/toybox netcat -l -p 2323`
  - payload `hello-from-host-over-ncm-ipv6` 수신 확인

산출:

- `docs/reports/NATIVE_INIT_V54_NCM_LINK_2026-04-25.md`

### V55. NCM Operations Helper — 완료

목표:

- NCM을 매번 수동 설정하지 않고 host helper로 재현 가능하게 켠다.
- device `ncm0`와 host `enx...`를 `192.168.7.2/24` ↔ `192.168.7.1/24`로 고정한다.
- toybox `netcat`의 serial stdin 충돌을 피하기 위해 전용 TCP helper로 양방향 payload를 검증한다.

구현:

- `scripts/revalidation/ncm_host_setup.py`
  - `setup|status|ping|off`
  - bridge `127.0.0.1:54321` 기준으로 `a90_usbnet ncm/status/off` 실행
  - `ncm.host_addr`를 파싱해 `/sys/class/net/*/address`에서 host interface 자동 탐지
  - host `sudo ip addr replace`, `ip link set up`, `ping` 검증 수행
- `stage3/linux_init/a90_nettest.c`
  - `listen <port> <timeout_sec> <expect>`
  - `send <host_ipv4> <port> <payload>`
- `scripts/revalidation/build_nettest_helper.sh`
  - static ARM64 `a90_nettest` 빌드

검증:

- local Python syntax check — PASS
- static ARM64 `a90_nettest` build — PASS
- `ncm_host_setup.py status` host interface 자동 탐지 — PASS
- `ncm_host_setup.py ping` 3/3, 0% loss — PASS
- static `a90_nettest` `/cache/bin` 배치와 SHA256 일치 — PASS
- host→device TCP payload — PASS
- device→host TCP payload — PASS
- 30초 ping stability 30/30, 0% loss — PASS
- rollback `off`는 작업 링크 유지를 위해 이번 pass에서는 실행하지 않음

산출:

- `docs/reports/NATIVE_INIT_V55_NCM_OPS_2026-04-25.md`

### V56. NCM TCP Control Helper — 완료

목표:

- USB NCM 위에서 serial bridge보다 빠른 작은 TCP 명령/응답 채널을 확보한다.
- serial bridge는 rescue/fallback으로 유지한다.

구현:

- `stage3/linux_init/a90_tcpctl.c`
  - `listen <port> <idle_timeout_sec> [max_clients]`
  - command: `help`, `ping`, `version`, `status`, `run`, `quit`, `shutdown`
  - `run`은 absolute path, stdin `/dev/null`, stdout/stderr TCP 반환, 10초 timeout
- `scripts/revalidation/build_tcpctl_helper.sh`
  - static ARM64 `a90_tcpctl` 빌드

검증:

- host-native protocol smoke test — PASS
- static ARM64 build — PASS
- `/cache/bin/a90_tcpctl` 배치와 SHA256 일치 — PASS
- TCP `ping`, `version`, `status` — PASS
- TCP `run /cache/bin/toybox uname -a` — PASS
- TCP `run /cache/bin/toybox ifconfig ncm0` — PASS
- TCP `shutdown` 후 serial `run` 종료 — PASS
- 이후 serial bridge `version`과 NCM ping 3/3 — PASS

산출:

- `docs/reports/NATIVE_INIT_V56_TCPCTL_2026-04-26.md`

### V57. TCP Control Host Wrapper — 완료

목표:

- `a90_tcpctl` launch/client/stop을 host script 하나로 반복 가능하게 만든다.
- smoke test로 NCM TCP control 채널을 빠르게 재검증한다.

구현:

- `scripts/revalidation/tcpctl_host.py`
  - `install`
  - `start`
  - `call`
  - `ping`, `version`, `status`
  - `run`
  - `stop`
  - `smoke`

검증:

- Python syntax/help — PASS
- `tcpctl_host.py smoke` — PASS
- TCP `ping`, `version`, `status`, `run`, `shutdown` — PASS
- serial `run` 종료와 bridge `version` — PASS
- NCM ping 3/3 — PASS

산출:

- `docs/reports/NATIVE_INIT_V57_TCPCTL_HOST_WRAPPER_2026-04-26.md`

### V58. TCP Control Soak — 완료

목표:

- USB NCM + `a90_tcpctl` 조합이 짧은 smoke를 넘어 일정 시간 반복 운용 가능한지 확인한다.
- serial bridge는 launch/rescue 채널로 유지하고, 실제 명령 왕복은 TCP control로 반복한다.

구현:

- `scripts/revalidation/tcpctl_host.py`
  - `soak`
  - 기본 300초, 10초 간격
  - TCP `ping` 매 사이클
  - TCP `status`와 `run /cache/bin/toybox uptime` 매 6사이클
  - host NCM ping 매 사이클
  - 종료 시 TCP `shutdown`, serial `[done] run`, bridge `version`, final NCM ping 검증

검증:

- Python syntax/help — PASS
- short soak 20초/4사이클 — PASS
- main soak 300초/30사이클 — PASS
- TCP ping 30/30 — PASS
- TCP status 5/5 — PASS
- TCP run uptime 5/5 — PASS
- host ping 30/30 — PASS
- `tcpctl: served=42 stop=1`, serial `[done] run (300509ms)` — PASS
- final NCM ping 3/3, 0% loss — PASS

남은 범위:

- 물리 USB unplug/replug 또는 UDC reset 이후 reconnect soak는 별도 항목으로 남긴다.

산출:

- `docs/reports/NATIVE_INIT_V58_TCPCTL_SOAK_2026-04-26.md`

### V59. AT Serial Noise Filter — 완료

목표:

- host NetworkManager/modem probe가 ACM serial에 던지는 unsolicited `AT` 계열 문자열을 shell 오류로 처리하지 않는다.
- filter는 host bridge가 아니라 native init shell 입력 경로에 넣어 device 단독 안정성을 높인다.

구현:

- `stage3/linux_init/init_v59.c`
  - `INIT_VERSION`을 `v59`로 갱신
  - `is_unsolicited_at_noise()` 추가
  - `AT`, `ATE0`, `AT+...`, `ATQ0 ...` 형태의 printable modem command line을 command dispatch 전에 무시
  - 무시한 line은 `/cache/native-init.log`에 `serial: ignored AT probe ...`로 기록

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v59.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v59 boot — PASS
- bridge `version` → `A90 Linux init v59` — PASS
- serial 입력 `AT`, `ATE0`, `AT+GCAP`, `ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0`, `version` — PASS
- 출력에 `unknown command: AT` 없음 — PASS
- `/cache/native-init.log`에 ignored AT probe 4건 기록 — PASS

산출:

- `docs/reports/NATIVE_INIT_V59_AT_NOISE_2026-04-26.md`

### V60. Opt-in Boot Netservice — 완료

목표:

- NCM/tcpctl을 부팅마다 수동 시작하지 않고 필요할 때만 자동 시작하는 service 정책으로 정리한다.
- default OFF를 유지해 serial bridge와 recovery 복구 경로를 보존한다.
- `/cache/native-init-netservice` flag가 있을 때만 boot-time NCM/tcpctl을 켠다.

구현:

- `stage3/linux_init/init_v60.c`
  - `INIT_VERSION`을 `v60`으로 갱신
  - `netservice [status|start|stop|enable|disable]` 추가
  - `enable`은 flag 생성 후 NCM/tcpctl 시작
  - `disable`은 flag 제거, tracked tcpctl 종료, `a90_usbnet off`, console reattach 수행
  - boot path에서 flag가 있으면 `/cache/bin/a90_usbnet ncm`, `ifconfig ncm0 192.168.7.2/24`, `a90_tcpctl listen 2325 3600 0` 실행
  - `/cache/native-init-netservice.log`에 helper 출력과 실패 원인 기록
- `scripts/revalidation/ncm_host_setup.py`
  - 이미 NCM이 active면 `a90_usbnet ncm` 재실행 없이 host/device IP와 ping만 검증

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v60.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v60 boot — PASS
- default OFF boot: `enabled=no`, `ncm0=absent`, `tcpctl=stopped` — PASS
- enabled flag boot auto-start: `enabled=yes`, `ncm0=present`, `tcpctl=running pid=544` — PASS
- host `enx0a2eb7a94b2f`에 `192.168.7.1/24` 설정 후 `192.168.7.2` ping 3/3 — PASS
- `tcpctl_host.py ping`, `status`, `run /cache/bin/toybox uptime` — PASS
- `netservice disable` rollback 후 `enabled=no`, `ncm0=absent`, `tcpctl=stopped` — PASS

산출:

- `stage3/linux_init/init_v60`
  - SHA256 `4a274b02f793be79872c4ff164dcead332b33e4f7cf281c35f1d59625774dd09`
- `stage3/ramdisk_v60.cpio`
  - SHA256 `f8b153804c561e26c784c713668a6e8e3dfb0cb10b83a9a72c659f1d8c46285c`
- `stage3/boot_linux_v60.img`
  - SHA256 `c57fbf4645790826fbd5e804ff605c25b95cffb4c5eb0ff9076202581e6e828a`
- `docs/reports/NATIVE_INIT_V60_NETSERVICE_2026-04-26.md`

### V60.1. Netservice UDC Reconnect Validation — 완료

목표:

- v60 `netservice stop/start`로 software UDC 재열거 후 ACM serial, NCM, TCP control이 복구되는지 확인한다.
- NCM 재열거마다 host `enx...` 이름이 바뀌는 문제를 운영 도구와 문서에 반영한다.

구현:

- `scripts/revalidation/netservice_reconnect_soak.py`
  - `status`, `once`, `soak` command 추가
  - `a90_usbnet status`의 `ncm.host_addr` MAC으로 현재 host interface 자동 탐지
  - `--manual-host-config`로 sudo 불가 환경에서 현재 `sudo ip ... dev <enx...>` 명령 출력 후 대기

검증:

- stale `enx0a2eb7a94b2f`에 host IP 설정 시 `Cannot find device` — 관찰됨
- 새 interface `enxba06f3efab0f`에 `192.168.7.1/24` 설정 — PASS
- `192.168.7.2` ping 3/3, 0% loss — PASS
- `tcpctl_host.py ping` — PASS
- `tcpctl_host.py status` — PASS
- `tcpctl_host.py run /cache/bin/toybox uptime` — PASS
- final `netservice stop`, `ncm0=absent`, `tcpctl=stopped`, bridge `version` v60 — PASS

발견:

- USB 재열거 중 host modem probe fragment `A` 또는 `ATAT...`가 serial output을 오염시킬 수 있음
- v59/v60 filter는 full `AT` line은 처리하지만 single `A` fragment는 아직 보강 필요

산출:

- `docs/reports/NATIVE_INIT_V60_RECONNECT_2026-04-26.md`

### V61. CPU/GPU Usage Percent HUD — 완료

목표:

- 기존 CPU/GPU 온도 표시 옆에 사용률 `%`만 먼저 추가한다.
- GPU clock/frequency 표시는 공간 확인 뒤 후순위로 둔다.

구현:

- `stage3/linux_init/init_v61.c`
  - `INIT_VERSION`을 `v61`로 갱신
  - `/proc/stat` aggregate delta 기반 CPU usage 계산
  - KGSL `/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage` 기반 GPU busy `%` 표시
  - `status`와 HUD row 2를 `CPU <temp> <usage> GPU <temp> <usage>` 형태로 변경

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v61.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v61 boot — PASS
- bridge `version` → `A90 Linux init v61` — PASS
- `status` → `thermal: cpu=35.1C 0% gpu=33.5C 0%` — PASS
- `statushud` redraw 후 `thermal: cpu=35.3C 12% gpu=33.6C 0%` — PASS
- final `autohud: running`, `netservice: disabled tcpctl=stopped` — PASS

산출:

- `stage3/linux_init/init_v61`
  - SHA256 `7fce8bac65af8cd997d7f150c0939b6e4fa757ea0ecfeb89e0213c3fa955f427`
- `stage3/ramdisk_v61.cpio`
  - SHA256 `2ce70282a001db47d42b900ccc0bfaf3aed7dee1528107048912bfbaab53d729`
- `stage3/boot_linux_v61.img`
  - SHA256 `40a33381be60ea8eaf91e7f09256d3d0de100c8959c3687a3b4aa95696c7cdb2`
- `docs/reports/NATIVE_INIT_V61_CPU_GPU_USAGE_2026-04-26.md`

### V62. CPU Stress Gauge Validation — 완료

목표:

- v61 CPU usage `%`가 실제 CPU 부하에서 변하는지 검증한다.
- `/dev/null`/`/dev/zero`가 없거나 regular file로 오염돼도 boot-time에 char device로 복구한다.

구현:

- `stage3/linux_init/init_v62.c`
  - `INIT_VERSION`을 `v62`로 갱신
  - `/dev/null` rdev `1:3`, `/dev/zero` rdev `1:5` 보정
  - `cpustress [sec] [workers]` 명령 추가
  - worker fork, timeout, q/Ctrl-C 취소 처리

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v62.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v62 boot — PASS
- bridge `version` → `A90 Linux init v62` — PASS
- `/dev/null` → `mode=0600`, `rdev=1:3` — PASS
- `/dev/zero` → `mode=0600`, `rdev=1:5` — PASS
- `cpustress 10 8` 전 `thermal: cpu=34.9C 0% gpu=33.3C 0%` — PASS
- `cpustress 10 8` 후 `thermal: cpu=36.3C 29% gpu=34.6C 0%` — PASS
- cooldown 후 `thermal: cpu=35.4C 0% gpu=33.7C 0%` — PASS

산출:

- `stage3/linux_init/init_v62`
  - SHA256 `016f67ec1bd713533ed8d2d12e5e5f7cd5709406ce6351fa0d22f30d0bcdfa33`
- `stage3/ramdisk_v62.cpio`
  - SHA256 `13ced5f0e0d97887fe84036b777cd5efdc97b0c81089261b9397f5da12169629`
- `stage3/boot_linux_v62.img`
  - SHA256 `8c422903226980855e23b75379a60b4ec3ec0a680c457b28adfa5417fdf870b1`
- `docs/reports/NATIVE_INIT_V62_CPUSTRESS_2026-04-26.md`

### V63. App Menu / CPU Stress Screen App — 완료

목표:

- 기존 단일 화면 메뉴를 앱 폴더 형태로 확장한다.
- LOG/NETWORK/CPU STRESS가 한 프레임만 보이고 사라지는 문제를 고친다.
- CPU stress는 버튼으로 5/10/30/60초를 선택하고, 실행 중 CPU 관련 정보를 전용 화면에 표시한다.

구현:

- `stage3/linux_init/init_v63.c`
  - `MAIN MENU` 아래 `APPS >`, `NETWORK >`, `POWER >` 계층 추가
  - `APPS / TOOLS / CPU STRESS` 시간 선택 메뉴 추가
  - `SCREEN_APP_LOG`, `SCREEN_APP_NETWORK`, `SCREEN_APP_CPU_STRESS` active app state 추가
  - CPU stress screen app에서 CPU 온도/사용률/load, online/present core, core frequency, memory, power, worker 수 표시
  - 자동 HUD 메뉴의 help/menu 간격과 안내 문구 밝기 조정

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v63.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v63 boot — PASS
- bridge `version` → `A90 Linux init v63` — PASS
- 자동 메뉴에서 `APPS >`, `TOOLS >`, `CPU STRESS >` 계층 표시 확인 — PASS
- `HIDE MENU`와 serial `hide` 경로 확인 — PASS

산출:

- `stage3/linux_init/init_v63`
  - SHA256 `062eb9a780c0fe71890e80d0c961b5b3016d3d35e0da19fa99e5289bbde04a00`
- `stage3/ramdisk_v63.cpio`
  - SHA256 `7b9d3f71f648e7f9765fc6c1827c66c0dcc422f714b1ec67a334f9cbca5f53ce`
- `stage3/boot_linux_v63.img`
  - SHA256 `99025fba4c17348057920eab06b7bd98a97b5cc5f6acff21190981288a0ad09d`
- `docs/reports/NATIVE_INIT_V63_APP_MENU_2026-04-26.md`

### V64. Custom Boot Splash — 완료

목표:

- 부팅 직후 큰 `TEST` 디버그 화면 대신 프로젝트 전용 boot splash를 표시한다.
- 이후 기존처럼 상태 HUD/menu로 자동 전환한다.

구현:

- `stage3/linux_init/init_v64.c`
  - `INIT_VERSION`을 `v64`로 갱신
  - `BOOT_SPLASH_SECONDS` 2초 유지
  - `kms_draw_boot_splash()` 추가
  - boot frame 로그를 `display-splash` timeline으로 기록
  - serial boot 안내를 `splash 2s -> autohud 2s`로 변경

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v64.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v64 boot — PASS
- bridge `version` → `A90 Linux init v64` — PASS
- `timeline` → `display-splash rc=0 ... boot splash applied` — PASS
- `status` → `boot: BOOT OK shell 3S`, `autohud: running` — PASS

산출:

- `stage3/linux_init/init_v64`
  - SHA256 `f80152f02db376080bdcae3600ce6daf03e64bc08e0e092a8ae3b9116ea7bde2`
- `stage3/ramdisk_v64.cpio`
  - SHA256 `8560785b5e2832d40913b3b0e91a90e633041809a788200ebb6aa875c12ed018`
- `stage3/boot_linux_v64.img`
  - SHA256 `aa628f70f09a62f704b9d2078aae888ad57d95349fcaf8d3af47d95a3ad864ca`
- `docs/reports/NATIVE_INIT_V64_BOOT_SPLASH_2026-04-26.md`

### V65. Splash Safe Layout — 완료

목표:

- v64 custom splash가 보이지만 일부 텍스트가 잘리는 문제를 해결한다.
- 긴 상태 문구와 footer가 1080px 폭과 라운드 코너/안전 여백을 넘지 않게 한다.

구현:

- `stage3/linux_init/init_v65.c`
  - `INIT_VERSION`을 `v65`로 갱신
  - splash 기본 scale 축소
  - 좌우 margin을 넓히고 row width를 계산
  - `kms_draw_text_fit()`으로 각 줄을 `shrink_text_scale()`에 통과
  - 상태 문구를 짧게 정리
  - footer 위치를 조금 더 위로 올리고 card 폭 안에서 축소

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v65.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v65 boot — PASS
- bridge `version` → `A90 Linux init v65` — PASS
- `status` → `boot: BOOT OK shell 3S`, `autohud: running` — PASS
- `timeline` → `display-splash rc=0 ... boot splash applied` — PASS

산출:

- `stage3/linux_init/init_v65`
  - SHA256 `2cb2b9e5e8d989cddb92f3c1ef93b8f4674ba4359408445b19af5745ddc2f373`
- `stage3/ramdisk_v65.cpio`
  - SHA256 `b8184bb241c52b0d99e9efbceed16ded50598a24068a359c8d8e3abf78f1c16f`
- `stage3/boot_linux_v65.img`
  - SHA256 `143acc7925b8ac0006d972ca463c1993f5306b63c5187e9c3007a34fa71ed7d4`
- `docs/reports/NATIVE_INIT_V65_SPLASH_SAFE_LAYOUT_2026-04-26.md`

### V66. About App / Versioning — 완료

목표:

- 공식 semantic version과 기존 `vNN` build tag를 함께 사용한다.
- 만든이 `made by temmie0214`를 splash, `version`, `status`, ABOUT app에 표시한다.
- 앱 메뉴에서 version, changelog, credits를 확인할 수 있게 한다.

구현:

- `stage3/linux_init/init_v66.c`
  - `INIT_VERSION "0.7.3"`
  - `INIT_BUILD "v66"`
  - `INIT_CREATOR "made by temmie0214"`
  - `INIT_BANNER "A90 Linux init 0.7.3 (v66)"`
  - `APPS / ABOUT` 메뉴 추가
  - `VERSION`, `CHANGELOG`, `CREDITS` 화면 추가
- `docs/overview/VERSIONING.md`
  - `MAJOR.MINOR.PATCH`와 `vNN` build tag 규칙 정리
- `CHANGELOG.md`
  - 공식 버전별 업데이트 로그 추가

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v66.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v66 boot — PASS
- bridge `version` → `A90 Linux init 0.7.3 (v66)` 및 `made by temmie0214` — PASS
- `status` → `creator: made by temmie0214`, `boot: BOOT OK shell 3S` — PASS
- `timeline` → `init-start ... A90 Linux init 0.7.3 (v66)` — PASS

산출:

- `stage3/linux_init/init_v66`
  - SHA256 `31a8c6e8da1f2ab07fe26a96d6fa78ba02a9cb43e6bc4ea3080220f4efb41715`
- `stage3/ramdisk_v66.cpio`
  - SHA256 `446b070e9df82b6368122ca190c27c3298a147eb778f70c9d08cc7e9bcf7e972`
- `stage3/boot_linux_v66.img`
  - SHA256 `320a325531b6e2ffc35c8165179396638c1c8af5ee4a59517f1074dc92b3eb08`
- `docs/reports/NATIVE_INIT_V66_ABOUT_VERSIONING_2026-04-26.md`

### V67. Changelog Detail Screens — 완료

목표:

- 휴대폰 세로 화면을 활용해 changelog 내용을 더 길게 표시한다.
- ABOUT 계열 화면의 version 글씨 크기를 작게 통일한다.
- `CHANGELOG`를 버전 목록으로 만들고, 선택한 버전의 상세 변경점을 보여준다.

구현:

- `stage3/linux_init/init_v67.c`
  - `INIT_VERSION "0.7.4"`
  - `INIT_BUILD "v67"`
  - `APPS / ABOUT / CHANGELOG >` submenu 추가
  - `0.7.4 v67`~`0.6.0 v62` 상세 화면 추가
  - ABOUT 계열 text scale compact화

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v67.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v67 boot — PASS
- bridge `version` → `A90 Linux init 0.7.4 (v67)` 및 `made by temmie0214` — PASS
- `status` → `creator: made by temmie0214`, `boot: BOOT OK shell 3S`, `autohud: running` — PASS
- `timeline` → `init-start ... A90 Linux init 0.7.4 (v67)` — PASS

산출:

- `stage3/linux_init/init_v67`
  - SHA256 `642da01258a4a43016e5362d74fb2c142a30c42001217c88fa2ae2fe8aa05e04`
- `stage3/ramdisk_v67.cpio`
  - SHA256 `55d2b9c0323e2642c9d7095a62d668b85774476fe5079a43113ef7a5b3e7b6b2`
- `stage3/boot_linux_v67.img`
  - SHA256 `8b087d08ecc5dd459ffd36c22c520f5de9fb2c3ddecee0c212bd4fece57f8623`
- `docs/reports/NATIVE_INIT_V67_CHANGELOG_DETAILS_2026-04-26.md`

### V68. HUD Log Tail / Changelog History — 완료

목표:

- 메뉴를 숨긴 상태에서도 `/cache/native-init.log` tail을 화면에서 확인한다.
- changelog detail 화면을 더 과거 버전까지 확장한다.

검증:

- bridge `version` → `A90 Linux init 0.7.5 (v68)` — PASS

산출:

- `stage3/linux_init/init_v68`
  - SHA256 `24dcfe9b2351c6cb16a1af6737b12c950e5f1972c82f6ede6855b6ec210d64c5`
- `stage3/ramdisk_v68.cpio`
  - SHA256 `c33b9853be5e6faeea1254d47aa8fb165ca44919ce12679ea9d38d487a3cb358`
- `stage3/boot_linux_v68.img`
  - SHA256 `bc0982cb67f966affbc3de2d1d00c4b6a2797e1f79c1267863a29091fd1ddb41`

### V69. Input Gesture Layout — 완료

목표:

- VOL+/VOL-/POWER 3버튼만으로 단일/더블/롱/조합 입력을 분리한다.
- 기존 단일 클릭 메뉴 조작은 유지한다.
- 위험한 `POWER long`은 직접 reboot/poweroff에 묶지 않는다.

구현:

- `stage3/linux_init/init_v69.c`
  - `INIT_VERSION "0.8.0"`
  - `INIT_BUILD "v69"`
  - `inputlayout` command 추가
  - `waitgesture [count]` command 추가
  - `screenmenu`/`blindmenu` gesture action 적용

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v69.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v69 boot — PASS
- bridge `version` → `A90 Linux init 0.8.0 (v69)` 및 `made by temmie0214` — PASS
- `inputlayout` → 단일/더블/롱/조합 mapping 출력 — PASS
- `status` → `creator: made by temmie0214`, `boot: BOOT OK shell 3S` — PASS
- `timeline` → `init-start ... A90 Linux init 0.8.0 (v69)` — PASS

산출:

- `stage3/linux_init/init_v69`
  - SHA256 `bf9a5cc337d8ae0ca705c027053a0e81e3d4436926e331e089952b8916a280e9`
- `stage3/ramdisk_v69.cpio`
  - SHA256 `28fbb2f9ae618086bc704a73529d3cb3c4ebac050052f6dbd396d51503508ada`
- `stage3/boot_linux_v69.img`
  - SHA256 `1a333b5ee8e1c73722b9165f569f17a3257119690fccba3ce160b952792252d8`
- `docs/reports/NATIVE_INIT_V69_INPUT_LAYOUT_2026-04-26.md`

### V70. Input Monitor App — 완료

목표:

- 물리 버튼 이벤트를 raw input과 gesture decoder 결과로 동시에 관찰한다.
- 버튼을 누른 순간, 뗀 순간, hold duration, event gap, decoded action을 화면/serial/log에 남긴다.

구현:

- `stage3/linux_init/init_v70.c`
  - `INIT_VERSION "0.8.1"`
  - `INIT_BUILD "v70"`
  - `TOOLS / INPUT MONITOR` app 추가
  - `inputmonitor [events]` command 추가
  - raw event 2줄 카드 표시와 DOWN/UP/REPEAT 색상 구분
  - 최신 gesture 판정 상단 대형 패널 표시
  - `waitgesture`와 같은 decoder helper 공유

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v70.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v70 boot — PASS
- bridge `version` → `A90 Linux init 0.8.1 (v70)` 및 `made by temmie0214` — PASS
- `status` → `creator: made by temmie0214`, `boot: BOOT OK shell 3S` — PASS
- `inputlayout` → v69 gesture mapping 유지 — PASS

산출:

- `stage3/linux_init/init_v70`
  - SHA256 `d7082127bbfeafd0508cf7a3b90079dc0f3f1b8b8238140cceb5dfe9063d7d12`
- `stage3/ramdisk_v70.cpio`
  - SHA256 `98ae190435469f2817d6d04fce076e643f2cb5f9e1fbafd69d9c865e1d1907b3`
- `stage3/boot_linux_v70.img`
  - SHA256 `5e3657ba14705bdee9cc772cb8916601bfe1a92f31122475c1115896e2a42cb1`
- `docs/reports/NATIVE_INIT_V70_INPUT_MONITOR_2026-04-26.md`

### V71. HUD/Menu Live Log Tail Panel — 완료

구현:

- `stage3/linux_init/init_v71.c`
  - `INIT_VERSION "0.8.2"`
  - `INIT_BUILD "v71"`
  - 공통 `kms_draw_log_tail_panel()` renderer 추가
  - hidden HUD와 auto HUD menu visible 상태에 `LIVE LOG TAIL` 표시
  - manual `screenmenu`도 공간이 있을 때 live log tail 표시
  - live log tail 제목/본문 간격, 줄 수, wrap 처리 개선
  - POWER 메뉴가 아닌 auto menu 상태에서는 일반 serial 명령 허용

검증:

- static ARM64 build — PASS
- bridge `version` → `A90 Linux init 0.8.2 (v71)` 및 `made by temmie0214` — PASS
- bridge `status` → `autohud: running` — PASS
- `screenmenu` framebuffer present 후 `q` cancel 및 HUD restore — PASS
- menu-active `ls /` 허용, `waitkey 1`/`recovery` 보호 차단 — PASS

### V72. Display Test Screen + Color Packing — 완료

구현:

- `stage3/linux_init/init_v72.c`
  - `INIT_VERSION "0.8.3"`
  - `INIT_BUILD "v72"`
  - `TOOLS / DISPLAY TEST`와 `displaytest` 명령 추가
  - 색상 팔레트, 폰트 scale ladder, wrap sample, safe-area/cutout grid 표시
  - display test 상단을 `TOP LEFT SLOT` / `PUNCH HOLE` / `TOP RIGHT SLOT`으로 분리 표시
  - `DRM_FORMAT_XBGR8888` framebuffer color packing 보정
  - on-device changelog `0.8.3 v72` 추가

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v72.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v72 boot — PASS
- bridge `version` → `A90 Linux init 0.8.3 (v72)` 및 `made by temmie0214` — PASS
- bridge `displaytest` → framebuffer present `1080x2400` — PASS
- bridge `autohud 2` 후 `status` → `autohud: running` — PASS

산출:

- `stage3/linux_init/init_v72`
  - SHA256 `3215710e0e5cc4038dea74b0f22575cbeda9e90625cb53b45f702db2b4f08619`
- `stage3/ramdisk_v72.cpio`
  - SHA256 `7e8cad648cec15d7dffe1cb9e8a2b2afa1aa297a01b9450234c26b1cd6ffcc41`
- `stage3/boot_linux_v72.img`
  - SHA256 `2f7e7927f1f22d540a37d7bafd7176730bae24bee418dfb667bfd6805cf0eebf`
- `docs/reports/NATIVE_INIT_V72_DISPLAY_TEST_2026-04-27.md`

### V73. Shell Protocol V1 + a90ctl Wrapper — 완료

구현:

- `stage3/linux_init/init_v73.c`
  - `INIT_VERSION "0.8.4"`
  - `INIT_BUILD "v73"`
  - `cmdv1 <command> [args...]` shell wrapper 추가
  - `A90P1 BEGIN` / `A90P1 END` framed result 추가
  - END record에 `seq`, `cmd`, `rc`, `errno`, `duration_ms`, `status` 포함
  - unknown command와 menu busy 결과도 rc/status로 frame 처리
  - on-device changelog `0.8.4 v73` 추가
- `scripts/revalidation/a90ctl.py`
  - bridge로 `cmdv1` 실행
  - text/JSON 결과 출력
  - `--allow-error`, `--hide-on-busy`, `--quiet`, `--verbose` 지원

검증:

- static ARM64 build — PASS
- `stage3/boot_linux_v73.img` marker 확인 — PASS
- native → TWRP → boot partition flash → v73 boot — PASS
- bridge `version` → `A90 Linux init 0.8.4 (v73)` 및 `made by temmie0214` — PASS
- bridge `cmdv1 status` → `A90P1 END ... rc=0 ... status=ok` — PASS
- bridge `cmdv1 nope` → `A90P1 END ... rc=-2 ... status=unknown` — PASS
- bridge `cmdv1 waitkey 1` while menu visible → `A90P1 END ... rc=-16 ... status=busy` — PASS
- `a90ctl.py status`, `--json --allow-error nope`, `--hide-on-busy status` — PASS

산출:

- `stage3/linux_init/init_v73`
  - SHA256 `7ce8063b6e343dd49ec8e1f2a0856936794bee761242ae6bd333ae1a96b51083`
- `stage3/ramdisk_v73.cpio`
  - SHA256 `dfb14b9a9ab5c48cd95175a0301c4ba8f737638639f2d77dc87af5613524c5df`
- `stage3/boot_linux_v73.img`
  - SHA256 `241e44ef70eb3dc187c8dd44c62c26943c42bd952c7d122374295463d67f159a`
- `docs/reports/NATIVE_INIT_V73_CMDV1_PROTOCOL_2026-04-27.md`

### Host Tooling. native_init_flash cmdv1 Verify — 완료

구현:

- `scripts/revalidation/a90ctl.py`
  - `run_cmdv1_command(host, port, timeout, command)` import용 helper 추가
  - 기존 CLI 동작 유지
- `scripts/revalidation/native_init_flash.py`
  - `--verify-protocol {auto,cmdv1,raw}` 추가
  - 기본 `auto`는 `cmdv1 version/status`의 `rc=0`, `status=ok` 확인
  - `A90P1 END`가 없을 때만 pre-v73 호환용 raw `version` 검증으로 fallback
  - `recovery`/`hide`/TWRP reboot 경로는 연결 종료 가능성이 있어 raw bridge 유지

검증:

- `python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/native_init_flash.py` — PASS
- `native_init_flash.py --verify-only --expect-version "A90 Linux init 0.8.4 (v73)"` — PASS
- `native_init_flash.py --verify-only --verify-protocol raw --expect-version "A90 Linux init 0.8.4 (v73)"` — PASS
- `native_init_flash.py --verify-only --verify-protocol cmdv1 --expect-version "A90 Linux init 0.8.4 (v73)"` — PASS

### Host Tooling. NCM/tcpctl cmdv1 Adoption — 완료

구현:

- `scripts/revalidation/a90ctl.py`
  - reboot 직후 bridge listener가 먼저 열리고 ACM serial이 늦게 붙는 구간을 timeout 내 재시도
- `scripts/revalidation/ncm_host_setup.py`
  - `--device-protocol {auto,cmdv1,raw}` 추가
  - setup/status 쪽 짧은 device command는 `cmdv1` rc/status 우선
  - `off` rollback은 USB 재열거 가능성이 있어 raw bridge 유지
- `scripts/revalidation/netservice_reconnect_soak.py`
  - `--device-protocol {auto,cmdv1,raw}` 추가
  - bridge version/netservice status/usbnet status/ifconfig는 `cmdv1` rc/status 우선
  - `netservice start|stop`은 USB 재열거 가능성이 있어 raw bridge 유지
- `scripts/revalidation/tcpctl_host.py`
  - `--device-protocol {auto,cmdv1,raw}` 추가
  - install 후 chmod/sha256, smoke/soak bridge version은 `cmdv1` rc/status 우선
  - tcpctl listener/transfer streaming은 raw bridge 유지

검증:

- `python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/ncm_host_setup.py scripts/revalidation/netservice_reconnect_soak.py scripts/revalidation/tcpctl_host.py` — PASS
- 세 host script `--help` import/argparse smoke — PASS
- mock helper로 `cmdv1` success와 `A90P1 END` 미검출 auto raw fallback — PASS

### V74. cmdv1x Argument Encoding — 완료

구현:

- `stage3/linux_init/init_v74.c`
  - `INIT_VERSION "0.8.5"`
  - `INIT_BUILD "v74"`
  - `cmdv1x <len:hex-utf8-arg>...` 추가
  - 기존 `cmdv1 <command> [args...]` compatibility 유지
  - malformed `cmdv1x` decode 실패도 `A90P1 END ... status=error`로 frame 처리
  - on-device changelog `0.8.5 v74 CMDV1 ARG ENCODING` 추가
- `scripts/revalidation/a90ctl.py`
  - `encode_cmdv1_line()` 추가
  - simple argv는 legacy `cmdv1`, whitespace/empty/`#` 시작 인자는 `cmdv1x` 자동 선택
  - `shell_command_to_argv()` 공유 helper 추가
- `scripts/revalidation/ncm_host_setup.py`
- `scripts/revalidation/netservice_reconnect_soak.py`
- `scripts/revalidation/tcpctl_host.py`
  - command string parsing은 `a90ctl.py` helper로 통일

검증:

- static ARM64 build — PASS
- `stage3/ramdisk_v74.cpio`, `stage3/boot_linux_v74.img` 생성 — PASS
- boot image marker strings `A90 Linux init 0.8.5 (v74)`, `A90v74`, `cmdv1x` — PASS
- host encoder smoke: `status` → `cmdv1`, `echo "hello world"` → `cmdv1x` — PASS
- Python py_compile + mock legacy/encoded selection + diff check — PASS
- native → TWRP → boot partition flash → v74 boot — PASS
- `native_init_flash.py stage3/boot_linux_v74.img --from-native --expect-version "A90 Linux init 0.8.5 (v74)"` — PASS
- `a90ctl.py --json status` → `rc=0`, `status=ok` — PASS
- `a90ctl.py --json echo "hello world"` → `cmdv1x ...`, `rc=0`, `status=ok` — PASS
- malformed direct `cmdv1x` → `rc=-22`, `status=error` — PASS

산출:

- `stage3/linux_init/init_v74`
  - SHA256 `7868795581cf7974b6c2f24af7dfea75399a429d163f6dc7700007b069bdd872`
- `stage3/ramdisk_v74.cpio`
  - SHA256 `90060ba7c2cd57ad3bb1c271ccafc9bc109fa57767d80747e03db02b8b08f92a`
- `stage3/boot_linux_v74.img`
  - SHA256 `e12839be90ad59e13c8289e2eab8d9441f8bfd2b907bd0f7f819ff65f581f1b4`
- `docs/reports/NATIVE_INIT_V74_CMDV1X_ARG_ENCODING_2026-04-27.md`

## 보류 큐

- ADB 안정화 재검토
- dropbear SSH
- Buildroot/rootfs 묶음
- Android framework 복구 시도

### Physical USB Reconnect. ACM/NCM/tcpctl — 완료

구현:

- `scripts/revalidation/physical_usb_reconnect_check.py`
  - v74 bridge 기준 version 확인
  - netservice가 꺼져 있으면 start 후 NCM ping/tcpctl 검증
  - `READY` 출력 후 실제 USB 케이블 unplug/replug를 기다림
  - replug 후 bridge version, NCM host interface, ping, tcpctl status/run을 재검증
  - script가 netservice를 직접 시작했다면 기본적으로 ACM-only 상태로 복구
- `scripts/revalidation/README.md`
  - 물리 케이블 reconnect 검증 사용법 추가

사용:

```bash
python3 ./scripts/revalidation/physical_usb_reconnect_check.py --manual-host-config
```

주의:

- 현재 sudo noninteractive가 막혀 있으므로 host `enx...` IP 설정은 사용자가 출력된 명령을 직접 실행해야 할 수 있다.

검증:

- `physical_usb_reconnect_check.py --manual-host-config ...` — PASS
- baseline 전 netservice disabled → runner가 netservice start — PASS
- baseline NCM ping 3/3, tcpctl ping/status/run — PASS
- 실제 케이블 unplug 감지: `/dev/ttyACM0` disappeared — PASS
- replug 후 bridge `A90 Linux init 0.8.5 (v74)` recovery — PASS
- replug 후 NCM host interface `enx0644eea6f44d` 복구 — PASS
- replug 후 NCM ping 3/3, tcpctl ping/status/run — PASS
- final ACM-only restore: `ncm0=absent`, `tcpctl=stopped` — PASS

산출:

- `docs/reports/NATIVE_INIT_V74_PHYSICAL_USB_RECONNECT_2026-04-27.md`

### V75. Quiet Idle Serial Reattach Logs — 완료

구현:

- `stage3/linux_init/init_v75.c`
  - `INIT_VERSION "0.8.6"`
  - `INIT_BUILD "v75"`
  - idle serial reattach interval을 `60s`로 완화
  - `reason=idle-timeout` 성공 request/ok 로그 억제
  - idle failure와 수동/non-idle reattach 로그는 유지
  - on-device changelog `0.8.6 v75 QUIET IDLE REATTACH` 추가

검증:

- static ARM64 build — PASS
- `stage3/ramdisk_v75.cpio`, `stage3/boot_linux_v75.img` 생성 — PASS
- boot image marker strings `A90 Linux init 0.8.6 (v75)`, `A90v75`, `0.8.6 v75` — PASS
- native → TWRP → boot partition flash → v75 boot — PASS
- `cmdv1 version/status` verify: `rc=0`, `status=ok` — PASS
- 70초 이상 idle 후 신규 `idle-timeout` 성공 로그 없음 — PASS
- 수동 `reattach`는 `reason=command` request/ok 로그 유지 — PASS

산출:

- `stage3/linux_init/init_v75`
  - SHA256 `840d1cd349b203dd912e3c99dd6b799acfc4fe2f0295c52bdf3f0e9cfe4df1fe`
- `stage3/ramdisk_v75.cpio`
  - SHA256 `af5abb98fdd3f49a767a75db8bda51bcbfea1a9ed75b9e1f6c4dd781c28eb072`
- `stage3/boot_linux_v75.img`
  - SHA256 `50f76a3a9e84ad13f19116e9b6e5b3a1ece6a91b177b81ae8cab1509109452a5`
- `docs/reports/NATIVE_INIT_V75_QUIET_IDLE_REATTACH_2026-04-27.md`

### V76. AT Fragment Serial Noise Filter — 완료

구현:

- `stage3/linux_init/init_v76.c`
  - `INIT_VERSION "0.8.7"`
  - `INIT_BUILD "v76"`
  - `is_unsolicited_at_fragment_noise()` 추가
  - 짧은 `A`/`T` only fragment를 shell command dispatch 전에 무시
  - 기존 full `AT...` probe filter와 `cmdv1`/`cmdv1x` 경로 유지
  - on-device changelog `0.8.7 v76 AT FRAGMENT FILTER` 추가

검증:

- static ARM64 build — PASS
- `stage3/ramdisk_v76.cpio`, `stage3/boot_linux_v76.img` 생성 — PASS
- boot image marker strings `A90 Linux init 0.8.7 (v76)`, `A90v76`, `0.8.7 v76` — PASS
- native → TWRP → boot partition flash → v76 boot — PASS
- `cmdv1 version/status` verify: `rc=0`, `status=ok` — PASS
- raw bridge input `A`, `T`, `AT`, `ATA`, `ATAT`, `AT+GCAP`, `version` — unknown command 없음, `version` 정상 — PASS
- log에 `ignored AT fragment`와 `ignored AT probe` 기록 확인 — PASS
- `cmdv1x` whitespace echo smoke — PASS

산출:

- `stage3/linux_init/init_v76`
  - SHA256 `053986f290d7e87a080515253ad7e1dfbabc73baa462a1e978fe58acb4b1f467`
- `stage3/ramdisk_v76.cpio`
  - SHA256 `06e1d300cd20deea918a86a3eb7413756ddc09ee0ed198f031bb3ceda1d3a0c5`
- `stage3/boot_linux_v76.img`
  - SHA256 `016b2d0c38f3acd1e0868fd5fa86805e52ef88c2e22fdb240dc071b1b39f4b68`
- `docs/reports/NATIVE_INIT_V76_AT_FRAGMENT_FILTER_2026-04-27.md`

### V77. Display Test, Cutout Calibration — 완료

구현:

- `stage3/linux_init/init_v77.c`
  - `INIT_VERSION "0.8.8"`
  - `INIT_BUILD "v77"`
  - display test를 4페이지로 분리
  - page 1: color/pixel
  - page 2: font/wrap
  - page 3: safe/cutout calibration reference
  - page 4: HUD/menu preview
  - `cutoutcal [x y size]` 명령 추가
  - `TOOLS > CUTOUT CAL` interactive app 추가
  - app 조작: VOL+/VOL- adjust, POWER field 변경, POWER long/double 또는 VOL+DN back
  - auto menu app에서 VOL+/VOL- page 이동, POWER back
  - `displaytest [0-3|colors|font|safe|layout]` 지원
  - on-device changelog `0.8.8 v77 DISPLAY TEST PAGES` 추가

검증:

- static ARM64 build — PASS
- `stage3/ramdisk_v77.cpio`, `stage3/boot_linux_v77.img` 생성 — PASS
- boot image marker strings `A90 Linux init 0.8.8 (v77)`, `A90v77`, `0.8.8 v77` — PASS
- native → TWRP → boot partition flash → v77 display/cutout baseline boot — PASS
- `cmdv1 version/status` verify: `rc=0`, `status=ok` — PASS
- `displaytest colors/font/safe/layout` 각각 `rc=0`, `status=ok` — PASS
- `cutoutcal`, `cutoutcal 540 80 49`, `displaytest safe` 재검증 — PASS

비고:

- SD workspace 기능은 버전 의미를 맞추기 위해 `0.8.9 (v78)`로 승격했다.

### V78. Ext4 SD Workspace + Mountsd — 완료

구현:

- `stage3/linux_init/init_v78.c`
  - `INIT_VERSION "0.8.9"`
  - `INIT_BUILD "v78"`
  - v77 display/cutout baseline 유지
  - SD 카드 `/dev/block/mmcblk0p1`을 `ext4` label `A90_NATIVE`로 포맷
  - `mountsd [status|ro|rw|off|init]` 명령 추가
  - SD workspace 표준 경로: `/mnt/sdext/a90`
  - workspace 하위 디렉터리: `bin`, `logs`, `tmp`, `rootfs`, `images`, `backups`
  - `status` 출력에 `mountsd` 상태 통합
  - on-device changelog `0.8.9 v78 SD WORKSPACE` 추가

검증:

- static ARM64 build — PASS
- `stage3/ramdisk_v78.cpio`, `stage3/boot_linux_v78.img` 생성 — PASS
- boot image marker strings `A90 Linux init 0.8.9 (v78)`, `A90v78`, `0.8.9 v78` — PASS
- SD ext4 포맷: `LABEL="A90_NATIVE"`, `TYPE="ext4"` — PASS
- `mountsd init`, workspace dir 생성, write/sync/read — PASS
- `mountsd ro/off/status`와 최종 `status` 통합 출력 — PASS
- `autohud 2` restore와 최종 status — PASS

산출:

- `stage3/linux_init/init_v78`
  - SHA256 `fc2b8f57482deddfe31885e8089e2047d7af08c3ac36414a1e644a2d43ed7274`
- `stage3/ramdisk_v78.cpio`
  - SHA256 `d1e37f098b9a15e2b00e016b882ec40b3fd68ce81f3c68d0a7c303e7a7958fd8`
- `stage3/boot_linux_v78.img`
  - SHA256 `2f57f29e623838601b664001b92bb4ac43e47e03eb0d9cb45bd86322ec52d099`
- `docs/reports/NATIVE_INIT_V78_SD_WORKSPACE_2026-04-29.md`

### V79. Boot-Time SD Health Check + Cache Fallback — 완료

구현:

- `stage3/linux_init/init_v79.c`
  - `INIT_VERSION "0.8.10"`
  - `INIT_BUILD "v79"`
  - boot splash에 cache/SD/storage/serial/runtime 진행 로그 표시
  - expected SD UUID `c6c81408-f453-11e7-b42a-23a2c89f58bc` 확인
  - `/mnt/sdext/a90/.a90-native-id` identity marker 확인/초기화
  - boot-time write/sync/read probe로 SD rw 검증
  - 검증 성공 시 `/mnt/sdext/a90`를 main runtime storage로 설정
  - 실패 시 `/cache` fallback과 HUD warning 표시
  - `storage` 명령과 `status` storage section 추가
  - `mountsd status`에 current/expected UUID match 표시 추가
  - on-device changelog `0.8.10 v79 BOOT SD PROBE` 추가

검증:

- static ARM64 build — PASS
- `stage3/ramdisk_v79.cpio`, `stage3/boot_linux_v79.img` 생성 — PASS
- boot image marker strings `A90 Linux init 0.8.10 (v79)`, `A90v79`, `0.8.10 v79`, expected UUID, SD probe splash lines — PASS

산출:

- `stage3/linux_init/init_v79`
  - SHA256 `c631667a18a55c91e829a24211b5425bdcad2c24c3d4ef7aef98a0745d9e4d03`
- `stage3/ramdisk_v79.cpio`
  - SHA256 `68cb4b6764c5d8a106a24f4b270e5e96bf5a266fa11926213a78640a02a50cf1`
- `stage3/boot_linux_v79.img`
  - SHA256 `1e7363085c3edb541b88b360c6e801eef6fcc67feb421b752bdc236c805b8318`
- `docs/reports/NATIVE_INIT_V79_BOOT_STORAGE_2026-04-29.md`

### V80. PID1 Source Layout Split — 완료

- `stage3/linux_init/init_v80.c`
  - `INIT_VERSION "0.8.11"`
  - `INIT_BUILD "v80"`
  - include 기반 entrypoint로 전환
- `stage3/linux_init/v80/*.inc.c`
  - `00_prelude`
  - `10_core_log_console`
  - `20_device_display`
  - `30_status_hud`
  - `40_menu_apps`
  - `50_boot_services`
  - `60_shell_basic_commands`
  - `70_storage_android_net`
  - `80_shell_dispatch`
  - `90_main`
- 의도:
  - PID1을 아직 여러 프로세스로 쪼개지 않고, 단일 static `/init` binary는 유지
  - static global/state를 유지해서 v79 behavior drift를 최소화
  - 다음 단계에서 helper/process 분리 후보를 더 안전하게 고르기 위한 구조 확보
- 검증:
  - static ARM64 build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v80.cpio`, `stage3/boot_linux_v80.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.11 (v80)`, `A90v80`, `0.8.11 v80 SOURCE MODULES` — PASS
  - TWRP flash and post-boot `cmdv1 version/status` — PASS
  - bridge regression: `storage`, `mountsd status`, `help`, `inputlayout`, `displaytest safe`, `statushud`, `logpath`, `timeline`, `autohud` — PASS
- 산출:
  - `stage3/linux_init/init_v80`
    - SHA256 `f8ad48229cc96cc9a580dbf54b6a5aad847499fa1b9ca5abc517523bbf34292a`
  - `stage3/ramdisk_v80.cpio`
    - SHA256 `8d8c4485ae2d65dfcfff3c867b75dba712fa45b28738dca665af1051b24c6fed`
  - `stage3/boot_linux_v80.img`
    - SHA256 `15a23e7485cc08e3eb46aa515ddc341ba2b14b115415b1216b805947f9612181`
  - `docs/reports/NATIVE_INIT_V80_SOURCE_MODULES_2026-04-29.md`

### V81. Config/Util True Base Modules — 완료

- `stage3/linux_init/a90_config.h`
- `stage3/linux_init/a90_util.c/h`
- 의도:
  - version/path/constant와 공통 파일/시간/errno helper를 실제 `.c/.h` API로 승격
  - PID1 include tree behavior drift를 최소화하고 다음 모듈 추출 기반 확보
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - TWRP flash and post-boot `cmdv1 version/status` — PASS
  - bridge regression: `storage`, `mountsd status`, `help`, `inputlayout`, `displaytest safe`, `statushud`, `logpath`, `timeline`, `autohud` — PASS
- 산출:
  - `docs/reports/NATIVE_INIT_V81_CONFIG_UTIL_2026-04-29.md`

### V82. Log/Timeline True API Modules — 완료

- `stage3/linux_init/a90_log.c/h`
- `stage3/linux_init/a90_timeline.c/h`
- `stage3/linux_init/init_v82.c`
- `stage3/linux_init/v82/*.inc.c`
- 의도:
  - native log path/state와 boot timeline array를 include tree 밖 실제 `.c/.h` API로 승격
  - console/shell/cmdproto, storage, KMS/HUD/menu, netservice는 v82에서 이동하지 않고 안정성 유지
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v82.cpio`, `stage3/boot_linux_v82.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.13 (v82)`, `A90v82`, `0.8.13 v82 LOG TIMELINE API` — PASS
  - TWRP flash and post-boot `cmdv1 version/status` — PASS
  - bridge regression: `version`, `status`, `logpath`, `timeline`, `bootstatus`, `storage`, `mountsd status`, `displaytest safe`, `autohud 2` — PASS
- 산출:
  - `stage3/linux_init/init_v82`
    - SHA256 `56073411436ded0d75ce53ca2bdb70ca486201588d68dae4dff69029f34a5646`
  - `stage3/ramdisk_v82.cpio`
    - SHA256 `2d22fed414f101d0bd033754f127101730a6ad928ac7e6454e93587892cd3a4f`
  - `stage3/boot_linux_v82.img`
    - SHA256 `b023e1cf38c5fa1f0328030975189e99bcbb47a9715dadde1af0070badb6ab73`
  - `docs/reports/NATIVE_INIT_V82_LOG_TIMELINE_2026-04-29.md`

### V83. Console True API Module — 완료

- `stage3/linux_init/a90_console.c/h`
- `stage3/linux_init/init_v83.c`
- `stage3/linux_init/v83/*.inc.c`
- 의도:
  - `console_fd`, attach/reattach, readline, cancel polling, console write/printf를 실제 `.c/.h` API로 승격
  - shell dispatch와 `cmdv1/cmdv1x` framed protocol은 v83에서 이동하지 않고 다음 분리 후보로 보존
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v83.cpio`, `stage3/boot_linux_v83.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.14 (v83)`, `A90v83`, `0.8.14 v83 CONSOLE API` — PASS
  - TWRP flash and post-boot `cmdv1 version/status` — PASS
  - bridge regression: `version`, `status`, `logpath`, `timeline`, `bootstatus`, `storage`, `mountsd status`, `displaytest safe`, `autohud 2` — PASS
  - console regression: `cat`, `logcat`, `run /bin/a90sleep 1`, `cpustress 3 2`, `watchhud 1 2`, q cancel, `reattach`, `usbacmreset` — PASS
- 산출:
  - `stage3/linux_init/init_v83`
    - SHA256 `0ae4f025d1c9bff5cb2bd89f42a15d2065c62eac18aa568cc13b9e8b0812e8e5`
  - `stage3/ramdisk_v83.cpio`
    - SHA256 `28d5cb735da2b3180df7f8aa100a3a1b47c5ec6f9870363a9f20b82d317cd878`
  - `stage3/boot_linux_v83.img`
    - SHA256 `1a9bdc7582485c95eee107753627e66aa4d2f53ed03bdb3039da18fab027c124`
  - `docs/reports/NATIVE_INIT_V83_CONSOLE_API_2026-04-29.md`
  - `docs/reports/NATIVE_INIT_V83_CONSOLE_SHELL_CMDPROTO_DEPENDENCY_MAP_2026-04-29.md`

### V84. Cmdproto True API Module — 완료

- `stage3/linux_init/a90_cmdproto.c/h`
- `stage3/linux_init/init_v84.c`
- `stage3/linux_init/v84/*.inc.c`
- 의도:
  - `cmdv1/cmdv1x` frame/status/decode 책임을 실제 `.c/.h` API로 승격
  - shell command table, busy gate, last result, dispatch는 v84 include tree에 보존
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v84.cpio`, `stage3/boot_linux_v84.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.15 (v84)`, `A90v84`, `0.8.15 v84 CMDPROTO API` — PASS
  - TWRP flash and post-boot `cmdv1 version/status` — PASS
  - protocol regression: `cmdv1` ok/unknown/busy, malformed `cmdv1x`, whitespace argv — PASS
  - bridge regression: `logpath`, `timeline`, `bootstatus`, `storage`, `mountsd status`, `displaytest safe`, `autohud 2` — PASS
  - cancel regression: `run`, `cpustress`, `watchhud` q cancel — PASS
- 산출:
  - `stage3/linux_init/init_v84`
    - SHA256 `e52d034cbd3a741841e7be9ed45b8c9a54d5c2db491075fde022097374879886`
  - `stage3/ramdisk_v84.cpio`
    - SHA256 `8223b1c31d4ccca2521647feb9d50d864dd2332a260cc79f2272d5e74547763f`
  - `stage3/boot_linux_v84.img`
    - SHA256 `0a0be54d12489d7aa08437cb7e1aa3537448ddfed49393538a144e71f084bdcd`
  - `docs/reports/NATIVE_INIT_V84_CMDPROTO_API_2026-04-30.md`

### V85. Run/Service Lifecycle API Module — 완료

- `stage3/linux_init/a90_run.c/h`
- `stage3/linux_init/a90_service.c/h`
- `stage3/linux_init/init_v85.c`
- `stage3/linux_init/v85/*.inc.c`
- 의도:
  - `run`/timeout/cancel/reap/stop 책임을 실제 `.c/.h` API로 승격
  - `autohud`, `tcpctl`, `adbd` PID를 service registry 내부 static 상태로 관리
  - netservice 정책과 shell dispatch는 v85 include tree에 보존
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v85.cpio`, `stage3/boot_linux_v85.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.16 (v85)`, `A90v85`, `0.8.16 v85 RUN SERVICE API` — PASS
  - TWRP flash and post-boot `cmdv1 version/status` — PASS
  - bridge regression: `logpath`, `timeline`, `bootstatus`, `storage`, `mountsd status` — PASS
  - runtime regression: `run`, `runandroid`, `cpustress`, `watchhud`, `autohud`, `stophud` — PASS
  - cancel regression: `run`, `cpustress`, `watchhud` q cancel — PASS
  - service regression: `startadbd`, stale PID status, `stopadbd`, `netservice status/start/stop` — PASS
  - NCM host ping은 host `sudo` IP 설정이 필요해 Codex 세션에서는 보류
- 산출:
  - `stage3/linux_init/init_v85`
    - SHA256 `ca227754279f8f23484dce6db4b0b8df9c6cb0412deec916be32dd9a028c31f2`
  - `stage3/ramdisk_v85.cpio`
    - SHA256 `5d35a08d472906b6ae9ad6e0dc0a364a6b1a08e42bc0de51674073901a19fc68`
  - `stage3/boot_linux_v85.img`
    - SHA256 `9e3da0ffd0616292b563c06acee9977de402db84f1de6994db0feb6cf6cf367e`
  - `docs/plans/NATIVE_INIT_V85_RUN_SERVICE_PLAN_2026-04-30.md`
  - `docs/reports/NATIVE_INIT_V85_RUN_SERVICE_API_2026-04-30.md`

### V86. KMS/Draw API Module — 완료

- `stage3/linux_init/a90_kms.c/h`
- `stage3/linux_init/a90_draw.c/h`
- `stage3/linux_init/init_v86.c`
- `stage3/linux_init/v86/*.inc.c`
- 의도:
  - DRM/KMS dumb-buffer 상태와 framebuffer drawing primitive를 실제 `.c/.h` API로 승격
  - HUD/menu/input/displaytest 정책은 v86 include tree에 보존해 behavior drift 최소화
  - v86 include tree의 direct `kms_state` / `struct kms_display_state` 접근 제거
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v86.cpio`, `stage3/boot_linux_v86.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.17 (v86)`, `A90v86`, `0.8.17 v86 KMS DRAW API` — PASS
  - native bridge → TWRP flash → post-boot `cmdv1 version/status` — PASS
  - display regression: `kmsprobe`, `kmssolid`, `kmsframe`, `statushud`, `displaytest`, `cutoutcal`, `autohud` — PASS
  - blocking regression: raw `screenmenu` + q cancel, raw `inputmonitor 0` + q cancel — PASS
- 산출:
  - `stage3/linux_init/init_v86`
    - SHA256 `e3d5e777a3825fa2c5212ab8b7de2fda74b8ced05881b82d75a666fa58ef1e81`
  - `stage3/ramdisk_v86.cpio`
    - SHA256 `6d69aa340162c6a3279d2fa73a10452b50bb5956814da9bdc73524e85e06ebdd`
  - `stage3/boot_linux_v86.img`
    - SHA256 `ca9991061edd1a7a1f33e61ebdbd61df4be5ce7bd9e3d3c5d23351b0c03afbc3`
  - `docs/plans/NATIVE_INIT_V86_KMS_DRAW_PLAN_2026-04-30.md`
  - `docs/reports/NATIVE_INIT_V86_KMS_DRAW_API_2026-04-30.md`

### V87. Input API Module — PASS

- `stage3/linux_init/a90_input.c/h`
- `stage3/linux_init/init_v87.c`
- `stage3/linux_init/v87/*.inc.c`
- 의도:
  - 물리 버튼 open/close, key wait, gesture wait, decoder, menu action mapping을 실제 `.c/.h` API로 승격
  - menu/HUD/displaytest 정책은 v87 include tree에 보존해 behavior drift 최소화
  - `BOOT OK shell 3S` 형태의 절삭 시간을 `BOOT OK shell 4.0s` 형태의 0.1초 표기로 개선
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v87.cpio`, `stage3/boot_linux_v87.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.18 (v87)`, `A90v87`, `0.8.18 v87 INPUT API` — PASS
  - old direct `key_wait_context` / `open_key_wait_context` / `wait_for_input_gesture` 구현 제거 — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - `bootstatus`의 `BOOT OK shell 4.0s` 0.1초 표기 — PASS
  - `logpath`, `timeline`, `storage`, `mountsd status`, `inputlayout`, `inputcaps event0/event3` — PASS
  - `kmsprobe`, `kmsframe`, `statushud`, `displaytest safe`, `cutoutcal`, `autohud 2` — PASS
  - `run /bin/a90sleep 1`, `cpustress 3 2`, `watchhud 1 2` — PASS
- 산출:
  - `stage3/linux_init/init_v87`
    - SHA256 `122db3f8a089667fecab864e9e63d5ab65961da774ad20196820d74d5e124bc0`
  - `stage3/ramdisk_v87.cpio`
    - SHA256 `5d6cc0825da26c3bb89b8b45741c06814df1933ce32902662577ecedb49dfdb6`
  - `stage3/boot_linux_v87.img`
    - SHA256 `ad93b1bf69586a468e6fafdcf2045d1c6192b01dae96f02bc6b7c0edddb6a970`
  - `docs/plans/NATIVE_INIT_V87_INPUT_API_PLAN_2026-04-30.md`
  - `docs/reports/NATIVE_INIT_V87_INPUT_API_2026-04-30.md`

### V88. HUD API Module — PASS

- `stage3/linux_init/a90_hud.c/h`
- `stage3/linux_init/init_v88.c`
- `stage3/linux_init/v88/*.inc.c`
- 의도:
  - boot splash, status HUD, boot summary, warning/status display, log tail panel을 `a90_hud.c/h`로 분리
  - `screenmenu`, `blindmenu`, app routing, displaytest, cutoutcal, inputmonitor 화면은 v88 include tree에 유지
  - `hud -> kms/draw/metrics/storage/timeline/log` 방향은 허용하고 `hud -> menu`, `input -> menu`, `draw -> hud` 순환은 금지
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v88.cpio`, `stage3/boot_linux_v88.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.19 (v88)`, `A90v88`, `0.8.19 v88 HUD API` — PASS
  - old direct `kms_draw_status_overlay` / `kms_draw_log_tail_panel` / `kms_draw_boot_splash` 구현 제거 — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - `statushud`, `autohud 2`, `watchhud 1 2`, `displaytest safe`, `storage`, `mountsd status` — PASS
  - `screenmenu` 표시와 raw `q` cancel recovery — PASS
- 산출:
  - `stage3/linux_init/init_v88`
    - SHA256 `2897aacfe521eaeffd09cbaef05b0d42f102090f38e886a76d7e16e34e0e48cc`
  - `stage3/ramdisk_v88.cpio`
    - SHA256 `0d5875e70078a25a72c7682fcd5a056be9956ae20ee0e2186aca24f686357091`
  - `stage3/boot_linux_v88.img`
    - SHA256 `a8b7a79be3866533042d9fbf883587943c12d195eb3486289b15683317852a6a`
  - `docs/plans/NATIVE_INIT_V88_HUD_API_PLAN_2026-05-02.md`
  - `docs/reports/NATIVE_INIT_V88_HUD_API_2026-05-02.md`

### V89. Menu Control API + Nonblocking Screenmenu — PASS

- `stage3/linux_init/a90_menu.c/h`
- `stage3/linux_init/init_v89.c`
- `stage3/linux_init/v89/*.inc.c`
- 의도:
  - menu page/action/app enum, item/page table, menu state 이동을 `a90_menu.c/h`로 분리
  - `screenmenu`/`menu`를 shell 점유 foreground 명령에서 background HUD show request로 변경
  - `hide`/`hidemenu`/`resume`을 정식 command로 등록
  - `blindmenu`는 rescue foreground menu로 유지
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v89.cpio`, `stage3/boot_linux_v89.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.20 (v89)`, `A90v89`, `0.8.20 v89 MENU CONTROL API` — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - `screenmenu` 즉시 반환 `rc=0/status=ok/duration_ms=0` — PASS
  - menu visible 중 `status`, `logpath`, `timeline`, `storage` 응답 — PASS
  - `hide`, `bootstatus`, `statushud`, `autohud 2`, `displaytest safe`, `cutoutcal`, `watchhud 1 2` — PASS
- 산출:
  - `stage3/linux_init/init_v89`
    - SHA256 `516d3b0c93104c00a0a5d9a8633cfe7041a75b7cfcf35871d65cb9ccbefe689f`
  - `stage3/ramdisk_v89.cpio`
    - SHA256 `2a702cfdbe82633407583137dc5871b1a0911565cea1f3fcc1cfe0141cd2628e`
  - `stage3/boot_linux_v89.img`
    - SHA256 `57a6b5b5a9091c5fe0339e5359ec34e68af00f040c64dfc902636aaedbc618ba`
  - `docs/reports/NATIVE_INIT_V89_MENU_CONTROL_API_2026-05-02.md`

### V90. Metrics API — PASS

- `stage3/linux_init/a90_metrics.c/h`
- `stage3/linux_init/init_v90.c`
- `stage3/linux_init/v90/*.inc.c`
- 의도:
  - 배터리/CPU/GPU/MEM/전력/uptime sysfs snapshot 책임을 `a90_metrics.c/h`로 분리
  - HUD는 metrics snapshot을 표시하는 renderer로 유지
  - `status`, status HUD, CPU stress 화면의 metric callsite를 `a90_metrics_*` API로 통일
- 검증:
  - static ARM64 multi-source build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v90.cpio`, `stage3/boot_linux_v90.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.21 (v90)`, `A90v90`, `0.8.21 v90 METRICS API` — PASS
  - old HUD metrics API 제거 확인 — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - `statushud`, `autohud 2`, `watchhud 1 2`, `screenmenu`, `hide`, `storage`, `mountsd status` — PASS
  - `cpustress 3 2`, `displaytest safe`, `cutoutcal` — PASS
- 산출:
  - `stage3/linux_init/init_v90`
    - SHA256 `106c1b7d28bf6d9d82042bc4f3588bc3045ec3e06534cdbc58213cf859e6f4c1`
  - `stage3/ramdisk_v90.cpio`
    - SHA256 `66a2988105ab97db31154ab8e10ed5f11331adfee64bedcd9e95f20d7847295b`
  - `stage3/boot_linux_v90.img`
    - SHA256 `0a968f4732a948e1994b4788d29e46e81d74c2dc4170417c4e4d198d6440beee`
  - `docs/reports/NATIVE_INIT_V90_METRICS_API_2026-05-02.md`

### V91. CPU Stress External Helper — PASS

- `stage3/linux_init/helpers/a90_cpustress.c`
- `stage3/linux_init/init_v91.c`
- `stage3/linux_init/v91/*.inc.c`
- 의도:
  - CPU stress worker fork를 PID1 내부에서 제거하고 `/bin/a90_cpustress` helper로 분리
  - shell `cpustress`와 menu CPU stress app이 `a90_run` 기반 helper 실행/stop/reap을 사용
  - cancel/timeout 시 process-group stop으로 helper worker tree를 함께 종료
- 검증:
  - static ARM64 helper/init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v91.cpio`, `stage3/boot_linux_v91.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.22 (v91)`, `A90v91`, `0.8.22 v91 CPUSTRESS HELPER` — PASS
  - v91 tree old PID1 `cpustress_worker`/PID array 직접 관리 제거 확인 — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - `run /bin/a90_cpustress 1 1`, `cpustress 3 2`, q cancel — PASS
  - `statushud`, `autohud 2`, `watchhud 1 2`, `screenmenu`, `hide`, menu-visible `status`, dangerous-command busy gate — PASS
- 산출:
  - `stage3/linux_init/init_v91`
    - SHA256 `886f267b26ce4198668f933dafafbe93b81a8aa6c9bbec05cc77958b76aaf65d`
  - `stage3/linux_init/helpers/a90_cpustress`
    - SHA256 `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd`
  - `stage3/ramdisk_v91.cpio`
    - SHA256 `ebd8c61fbc45c36aaecc77d98c29c54e4beacabd8369cb56b54d90a10668cac1`
  - `stage3/boot_linux_v91.img`
    - SHA256 `a0f027375da3bdd92fc2a4f3d6ed1e6a7ff3963dfcc5961d699dcb829477607f`
  - `docs/reports/NATIVE_INIT_V91_CPUSTRESS_HELPER_2026-05-02.md`

### V92. Shell/Controller Cleanup — PASS

- `stage3/linux_init/a90_shell.c/h`
- `stage3/linux_init/a90_controller.c/h`
- `stage3/linux_init/init_v92.c`
- `stage3/linux_init/v92/*.inc.c`
- 의도:
  - shell command flags/types, last result, protocol sequence, command lookup/result formatting을 `a90_shell` API로 분리
  - auto-menu/power-page busy gate와 hide word policy를 `a90_controller` API로 분리
  - command handler body와 command table entry는 v92 include tree에 유지해 visibility risk를 낮춤
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v92.cpio`, `stage3/boot_linux_v92.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.23 (v92)`, `A90v92`, `0.8.23 v92 SHELL CONTROLLER API` — PASS
  - old direct shell helper removal 확인 — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - unknown command `status=unknown`, menu busy/power-page busy `status=busy` — PASS
  - `screenmenu`, menu-visible `status/logpath/timeline/storage`, `hide` — PASS
  - `cpustress 3 2`, `autohud 2`, `watchhud 1 2` — PASS
- 산출:
  - `stage3/linux_init/init_v92`
    - SHA256 `d2bffdd2111406a2c409a0a03f5605163e016f86cf775199856daf70cd8017f5`
  - `stage3/ramdisk_v92.cpio`
    - SHA256 `1cd524c1ece925b3d5d70b7ee19a7247f1a40c00aab24535f165911fde335880`
  - `stage3/boot_linux_v92.img`
    - SHA256 `817a6a9e2b6c7f1c64e28d972122cd4c3ab022a9430a74a0fbfbef9301079b23`
  - `docs/reports/NATIVE_INIT_V93_STORAGE_API_2026-05-02.md`
  - `docs/reports/NATIVE_INIT_V94_BOOT_SELFTEST_API_2026-05-03.md`

### V93. Storage API First Split — PASS

- `stage3/linux_init/a90_storage.c/h`
- `stage3/linux_init/init_v93.c`
- `stage3/linux_init/v93/*.inc.c`
- 의도:
  - boot storage state, SD workspace probe, `/cache` fallback, `storage`/`mountsd` command logic을 `a90_storage.c/h`로 분리
  - HUD/menu/shell dispatch/netservice가 storage 내부 상태를 직접 보지 않게 status snapshot API로 연결
  - netservice/USB gadget 정책은 v94 후보로 분리해 v93 리스크를 boot-critical storage에 한정
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v93.cpio`, `stage3/boot_linux_v93.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.24 (v93)`, `A90v93`, `0.8.24 v93 STORAGE API` — PASS
  - v93 tree old storage globals 제거 확인 — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - `storage`, `mountsd status`, `mountsd ro/rw/init/off`, `logpath`, `timeline`, `bootstatus` — PASS
  - `mountsd off` + `mountsd init` 후 SD log path 복귀 — PASS
  - `statushud`, `autohud 2`, `screenmenu`, `hide`, `netservice status` — PASS
- 산출:
  - `stage3/linux_init/init_v93`
    - SHA256 `1f013323161b90f1b308631e91a2bbd15fac20d1a86ee3c6990d3c1b1c92855c`
  - `stage3/ramdisk_v93.cpio`
    - SHA256 `6a176f9cdf16b98c6945e87f19d754ab8a7e0de5732b2f1b67c52200a3c068e6`
  - `stage3/boot_linux_v93.img`
    - SHA256 `d62e861dfec7826a85e37d5f80d9c3ac562e65aaf35f37400d1bdafd5ffc889d`
  - `docs/reports/NATIVE_INIT_V93_STORAGE_API_2026-05-02.md`

### V94. Boot Selftest API — PASS

- `stage3/linux_init/a90_selftest.c/h`
- `stage3/linux_init/init_v94.c`
- `stage3/linux_init/v94/*.inc.c`
- 의도:
  - boot-time non-destructive selftest로 모듈화 회귀를 빠르게 감지
  - log/timeline/storage/metrics/KMS/input/service/ACM configfs 상태만 조회
  - 실패는 warn-only로 기록하고 shell/HUD 진입은 유지
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v94.cpio`, `stage3/boot_linux_v94.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.25 (v94)`, `A90v94`, `0.8.25 v94 BOOT SELFTEST API` — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - boot selftest `pass=8 warn=0 fail=0 duration=39ms` — PASS
  - `bootstatus`, `selftest`, `selftest verbose`, `selftest run`, `timeline`, `logcat` — PASS
  - `storage`, `mountsd status`, `statushud`, `autohud 2`, `screenmenu`, `hide`, `netservice status` — PASS
- 산출:
  - `stage3/linux_init/init_v94`
    - SHA256 `c679e021a154643d1b84dfe955c56591cf4fc113d1cd5d6aea8b6c8581aa64bd`
  - `stage3/ramdisk_v94.cpio`
    - SHA256 `31a69d6463131587e48462e05a61c15966f7dc20daf7d0a1099117041164b6be`
  - `stage3/boot_linux_v94.img`
    - SHA256 `ecf0665bc47c9315edaeb46b38ffe0c64c4ff6b6498378292934d8c580753d98`
  - `docs/reports/NATIVE_INIT_V94_BOOT_SELFTEST_API_2026-05-03.md`

### V95. Netservice / USB Gadget API — PASS

- `stage3/linux_init/a90_usb_gadget.c/h`
- `stage3/linux_init/a90_netservice.c/h`
- `stage3/linux_init/init_v95.c`
- `stage3/linux_init/v95/*.inc.c`
- 의도:
  - USB configfs/UDC/ACM primitive를 USB gadget API로 분리
  - NCM/tcpctl start/stop/enable/disable policy를 netservice API로 분리
  - shell/status/menu/selftest는 status snapshot API를 통해 상태 조회
  - USB 재열거 명령은 raw-control friendly 동작 유지
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v95.cpio`, `stage3/boot_linux_v95.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.26 (v95)`, `A90v95`, `0.8.26 v95 NETSERVICE USB API` — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - boot selftest `pass=8 warn=0 fail=0 duration=39ms` — PASS
  - `bootstatus`, `selftest verbose`, `storage`, `mountsd status`, `statushud`, `autohud 2`, `screenmenu`, `hide` — PASS
  - `usbacmreset` after hide, bridge reconnect, `version` — PASS
  - `netservice start`, host NCM ping 3/3, `tcpctl_host.py ping/status/run` — PASS
  - `netservice enable` → reboot → `enabled=yes`, `ncm0=present`, `tcpctl=running` — PASS
  - `netservice disable`, `ncm0=absent`, `tcpctl=stopped`, bridge `version` — PASS
- 산출:
  - `stage3/linux_init/init_v95`
    - SHA256 `13390d59c7a1d4dd460d2e88b6424ddc1759bb79d80aadbd2fd48382faa34390`
  - `stage3/ramdisk_v95.cpio`
    - SHA256 `3d6080c15201766f725cc3adf4c434278f528ea4ab5776e6d759f56ea95c81e5`
  - `stage3/boot_linux_v95.img`
    - SHA256 `cab9b2466e3162ec429e2634728e793990fe8cafc217e3be6b2c9a2f684b5824`
  - `docs/reports/NATIVE_INIT_V95_NETSERVICE_USB_API_2026-05-03.md`

### V96. Structure Audit / Refactor Debt Cleanup — PASS

- `stage3/linux_init/init_v96.c`
- `stage3/linux_init/v96/*.inc.c`
- `stage3/linux_init/a90_console.c`
- `stage3/linux_init/a90_menu.c/h`
- 의도:
  - v95 모듈 분리 이후 중복/겹침/직접 path 접근/남은 lifecycle 중복을 감사
  - stale `A90v83` console reattach klog marker를 `INIT_BUILD` 기반 출력으로 정리
  - v96 ABOUT/changelog/menu entry 추가
  - SD runtime, BusyBox, remote shell, Wi-Fi 기능 추가는 v97+로 보류
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v96.cpio`, `stage3/boot_linux_v96.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.27 (v96)`, `A90v96`, `0.8.27 v96 STRUCTURE AUDIT` — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - boot selftest `pass=8 warn=0 fail=0 duration=39ms` — PASS
  - `bootstatus`, `selftest verbose`, `storage`, `mountsd status`, `statushud`, `autohud 2`, `screenmenu`, `hide`, `netservice status` — PASS
- 산출:
  - `stage3/linux_init/init_v96`
    - SHA256 `2cee558e62f840dd9337ec1852d49116f4ffff99092a35bddece90f9659e65be`
  - `stage3/ramdisk_v96.cpio`
    - SHA256 `f41140ae0c8ad45170adc2927a438c70b002985e1b8e0f493b5711998cc2fe61`
  - `stage3/boot_linux_v96.img`
    - SHA256 `e890a3f4ac3ae59f3bff7a7307551c0545189e664e272b120198eb3b3762dacf`
  - `docs/reports/NATIVE_INIT_V96_STRUCTURE_AUDIT_2026-05-03.md`

### V97. SD Runtime Root — PASS

- `stage3/linux_init/init_v97.c`
- `stage3/linux_init/v97/*.inc.c`
- `stage3/linux_init/a90_runtime.c/h`
- 의도:
  - `/mnt/sdext/a90`를 native runtime root로 격상
  - runtime directory contract `bin/etc/logs/tmp/state/pkg/run` 고정
  - SD가 없거나 unsafe이면 `/cache/a90-runtime` fallback 유지
  - helper deployment, BusyBox, remote shell, Wi-Fi는 v98+로 보류
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v97.cpio`, `stage3/boot_linux_v97.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.28 (v97)`, `A90v97`, `0.8.28 v97 SD RUNTIME ROOT` — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - boot selftest `pass=9 warn=0 fail=0 duration=37ms` — PASS
  - `runtime`, `bootstatus`, `selftest verbose`, `storage`, `mountsd status`, `statushud`, `autohud 2`, `screenmenu`, `hide`, `netservice status` — PASS
- 산출:
  - `stage3/linux_init/init_v97`
    - SHA256 `f0868caa0f6b4b2bbc086870facb93f72ac3983b064dc43991871d678e445c78`
  - `stage3/ramdisk_v97.cpio`
    - SHA256 `9bc749822729f29a6653d5d3b6eb60fcba0038ccb7162c359bada046bdff0473`
  - `stage3/boot_linux_v97.img`
    - SHA256 `e170ec5b3d3eed6ddeb753471feac077b8afa57e450ee4ea37df5219ba28bd5b`
  - `docs/reports/NATIVE_INIT_V97_SD_RUNTIME_ROOT_2026-05-03.md`

### V98. Helper Deployment / Package Manifest — PASS

- `stage3/linux_init/init_v98.c`
- `stage3/linux_init/v98/*.inc.c`
- `stage3/linux_init/a90_helper.c/h`
- `scripts/revalidation/helper_deploy.py`
- 의도:
  - v97 runtime root 위에 helper inventory와 manifest path를 정의
  - `helpers` command로 helper path/presence/mode/fallback 상태 노출
  - `cpustress`는 preferred helper path를 사용하되 ramdisk fallback 유지
  - device-side SHA256은 PID1에서 수행하지 않고 host-side manifest material로 보류
  - BusyBox, remote shell, Wi-Fi는 v99+로 보류
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v98.cpio`, `stage3/boot_linux_v98.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.29 (v98)`, `A90v98`, `0.8.29 v98 HELPER DEPLOY` — PASS
  - TWRP flash → post-boot `cmdv1 version/status` — PASS
  - boot selftest `pass=10 warn=0 fail=0 duration=41ms` — PASS
  - `helpers`, `helpers verbose`, `helpers path a90_cpustress`, `cpustress 3 2`, `helper_deploy.py status/manifest/verify` — PASS
  - `runtime`, `storage`, `mountsd status`, `statushud`, `autohud 2`, `screenmenu`, `hide`, `netservice status` — PASS
- 산출:
  - `stage3/linux_init/init_v98`
    - SHA256 `0d55f6b70d71eba4524790fa72d4276694512806bc515f878a10a0693f0beac3`
  - `stage3/ramdisk_v98.cpio`
    - SHA256 `9b578bd02a0df42534381694ebcfd77d9943e746be3eff998c123bcb9c03ee8a`
  - `stage3/boot_linux_v98.img`
    - SHA256 `c341bc56cfd881bceaf61cb6a30193329ee65f32d686979a236a2e3322039d2e`
  - `docs/reports/NATIVE_INIT_V98_HELPER_DEPLOY_2026-05-03.md`

### V99. BusyBox Static Userland Evaluation — PASS

- `stage3/linux_init/init_v99.c`
- `stage3/linux_init/v99/*.inc.c`
- `stage3/linux_init/a90_userland.c/h`
- `scripts/revalidation/build_static_busybox.sh`
- `scripts/revalidation/busybox_userland.py`
- 의도:
  - static ARM64 BusyBox를 SD runtime root의 optional userland로 평가
  - native PID1 shell은 유지하고 `busybox`/`toybox` wrapper command만 추가
  - BusyBox/toybox inventory를 `status`, `bootstatus`, `selftest`, `userland`에서 확인
  - remote shell/dropbear는 v100+로 보류
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - static BusyBox 1.36.1 build and SHA256 verification — PASS
  - `stage3/ramdisk_v99.cpio`, `stage3/boot_linux_v99.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.8.30 (v99)`, `A90v99`, `0.8.30 v99 BUSYBOX USERLAND` — PASS
  - native flash → post-boot `cmdv1 version/status` — PASS
  - boot selftest `pass=11 warn=0 fail=0 duration=39ms` — PASS
  - `userland`, `userland verbose`, `userland test busybox`, `busybox sh -c`, `busybox ls /proc`, `userland test toybox` — PASS
  - `runtime`, `helpers verbose`, `storage`, `mountsd status`, `statushud`, `autohud 2`, `screenmenu`, `hide`, `netservice status` — PASS
- 산출:
  - `stage3/linux_init/init_v99`
    - SHA256 `fce445e98690773aa8a26d024d9e07a110a703ef28b9cdd933dbdf4bb2b3558a`
  - `stage3/ramdisk_v99.cpio`
    - SHA256 `4f8daa03c24c864afd0be76a9bbf6d2c6d849dce7ece51f1d5fdca6e565047d6`
  - `stage3/boot_linux_v99.img`
    - SHA256 `8d51b9a8f48e96472be9949e607e5868f5a8f4cad60580f37930e459c8ee4eaf`
  - BusyBox binary
    - SHA256 `95fcbded9318a643e51e15bc5b0f2f5281996e0b82d303ce0af8f9acc9685e7c`
  - `docs/reports/NATIVE_INIT_V99_BUSYBOX_USERLAND_2026-05-03.md`

### V100. Remote Shell Prototype — PASS

- `stage3/linux_init/init_v100.c`
- `stage3/linux_init/v100/*.inc.c`
- `stage3/linux_init/helpers/a90_rshell.c`
- `scripts/revalidation/rshell_host.py`
- 의도:
  - verified USB NCM 위에 opt-in custom TCP remote shell 후보를 추가
  - token auth와 NCM-only bind로 최소 보안 경계를 둠
  - Dropbear/PTY/SSH key 정책은 v101+ 이후로 보류
  - ACM serial bridge를 rescue/control channel로 유지
- 검증:
  - static ARM64 init/helper build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v100.cpio`, `stage3/boot_linux_v100.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.9.0 (v100)`, `A90v100`, `0.9.0 v100 REMOTE SHELL`, `A90RSH1` — PASS
  - native flash → post-boot `cmdv1 version/status` — PASS
  - boot selftest `pass=11 warn=0 fail=0 duration=33ms` — PASS
  - `bootstatus`, `helpers verbose`, `userland`, `storage`, `mountsd status`, `stat /bin/a90_rshell` — PASS
  - host NCM ping `192.168.7.1` → `192.168.7.2`: `3/3` — PASS
  - `rshell_host.py exec 'echo A90_RSHELL_OK'` and `rshell_host.py smoke` — PASS
  - `rshell stop` leaves no `a90_rshell` process — PASS
  - `netservice stop` rollback restores ACM serial and reports `ncm0=absent`, `tcpctl=stopped` — PASS
- 산출:
  - `stage3/linux_init/init_v100`
    - SHA256 `073f80024682fbdc655a4b3e99a025ef1d045d3e3ddf5bb63e0ded97d55f5a54`
  - `stage3/linux_init/helpers/a90_rshell`
    - SHA256 `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d`
  - `stage3/ramdisk_v100.cpio`
    - SHA256 `a27217ece3bea98ce6f6bbf3a468d09ca50fade7d7b3efc05f1e28dea26ee79a`
  - `stage3/boot_linux_v100.img`
    - SHA256 `1d15bcba2999d0c46caec3d568ac937201c13a924dd09a1586719154c22abd0c`
  - `docs/reports/NATIVE_INIT_V100_REMOTE_SHELL_2026-05-03.md`

### V101. Minimal Service Manager — PASS

- `stage3/linux_init/init_v101.c`
- `stage3/linux_init/v101/*.inc.c`
- `stage3/linux_init/a90_service.c/h`
- 의도:
  - PID-only service registry를 metadata/status API로 확장
  - `service list/status/start/stop/enable/disable` 공통 operator view 추가
  - autohud/tcpctl/adbd/rshell의 실제 start/stop 구현은 기존 owner에 유지
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v101.cpio`, `stage3/boot_linux_v101.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.9.1 (v101)`, `A90v101`, `0.9.1 v101 SERVICE MANAGER` — PASS
  - native flash → post-boot `cmdv1 version/status` — PASS
  - `service list`, `service status autohud/tcpctl/rshell/adbd` — PASS
  - `service stop/start autohud` — PASS
  - unsupported `service enable autohud/adbd` returns `-EOPNOTSUPP` — PASS
  - `service enable/disable tcpctl`, NCM ping, `tcpctl_host.py ping/status`, ACM rollback — PASS
  - `service start/stop rshell`, `rshell_host.py smoke`, rshell flag disable, tcpctl rollback — PASS
  - `statushud`, `autohud 2`, `screenmenu`, `hide`, `cpustress 3 2`, `storage`, `mountsd status` — PASS
- 산출:
  - `stage3/linux_init/init_v101`
    - SHA256 `5921c53e5c6992bb20c3d2ee55e653dd793cb5d76bf020ccb4d3e9fc621e620c`
  - `stage3/ramdisk_v101.cpio`
    - SHA256 `2a72368840d4c531be28972bd99ff736953aa5160b40e4bc023e64fd3a870ff6`
  - `stage3/boot_linux_v101.img`
    - SHA256 `c5d4f970534d7b7ddc42083ec1b3b7cbc98d0f56a9c726a1932d27cdff266624`
  - `docs/reports/NATIVE_INIT_V101_SERVICE_MANAGER_2026-05-03.md`

### V102. Diagnostics / Log Bundle — PASS

- `stage3/linux_init/init_v102.c`
- `stage3/linux_init/v102/*.inc.c`
- `stage3/linux_init/a90_diag.c/h`
- `scripts/revalidation/diag_collect.py`
- 의도:
  - read-only `diag [summary|full|bundle|paths]` command 추가
  - version/bootstatus/selftest/storage/runtime/helpers/userland/service/network/rshell/log tail을 한 번에 수집
  - host-side serial-first collector로 회귀 증거를 텍스트 파일로 저장
  - Wi-Fi inventory와 NCM optional checks는 v103+로 분리
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v102.cpio`, `stage3/boot_linux_v102.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.9.2 (v102)`, `A90v102`, `0.9.2 v102 DIAGNOSTICS`, `diag [summary|full|bundle|paths]` — PASS
  - native flash → post-boot `cmdv1 version/status` — PASS
  - `diag`, `diag full`, `diag paths`, `diag bundle` — PASS
  - `diag_collect.py --out tmp/diag/v102-smoke.txt` — PASS
  - `diag_collect.py --device-bundle --boot-image stage3/boot_linux_v102.img --out tmp/diag/v102-bundle.txt` — PASS
  - `service list`, `storage`, `runtime`, `statushud`, `autohud 2`, `screenmenu`, `hide`, `cpustress 3 2` — PASS
- 산출:
  - `stage3/linux_init/init_v102`
    - SHA256 `49499e5da3c84ef50996655605e06d1f33cd514862aeb361a97411e9b9db154a`
  - `stage3/ramdisk_v102.cpio`
    - SHA256 `375110ae184997fcf5334704ed1a8f738a3088e7e150467e9fc995f01ff86780`
  - `stage3/boot_linux_v102.img`
    - SHA256 `aca7aef3077334eb4b7e0f61fdfa27943b8ca23736271b10dd414f8029d1c49d`
  - `docs/reports/NATIVE_INIT_V102_DIAGNOSTICS_2026-05-03.md`

## 지금 바로 진행할 항목

1. v113 runtime package layout

   - 기준 문서: `docs/plans/NATIVE_INIT_V109_V116_ROADMAP_2026-05-04.md`
   - 최신 결과: `docs/reports/NATIVE_INIT_V112_USB_SERVICE_SOAK_2026-05-04.md`
   - v109 결과: `docs/reports/NATIVE_INIT_V109_STRUCTURE_AUDIT_2026-05-04.md`
   - v110 결과: `docs/reports/NATIVE_INIT_V110_APP_CONTROLLER_CLEANUP_2026-05-04.md`
   - v111 결과: `docs/reports/NATIVE_INIT_V111_EXTENDED_SOAK_RC_2026-05-04.md`
   - v112 결과: `docs/reports/NATIVE_INIT_V112_USB_SERVICE_SOAK_2026-05-04.md`
   - 다음 실행 항목: v113 runtime package layout
   - 목적: SD runtime root, package/helper/runtime directory contract를 destructive migration 없이 명확히 정리
   - 보류: risky Wi-Fi bring-up, partition writes, automatic remote downloads

### V106-V108. UI/App Architecture Split — DONE

- v106 계획: `docs/plans/NATIVE_INIT_V106_UI_APP_ABOUT_PLAN_2026-05-04.md`
  - 결과: `docs/reports/NATIVE_INIT_V106_UI_APP_ABOUT_2026-05-04.md`
  - 목표: ABOUT/version/changelog 화면 렌더링을 `a90_app_about.c/h`로 분리
  - 기준: `A90 Linux init 0.9.6 (v106)` / `0.9.6 v106 APP ABOUT API`
  - 성격: 구조 개선, 메뉴 UX 변경 없음
- v107 계획: `docs/plans/NATIVE_INIT_V107_UI_APP_DISPLAYTEST_PLAN_2026-05-04.md`
  - 결과: `docs/reports/NATIVE_INIT_V107_UI_APP_DISPLAYTEST_2026-05-04.md`
  - 목표: `displaytest`와 `cutoutcal` 렌더링을 `a90_app_displaytest.c/h`로 분리
  - 기준: `A90 Linux init 0.9.7 (v107)` / `0.9.7 v107 APP DISPLAYTEST API`
  - 성격: display/cutout 화면 동작 보존
- v108 계획: `docs/plans/NATIVE_INIT_V108_UI_APP_INPUTMON_PLAN_2026-05-04.md`
  - 결과: `docs/reports/NATIVE_INIT_V108_UI_APP_INPUTMON_2026-05-04.md`
  - 목표: input layout/monitor/wait UI를 `a90_app_inputmon.c/h`로 분리
  - 기준: `A90 Linux init 0.9.8 (v108)` / `0.9.8 v108 APP INPUTMON API`
  - 성격: 저수준 `a90_input.c/h` 유지, app UI만 분리
- 공통 검증:
  - static ARM64 build, marker strings, `git diff --check`, host Python `py_compile`
  - real-device flash 후 `version`, `status`, `bootstatus`, `selftest verbose`, `screenmenu`, `hide`
  - 각 app별 화면/입력 회귀와 3-cycle quick soak

### V105. Long-Run Soak / Recovery RC — PASS

- 계획: `docs/plans/NATIVE_INIT_V105_SOAK_RC_PLAN_2026-05-04.md`
- 산출: `docs/reports/NATIVE_INIT_V105_SOAK_RC_2026-05-04.md`
- `stage3/linux_init/init_v105.c`
- `stage3/linux_init/v105/*.inc.c`
- `scripts/revalidation/native_soak_validate.py`
- 의도:
  - v96-v104 stack을 recovery-friendly 안정 기준 후보로 검증
  - bounded host quick soak로 serial/service/runtime/diagnostics/UI command 반복 검증
  - Wi-Fi bring-up, rfkill write, module load/unload, firmware/vendor mutation 금지
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v105.cpio`, `stage3/boot_linux_v105.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.9.5 (v105)`, `A90v105`, `0.9.5 v105 SOAK RC` — PASS
  - native flash → post-boot `cmdv1 version/status` — PASS
  - required command regression set — PASS
  - `native_soak_validate.py --cycles 10 --sleep 2` 14-command cycle — PASS
  - final `status` and `service list` after soak — PASS
- 산출:
  - `stage3/linux_init/init_v105`
    - SHA256 `624242bafb44598feaddf636a60b64a996d44f5e05dc622f64b79518706a8209`
  - `stage3/ramdisk_v105.cpio`
    - SHA256 `6733a511a5cc8a5a79c09333510c0d1913219ed13e15b3a2cbd1e7550be27726`
  - `stage3/boot_linux_v105.img`
    - SHA256 `2dcda57156385c2d092a0865ea31bd7853399287df5633d39b08ae4b01d53338`
  - `docs/reports/NATIVE_INIT_V105_SOAK_RC_2026-05-04.md`

### V104. Wi-Fi Feasibility Gate — PASS

- 계획: `docs/plans/NATIVE_INIT_V104_WIFI_FEASIBILITY_PLAN_2026-05-04.md`
- 산출: `docs/reports/NATIVE_INIT_V104_WIFI_FEASIBILITY_2026-05-04.md`
- `stage3/linux_init/init_v104.c`
- `stage3/linux_init/v104/*.inc.c`
- `stage3/linux_init/a90_wififeas.c/h`
- 의도:
  - v103 read-only inventory를 기반으로 Wi-Fi bring-up 가능 여부를 deterministic gate로 판정
  - native default, mounted-system read-only 상태를 분리해 `baseline-required`/`no-go`/`go-read-only-only` 결정
  - Wi-Fi enablement, rfkill write, module load/unload, firmware/vendor mutation 금지
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v104.cpio`, `stage3/boot_linux_v104.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.9.4 (v104)`, `A90v104`, `0.9.4 v104 WIFI FEASIBILITY`, `wififeas [summary|full|gate|paths]` — PASS
  - native flash → post-boot `cmdv1 version/status` — PASS
  - `wififeas`, `wififeas gate`, `wififeas full`, `wififeas paths` — PASS
  - default native decision: `baseline-required` — PASS
  - `mountsystem ro` extended decision: `no-go` because Android-side candidates exist but WLAN/rfkill/module gates are missing — PASS
  - `diag`, `storage`, `runtime`, `service list`, `netservice status`, `statushud`, `autohud 2`, `screenmenu`, `hide`, `cpustress 3 2` — PASS
- 산출:
  - `stage3/linux_init/init_v104`
    - SHA256 `ac3220826e78782a7c4fa523b62d893bd3764d6df48b8d68e32065fe111cb802`
  - `stage3/ramdisk_v104.cpio`
    - SHA256 `0816ff76577702d28238e86ee32bdc9388646a5c5ca7ae685a544b937947029c`
  - `stage3/boot_linux_v104.img`
    - SHA256 `c1fe4f5fe6d569e8ff19ee73d2e6c3742948c605fa36c41c6beef9d1c86fe8eb`
  - `docs/reports/NATIVE_INIT_V104_WIFI_FEASIBILITY_2026-05-04.md`

### V103. Wi-Fi Read-Only Inventory — PASS

- 계획: `docs/plans/NATIVE_INIT_V103_WIFI_INVENTORY_PLAN_2026-05-04.md`
- 산출: `docs/reports/NATIVE_INIT_V103_WIFI_INVENTORY_2026-05-04.md`
- `stage3/linux_init/init_v103.c`
- `stage3/linux_init/v103/*.inc.c`
- `stage3/linux_init/a90_wifiinv.c/h`
- `scripts/revalidation/wifi_inventory_collect.py`
- 의도:
  - native init에서 보이는 WLAN, rfkill, firmware, module, vendor path를 read-only로 수집
  - Wi-Fi bring-up 전에 Android/TWRP/native init visibility 차이를 확인할 evidence format 준비
  - Wi-Fi enablement, rfkill write, module load/unload, firmware/vendor mutation 금지
- 검증:
  - static ARM64 init build with `-Wall -Wextra` — PASS
  - `stage3/ramdisk_v103.cpio`, `stage3/boot_linux_v103.img` 생성 — PASS
  - boot image marker strings `A90 Linux init 0.9.3 (v103)`, `A90v103`, `0.9.3 v103 WIFI INVENTORY`, `wifiinv [summary|full|paths]` — PASS
  - native flash → post-boot `cmdv1 version/status` — PASS
  - `wifiinv`, `wifiinv paths`, `wifiinv full` — PASS
  - default native inventory: no `wlan*`, no Wi-Fi rfkill, no WLAN/CNSS/QCA module match — PASS
  - `mountsystem ro` extended inventory: `/mnt/system/system/etc/init/wifi.rc`, `wificond.rc`, carrier Wi-Fi config candidates detected — PASS
  - `wifi_inventory_collect.py --native-only --boot-image stage3/boot_linux_v103.img` — PASS
  - `diag`, `storage`, `runtime`, `service list`, `netservice status`, `statushud`, `autohud 2`, `screenmenu`, `hide`, `cpustress 3 2` — PASS
- 산출:
  - `stage3/linux_init/init_v103`
    - SHA256 `9d1bac55549abb0e7aac2112896f66c362cc38dd1093212d4beb4bcb65c33a85`
  - `stage3/ramdisk_v103.cpio`
    - SHA256 `0758b63988b2edfb27cf2bc05da484dac099391bfc488f8a6c13aa976b7c61c4`
  - `stage3/boot_linux_v103.img`
    - SHA256 `dca3ee7ac77f366176d833b40450b0b1e3e55ebaf46ddc11c4d3a5f19454622b`
  - `docs/reports/NATIVE_INIT_V103_WIFI_INVENTORY_2026-05-04.md`

### V109. Post-v108 Structure Audit — DONE

- result: `docs/reports/NATIVE_INIT_V109_STRUCTURE_AUDIT_2026-05-04.md`
- build: `A90 Linux init 0.9.9 (v109)`
- artifacts: `stage3/linux_init/init_v109`, `stage3/ramdisk_v109.cpio`, `stage3/boot_linux_v109.img`
- validation: real-device flash PASS, cmdv1 version/status PASS, 3-cycle quick soak PASS
- next execution item: v113 runtime package layout

### V110. App Controller Cleanup — DONE

- result: `docs/reports/NATIVE_INIT_V110_APP_CONTROLLER_CLEANUP_2026-05-04.md`
- build: `A90 Linux init 0.9.10 (v110)`
- artifacts: `stage3/linux_init/init_v110`, `stage3/ramdisk_v110.cpio`, `stage3/boot_linux_v110.img`
- validation: real-device flash PASS, controller busy gate PASS, 3-cycle quick soak PASS
- next execution item: v113 runtime package layout

### V111. Extended Soak RC — DONE

- result: `docs/reports/NATIVE_INIT_V111_EXTENDED_SOAK_RC_2026-05-04.md`
- build: `A90 Linux init 0.9.11 (v111)`
- artifacts: `stage3/linux_init/init_v111`, `stage3/ramdisk_v111.cpio`, `stage3/boot_linux_v111.img`
- validation: real-device flash PASS, 10-cycle extended soak PASS, final service/selftest PASS
- next execution item: v113 runtime package layout

### V112. USB/NCM Service Soak — DONE

- result: `docs/reports/NATIVE_INIT_V112_USB_SERVICE_SOAK_2026-05-04.md`
- build: `A90 Linux init 0.9.12 (v112)`
- artifacts: `stage3/linux_init/init_v112`, `stage3/ramdisk_v112.cpio`, `stage3/boot_linux_v112.img`
- validation: real-device flash PASS, NCM ping PASS, `tcpctl_host.py ping/status/run` PASS, ACM rollback PASS, 3-cycle quick soak PASS
- next execution item: v113 runtime package layout

### V109-V116. Post-v108 Stability and Runtime Cycle — IN PROGRESS

- roadmap: `docs/plans/NATIVE_INIT_V109_V116_ROADMAP_2026-05-04.md`
- baseline: `A90 Linux init 0.9.8 (v108)`
- first execution item: v109 post-v108 structure audit — DONE
- next execution item: v113 runtime package layout
- guardrails: no risky Wi-Fi bring-up, no partition writes, USB ACM serial remains rescue channel
