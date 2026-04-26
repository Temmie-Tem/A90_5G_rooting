# Native Linux Rechallenge Progress Log

## 2026-04-23

### Stage 0 기준점 캡처 완료
- `scripts/revalidation/verify_device_state.sh` 통과 — 기준점 A 신호 전부 정상
- `scripts/revalidation/capture_baseline.sh --label baseline_a` 완료
  - 저장 경로: `backups/baseline_a_20260423_030309/`
  - boot.img (64MB), recovery.img (82MB), vbmeta.img (64KB) + SHA256SUMS
- 캡처 스크립트 버그 수정: Magisk `su -c` 인용 문제 → `sq_escape` 헬퍼로 단일 따옴표 래핑
- 다운로드 모드 값 사진으로 캡처 후 매트릭스 기준점 섹션 채움

### Stage 1 row 2, 4 완료
- row 2 (patched AP + stock recovery): 현재 기준점 A 상태 그대로 기록 (플래시 없음)
- row 4 (patched AP + TWRP): `adb shell su -c dd`로 recovery 파티션에 TWRP 직접 기록
  - sha256 검증 후 재부팅 → 정상 시스템 부팅, recovery fallback 없음
  - Magisk root / ADB / Wi-Fi 전부 유지
  - `verifiedbootstate=orange` 유지 (vbmeta Magisk 패치가 TWRP 서명 불일치 흡수)
- row 1, 3 (stock AP 포함 조합): stock AP 롤백이 필요한 시점에 자연 관찰 예정으로 deferred

### 기준점 재설정
- 기존 2025 방향 문서를 `docs/archive/legacy/`로 이동
- 상단 문서 트리를 현재 rooted baseline 중심으로 재구성

### native Linux rechallenge 재개
- 공식 목표를 `부트체인 재검증 자체`에서 `native Linux 부팅 재도전`으로 다시 고정
- rooted baseline A를 모든 후속 실험의 유일한 출발점으로 설정
- debloat와 최소 패키지화는 메인 목표에서 분리하고 참고용 보조 실험으로 유지

### 실행 문서 정비
- `docs/plans/NATIVE_LINUX_RECHALLENGE_PLAN.md` 추가
- `docs/plans/REVALIDATION_PLAN.md`를 단계형 실행 체크리스트로 재작성
- `docs/reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md` 작업 시트 추가
- `scripts/revalidation/`에 기준점 점검과 캡처용 헬퍼 추가

### 현재 rooted baseline
- patched AP 부팅 성공
- `Magisk 30.7` 확인
- `su` 동작 확인
- ADB 정상
- Wi-Fi 등록 및 연결 확인

### 다운로드 모드 스냅샷
- `RPMB Fuse Set`
- `RPMB PROVISIONED`
- `CURRENT BINARY : Custom (0x303)`
- `FRP LOCK : OFF`
- `OEM LOCK : OFF (U)`
- `WARRANTY VOID : 0x1 (0xE03)`
- `QUALCOMM SECUREBOOT : ENABLE`
- `RP SWREV : B5(1,1,1,5,1,1) K5 S5`
- `SECURE DOWNLOAD : ENABLE`
- `DID : 2030A54C447F3A11`
- `KG` 줄은 이번 사진 크롭에 보이지 않아 미확인 상태로 유지

### KG 미표시 관련 공식 문서 재확인
- Samsung Knox 공식 문서 기준으로 `KG STATE`가 다운로드 모드에 항상 표시된다는 규칙은 찾지 못함
- 공식 문서에서 Knox Guard는 cloud-managed device state로 설명되며,
  장치는 콘솔 등록, 활성화, 완료, 삭제에 따라 관리 상태가 변함
- 공식 문서상 `Completed` 또는 삭제 이후에는 Knox Guard client가
  비활성화되거나 영구 제거되고 더 이상 추적되지 않음
- 따라서 `KG 줄 자체가 안 뜨는 현상`은 공식 문서와 모순되지 않음
- 다만 공식 문서만으로 `KG 미표시 = 특정 KG 상태`라고 단정할 근거는 없음

참고 링크:

- https://docs.samsungknox.com/admin/knox-guard/
- https://docs.samsungknox.com/dev/knox-guard/how-knox-guard-works/
- https://docs.samsungknox.com/admin/knox-guard/kbas/what-happens-to-device-once-it-is-fully-paid/
- https://docs.samsungknox.com/admin/knox-guard/how-to-guides/manage-devices/view-device-details/

### 최소 부팅 상태
- allowlist 재적용 후 `user 0` 패키지 수 `92`
- 남은 extra `3개`
  - `com.samsung.android.game.gos`
  - `com.samsung.android.themecenter`
  - `com.sec.android.sdhms`

### 비고
- `com.google.android.documentsui`는 `user 0` 제거 후 재부팅 유지 확인
- `com.google.android.partnersetup`는 제거 시도 후 재부팅 시 복귀
- `GOS`, `SDHMS`는 `pm uninstall --user 0` / `su -c` 모두 실질 제거 실패
- `ThemeCenter`는 `DELETE_FAILED_INTERNAL_ERROR`

### Stage 3 후속 점검
- TWRP에서 `/cache/v2c_step = 9_udc_set` 확인
  - `v2c`는 최소한 configfs/functionfs 설정과 UDC 활성화까지 도달
- `/cache/adbd_exec_failed = 013` 파일은 남아 있었으나, TWRP에서
  `LD_LIBRARY_PATH=/cache/adb/lib /cache/adb/adbd --help` 재현 시
  `Permission denied`가 아니라 `Segmentation fault (rc=139)` 확인
- 커널 설정 재확인:
  - `CONFIG_USB_CONFIGFS_ACM=y`
  - `CONFIG_USB_F_ACM=y`
  - `CONFIG_USB_CONFIGFS_RNDIS=y`
- 따라서 다음 후보를 `Android adbd`에서 `USB ACM serial mini-shell`로 전환
  - 새 산출물:
    - `stage3/linux_init/init_v3.c`
    - `stage3/ramdisk_v3.cpio`
    - `stage3/boot_linux_v3.img`
- `boot_linux_v3.img`를 boot 파티션에 기록 후 `twrp reboot system` 실행
  - host `lsusb`: `04e8:6861 Samsung Electronics Co., Ltd SAMSUNG_Android`
  - host `adb devices -l`: 빈 목록
  - host `/dev/ttyACM0` 생성 확인
- 결론:
  - `native init -> USB ACM gadget` 경로는 실증
  - 마지막 남은 확인은 host serial open 후 mini-shell 배너/명령 응답 검증
  - 현재 Codex 세션 계정은 `dialout` 그룹이 아니어서 `/dev/ttyACM0` 직접 열 수 없음

### Native shell probe 정리
- `serial -> TCP` 브릿지로 `v8` shell에 직접 접속해 `/proc`, `/dev`, `/sys/class` probe 수행
- 확인된 것:
  - `SM8150` 기반 kernel/userspace shell 정상
  - `/cache`와 `/mnt/system` 마운트 정상
  - `backlight`, `input`, `drm`, `power_supply`, `udc` 클래스가 이미 커널에 노출됨
  - 현재 brightness `255 / 365`
  - `event0`~`event8` 존재
  - `/sys/class/drm`에 `card0`, `card0-DSI-1`, `renderD128`, `sde-crtc-*` 존재
- `adbd` 추적 결과:
  - `startadbd`는 실행되지만 `adbd`는 zombie
  - `/dev/usb-ffs/adb`에는 `ep0`만 있고 `ep1/ep2` 미생성
  - host `lsusb -v`도 ACM 2-interface만 표시
