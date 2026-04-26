# Native Init Task Queue (2026-04-25)

이 문서는 `A90 Linux init 0.8.4 (v73)` 이후 바로 실행할 작업 큐다.
큰 방향은 “보이는 부팅 → 복구 가능한 로그 → 단독 조작 → 작은 userland → USB networking” 순서다.

## 현재 고정 기준점

- latest verified native init: `A90 Linux init 0.8.4 (v73)`
- official version: `0.8.4`
- build tag: `v73`
- creator: `made by temmie0214`
- latest source: `stage3/linux_init/init_v73.c`
- latest boot image: `stage3/boot_linux_v73.img`
- known-good fallback: `stage3/boot_linux_v48.img`
- control channel: USB ACM serial bridge
- log: `/cache/native-init.log`
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

## 보류 큐

- ADB 안정화 재검토
- dropbear SSH
- Buildroot/rootfs 묶음
- Android framework 복구 시도

## 지금 바로 진행할 항목

1. `cmdv1` argument quoting/escaping 규칙 설계
2. NCM/reconnect/tcpctl host scripts에도 parsed rc 적용 범위 결정
3. display test를 다중 페이지형 app으로 확장할지 판단
4. 실제 케이블 unplug/replug 이후 ACM/NCM/tcpctl 복구 확인
5. USB 재열거 중 `A`/`ATAT...` serial noise hardening
6. Wi-Fi 드라이버/펌웨어 read-only 인벤토리 트랙 분리
