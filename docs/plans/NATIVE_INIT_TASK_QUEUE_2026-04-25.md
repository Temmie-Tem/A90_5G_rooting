# Native Init Task Queue (2026-04-25)

이 문서는 `A90 Linux init v53` 이후 바로 실행할 작업 큐다.
큰 방향은 “보이는 부팅 → 복구 가능한 로그 → 단독 조작 → 작은 userland → USB networking” 순서다.

## 현재 고정 기준점

- latest verified native init: `A90 Linux init v53`
- latest source: `stage3/linux_init/init_v53.c`
- latest boot image: `stage3/boot_linux_v53.img`
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

## 보류 큐

- ADB 안정화 재검토
- dropbear SSH
- Buildroot/rootfs 묶음
- Android framework 복구 시도

## 지금 바로 진행할 항목

1. `a90_tcpctl` launch/client/stop host wrapper 작성
2. 5~10분 NCM + tcpctl 유지와 reconnect 안정성 확인
3. unsolicited `AT` serial noise 필터링 또는 무시 정책 구현
4. boot-time NCM/tcpctl service 정책 결정
5. Wi-Fi 드라이버/펌웨어 read-only 인벤토리 트랙 분리