- 외부 문서 대조 결과:
  - FunctionFS는 descriptors/strings가 `ep0`에 써져야 `ep#` 파일 생성
  - AOSP init도 `start adbd -> sys.usb.ffs.ready -> ffs.adb symlink -> UDC bind` 순서를 사용
- 현재 권장 방향:
  - Android dynamic binary / ADB 추적은 잠시 보류
  - 다음 probe는 `input + backlight + drm`
  - 장기 통신층 후보는 `USB networking + SSH`
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_SHELL_PROBE_2026-04-23.md`

### Input / backlight / DRM probe 추가
- `input0`~`input8` 이름 확인:
  - `qpnp_pon`, `meta_event`, `grip_sensor`, `gpio_keys`, `hall`,
    `certify_hall`, `sec_touchscreen`, `sec_touchproximity`, `sec_touchpad`
- 의미:
  - 입력 장치 enumeration은 충분히 진행돼 있고,
    `gpio_keys`와 touchscreen 계열이 모두 보이므로 버튼/터치 추적 가능성 높음
- 버튼 매핑 실측:
  - `event0 (qpnp_pon)` → `KEY_POWER` + `KEY_VOLUMEDOWN`
    - raw key bitmap: `14000000000000 0`
  - `event3 (gpio_keys)` → `KEY_VOLUMEUP`
    - raw key bitmap: `8000000000000 0`
- `v13`에서 `inputcaps` bitmap word ordering 수정 후 자동 해석도 일치 확인:
  - `inputcaps event0` → `KEY_VOLUMEDOWN=yes`, `KEY_POWER=yes`
  - `inputcaps event3` → `KEY_VOLUMEUP=yes`
- backlight:
  - `panel0-backlight`
  - 현재 `255 / 365`
- DRM:
  - `card0-DSI-1`에 `enabled`, `status`, `modes`, `dpms`, `edid` 노출
  - `card0` 아래에 `sde-crtc-*`, `card0-DSI-1`, `card0-DP-1` 존재
- 현재 blocker:
  - `v9`에서 `writefile` 명령 추가 후 backlight sysfs write 성공
    - `255 -> 32 -> 255` round-trip 확인
  - 즉, 최소 sysfs 조작 primitive는 확보
  - 다음 blocker는 실제 화면 반응 확인과
    `input/drm` 추가 식별

### Native init v40/v41 운영 안정화
- `v40`에서 shell command result를 정밀화:
  - 성공 명령은 `[done]`
  - syscall/usage/open/mount 실패는 `[err] rc=<code> errno=<errno>`
  - `last` 명령으로 마지막 command/result/duration 확인
- `v41`에서 `/cache/native-init.log` 파일 로그 추가:
  - boot step, display probe, serial attach, autohud start 기록
  - command start/end, result code, errno, duration 기록
  - `logpath`, `logcat` 명령 추가
- `v41` 검증 중 block major/minor 변동 문제 확인:
  - 기존 hardcoded `sda31 = 259:15`는 부팅 순서에 따라 틀릴 수 있음
  - 실제 검증 부팅에서 `sda31 = 259:34`로 나타나 `/cache` mount가 fallback 됨
  - `sda28`, `sda31` 노드를 `/sys/class/block/<name>/dev` 기반으로 동적 생성하도록 수정
- 최종 v41 실기 확인:
  - `logpath` → `/cache/native-init.log`
  - `/dev/block/sda31 /cache ext4 rw`
  - `cat /definitely-missing` 실패가 log에 `rc=-2 errno=2`로 기록
  - `mountsystem ro` 성공
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V41_LOGGING_2026-04-25.md`

### Native init v42 blocking cancel
- `v42`에서 blocking command 취소 정책 추가:
  - `q`/`Q`는 soft cancel
  - `Ctrl-C`는 hard cancel
  - shell result는 `-ECANCELED` (`errno=125`)로 기록
- 실기 검증 완료:
  - `waitkey 10` + `q`
  - `readinput event0 100` + `q`
  - `watchhud 1 10` + `q`
  - `blindmenu` + `q`
  - `waitkey 10` + `Ctrl-C`
- 확인된 후속 상태:
  - 취소 후 `last`, `status` 정상
  - `autohud 2`로 HUD 복구 성공
  - `/cache/native-init.log`에 `cancel: ... soft q`, `cancel: ... hard Ctrl-C` 기록
- `run`/`runandroid`에는 cancelable child wait를 넣었지만,
  안전한 long-running static test binary가 없어 실기 cancel은 다음 작업으로 남김
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V42_CANCEL_2026-04-25.md`

### Native init v43 boot timeline
- `v43`에서 boot readiness timeline 추가:
  - `init-start`
  - `base-mounts`
  - `early-nodes`
  - `resource-drm`
  - `resource-input0`
  - `resource-input3`
  - `resource-battery`
  - `resource-thermal`
  - `cache-mount`
  - `usb-gadget`
  - `ttyGS0`
  - `display-probe`
  - `console`
  - `autohud`
  - `shell`
- `/cache` mount 전 timeline은 cache log 선택 후 replay하도록 구현
- 실기 확인:
  - `timeline` → 15개 step 표시
  - `logcat` → `timeline: replay=cache ...` 기록 확인
  - `status` → `A90 Linux init v43`, autohud running 확인
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V43_TIMELINE_2026-04-25.md`

### Native init v44 HUD boot summary
- `v44`에서 timeline 기반 boot summary를 HUD/status에 연결:
  - 정상 부팅: `BOOT OK <last-step> <sec>S`
  - 실패 기록 존재 시: `BOOT ERR <step> E<errno>`
- `bootstatus` 명령 추가
- HUD 첫 줄과 footer에 boot summary 표시
- 실기 확인:
  - `bootstatus` → `BOOT OK shell 3S`
  - `status` → boot summary 출력
  - `statushud` → framebuffer draw 성공
  - `autohud 2` → 자동 HUD 복구 성공
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V44_HUD_BOOT_2026-04-25.md`

### Native init v45 run cancel + log preservation
- `v45`에서 ramdisk helper `/bin/a90sleep` 추가
- `run /bin/a90sleep 30` 실행 후 `q` cancel 실기 확인:
  - child `SIGTERM`
  - prompt 복귀
  - `last`에 `errno=125`
  - `/cache/native-init.log`에 `cancel: run soft q`
- native init → TWRP recovery → native init 왕복 후 `/cache/native-init.log` 보존 확인:
  - v44 boot log와 v45 boot log가 같은 파일에 append됨
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V45_RUN_LOG_2026-04-25.md`

### Native init v46 storage / partition map
- `v45` 실기 관찰값과 baseline by-name listing을 묶어 저장소 안전 등급을 정리
- 확인된 현재 persistent write 영역:
  - `/cache` → `cache -> /dev/block/sda31`, ext4 rw, native init log 저장소로 검증 완료
- 대용량 후보:
  - `userdata -> /dev/block/sda33`, 약 110 GiB
  - Android FBE/user data와 엮여 있어 백업/포맷 의사결정 전까지 보류
  - `mmcblk0p1`, 약 59.6 GiB, by-name mapping 없음, 정체 확인 전까지 보류
- do-not-touch 영역:
  - `efs`, `sec_efs`, modem/modemst/fsg 계열
  - `persist`, `param`, `misc`
  - `keydata`, `keyrefuge`, `keymaster`, `keystore`, `storsec`, `secdata`
  - `xbl`, `abl`, `tz`, `hyp`, `cmnlib`, `vbmeta` 등 boot/security 계열
