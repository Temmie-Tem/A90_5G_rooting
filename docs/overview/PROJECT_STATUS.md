# Samsung Galaxy A90 5G - 현재 상태

## 기준점 A

**디바이스**: Samsung Galaxy A90 5G (`SM-A908N`)  
**빌드**: `A908NKSU5EWA3` / Android 12  
**루트 상태**: `Magisk 30.7`, `su` 동작 확인  
**ADB**: 정상  
**Wi-Fi**: ADB shell로 WPA2 네트워크 등록 및 연결 확인  
**현재 패키지 수**: `user 0` 기준 `92`

## 현재 확인된 사실

- stock 기반 Android 부팅 가능
- patched AP 부팅 가능
- `adb shell su -c id`로 root 획득 가능
- `getenforce`는 `Enforcing`
- 다운로드 모드 사진 기준 `CURRENT BINARY : Custom (0x303)`
- 다운로드 모드 사진 기준 `FRP LOCK : OFF`, `OEM LOCK : OFF (U)`
- 다운로드 모드 사진 기준 `QUALCOMM SECUREBOOT : ENABLE`, `SECURE DOWNLOAD : ENABLE`
- 다운로드 모드 사진 기준 `WARRANTY VOID : 0x1 (0xE03)`
- Samsung Knox 공식 문서 기준 `KG STATE` 줄은 다운로드 모드에 항상 표시된다고 볼 근거를 찾지 못함
- 최소 부팅 allowlist 재적용 후에도 부팅 유지
- allowlist 밖에 남는 패키지는 현재 `3개`
  - `com.samsung.android.game.gos`
  - `com.samsung.android.themecenter`
  - `com.sec.android.sdhms`

## 현재 공식 목표

이번 트랙의 공식 목표는 `native Linux 부팅 재도전`입니다.

접근 순서는 고정합니다.

### 1. 기준점 유지
- 부팅 가능
- ADB 가능
- `su` 가능
- Wi-Fi 가능
- `stock firmware + patched AP`로 복구 가능

### 2. 1단계 재검증: 부트체인 관찰 재구성
- `stock AP + stock recovery`
- `patched AP + stock recovery`
- `stock AP + TWRP`
- `patched AP + TWRP`
- 각 조합에서 flash 결과, 다운로드 모드 문구, 첫 부팅, recovery fallback, ADB, `su`를 같은 형식으로 기록

### 3. 2단계 재검증: 보안 경계 분해
- boot image 수용 여부
- recovery 교체 허용 여부
- `official binaries only` 발생 조건
- KG 표기 변화와 결과 상관관계
- factory reset 유무 영향

### 4. 3단계 재도전: native Linux 진입 후보 실험
- `patched AP 유지 + Linux 진입 가능성 있는 ramdisk/init 경로`
- `recovery` 경로 활용
- `vbmeta/부트 이미지 조합 변형`
- 필요 시 `TWRP` 기반 보조 경로

## 성공 조건

- `adb devices` 정상
- `getprop sys.boot_completed = 1`
- `adb shell su -c id`가 `uid=0(root)`
- 필요 시 Wi-Fi 연결 가능

단계별 종료 기준:

- 1단계 종료: 4개 기본 조합 결과표 완성
- 2단계 종료: 실제 차단 경계에 대한 결론 1개 이상 확보
- 3단계 종료: 다른 초기 userspace 실행, recovery 기반 Linux 초기 진입, 또는 native 경로 차단 이유 중 하나를 재현 가능한 형태로 확보

## 실패 조건

- bootloop
- recovery fallback
- download mode로 자동 복귀
- ADB 상실
- `su` 상실

## 보류 대상

현재 기준점 안정성 때문에 아래 축은 우선 보류합니다.

- `kgclient`
- `klmsagent`
- `knox.attestation`
- `fmm`
- telephony / IMS / network stack

## 기준점 고정 항목

각 실험 시작 전 다음 값을 반드시 저장합니다.

- 현재 `boot`, `recovery`, `vbmeta`
- 다운로드 모드 화면의 `KG`, `OEM LOCK`, custom binary 문구
- `adb`, `su`, `boot_completed`, `Wi-Fi` 상태
- 필요 시 `ro.build.fingerprint`, `ro.boot.verifiedbootstate`

현재 확보된 다운로드 모드 값:

