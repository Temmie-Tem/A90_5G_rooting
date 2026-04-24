# Native Init v39 Status (2026-04-25)

이 문서는 Samsung A90 5G (`SM-A908N`)에서 Android userspace 대신
커스텀 static `/init`를 실행하는 Stage 3 native init 실험의 최신 상태를
`init_v39` 기준으로 정리한 기록이다.

현재 주 통신 채널은 ADB가 아니라 USB CDC ACM serial이다.
Host에서는 `scripts/revalidation/serial_tcp_bridge.py`로 `/dev/ttyACM0`를
`127.0.0.1:54321` TCP로 브릿지해 사용한다.

---

## 요약

- 최신 실기 확인 버전: `A90 Linux init v39`
- 최신 소스: `stage3/linux_init/init_v39.c`
- 최신 boot image: `stage3/boot_linux_v39.img`
- boot image SHA256:
  - `629f81ecdb222cf386c9e1cb0c1e4fd0c2106d313a68b6386273bc99d5b71102`
- 부팅 흐름:
  1. stock Android kernel 부팅
  2. ramdisk의 커스텀 `/init` 실행
  3. USB ACM serial console 준비
  4. KMS TEST 패턴 약 2초 표시
  5. 상태 HUD 자동 전환
  6. `autohud 2` 주기 갱신 유지
  7. serial shell prompt 제공
- ADB 안정화는 보류. 현재는 ACM serial을 주 제어 채널로 유지한다.

---

## 부팅 구조

현재 실험은 커널 자체를 교체하지 않고, boot image ramdisk의 `/init`를
커스텀 static ARM64 init로 교체하는 방식이다.

- kernel:
  - `Linux 4.14.190-25818860-abA908NKSU5EWA3`
- machine:
  - `aarch64`
- boot image header/offset/cmdline은 기존 실기 검증 이미지 계열을 유지한다.
- Android framework/init은 실행하지 않는다.
- PID 1은 `stage3/linux_init/init_v39.c`에서 빌드한 native init이다.

복구는 TWRP에서 known-good boot image를 `boot` 파티션에 다시 dd하여 수행한다.

---

## Serial 제어 채널

### Device side

- USB gadget configfs 기반 ACM function 사용
- `/dev/ttyGS0`를 init shell의 stdin/stdout/stderr로 attach
- boot 이후 host에는 `/dev/ttyACM0`로 노출

### Host side

브릿지 실행:

```bash
sudo python3 ./scripts/revalidation/serial_tcp_bridge.py --port 54321
```

접속:

```bash
nc 127.0.0.1 54321
```

권장 콘솔:

```bash
python3 ./scripts/revalidation/serial_console.py --port 54321
```

주의:

- 브릿지는 클라이언트 1개만 허용한다.
- `nc`, `serial_console.py`, 자동 probe 스크립트를 동시에 붙이면 충돌할 수 있다.
- host 계정에 `dialout` 권한이 없으면 브릿지는 `sudo`가 필요하다.

---

## Shell 상태

v36부터 긴 `if/else` dispatch를 command table 기반으로 리팩터링했다.
v37부터 serial attach 직후 입력 drain과 startup sync를 보강했다.
v39에서는 startup banner를 `#` 주석형으로 바꾸고, shell이 `#` 라인과
`a90:` prompt 반향을 무시하도록 했다.

### 확인된 기본 명령

- `help`
- `version`
- `status`
- `last`
- `uname`
- `pwd`
- `cd`
- `ls`
- `cat`
- `stat`
- `mounts`
- `mountsystem [ro|rw]`
- `prepareandroid`
- `sync`
- `reboot`
- `recovery`
- `poweroff`

### Shell observability

- 정상 완료:
  - `[done] <cmd> (<ms>)`
- unknown command:
  - `[err] unknown command: <cmd>`
- `last`:
  - 마지막 명령명
  - result code
  - errno
  - duration
  - command flags

실기 확인 예:

```text
version
A90 Linux init v39
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
[done] version (0ms)
```

```text
status
init: A90 Linux init v39
battery: 100% Full temp=31.7C voltage=4323mV
power: now=0.4W? avg=0.4W?
thermal: cpu=37.3C gpu=35.5C
memory: 250/5375MB used
display: 1080x2400 connector=28 crtc=133 current_buffer=0
adbd: stopped
autohud: running
[done] status (18ms)
```

---

## Display / KMS

v39는 DRM/KMS dumb framebuffer를 직접 생성하고 `DRM_IOCTL_MODE_SETCRTC`로
화면을 표시한다.

확인된 display path:

- resolution: `1080x2400`
- connector: `28`
- crtc: `133`
- dumb buffer: 사용 가능
- page flip: 이전 실험에서 `Inappropriate ioctl for device`로 실패
- 현재 방식: double buffer + `SETCRTC` 기반 present

### 부팅 화면 시퀀스

v39의 자동 화면 흐름:

1. `boot_auto_frame()`에서 TEST 패턴 표시
2. `BOOT_TEST_SECONDS` 동안 유지 (현재 2초)
3. console attach 이후 `start_auto_hud(BOOT_HUD_REFRESH_SECONDS)` 호출
4. 상태 HUD가 자동 갱신됨 (현재 2초 주기)

실기 확인:

- TEST 패턴 표시 확인
- 약 2초 후 상태 HUD 전환 확인
- `status`에서 `autohud: running` 확인

---

## HUD 표시 정보

현재 HUD는 5x7 bitmap font를 software rendering으로 확대하여 그린다.
텍스트 콘솔이나 font engine이 아니라, 내부 비트맵 glyph를 framebuffer에
사각형 픽셀 블록으로 그리는 방식이다.

표시 항목:

- init name / uptime
- battery percent / battery temperature
- CPU thermal average
- GPU thermal average
- memory used / total
- load average
- estimated power now / avg
- refresh seconds
- sequence counter

전력값 주의:

- `power_now`, `power_avg`가 존재한다.
- 현재 표시값은 `0.4W?`처럼 `?`를 붙인다.
- Samsung vendor sysfs 단위가 표준 power_supply 문서의 µW와 다르게 보일 수 있어
  아직 추정값으로 취급한다.

---

## Input / Button

물리 버튼 입력은 evdev로 확인되었다.

| event | device | keys |
|---|---|---|
| `event0` | `qpnp_pon` | `KEY_POWER`, `KEY_VOLUMEDOWN` |
| `event3` | `gpio_keys` | `KEY_VOLUMEUP` |

사용 가능한 명령:

- `inputinfo [eventX]`
- `inputcaps <eventX>`
- `readinput <eventX> [count]`
- `waitkey [count]`
- `blindmenu` / `menu`

현재 `blindmenu`는 serial 기반 텍스트 안내 메뉴이며,
화면 기반 버튼 UI는 아직 구현하지 않았다.

---

## Android / ADB 상태

ADB는 현재 우선순위에서 제외했다.

확인된 이전 상태:

- `startadbd` 명령은 존재
- `adbd`는 zombie로 종료되는 케이스가 있음
- FunctionFS는 `ep0`만 생성되고 `ep1`/`ep2`가 생성되지 않음
- Android property service, SELinux context, bionic/apex runtime 환경 없이
  stock Android `adbd`를 단독 실행하는 것은 불안정

현재 판단:

- 주 제어 채널은 USB ACM serial
- ADB 안정화는 추후 과제
- 당장 다음 개선은 shell/HUD/log/on-screen menu 쪽이 우선

---

## 알려진 한계

- 일반 Linux 서버 환경은 아님
  - 네트워크 없음
  - SSH 없음
  - init/service manager 없음
  - package manager 없음
- shell은 custom minimal shell
  - pipe/redirection 없음
  - quote parsing 없음
  - command history 없음
- 많은 legacy `cmd_*` 함수는 내부 실패를 아직 구조적으로 반환하지 않는다.
  - v36에서 command table과 result wrapper는 들어갔지만,
    모든 명령의 정확한 return code 전파는 아직 미완성이다.
- blocking 명령 취소/timeout 정책은 일부만 구현됨
  - `watchhud`: `q`/`Ctrl-C` 지원
  - `waitkey`, `blindmenu`, `readinput`, `run`: 추가 개선 필요
- display 명령은 `autohud`를 stop한다.
  - pause/resume이 아니라 stop 정책이다.

---

## 다음 우선순위 후보

1. **shell return code 정밀화**
   - display/mount/file/input 명령부터 `int` 반환화
   - `[done]` 의미를 실제 성공으로 더 가깝게 만들기
2. **파일 로그 추가**
   - `/cache/native-init.log`
   - boot step, command result, errno, duration 기록
3. **blocking 명령 취소 정책 통일**
   - `q`/`Ctrl-C`/timeout
   - `waitkey`, `readinput`, `blindmenu`, `run`
4. **on-screen menu**
   - `blindmenu`를 실제 화면 UI로 확장
   - VOL+/VOL-/POWER 조작 표시
5. **networking 검토**
   - ADB보다 RNDIS/NCM + SSH/dropbear가 더 현실적인지 별도 판단

---

## 관련 커밋

- `4ff283f` — `Refactor native init shell dispatch`
- `0aeefe7` — `Stabilize native init serial startup`
- `1505435` — `Add native init boot HUD sequence`
- `f1f1e73` — `Update native init project status`

---

## 현재 결론

v39 기준으로 native init 환경은 단순 proof-of-concept를 넘어,
화면/HUD/serial shell/버튼 입력이 결합된 최소 임베디드 콘솔 단계에 도달했다.

다음 단계는 새 하드웨어 기능을 늘리기보다,
명령 결과 정확도, 로그, blocking command 취소, 화면 메뉴 같은 운영 안정성을
높이는 방향이 적절하다.