- 설계 규칙:
  - 파티션은 by-name과 `/sys/class/block/<name>/dev` 기준으로 식별
  - major/minor는 v41 cache mount 실패 사례 때문에 hardcode 금지
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_STORAGE_MAP_2026-04-25.md`

### Native init v47 screen menu
- `v47`에서 KMS 기반 화면 메뉴 초안 추가:
  - `menu`
  - `screenmenu`
  - 기존 `blindmenu`는 serial-only fallback으로 유지
- 메뉴 항목:
  - `RESUME`
  - `STATUS`
  - `LOG`
  - `RECOVERY`
  - `REBOOT`
  - `POWEROFF`
- 조작 정책:
  - VOLUP: 이전 항목
  - VOLDOWN: 다음 항목
  - POWER: 선택
  - serial `q`/Ctrl-C: cancel
- 실기 검증 완료:
  - `stage3/boot_linux_v47.img` 플래시
  - `version` → `A90 Linux init v47`
  - `menu` 진입 → `screenmenu` framebuffer present
  - serial `q` cancel → `errno=125`
  - cancel 후 `status`에서 `autohud: running` 확인
- 남은 수동 검증:
  - 실제 버튼으로 메뉴 이동/선택
  - `STATUS`/`LOG` 화면 진입 후 복귀
  - `RECOVERY`, `REBOOT`, `POWEROFF` 위험 동작은 필요 시 별도 확인
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V47_SCREEN_MENU_2026-04-25.md`

### Native init USB gadget map
- `init_v47` 기준 USB gadget 구성을 문서화:
  - configfs gadget: `g1`
  - function: `acm.usb0`
  - config symlink: `configs/b.1/f1 -> functions/acm.usb0`
  - UDC: `a600000.dwc3`
  - VID/PID: `04e8:6861`
- host 관찰:
  - `/dev/ttyACM0`
  - driver `cdc_acm`
  - negotiated speed SuperSpeed 5Gbps
  - CDC ACM control/data 2-interface만 노출
- ADB 판단:
  - `startadbd`는 `ffs.adb`와 FunctionFS mount 경로를 갖고 있음
  - 과거 실측 기준 `ep0 only`, `ep1/ep2 missing`, `adbd zombie`가 blocker
  - Android property/SELinux/bionic/apex runtime 없이 adbd 단독 안정화는 후순위
- USB networking 판단:
  - 다음 확장 후보는 `rndis.usb0`, `ncm.usb0`, `ecm.usb0`
  - ACM serial은 rescue/control channel로 유지한 채 두 번째 function으로 probe해야 함
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_USB_GADGET_MAP_2026-04-25.md`

### Native init V49 static userland 후보
- `v47` 기준 다음 큐를 작은 Linux userland 쪽으로 승격:
  - BusyBox/static ARM64
  - toybox/static ARM64
  - 장기 후보로 Buildroot/rootfs
- 현재 실행 기반:
  - `run <path> [args...]`는 static helper 실행, exit status, q/Ctrl-C cancel 지원
  - `PATH=/cache:/cache/bin:/bin:/system/bin`
  - `/cache`는 safe persistent write 영역
- 로컬 빌드 환경 확인:
  - `aarch64-linux-gnu-gcc`, `strip`, `readelf` 있음
  - 초기에는 host `make`, host `gcc`, `musl-gcc` 없음
  - 간단한 AArch64 static hello binary 빌드는 성공
- 빌드 prerequisite 설치 후 재확인:
  - `build-essential`, `make`, `gcc` 설치 확인
  - `binutils-aarch64-linux-gnu`, `libc6-dev-arm64-cross` 설치 확인
- `scripts/revalidation/build_static_toybox.sh` 추가:
  - 공식 `toybox-0.8.13.tar.gz` 다운로드
  - source SHA256 고정
  - `CC=aarch64-linux-gnu-gcc`, `LDFLAGS=--static` 빌드
  - `LOGIN`, `MKPASSWD`, `PASSWD`, `SU`, `SULOGIN`, `GETTY` 비활성화
  - `IP`, `ROUTE`, `HEXDUMP` 추가 활성화
- host 빌드 산출물:
  - `external_tools/userland/bin/toybox-aarch64-static-0.8.13`
  - SHA256 `92a0917579c76fec965578ac242afbf7dedc4428297fb90f4c9caf7f538a718c`
  - static ELF 확인: `INTERP` segment 없음, dynamic section 없음
- 실기 배치:
  - TWRP ADB로 `/cache/bin/toybox` push
  - mode `0755`, size `1567176`
  - remote SHA256 일치 확인
- native init 실행 확인:
  - `run /cache/bin/toybox --help` — PASS
  - `run /cache/bin/toybox uname -a` — PASS
  - `run /cache/bin/toybox ls /proc` — PASS
  - `run /cache/bin/toybox ps -A` / `ps -ef` — PASS
  - `run /cache/bin/toybox dmesg -s 1024` — PASS
  - `run /cache/bin/toybox hexdump -C /proc/version` — PASS
  - `run /cache/bin/toybox ifconfig -a` — PASS
  - `run /cache/bin/toybox route -n` — PASS
  - `run /cache/bin/toybox netcat --help` — PASS
- 주의:
  - `ps` 단독은 `rc=1`; `ps -A`/`ps -ef` 사용
  - `netcat -h`는 `rc=1`; `netcat --help` 사용
  - `ip addr`/`ip link`는 일부 interface 출력 후 `rc=1`; USB network 추가 후 재검증
- 판단:
  - boot ramdisk 포함 전 `/cache/bin/toybox` explicit 실행으로 먼저 검증
  - BusyBox는 GPLv2 배포 의무 고려
  - toybox는 Android 계열과 라이선스 측면에서 비교 후보
  - USB networking probe 전에 `ip`/`ifconfig`/`route`/`nc` 계열 applet 확보 여부 확인
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_USERLAND_CANDIDATES_2026-04-25.md`

### Native init V48 USB reattach + NCM probe
- `init_v47`에서 외부 USB gadget rebind 후 host `/dev/ttyACM0`는 돌아오지만
  device-side native init이 기존 `/dev/ttyGS0` fd에 묶여 serial 응답이 끊기는 문제 확인
- `init_v48` 구현:
  - `read_line()`을 `poll()` 기반으로 변경
  - `POLLHUP`/`POLLERR`/`POLLNVAL`, read error/eof, idle timeout 때 console reattach 시도
  - `reattach`, `usbacmreset` 명령 추가
  - `startadbd`/`stopadbd` rebind 뒤 console reattach 호출
- `serial_tcp_bridge.py` 개선:
  - serial device identity `(st_dev, st_ino, st_rdev)` 추적
  - USB 재열거로 `/dev/ttyACM0`가 새 노드가 되면 fd를 닫고 재연결
- `a90_usbnet` helper 추가:
  - `status|ncm|rndis|probe-ncm|probe-rndis|off`
  - `probe-*`는 child process로 분리하고 15초 뒤 ACM-only rollback
  - `/cache/usbnet.log` 기록
- 빌드 산출:
  - `stage3/linux_init/init_v48`
  - `stage3/ramdisk_v48.cpio`
  - `stage3/boot_linux_v48.img`
  - boot image SHA256 `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
- 실기 플래시:
  - `stage3/boot_linux_v48.img` push
  - remote SHA256 일치
  - `version` → `A90 Linux init v48`
- ACM rebind 검증:
  - `usbacmreset` → `# serial console reattached: usbacmreset`
  - `run /cache/bin/a90_usbnet off` 후 약 3초 내 `version` 복구
