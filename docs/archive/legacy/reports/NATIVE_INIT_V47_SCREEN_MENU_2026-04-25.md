# Native Init v47 Screen Menu (2026-04-25)

`A90 Linux init v47`는 v45/v46 기준 위에 화면 기반 메뉴 초안을 추가한 버전이다.
목표는 serial 없이도 VOL+/VOL-/POWER 버튼만으로 상태 확인과 복구 동작을 선택할 수
있는 최소 UI를 만드는 것이다.

## 산출물

- init source: `stage3/linux_init/init_v47.c`
- helper source: `stage3/linux_init/a90_sleep.c`
- local init binary: `stage3/linux_init/init_v47`
- local helper binary: `stage3/linux_init/a90_sleep`
- local ramdisk: `stage3/ramdisk_v47.cpio`
- local boot image: `stage3/boot_linux_v47.img`

SHA256:

```text
6932a21fac56130a787de48588c7a3203115fb1d8e4e854d7292ad287ca3fc43  stage3/linux_init/init_v47
f5b4ff7888c21ed226c0b21ab89f3b20610f72cb013c18cf67b81c991c4efe12  stage3/linux_init/a90_sleep
44aa42b0d0feb106a215f57f670b7e28657e097be89f8bdd476eec681d8ed922  stage3/ramdisk_v47.cpio
fb878668fb4267703417d47d61a704be3322792950e779e2adc28f01221691c8  stage3/boot_linux_v47.img
```

## 구현 내용

- `menu`와 `screenmenu` 명령을 화면 렌더링 메뉴로 연결
- 기존 `blindmenu`는 serial-only fallback으로 유지
- 메뉴 항목:
  - `RESUME`
  - `STATUS`
  - `LOG`
  - `RECOVERY`
  - `REBOOT`
  - `POWEROFF`
- 조작:
  - VOLUP: 이전 항목
  - VOLDOWN: 다음 항목
  - POWER: 선택
  - serial `q`/Ctrl-C: 취소
- `STATUS`는 기존 sensor HUD를 표시한 뒤 버튼 입력으로 메뉴에 복귀
- `LOG`는 boot summary, log readiness, last command/result, log path를 화면에 표시
- 메뉴 진입 시 autohud를 멈추고, resume/cancel 시 기존 autohud가 켜져 있었다면 복구

## 로컬 검증

빌드:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v47 stage3/linux_init/init_v47.c
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/a90_sleep stage3/linux_init/a90_sleep.c
aarch64-linux-gnu-strip stage3/linux_init/init_v47 stage3/linux_init/a90_sleep
```

결과:

- compile 성공
- `-Wall -Wextra` 기준 신규 경고 없음
- `stage3/ramdisk_v47.cpio` entries:
  - `.`
  - `bin`
  - `bin/a90sleep`
  - `init`
- boot image marker 확인:
  - `A90 Linux init v47`
  - `A90v47`
  - `A90 SCREEN MENU`
  - `screenmenu`
  - `a90sleep: sleeping`

## 실기 검증 결과

검증 상태:

- `native_init_flash.py --from-native`로 native init v45 → TWRP → v47 boot flash → system boot 수행
- TWRP recovery ADB remote SHA256 일치 확인
- `twrp reboot system`으로 native init v47 부팅
- USB ACM serial bridge (`127.0.0.1:54321`)로 검증
- 결과: **PASS**

확인 출력:

```text
A90 Linux init v47
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
```

`menu` 진입 후 serial `q` 취소:

```text
screenmenu: VOLUP=prev VOLDOWN=next POWER=select q/Ctrl-C=cancel
screenmenu: [1/6] RESUME - RETURN TO HUD
screenmenu: presented framebuffer 1080x2400 on crtc=133
screenmenu: cancelled by q
[err] menu rc=-125 errno=125 (Operation canceled) (212ms)
```

취소 후 상태:

```text
init: A90 Linux init v47
boot: BOOT OK shell 3S
display: 1080x2400 connector=28 crtc=133 current_buffer=1
adbd: stopped
autohud: running
```

## 남은 확인

- 실제 버튼으로 VOLUP/VOLDOWN 이동 확인
- POWER로 `STATUS`와 `LOG` 화면 진입/복귀 확인
- 위험 동작인 `RECOVERY`, `REBOOT`, `POWEROFF`는 의도한 순간에만 수동 검증
- 메뉴 화면의 문구/크기/위치가 장시간 사용에도 잘 보이는지 조정

