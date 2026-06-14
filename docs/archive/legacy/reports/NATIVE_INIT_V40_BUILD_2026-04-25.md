# Native Init v40 Build and Device Verification (2026-04-25)

이 문서는 `A90 Linux init v40`의 변경점, 빌드 산출물, 실기 검증 결과를 기록한다.

`v40`은 새 하드웨어 기능을 늘리는 버전이 아니라,
`v39` 이후 첫 번째 운영 안정성 작업인 **shell return code 정밀화**를 적용한 버전이다.

---

## 산출물

- source: `stage3/linux_init/init_v40.c`
- local binary: `stage3/linux_init/init_v40`
- local ramdisk: `stage3/ramdisk_v40.cpio`
- local boot image: `stage3/boot_linux_v40.img`

SHA256:

- `stage3/linux_init/init_v40`
  - `dd4fbbe3acdc31817be382b27776d8e144585283ea596f08056422b07744b0d0`
- `stage3/ramdisk_v40.cpio`
  - `e6aed1364ac1a6df864532e5b7e295b11bd4810040a8e03861f731745cb38972`
- `stage3/boot_linux_v40.img`
  - `3356bbec44a68413327a15d95856eea691f08b66814e6ca9925e90ef83be1995`

주의:

- `stage3/linux_init/init_v40`, `stage3/ramdisk_v40.cpio`,
  `stage3/boot_linux_v40.img`, `stage3/ramdisk_v40/`는 local generated artifact이며
  `.gitignore` 대상이다.
- git에는 `stage3/linux_init/init_v40.c`와 이 보고서만 기록한다.

---

## 변경 목표

기존 `v39`는 command table과 `[done]`/`[err]` wrapper가 있었지만,
여러 `cmd_*` 함수가 내부 실패를 출력만 하고 handler에는 `0`을 반환했다.

그 결과:

- `cat /missing`처럼 실패한 명령도 `[done] cat`으로 보일 수 있음
- `last`의 `code`, `errno`가 실제 실패와 어긋날 수 있음
- 이후 로그/메뉴/자동화에서 명령 성공 여부를 신뢰하기 어려움

`v40`의 목표:

- 실패한 syscall/open/mount/ioctl/exec 결과를 shell result로 올린다.
- usage error는 `-EINVAL`로 반환한다.
- 외부 process exit code는 positive `rc`로 보존한다.
- negative errno와 positive process rc를 shell 출력에서 구분한다.

---

## 주요 변경점

### 1. 공통 helper

- `negative_errno_or(fallback_errno)` 추가
  - `errno`가 설정되어 있으면 `-errno` 반환
  - `errno`가 0이면 fallback errno 반환
- `write_all_checked()` 추가
  - file write path에서 write 실패를 감지하기 위한 checked writer

### 2. shell result 출력

negative errno:

```text
[err] cat rc=-2 errno=2 (No such file or directory) (0ms)
```

positive process rc:

```text
[err] run rc=127 (1ms)
```

성공:

```text
[done] status (0ms)
```

### 3. return code 전환 대상

우선 전환한 명령군:

- file:
  - `ls`
  - `cat`
  - `stat`
  - `writefile`
- mount/layout:
  - `mounts`
  - `mountsystem`
  - `prepareandroid`
  - `mountfs`
  - `umount`
- display:
  - `kmsprobe`
  - `kmssolid`
  - `kmsframe`
  - `statusscreen`
  - `statushud`
  - `watchhud`
  - `autohud`
  - `stophud`
  - `clear`
- input:
  - `inputinfo`
  - `inputcaps`
  - `readinput`
  - `waitkey`
  - `blindmenu`
- process:
  - `run`
  - `runandroid`
  - `startadbd`
  - `stopadbd`

---

## 로컬 검증

빌드:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v40 stage3/linux_init/init_v40.c
aarch64-linux-gnu-strip stage3/linux_init/init_v40
```

결과:

- compile 성공
- `-Wall -Wextra` 기준 신규 경고 없음
- boot image unpack 확인 성공
- ramdisk entries:
  - `.`
  - `init`
- boot image 내부 marker 확인:
  - `A90 Linux init v40`
  - `A90v40`

---

## 실기 검증 결과

검증 상태:

- TWRP recovery ADB로 `stage3/boot_linux_v40.img`를 boot 파티션에 기록
- `twrp reboot system`으로 native init 부팅
- USB ACM serial bridge (`127.0.0.1:54321`)로 검증
- 결과: **PASS**

Flash 기록:

```text
stage3/boot_linux_v40.img: 1 file pushed
3356bbec44a68413327a15d95856eea691f08b66814e6ca9925e90ef83be1995  /tmp/boot_linux_v40.img
50630656 bytes copied
```

부팅 확인:

```text
version
A90 Linux init v40
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
[done] version (0ms)
```

성공 명령 확인:

```text
status
[done] status (18ms)