- NCM probe:
  - host에서 phone `04e8:6861`에 `cdc_acm` + `cdc_ncm` composite interface 확인
  - host `enx26eaa7b343d7` / `enx425f6b65a0cb` 형태 NCM interface 생성 확인
  - device toybox `ifconfig -a`에서 `ncm0` 확인
  - rollback 후 ACM-only와 `version` 복구 확인
- 다음 작업:
  - persistent NCM mode 정리
  - device `ncm0`와 host `enx...`에 IPv4 설정
  - `ping`/toybox `netcat`으로 실제 패킷 통신 검증
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V48_USB_REATTACH_NCM_2026-04-25.md`

## v49: 상태 HUD TUI 개선 (2026-04-25)

- `kms_draw_status_overlay` 전면 개선:
  - **bug fix**: PWR 라인(line5) card 배경 누락 → 추가
  - **bug fix**: `W?` 접미사 제거 (폰트에 `?` 없음, debug artifact)
  - **layout**: 5개 card를 화면 전체 높이에 동적 spread (card_gap dynamic 계산)
  - **color**: BOOT OK = green(`0x88ee88`), BOOT ERR = red(`0xff6666`)
  - **color**: BAT % 기반 색상 — >50% green, 20-50% amber, ≤20% red
  - **label**: 라벨(`A90 INIT`/`BAT`/`CPU`/`MEM`/`PWR`) dim gray(`0x909090`), 값 white
  - **battery**: `Charging`→`CHG`, `Discharging`→`DSC`, `Full`→`FUL` 태그 표시
  - **footer**: `REF Xs SEQ N` 디버그 info → `A90v49 UP <uptime>` 로 교체
- 빌드 산출:
  - `stage3/linux_init/init_v49` SHA256 `5c6433a621c8d69d38af19b157afe3d5aa455c3a597aabee1add733c305c0664`
  - `stage3/ramdisk_v49.cpio` SHA256 `4bda81c5b2834ed3901bec76edb67e50abf50052da29d729ccdc97ec0eee19bc`
  - `stage3/boot_linux_v49.img` SHA256 `38ea2e20a33af450388fe40e4d2d9aa0abb11b592efb34102ca52723a361968e`
- 실기 결과:
  - `stage3/boot_linux_v49.img`는 local marker와 boot partition prefix SHA256 readback은 일치
  - `adb shell 'twrp reboot'`로 system boot 시 Android `/system/bin/init second_stage`로 진입
  - v49는 native init stable로 인정하지 않고 격리
  - `stage3/boot_linux_v48.img`로 복구 후 `A90 Linux init v48` bridge 응답 확인

## v53: 화면 메뉴 busy gate + flash auto-hide (2026-04-25)

- 배경:
  - v52 화면 메뉴는 실기에서 `A90 INIT BOOT OK CONSOLE`, BAT/CPU/GPU/MEM/PWR, 메뉴 항목 표시 확인
  - 메뉴가 떠 있는 동안 serial 명령이 동시에 실행되면 버튼 UI와 host automation이 충돌할 수 있음
- `init_v53` 구현:
  - `/tmp/a90-auto-menu-active`로 자동 메뉴 active state 공유
  - `/tmp/a90-auto-menu-request`로 serial `hide` 요청 전달
  - 메뉴 active 중 위험/장시간 명령은 `[busy] auto menu active; send hide/q or select HIDE MENU`로 즉시 차단
  - `version`, `status`, `bootstatus`, `timeline`, `last`, `logpath`, `logcat`, `uname`, `pwd`, `mounts`, `reattach`, `stophud`는 허용
  - `start_auto_hud()`가 fork 전에 active state를 먼저 기록해 boot 직후 command race 완화
- `native_init_flash.py` 개선:
  - `--from-native`에서 `recovery`가 `[busy]`로 막히면 자동으로 `hide` 전송
  - 3초 뒤 `recovery` 재시도, 최대 3회
- 빌드 산출:
  - `stage3/linux_init/init_v53` SHA256 `4c742213dc1d2541db2d45e61af2a64d829d2f008975622465e5b78ce5c4bdbd`
  - `stage3/ramdisk_v53.cpio` SHA256 `139f0dceea7c5c64d501463d678dd3f80c29385566e22babeb28a4465ddf6001`
  - `stage3/boot_linux_v53.img` SHA256 `44cb9ebb3cc65ab0b3316afe69592c8b7fa7a05a96c872dfd2a4f9f884d98046`
- 실기 플래시:
  - local image SHA256, remote SHA256, boot partition prefix SHA256 모두 `44cb9ebb3cc65ab0b3316afe69592c8b7fa7a05a96c872dfd2a4f9f884d98046`
  - `version` → `A90 Linux init v53`
- 실기 검증:
  - `echo busytest` → `[busy] auto menu active; send hide/q or select HIDE MENU`
  - `version` → menu active 중에도 정상 응답
  - `hide` → `[busy] auto menu active; hide requested`
  - 3초 후 `echo afterhide` → `[done] echo`
  - `cat /tmp/a90-auto-menu-active` → `0`
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V53_MENU_BUSY_2026-04-25.md`

## v54: USB NCM persistent link + IPv6 netcat 검증 (2026-04-25)

- code change 없이 `A90 Linux init v53` runtime에서 진행
- `run /cache/bin/a90_usbnet ncm`으로 ACM + NCM persistent composite 구성
- host 관찰:
  - `04e8:6861` Samsung device
  - interface 0/1: `cdc_acm`
  - interface 2/3: `cdc_ncm`
  - host network: `enx6e0617d3b2a3`
- device 관찰:
  - `functions: ncm.usb0,acm.usb0`
  - `f1 -> acm.usb0`, `f2 -> ncm.usb0`
  - `ncm.ifname: ncm0`
  - `ncm.dev_addr: fa:3d:4b:0f:b5:83`
  - `ncm.host_addr: 6e:06:17:d3:b2:a3`
- device IPv4:
  - `ifconfig ncm0 192.168.7.2 netmask 255.255.255.0 up` 성공
- host IPv4:
  - non-sudo `ip addr add 192.168.7.1/24 dev enx6e0617d3b2a3`는 `Operation not permitted`
  - user sudo 설정 후 host `enx6e0617d3b2a3`에 `192.168.7.1/24` 설정 성공
  - `ping -c 3 192.168.7.2`: 3/3 PASS, 0% packet loss, avg 약 1.95ms
- IPv6 link-local:
  - host → device `ping -6 fe80::f83d:4bff:fe0f:b583%enx6e0617d3b2a3` 응답 확인
- TCP:
  - device `/cache/bin/toybox netcat -l -p 2323`
  - host `nc -6 fe80::f83d:4bff:fe0f:b583%enx6e0617d3b2a3 2323`
  - payload `hello-from-host-over-ncm-ipv6` 수신 확인