- `CURRENT BINARY : Custom (0x303)`
- `FRP LOCK : OFF`
- `OEM LOCK : OFF (U)`
- `WARRANTY VOID : 0x1 (0xE03)`
- `QUALCOMM SECUREBOOT : ENABLE`
- `SECURE DOWNLOAD : ENABLE`
- `KG`는 이번 사진으로는 미확인

공식 문서 재확인 결과:

- Samsung Knox Guard 문서는 장치가 Knox Guard에 등록, 활성화, 완료, 삭제되며
  관리 상태가 변한다고 설명함
- 그러나 다운로드 모드에 `KG STATE` 줄이 항상 보여야 한다는 표시 규칙은 설명하지 않음
- 현재는 `KG 미표시`를 독립 관찰값으로 취급하고,
  특정 KG 상태로 자동 해석하지 않음

## 현재 폰 상태

- patched AP (Magisk 30.7) + **TWRP recovery**
- 최신 실기 확인: `stage3/boot_linux_v48.img` (`A90 Linux init v48`)
- 부팅 흐름: TEST 패턴 약 2초 → 상태 HUD 자동 전환 → USB ACM serial shell
- 로그 상태: `/cache/native-init.log`에 boot/command/result 기록
- blocking 상태: `waitkey`, `readinput`, `watchhud`, `blindmenu` q/Ctrl-C 취소 확인
- boot timeline: `timeline` 명령과 `/cache/native-init.log` replay 확인
- HUD 상태: `BOOT OK shell` summary 표시와 `statushud` draw 확인
- run 상태: `/bin/a90sleep` helper로 `run` q 취소 확인
- log 보존: native init → recovery → native init 왕복 후 v44/v45/v47 log append 확인
- storage 상태: `/cache` safe write, `userdata` conditional, critical partitions do-not-touch 기준 문서화
- screen menu 상태: `menu`/`screenmenu` 화면 진입과 q 취소 확인
- USB 상태: ACM-only gadget `04e8:6861` / host `cdc_acm` 기준 문서화
- userland 상태: `toybox 0.8.13` static ARM64 host 빌드와 `/cache/bin/toybox` 실기 실행 확인
- USB reattach 상태: `usbacmreset`와 외부 helper `off` 후 serial bridge 복구 확인
- USB NCM 상태: host `cdc_ncm` composite interface와 device `ncm0` 임시 생성 확인
- 상세 최신 상태: `docs/reports/NATIVE_INIT_V48_USB_REATTACH_NCM_2026-04-25.md`
- v47 screen menu 기록: `docs/reports/NATIVE_INIT_V47_SCREEN_MENU_2026-04-25.md`
- USB gadget map 기록: `docs/reports/NATIVE_INIT_USB_GADGET_MAP_2026-04-25.md`
- static userland 후보 기록: `docs/reports/NATIVE_INIT_USERLAND_CANDIDATES_2026-04-25.md`
- v46 storage map 기록: `docs/reports/NATIVE_INIT_STORAGE_MAP_2026-04-25.md`
- v45 run/log preservation 기록: `docs/reports/NATIVE_INIT_V45_RUN_LOG_2026-04-25.md`
- v44 HUD boot summary 기록: `docs/reports/NATIVE_INIT_V44_HUD_BOOT_2026-04-25.md`
- v43 boot timeline 기록: `docs/reports/NATIVE_INIT_V43_TIMELINE_2026-04-25.md`
- v42 blocking cancel 기록: `docs/reports/NATIVE_INIT_V42_CANCEL_2026-04-25.md`
- v41 파일 로그 기록: `docs/reports/NATIVE_INIT_V41_LOGGING_2026-04-25.md`
- v40 shell return code 기록: `docs/reports/NATIVE_INIT_V40_BUILD_2026-04-25.md`
- v39 기준 전체 상태 기록: `docs/reports/NATIVE_INIT_V39_STATUS_2026-04-25.md`
- 다음 작업 목록: `docs/plans/NATIVE_INIT_NEXT_WORK_2026-04-25.md`
- 복구: `backups/baseline_a_20260423_030309/boot.img` dd 복구 가능

## Stage 3 달성 사항 (2026-04-23)

### 3-1. native Linux init 진입 (초기)

- `aarch64-linux-gnu-gcc -static` 으로 빌드한 static init 바이너리를 ramdisk에 탑재
- Android kernel이 우리 init을 pid 1로 실행
- proc / sys / devtmpfs / ext4(/dev/block/sda31) 마운트 성공
- 핵심 우회: devtmpfs async 초기화 문제를 `mknod(makedev(259,15))` 로 해결