ls /
[done] ls (1ms)

stat /proc
[done] stat (0ms)

mounts
[done] mounts (0ms)
```

실패 명령 확인:

```text
cat /definitely-missing
[err] cat rc=-2 errno=2 (No such file or directory) (0ms)

stat /definitely-missing
[err] stat rc=-2 errno=2 (No such file or directory) (0ms)

mountsystem nope
[err] mountsystem rc=-22 errno=22 (Invalid argument) (0ms)

kmssolid nope
[err] kmssolid rc=-22 errno=22 (Invalid argument) (0ms)

writefile /definitely-missing/path value
[err] writefile rc=-2 errno=2 (No such file or directory) (0ms)

run /definitely-missing
[exit 127]
[err] run rc=127 (1ms)

last
last: command=run code=127 errno=0 duration=1ms flags=0x2
[done] last (0ms)
```

Display/HUD 확인:

```text
statushud
[done] statushud (29ms)

clear
[done] clear (8ms)

autohud 2
[done] autohud (0ms)
```

Input/mount/sysfs 확인:

```text
inputinfo
[done] inputinfo (1ms)

inputcaps event0
KEY_VOLUMEDOWN(114)=yes
KEY_POWER(116)=yes
[done] inputcaps (0ms)

inputcaps event3
KEY_VOLUMEUP(115)=yes
[done] inputcaps (0ms)

kmsprobe
[done] kmsprobe (0ms)

mountsystem ro
[done] mountsystem (8ms)

writefile /sys/class/backlight/panel0-backlight/brightness 200
[done] writefile (2ms)
```

관찰:

- `writefile`은 현재 `O_WRONLY`로 기존 path를 여는 동작이다.
  - sysfs/backlight 같은 기존 파일 쓰기는 성공했다.
  - `/cache/v40_probe`처럼 새 regular file 생성은 실패한다.
  - 새 파일 생성용 명령은 추후 `touch`/`writefile-create`/로그 구현에서 별도로 다룬다.
- TWRP/system 전환 중 host-side 자동화에서 두 가지 주의점이 확인됐다.
  - `adb devices`의 state 판정은 `grep -E '\t...'` 대신 whitespace split/`awk` 방식으로 해야 한다.
  - TWRP에서 system boot 요청은 `adb shell reboot system`보다 `adb shell twrp reboot system`이 안정적이다.
  - serial device가 없는 동안 bridge client가 먼저 붙으면 명령이 유실될 수 있으므로,
    `serial_tcp_bridge.py`는 serial 미연결 시 client를 거절하도록 보강했다.
  - 재사용 헬퍼: `scripts/revalidation/native_init_flash.py`
- `waitkey`는 이번 자동 검증에서 제외했다.
  - 버튼 입력이 필요한 수동 검증 항목으로 유지한다.
- `kmssolid nope`는 display command라 autohud를 중단하지만,
  이후 `autohud 2`로 정상 복구됨을 확인했다.

---

## 실기 검증 체크리스트

TWRP에서 `stage3/boot_linux_v40.img`를 boot 파티션에 기록한 뒤 system boot했다.

부팅 확인:

```text
version
```

기대:

```text
A90 Linux init v40
[done] version
```

성공 명령:

```text
status
ls /
stat /proc
mounts
```

기대:

```text
[done] status
[done] ls
[done] stat
[done] mounts
```

실패 명령:

```text
cat /definitely-missing
stat /definitely-missing
mountsystem nope
kmssolid nope
writefile /definitely-missing/path value
run /definitely-missing
last
```

기대:

- `cat`, `stat`은 `errno=2`
- `mountsystem nope`, `kmssolid nope`는 `errno=22`
- `writefile`은 open 실패 errno를 보고
- `run /definitely-missing`은 child exit `127`을 positive rc로 보고
- `last`는 마지막 실패 command/result/duration을 표시

화면 명령:

```text
statushud
clear
autohud 2
stophud
```

기대:

- 정상 출력 시 `[done]`
- KMS 실패 시 `[err]`로 전파

입력 명령:

```text
inputinfo
inputcaps event0
inputcaps event3
waitkey 1
```

기대:

- event node open 실패 시 `[err]`
- 정상 입력 시 `[done] waitkey`

---

## 다음 단계

v40 실기 검증이 통과했으므로 다음 순서로 진행한다.

1. `/cache/native-init.log` 추가
2. boot readiness timeline 기록
3. blocking command 취소 정책 통일
4. HUD boot progress/error 표시

추후 regression이 있으면 `v39`를 기준으로 되돌리고,
해당 명령군만 작은 패치로 분리한다.