- 특이사항:
  - USB 재열거 후 host modem probe로 보이는 `AT` 문자열이 serial shell에 한 번 유입됨
  - shell noise filter 또는 ignore 정책 후보로 기록
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V54_NCM_LINK_2026-04-25.md`

## v55: NCM 운영 helper + TCP nettest helper 검증 (2026-04-25)

- 목적:
  - USB NCM을 수동 실험이 아니라 반복 운용 가능한 기본 네트워크 경로로 고정
  - host interface 이름을 `ncm.host_addr` 기반으로 자동 탐지
  - toybox `netcat` stdin 경쟁을 피하고 양방향 TCP payload 검증을 전용 static helper로 분리
- 추가:
  - `scripts/revalidation/ncm_host_setup.py`
    - `setup|status|ping|off`
    - `run /cache/bin/a90_usbnet ncm/status/off`
    - device `ncm0` IP 설정
    - host `192.168.7.1/24` 설정과 ping 검증
    - v53 menu busy state일 때 `hide` 후 재시도
  - `stage3/linux_init/a90_nettest.c`
    - `listen <port> <timeout_sec> <expect>`
    - `send <host_ipv4> <port> <payload>`
  - `scripts/revalidation/build_nettest_helper.sh`
    - static ARM64 `a90_nettest` 빌드
- 검증:
  - Python syntax check PASS
  - static ARM64 build PASS
  - `ncm_host_setup.py status` host interface 자동 탐지 PASS
  - `ncm_host_setup.py ping`: 3/3 PASS, 0% packet loss
  - `/cache/bin/a90_nettest` 배치 후 SHA256 일치
  - host→device TCP payload PASS
  - device→host TCP payload PASS
  - 30초 ping stability: 30/30 PASS, 0% packet loss
  - ACM serial bridge는 NCM traffic 이후 `version` 응답 유지
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V55_NCM_OPS_2026-04-25.md`

## v56: NCM TCP control helper 검증 (2026-04-26)

- 목적:
  - USB NCM 링크 위에서 serial bridge보다 빠른 작은 명령/응답 채널 확보
  - serial bridge는 rescue/fallback으로 유지
- 추가:
  - `stage3/linux_init/a90_tcpctl.c`
    - `listen <port> <idle_timeout_sec> [max_clients]`
    - TCP command: `help`, `ping`, `version`, `status`, `run`, `quit`, `shutdown`
    - `run`은 absolute path만 허용, stdin `/dev/null`, stdout/stderr TCP 반환, 10초 timeout
  - `scripts/revalidation/build_tcpctl_helper.sh`
    - static ARM64 `a90_tcpctl` 빌드
- 산출:
  - `external_tools/userland/bin/a90_tcpctl-aarch64-static`
  - SHA256 `997a5d717c235c2d3cd8757223e68003ce6b68cffee73f06681d1bee16519faf`
- 실기 검증:
  - `/cache/bin/a90_tcpctl` 배치 후 SHA256 일치
  - `run /cache/bin/a90_tcpctl listen 2325 60 8`
  - host `printf 'ping\n' | nc 192.168.7.2 2325` → `pong`, `OK`
  - `version` → `a90_tcpctl v1`, `OK`
  - `status` → kernel/uptime/load/mem, `OK`
  - `run /cache/bin/toybox uname -a` → `[exit 0]`, `OK`
  - `run /cache/bin/toybox ifconfig ncm0` → `192.168.7.2` 포함, `[exit 0]`, `OK`
  - `shutdown` → server 종료, serial `run`이 `[done]`
  - 이후 serial bridge `version`과 NCM ping 3/3 PASS
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V56_TCPCTL_2026-04-26.md`

## v57: TCP control host wrapper 검증 (2026-04-26)

- 목적:
  - `a90_tcpctl`을 직접 `nc` 조합으로 다루지 않고 host wrapper로 반복 운용
  - launch/client/stop/smoke를 하나의 도구로 묶어 다음 실험 속도 향상
- 추가:
  - `scripts/revalidation/tcpctl_host.py`
    - `install`
    - `start`
    - `call`
    - `ping`, `version`, `status`
    - `run`
    - `stop`
    - `smoke`
- 검증:
  - Python syntax/help PASS
  - `python3 scripts/revalidation/tcpctl_host.py smoke` PASS
  - smoke 내용:
    - bridge로 `/cache/bin/a90_tcpctl listen 2325 60 8` 실행
    - TCP `ping`, `version`, `status` PASS
    - TCP `run /cache/bin/toybox uname -a` PASS
    - TCP `run /cache/bin/toybox ifconfig ncm0` PASS
    - TCP `shutdown` PASS
    - serial `run`이 `[done]`으로 종료
    - 이후 serial `version`과 NCM ping 3/3 PASS
- 수정:
  - 첫 smoke에서 wrapper가 serial `[done] run`을 종료 조건으로 보지 않아 실패 처리
  - `BridgeRunThread`가 `[done] run`, `[err] run`, `[busy]`를 보면 종료하도록 수정
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V57_TCPCTL_HOST_WRAPPER_2026-04-26.md`

## v58: TCP control soak 검증 (2026-04-26)

- 목적:
  - USB NCM + `a90_tcpctl` 경로가 짧은 smoke를 넘어 반복 운용 가능한지 확인
  - serial bridge는 launch/rescue 채널로 유지하고, 실질 명령은 TCP control로 반복
- 추가:
  - `scripts/revalidation/tcpctl_host.py`
    - `soak`
    - 기본 300초/10초 간격
    - TCP `ping`, 주기적 `status`, 주기적 `run /cache/bin/toybox uptime`, host NCM ping
- 실기 검증:
  - `python3 -m py_compile scripts/revalidation/tcpctl_host.py` PASS
  - `python3 scripts/revalidation/tcpctl_host.py soak --help` PASS
  - short soak 20초/4사이클 PASS
  - main soak 300초/30사이클 PASS
  - TCP ping 30/30 PASS
  - TCP status 5/5 PASS
  - TCP run uptime 5/5 PASS
  - host ping 30/30 PASS
  - `tcpctl: served=42 stop=1`
  - serial `[done] run (300509ms)`
  - final NCM ping 3/3, 0% packet loss
- 판단:
  - 현재 NCM + TCP control은 짧은 개발 세션용 기본 서버형 제어망으로 충분히 안정적
  - 물리 USB 재연결/UDC reset reconnect soak는 별도 항목으로 남김
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V58_TCPCTL_SOAK_2026-04-26.md`

## v59: AT serial noise filter 검증 (2026-04-26)

- 목적:
  - host NetworkManager/modem probe가 ACM serial에 던지는 `AT` 계열 line을 shell 오류로 만들지 않음
  - bridge 쪽 임시 필터가 아니라 native init shell 입력 경로에서 device 자체 안정성 확보
- 추가:
  - `stage3/linux_init/init_v59.c`
    - `INIT_VERSION "v59"`
    - `is_unsolicited_at_noise()`
    - command dispatch 전에 `AT`, `ATE0`, `AT+...`, `ATQ0 ...` line 무시
    - 무시한 line은 `/cache/native-init.log`에 `serial: ignored AT probe ...` 기록
- 산출:
  - `stage3/linux_init/init_v59`
    - SHA256 `7c87459e49e77abf969256b0726cc6329470dc56ea0b7d73acfff4f4ab16d735`
  - `stage3/ramdisk_v59.cpio`
    - SHA256 `aa9ab262e77fd5f7d9795e2139f8c07794848314d81e38ef93a113d26c20b217`
  - `stage3/boot_linux_v59.img`
    - SHA256 `9c4eb1b4b8024a481e71a5bb584c48fe11f1d454983a6e541e49213818120e07`
- 실기 검증:
  - `native_init_flash.py stage3/boot_linux_v59.img --expect-version "A90 Linux init v59" --from-native` PASS
  - boot partition prefix SHA256 readback PASS
  - bridge `version` → `A90 Linux init v59`
  - serial 입력:
    - `AT`
    - `ATE0`
    - `AT+GCAP`
    - `ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0`
    - `version`
  - 출력에 `unknown command: AT` 없음
  - `/cache/native-init.log`에 ignored AT probe 4건 기록 확인
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V59_AT_NOISE_2026-04-26.md`

