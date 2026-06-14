# Native Init v42 Blocking Cancel Report (2026-04-25)

`A90 Linux init v42`는 v41의 `/cache/native-init.log` 위에 blocking command 취소
정책을 추가한 후보이다. 목표는 오래 기다리는 명령에서 serial shell을 잃지 않고
항상 prompt로 돌아오는 것이다.

## 산출물

- source: `stage3/linux_init/init_v42.c`
- local binary: `stage3/linux_init/init_v42`
- local ramdisk: `stage3/ramdisk_v42.cpio`
- local boot image: `stage3/boot_linux_v42.img`

SHA256:

```text
2e0455fbad8a701f6334dbf58ca78d80725cfac4b2038702997f45e2e424d309  stage3/linux_init/init_v42
dc730747de4543781d14d0a488bbe2edeadab86e79e764ad83601ceac4a5fec1  stage3/ramdisk_v42.cpio
bc9d692a9edfe74abd47afc118716e81037c8833bcd35892a6faeab1f900fff7  stage3/boot_linux_v42.img
```

## 구현 내용

- 공통 console cancel helper 추가
  - `q`/`Q`: soft cancel
  - `Ctrl-C`: hard cancel
  - shell result는 `-ECANCELED` (`errno=125`)로 기록
- blocking command 안내 문구 추가
- `watchhud` cancel 처리 통일
- `readinput`을 nonblocking input poll + serial cancel poll 구조로 변경
- `waitkey`, `blindmenu` input poll에 serial cancel fd 추가
- `run`, `runandroid`에 cancelable child wait 추가
  - cancel 시 `SIGTERM`
  - timeout 후 `SIGKILL`
- cancel event를 `/cache/native-init.log`에 기록

## 로컬 검증

빌드:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v42 stage3/linux_init/init_v42.c
aarch64-linux-gnu-strip stage3/linux_init/init_v42
```

결과:

- compile 성공
- `-Wall -Wextra` 기준 신규 경고 없음
- boot image unpack 확인 성공
- ramdisk entries:
  - `.`
  - `init`
- boot image 내부 marker 확인:
  - `A90 Linux init v42`
  - `A90v42`
  - `q/Ctrl-C cancels`
  - `/cache/native-init.log`

## 실기 검증 결과

검증 상태:

- `native_init_flash.py --from-native`로 native init → TWRP → boot flash → system boot 수행
- TWRP recovery ADB remote SHA256 일치 확인
- `twrp reboot system`으로 native init 부팅
- USB ACM serial bridge (`127.0.0.1:54321`)로 검증
- 결과: **PASS**

Flash 기록:

```text
local image sha256: bc9d692a9edfe74abd47afc118716e81037c8833bcd35892a6faeab1f900fff7
remote image sha256: bc9d692a9edfe74abd47afc118716e81037c8833bcd35892a6faeab1f900fff7
50634752 bytes copied
```

부팅 확인:

```text
version
A90 Linux init v42
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
[done] version (0ms)
```

취소 검증:

```text
waitkey 10
waitkey: waiting for 10 key press(es), q/Ctrl-C cancels
waitkey: cancelled by q
[err] waitkey rc=-125 errno=125 (Operation canceled) (500ms)

readinput event0 100
readinput: waiting on /dev/input/event0 (100 events), q/Ctrl-C cancels
readinput: cancelled by q
[err] readinput rc=-125 errno=125 (Operation canceled) (499ms)

watchhud 1 10
watchhud: refresh=1s count=10, q/Ctrl-C cancels
watchhud: cancelled by q
[err] watchhud rc=-125 errno=125 (Operation canceled) (1000ms)

blindmenu
blindmenu: VOLUP=prev VOLDOWN=next POWER=select q/Ctrl-C=cancel
blindmenu: cancelled by q
[err] blindmenu rc=-125 errno=125 (Operation canceled) (500ms)

waitkey 10
waitkey: cancelled by Ctrl-C
[err] waitkey rc=-125 errno=125 (Operation canceled) (500ms)
```

후속 shell 확인:

```text
last
last: command=waitkey code=-125 errno=125 duration=500ms flags=0x2
last: error=Operation canceled
[done] last (0ms)

status
init: A90 Linux init v42
[done] status (17ms)

autohud 2
autohud: pid=546 refresh=2s
[done] autohud (1ms)
```

로그 확인:

```text
cancel: waitkey soft q
cmd: end name=waitkey rc=-125 errno=125 duration=500ms flags=0x2
cancel: readinput soft q
cmd: end name=readinput rc=-125 errno=125 duration=499ms flags=0x2
cancel: watchhud soft q
cmd: end name=watchhud rc=-125 errno=125 duration=1000ms flags=0x3
cancel: blindmenu soft q
cmd: end name=blindmenu rc=-125 errno=125 duration=500ms flags=0x6
cancel: waitkey hard Ctrl-C
cmd: end name=waitkey rc=-125 errno=125 duration=500ms flags=0x2
```

## 범위와 남은 점

- `waitkey`, `readinput`, `watchhud`, `blindmenu`는 실기 cancel 검증 완료
- `run`, `runandroid`는 cancelable child wait 코드가 들어갔지만,
  현재 native init 환경에 안전한 long-running static test binary가 없어 실기 cancel은 보류
- 다음 검증에서 `/cache/bin/sleep` 같은 static helper를 준비하면 `run` cancel을 확인할 수 있음

## 다음 작업

- boot readiness timeline 자동 기록
- HUD에 boot progress/error 표시
- recovery 왕복 후 `/cache/native-init.log` 보존 확인
- safe storage map report 작성
