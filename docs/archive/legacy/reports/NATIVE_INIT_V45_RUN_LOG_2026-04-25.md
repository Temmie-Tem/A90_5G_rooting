# Native Init v45 Run Cancel and Log Preservation Report (2026-04-25)

`A90 Linux init v45`는 v44의 HUD boot summary 위에 안전한 static helper를
ramdisk에 추가해 `run` cancel 동작을 실기 검증한 후보이다. 동시에 recovery 왕복 후
`/cache/native-init.log`가 보존되는지도 확인했다.

## 산출물

- init source: `stage3/linux_init/init_v45.c`
- helper source: `stage3/linux_init/a90_sleep.c`
- local init binary: `stage3/linux_init/init_v45`
- local helper binary: `stage3/linux_init/a90_sleep`
- local ramdisk: `stage3/ramdisk_v45.cpio`
- local boot image: `stage3/boot_linux_v45.img`

SHA256:

```text
bfc433ab6e400de83e505226ad064cac076cac52d0c128a818b43a7d8ba4ffaa  stage3/linux_init/init_v45
f5b4ff7888c21ed226c0b21ab89f3b20610f72cb013c18cf67b81c991c4efe12  stage3/linux_init/a90_sleep
7cedb9da2b6e5a5db9fc3c295f214c4227f876447e1f43f9c610355707ee668b  stage3/ramdisk_v45.cpio
f52703cfe89882912969f9b25627de3f884245b5fdb7989142f4f3119f8a3190  stage3/boot_linux_v45.img
```

## 구현 내용

- `init_v45` version marker 추가
- ramdisk에 `/bin/a90sleep` static helper 포함
- helper 동작:
  - 기본 30초 sleep
  - optional seconds argument
  - 시작/종료 메시지 출력
- 기존 v42의 cancelable child wait를 `run /bin/a90sleep 30`으로 실기 검증

## 로컬 검증

빌드:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v45 stage3/linux_init/init_v45.c
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/a90_sleep stage3/linux_init/a90_sleep.c
aarch64-linux-gnu-strip stage3/linux_init/init_v45 stage3/linux_init/a90_sleep
```

결과:

- compile 성공
- `-Wall -Wextra` 기준 신규 경고 없음
- ramdisk entries:
  - `.`
  - `bin`
  - `bin/a90sleep`
  - `init`
- boot image marker 확인:
  - `A90 Linux init v45`
  - `A90v45`
  - `a90sleep: sleeping`

## 실기 검증 결과

검증 상태:

- `native_init_flash.py --from-native`로 native init → TWRP → boot flash → system boot 수행
- TWRP recovery ADB remote SHA256 일치 확인
- `twrp reboot system`으로 native init 부팅
- USB ACM serial bridge (`127.0.0.1:54321`)로 검증
- 결과: **PASS**

부팅 확인:

```text
version
A90 Linux init v45
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
[done] version (0ms)
```

Helper 확인:

```text
stat /bin/a90sleep
mode=0755 uid=0 gid=0 size=663568
[done] stat (0ms)
```

`run` cancel 확인:

```text
run /bin/a90sleep 30
run: pid=549, q/Ctrl-C cancels
a90sleep: sleeping 30 seconds
run: terminating pid=549
run: cancelled by q
[err] run rc=-125 errno=125 (Operation canceled) (900ms)

last
last: command=run code=-125 errno=125 duration=900ms flags=0x2
last: error=Operation canceled
[done] last (0ms)
```

후속 상태 확인:

```text
status
init: A90 Linux init v45
boot: BOOT OK shell 3S
autohud: running
[done] status (18ms)
```

Log preservation 확인:

```text
logcat
[1478ms] timeline: replay=cache init-start rc=0 errno=0 ms=1472 detail=A90 Linux init v44
[1479ms] boot: A90 Linux init v44 start
[1365ms] timeline: replay=cache init-start rc=0 errno=0 ms=1360 detail=A90 Linux init v45
[1366ms] boot: A90 Linux init v45 start
[31660ms] cancel: run soft q
[31660ms] cmd: end name=run rc=-125 errno=125 duration=900ms flags=0x2
```

해석:

- native init → recovery → native init 왕복 후에도 `/cache/native-init.log`가 보존됐다.
- v44 이전 boot log와 v45 boot log가 같은 파일에 append됐다.
- `run` cancel은 `SIGTERM` 후 prompt 복귀와 `errno=125` 기록까지 확인됐다.

## 다음 작업

- safe storage map report 작성
- USB gadget map report 작성
- on-screen menu draft
- BusyBox/static userland 후보 검토