## v60: opt-in boot-time NCM/tcpctl netservice 검증 (2026-04-26)

- 목적:
  - USB NCM과 `a90_tcpctl`을 수동 실험이 아니라 부팅 시 켤 수 있는 opt-in service로 정리
  - default는 OFF로 유지해 ACM serial rescue 경로와 안전성을 보존
  - `/cache/native-init-netservice` flag가 있을 때만 boot-time NCM/tcpctl을 자동 시작
- 추가:
  - `stage3/linux_init/init_v60.c`
    - `INIT_VERSION "v60"`
    - `netservice [status|start|stop|enable|disable]` 명령 추가
    - `enable`은 flag 생성 후 NCM/tcpctl 시작, `disable`은 flag 제거와 rollback 수행
    - boot path에서 flag 확인 후 `/cache/bin/a90_usbnet ncm`, `ifconfig ncm0 192.168.7.2/24`, `a90_tcpctl listen 2325 3600 0` 순서로 시작
    - `/cache/native-init-netservice.log`에 helper/stdout/stderr 기록
  - `scripts/revalidation/ncm_host_setup.py`
    - 이미 NCM이 켜진 상태면 `a90_usbnet ncm` 재실행 없이 host/device IP와 ping만 검증
- 산출:
  - `stage3/linux_init/init_v60`
    - SHA256 `4a274b02f793be79872c4ff164dcead332b33e4f7cf281c35f1d59625774dd09`
  - `stage3/ramdisk_v60.cpio`
    - SHA256 `f8b153804c561e26c784c713668a6e8e3dfb0cb10b83a9a72c659f1d8c46285c`
  - `stage3/boot_linux_v60.img`
    - SHA256 `c57fbf4645790826fbd5e804ff605c25b95cffb4c5eb0ff9076202581e6e828a`
- 실기 검증:
  - default OFF boot: `enabled=no`, `ncm0=absent`, `tcpctl=stopped`
  - `netservice enable` 후 reboot auto-start: `enabled=yes`, `ncm0=present`, `tcpctl=running pid=544`
  - host NCM interface `enx0a2eb7a94b2f`, `192.168.7.1/24`
  - `ping -c 3 -W 2 192.168.7.2` 3/3 PASS, 0% loss
  - `tcpctl_host.py ping`, `status`, `run /cache/bin/toybox uptime` PASS
  - `netservice disable` rollback 후 `enabled=no`, `ncm0=absent`, `tcpctl=stopped`
  - bridge `version`은 rollback 후에도 `A90 Linux init v60`
- 수정 기록:
  - 초기 `a90_tcpctl listen 2325 86400 0`은 helper의 timeout 상한 때문에 `listen: invalid port or timeout`으로 실패
  - 최종값은 `3600s`로 고정해 boot-time tcpctl 시작 성공
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V60_NETSERVICE_2026-04-26.md`

## v60: netservice stop/start UDC reconnect 검증 (2026-04-26)

- 목적:
  - v60 `netservice stop/start`로 software UDC 재열거 후 ACM/NCM/tcpctl이 복구되는지 확인
  - host NCM interface 이름이 재열거마다 바뀌는지 확인하고 운영 절차에 반영
- 추가:
  - `scripts/revalidation/netservice_reconnect_soak.py`
    - `status`, `once`, `soak` subcommand
    - device `ncm.host_addr` MAC으로 현재 host `enx...` interface 자동 탐지
    - sudo 불가 환경용 `--manual-host-config` 옵션 추가
- 실기 검증:
  - stale `enx0a2eb7a94b2f`는 재열거 후 사라져 `Cannot find device` 발생
  - 새 interface `enxba06f3efab0f` 감지
  - host `192.168.7.1/24` 설정 후 `192.168.7.2` ping 3/3 PASS
  - TCP `ping`, `status`, `run /cache/bin/toybox uptime` PASS
  - final `netservice stop` 후 `ncm0=absent`, `tcpctl=stopped`, bridge `version` v60 확인
- 발견:
  - USB 재열거 중 host modem probe fragment `A`, `ATAT...`가 serial output을 오염시킬 수 있음
  - v61 후보로 짧은 `A` fragment와 반복 `ATAT...` filter hardening 필요
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V60_RECONNECT_2026-04-26.md`

## v61: HUD CPU/GPU usage percent 표시 검증 (2026-04-26)

- 목적:
  - 기존 CPU/GPU 온도 표시 옆에 사용률 `%`만 먼저 추가
  - 화면 공간을 과하게 쓰지 않고 `CPU <temp> <usage> GPU <temp> <usage>` 형태로 검증
- 추가:
  - `stage3/linux_init/init_v61.c`
    - `INIT_VERSION "v61"`
    - `/proc/stat` aggregate delta 기반 CPU 사용률 계산
    - `/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage` 기반 GPU busy `%` 읽기
    - `status`와 HUD row 2에 CPU/GPU usage 표시
- 산출:
  - `stage3/linux_init/init_v61`
    - SHA256 `7fce8bac65af8cd997d7f150c0939b6e4fa757ea0ecfeb89e0213c3fa955f427`
  - `stage3/ramdisk_v61.cpio`
    - SHA256 `2ce70282a001db47d42b900ccc0bfaf3aed7dee1528107048912bfbaab53d729`
  - `stage3/boot_linux_v61.img`
    - SHA256 `40a33381be60ea8eaf91e7f09256d3d0de100c8959c3687a3b4aa95696c7cdb2`
- 실기 검증:
  - `native_init_flash.py stage3/boot_linux_v61.img --from-native --expect-version "A90 Linux init v61"` PASS
  - boot partition prefix SHA256 readback PASS
  - bridge `version` → `A90 Linux init v61`
  - `status` 초기 CPU usage는 delta 기준 이전 샘플이 없어 `?`로 표시
  - 다음 `status`에서 `thermal: cpu=35.1C 0% gpu=33.5C 0%` 확인
  - `statushud` redraw 후 `thermal: cpu=35.3C 12% gpu=33.6C 0%` 확인
  - `autohud 2` 재시작 후 `autohud: running`, `netservice: disabled tcpctl=stopped` 확인
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V61_CPU_GPU_USAGE_2026-04-26.md`

## v62: CPU stress usage gauge와 `/dev` guard 검증 (2026-04-26)

- 목적:
  - v61에서 추가한 CPU usage `%`가 실제 부하에서 변하는지 실기 검증
  - `/dev/null`과 `/dev/zero`가 없거나 regular file로 오염되는 경우를 boot-time에 복구
- 추가:
  - `stage3/linux_init/init_v62.c`
    - `INIT_VERSION "v62"`
    - `/dev/null` rdev `1:3`, `/dev/zero` rdev `1:5` char node 보정
    - `cpustress [sec] [workers]` shell 명령 추가
    - `cpustress`는 fork worker 기반이며 q/Ctrl-C 취소 정책을 따른다.
- 산출:
  - `stage3/linux_init/init_v62`
    - SHA256 `016f67ec1bd713533ed8d2d12e5e5f7cd5709406ce6351fa0d22f30d0bcdfa33`
  - `stage3/ramdisk_v62.cpio`
    - SHA256 `13ced5f0e0d97887fe84036b777cd5efdc97b0c81089261b9397f5da12169629`
  - `stage3/boot_linux_v62.img`
    - SHA256 `8c422903226980855e23b75379a60b4ec3ec0a680c457b28adfa5417fdf870b1`
- 실기 검증:
  - `native_init_flash.py stage3/boot_linux_v62.img --from-native --expect-version "A90 Linux init v62"` PASS
  - boot partition prefix SHA256 readback PASS
  - bridge `version` → `A90 Linux init v62`
  - `/dev/null` → `mode=0600`, `rdev=1:3`
  - `/dev/zero` → `mode=0600`, `rdev=1:5`
  - `cpustress 10 8` 전 `thermal: cpu=34.9C 0% gpu=33.3C 0%`
  - `cpustress 10 8` 후 `thermal: cpu=36.3C 29% gpu=34.6C 0%`
  - cooldown 후 `thermal: cpu=35.4C 0% gpu=33.7C 0%`
  - 메모리 사용량은 `/dev/null` 복구 후 약 `250~252/5375MB` 범위로 안정
- 발견:
  - GPU usage가 0%인 것은 CPU-only stress와 KMS dumb-buffer HUD가 KGSL/3D GPU workload를 만들지 않기 때문에 정상이다.
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V62_CPUSTRESS_2026-04-26.md`