### 3-2. USB ACM serial console + 인터랙티브 셸 (v8~v22)

**현재 버전**: `init_v22` (`stage3/boot_linux_v22.img`)

ADB 방식이 막혀 USB CDC ACM serial (ttyGS0)로 전환, 인터랙티브 셸 확보:

- USB gadget: configfs `acm.usb0` function, UDC `a600000.dwc3`
- host 측: `/dev/ttyACM0` → `serial_tcp_bridge.py` → `127.0.0.1:54321` TCP
- 셸 명령: help / uname / pwd / cd / ls / cat / stat / mounts / mountsystem / prepareandroid / inputinfo / inputcaps / readinput / waitkey / blindmenu / drminfo / fbinfo / kmsprobe / kmssolid / kmsframe / mkdir / mknodc / mknodb / mountfs / umount / echo / writefile / run / runandroid / startadbd / stopadbd / sync / reboot / recovery / poweroff

**v15 → v22 주요 추가:**
- DRM/KMS 직접 제어: `drm.h` / `drm_mode.h` ioctl 기반 (`CREATE_DUMB`, `ADDFB`, `MAP_DUMB`, `SETCRTC`)
- 부팅 시 DRM/fb 노드 자동 생성 (`prepare_early_display_environment`)
- `boot_auto_frame()`: ttyGS0 연결 후 자동으로 화면에 어두운 배경+테두리 표시
- `kmssolid [color]`: 단색으로 화면 채우기 (black/white/red/green/blue/gray/0xRRGGBB)
- `kmsframe`: 어두운 배경 + 테두리 프레임 렌더링
- `kmsprobe`: DRM capabilities 및 connector/encoder/crtc 탐색
- `drminfo`, `fbinfo`: sysfs 기반 DRM/framebuffer 정보 조회

**확보된 관찰/제어 범위** (probe 결과 기준):

| 항목 | 상태 |
|---|---|
| USB ACM serial 제어채널 | 작동 |
| 인터랙티브 셸 | 작동 |
| /proc, /sys, /dev 마운트 | 작동 |
| /cache (ext4) 마운트 | 작동 |
| /mnt/system (sda28, ext4 ro) | 작동 (`mountsystem`) |
| system-as-root 구조 탐색 | 작동 (`prepareandroid`) |
| 물리 버튼 입력 (power/vol+/vol-) | 작동 (`waitkey`, `blindmenu`) |
| backlight sysfs 제어 | 작동 (`writefile /sys/class/backlight/...`) |
| DRM/KMS ioctl (dumb buffer + SETCRTC) | **작동** — 실화면 출력 확인 (`kmssolid`, `kmsframe`) |
| 부팅 시 자동 화면 표시 | **작동** — ttyGS0 연결 후 자동 렌더링 확인 |
| 커널 정보 | Linux 4.14.190, SM8150, 8코어, RAM 5.2GB free |
| ADB (adbd) | **미작동** (zombie, ep1/ep2 미생성) |

**버튼 매핑** (확인됨):

| event | device | keys |
|---|---|---|
| event0 | qpnp_pon | KEY_POWER, KEY_VOLUMEDOWN |
| event3 | gpio_keys | KEY_VOLUMEUP |

### 3-3. ADB 상태

- adbd: zombie 상태로 종료
- FunctionFS: ep0만 생성, ep1/ep2 미생성
- 원인: descriptors 등록 전 adbd 종료 (Android runtime/SELinux/property 없이 adbd 단독 실행 불안정)
- 현재 방향: ACM serial을 주 채널로 유지, ADB는 `startadbd` 셸 명령으로 재시도 가능 상태로 대기

## 다음 후보 작업

우선순위 순:

1. **USB NCM IP/link setup** — device `ncm0`와 host `enx...`에 IPv4를 설정해 ping 확인
2. **Toybox netcat 실사용** — NCM 링크 위에서 `netcat` 기반 TCP 통신 확인
3. **장기 저장소 의사결정** — `userdata`/`mmcblk0p1` 사용 여부를 별도 문서로 판단
4. **screen menu 버튼 수동 검증** — VOL+/VOL-/POWER로 `STATUS`/`LOG`/복구 동작 확인
5. **adbd 안정화 재검토** — serial/RNDIS보다 가치가 커졌을 때만 재개

**복구**: `backups/baseline_a_20260423_030309/boot.img` dd 복구 가능