## v63: 계층형 앱 메뉴와 CPU stress screen app (2026-04-26)

- 목적:
  - 자동 HUD 메뉴를 단일 리스트에서 APPS/TOOLS/LOGS/NETWORK/POWER 계층으로 확장
  - LOG/NETWORK/CPU STRESS 화면이 한 프레임만 보이고 사라지는 문제를 active app 상태로 해결
  - CPU stress를 버튼으로 5/10/30/60초 선택하고 실행 중 CPU 관련 정보를 화면에 표시
- 추가:
  - `stage3/linux_init/init_v63.c`
    - `MAIN MENU`, `APPS`, `APPS / TOOLS`, `TOOLS / CPU STRESS` 계층 메뉴
    - `SCREEN_APP_LOG`, `SCREEN_APP_NETWORK`, `SCREEN_APP_CPU_STRESS` persistent app state
    - CPU stress app dashboard: CPU 온도/사용률/load, core online/present, per-core frequency, memory, power, worker/test duration
    - menu help 위치와 글자 밝기 조정
- 산출:
  - `stage3/linux_init/init_v63`
    - SHA256 `062eb9a780c0fe71890e80d0c961b5b3016d3d35e0da19fa99e5289bbde04a00`
  - `stage3/ramdisk_v63.cpio`
    - SHA256 `7b9d3f71f648e7f9765fc6c1827c66c0dcc422f714b1ec67a334f9cbca5f53ce`
  - `stage3/boot_linux_v63.img`
    - SHA256 `99025fba4c17348057920eab06b7bd98a97b5cc5f6acff21190981288a0ad09d`
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V63_APP_MENU_2026-04-26.md`

## v64: custom boot splash 전환 (2026-04-26)

- 목적:
  - 부팅 직후 보이던 큰 `TEST` 디버그 화면을 프로젝트 전용 splash로 교체
  - 기존처럼 약 2초 후 상태 HUD/menu와 serial shell로 전환
- 추가:
  - `stage3/linux_init/init_v64.c`
    - `BOOT_SPLASH_SECONDS`
    - `kms_draw_boot_splash()`
    - `display-splash` timeline 기록
    - serial 안내 `splash 2s -> autohud 2s`
- 산출:
  - `stage3/linux_init/init_v64`
    - SHA256 `f80152f02db376080bdcae3600ce6daf03e64bc08e0e092a8ae3b9116ea7bde2`
  - `stage3/ramdisk_v64.cpio`
    - SHA256 `8560785b5e2832d40913b3b0e91a90e633041809a788200ebb6aa875c12ed018`
  - `stage3/boot_linux_v64.img`
    - SHA256 `aa628f70f09a62f704b9d2078aae888ad57d95349fcaf8d3af47d95a3ad864ca`
- 실기 검증:
  - `native_init_flash.py stage3/boot_linux_v64.img --from-native --expect-version "A90 Linux init v64"` PASS
  - bridge `version` → `A90 Linux init v64`
  - `timeline` → `display-splash rc=0 errno=0 detail=boot splash applied`
  - `status` → `boot: BOOT OK shell 3S`, `autohud: running`
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V64_BOOT_SPLASH_2026-04-26.md`

## v65: boot splash safe layout (2026-04-26)

- 목적:
  - v64 custom splash가 보이지만 일부 텍스트가 잘리는 문제 수정
  - 긴 상태 문구와 footer가 화면 폭/라운드 코너 안전 여백을 넘지 않도록 보정
- 추가:
  - `stage3/linux_init/init_v65.c`
    - `INIT_VERSION "v65"`
    - `kms_draw_text_fit()`으로 splash 각 줄을 `shrink_text_scale()`에 통과
    - splash 기본 scale 축소, 좌우 margin 확대, footer 위치 상향
    - 상태 문구를 짧게 정리
- 산출:
  - `stage3/linux_init/init_v65`
    - SHA256 `2cb2b9e5e8d989cddb92f3c1ef93b8f4674ba4359408445b19af5745ddc2f373`
  - `stage3/ramdisk_v65.cpio`
    - SHA256 `b8184bb241c52b0d99e9efbceed16ded50598a24068a359c8d8e3abf78f1c16f`
  - `stage3/boot_linux_v65.img`
    - SHA256 `143acc7925b8ac0006d972ca463c1993f5306b63c5187e9c3007a34fa71ed7d4`
- 실기 검증:
  - `native_init_flash.py stage3/boot_linux_v65.img --from-native --expect-version "A90 Linux init v65"` PASS
  - boot partition prefix SHA256 readback PASS
  - bridge `version` → `A90 Linux init v65`
  - `status` → `boot: BOOT OK shell 3S`, `autohud: running`
  - `timeline` → `display-splash rc=0 errno=0 detail=boot splash applied`
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V65_SPLASH_SAFE_LAYOUT_2026-04-26.md`

## v66: ABOUT app과 versioning 도입 (2026-04-26)

- 목적:
  - 기존 build 번호 `vNN`만 쓰던 상태에서 공식 semantic version을 병행
  - 만든이 `made by temmie0214`를 화면/명령 출력에 표시
  - 앱 메뉴에서 version, changelog, credits 확인
- 추가:
  - `stage3/linux_init/init_v66.c`
    - `INIT_VERSION "0.7.3"`
    - `INIT_BUILD "v66"`
    - `INIT_CREATOR "made by temmie0214"`
    - splash, `version`, `status`, timeline banner 갱신
    - `APPS / ABOUT` 메뉴와 `VERSION`/`CHANGELOG`/`CREDITS` 화면
  - `docs/overview/VERSIONING.md`
    - `MAJOR.MINOR.PATCH`와 `vNN` build tag 규칙
  - `CHANGELOG.md`
    - 공식 버전별 업데이트 로그
- 산출:
  - `stage3/linux_init/init_v66`
    - SHA256 `31a8c6e8da1f2ab07fe26a96d6fa78ba02a9cb43e6bc4ea3080220f4efb41715`
  - `stage3/ramdisk_v66.cpio`
    - SHA256 `446b070e9df82b6368122ca190c27c3298a147eb778f70c9d08cc7e9bcf7e972`
  - `stage3/boot_linux_v66.img`
    - SHA256 `320a325531b6e2ffc35c8165179396638c1c8af5ee4a59517f1074dc92b3eb08`
- 실기 검증:
  - `native_init_flash.py stage3/boot_linux_v66.img --from-native --expect-version "A90 Linux init 0.7.3 (v66)"` PASS
  - boot partition prefix SHA256 readback PASS
  - bridge `version` → `A90 Linux init 0.7.3 (v66)` / `made by temmie0214`
  - `status` → `creator: made by temmie0214`, `boot: BOOT OK shell 3S`
  - `timeline` → `init-start ... A90 Linux init 0.7.3 (v66)`
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V66_ABOUT_VERSIONING_2026-04-26.md`

## v67: changelog 상세 화면과 compact ABOUT typography (2026-04-26)

- 목적:
  - 휴대폰 세로 화면을 활용해 changelog를 더 길게 표시
  - ABOUT/VERSION/CHANGELOG/CREDITS 계열 글씨 크기를 작게 통일
  - `CHANGELOG`를 단일 요약 화면이 아니라 버전 목록 → 상세 화면 구조로 변경
- 추가:
  - `stage3/linux_init/init_v67.c`
    - `INIT_VERSION "0.7.4"`
    - `INIT_BUILD "v67"`
    - `APPS / ABOUT / CHANGELOG >` submenu 추가
    - `0.7.4 v67`~`0.6.0 v62` version별 detail 화면 추가
    - ABOUT 계열 text scale을 1080px 기준 `6` → `4`로 축소
- 산출:
  - `stage3/linux_init/init_v67`
    - SHA256 `642da01258a4a43016e5362d74fb2c142a30c42001217c88fa2ae2fe8aa05e04`
  - `stage3/ramdisk_v67.cpio`
    - SHA256 `55d2b9c0323e2642c9d7095a62d668b85774476fe5079a43113ef7a5b3e7b6b2`
  - `stage3/boot_linux_v67.img`
    - SHA256 `8b087d08ecc5dd459ffd36c22c520f5de9fb2c3ddecee0c212bd4fece57f8623`
- 실기 검증:
  - `native_init_flash.py stage3/boot_linux_v67.img --from-native --expect-version "A90 Linux init 0.7.4 (v67)"` PASS
  - boot partition prefix SHA256 readback PASS
  - bridge `version` → `A90 Linux init 0.7.4 (v67)` / `made by temmie0214`
  - `status` → `creator: made by temmie0214`, `boot: BOOT OK shell 3S`, `autohud: running`
  - `timeline` → `init-start ... A90 Linux init 0.7.4 (v67)`, `display-splash`, `shell`
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V67_CHANGELOG_DETAILS_2026-04-26.md`

## v68: HUD log tail과 changelog history 확장 (2026-04-26)

- 확인:
  - `badb353 Add v68 log tail HUD and full changelog history`
  - `stage3/linux_init/init_v68.c`
    - `INIT_VERSION "0.7.5"`
    - `INIT_BUILD "v68"`
    - HUD menu hidden 상태에서 `/cache/native-init.log` tail 표시
    - changelog list/detail을 v1 계열까지 확장
- 산출:
  - `stage3/linux_init/init_v68`
    - SHA256 `24dcfe9b2351c6cb16a1af6737b12c950e5f1972c82f6ede6855b6ec210d64c5`
  - `stage3/ramdisk_v68.cpio`
    - SHA256 `c33b9853be5e6faeea1254d47aa8fb165ca44919ce12679ea9d38d487a3cb358`
  - `stage3/boot_linux_v68.img`
    - SHA256 `bc0982cb67f966affbc3de2d1d00c4b6a2797e1f79c1267863a29091fd1ddb41`
- 실기 확인:
  - bridge `version` → `A90 Linux init 0.7.5 (v68)`

## v69: physical-button input gesture layout (2026-04-26)

- 목적:
  - 터치 없이 VOL+/VOL-/POWER만으로 더 풍부한 입력을 제공
  - 단일 클릭은 기존 메뉴 조작과 호환
  - 더블클릭, 롱프레스, 조합 입력을 안전한 메뉴 action으로 매핑
- 추가:
  - `stage3/linux_init/init_v69.c`
    - `INIT_VERSION "0.8.0"`
    - `INIT_BUILD "v69"`
    - `inputlayout` command 추가
    - `waitgesture [count]` debug command 추가
    - `screenmenu`/`blindmenu`가 gesture action 사용
    - `POWER long`은 destructive action에 묶지 않고 reserved 처리
- 산출:
  - `stage3/linux_init/init_v69`
    - SHA256 `bf9a5cc337d8ae0ca705c027053a0e81e3d4436926e331e089952b8916a280e9`
  - `stage3/ramdisk_v69.cpio`
    - SHA256 `28fbb2f9ae618086bc704a73529d3cb3c4ebac050052f6dbd396d51503508ada`
  - `stage3/boot_linux_v69.img`
    - SHA256 `1a333b5ee8e1c73722b9165f569f17a3257119690fccba3ce160b952792252d8`
- 실기 검증:
  - `native_init_flash.py stage3/boot_linux_v69.img --from-native --expect-version "A90 Linux init 0.8.0 (v69)"` PASS
  - boot partition prefix SHA256 readback PASS
  - bridge `version` → `A90 Linux init 0.8.0 (v69)` / `made by temmie0214`
  - `inputlayout` → 단일/더블/롱/조합 mapping 출력 PASS
  - `status` → `creator: made by temmie0214`, `boot: BOOT OK shell 3S`
  - `timeline` → `init-start ... A90 Linux init 0.8.0 (v69)`, `display-splash`, `shell`
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V69_INPUT_LAYOUT_2026-04-26.md`

## v70: input monitor app and raw/gesture trace (2026-04-26)

- 목적:
  - 물리 버튼 개선을 감이 아니라 raw event와 decoder 결과를 같이 보며 진행
  - 누른 순간, 뗀 순간, hold duration, event gap, gesture/action 판정을 한 화면/로그로 확인
- 추가:
  - `stage3/linux_init/init_v70.c`
    - `INIT_VERSION "0.8.1"`
    - `INIT_BUILD "v70"`
    - `TOOLS / INPUT MONITOR` screen app 추가
    - `inputmonitor [events]` shell command 추가
    - raw `DOWN`/`UP`/`REPEAT`, gap, hold, decoded gesture/action 출력
    - raw event를 2줄 카드로 표시하고 DOWN/UP/REPEAT 색상 구분
    - 최신 gesture 판정을 큰 상단 패널로 표시: single/double/long/combo, buttons, action, duration/gap
    - `waitgesture`와 같은 decoder helper를 공유하도록 정리
- 산출:
  - `stage3/linux_init/init_v70`
    - SHA256 `d7082127bbfeafd0508cf7a3b90079dc0f3f1b8b8238140cceb5dfe9063d7d12`
  - `stage3/ramdisk_v70.cpio`
    - SHA256 `98ae190435469f2817d6d04fce076e643f2cb5f9e1fbafd69d9c865e1d1907b3`
  - `stage3/boot_linux_v70.img`
    - SHA256 `5e3657ba14705bdee9cc772cb8916601bfe1a92f31122475c1115896e2a42cb1`
- 실기 검증:
  - `native_init_flash.py stage3/boot_linux_v70.img --from-native --expect-version "A90 Linux init 0.8.1 (v70)"` PASS
  - boot partition prefix SHA256 readback PASS
  - bridge `version` → `A90 Linux init 0.8.1 (v70)` / `made by temmie0214`
  - `status` → `boot: BOOT OK shell 3S`, `autohud: running`
  - `inputlayout` → v69 gesture mapping 유지 확인
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_V70_INPUT_MONITOR_2026-04-26.md`
