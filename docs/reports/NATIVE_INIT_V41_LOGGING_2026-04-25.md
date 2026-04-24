# Native Init v41 Logging Report (2026-04-25)

`A90 Linux init v41`은 v40의 shell result 정밀화 위에 파일 로그 계층을 추가한
후보이다. 목표는 serial이 끊기거나 화면만 남아도 부팅 진행, 명령 결과, 실패 원인을
나중에 확인할 수 있게 만드는 것이다.

## 산출물

- source: `stage3/linux_init/init_v41.c`
- local binary: `stage3/linux_init/init_v41`
- local ramdisk: `stage3/ramdisk_v41.cpio`
- local boot image: `stage3/boot_linux_v41.img`

SHA256:

```text
8cc901b12802371606b901663df5b6125934f28449540f035a0d7caa0dfbeec8  stage3/linux_init/init_v41
4439e4599fc2de5e6e5cc3d690389bc7b012dc9893fdaaf1c279a11f447e3586  stage3/ramdisk_v41.cpio
b2bd3f8dceea4a09048b4d55789db8d754f76226eb05a4dc03e20e9bb2dc9633  stage3/boot_linux_v41.img
```

## 구현 내용

- `/cache/native-init.log` 우선 파일 로그 추가
- `/cache` mount 실패 시 `/tmp/native-init.log` fallback
- 로그 크기 256 KiB 초과 시 `.1`로 단순 rotate
- `logpath`, `logcat` shell 명령 추가
- boot step, display probe, serial attach, autohud start 기록
- command start/end, result code, errno, duration 기록
- `sda28`, `sda31` 블록 노드를 `/sys/class/block/<name>/dev`에서 동적으로 생성

## 중간 발견

초기 v41 후보는 `/cache`가 아니라 `/tmp/native-init.log`로 fallback 됐다.
로그에는 다음처럼 남았다.

```text
boot: cache mount failed errno=30 error=Read-only file system log=/tmp/native-init.log
```

원인은 `mount_cache()`가 `sda31 = 259:15`를 고정해서 만들던 오래된 코드였다.
이번 부팅의 실제 `/proc/partitions`에서는 `sda31 = 259:34`였고, 잘못 만든
`/dev/block/sda31`은 다른 파티션을 가리켰다.

수정 후 `sda28` system과 `sda31` cache 모두 sysfs의 현재 major/minor를 읽어
노드를 만들도록 변경했다.

## 로컬 검증

빌드:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v41 stage3/linux_init/init_v41.c
aarch64-linux-gnu-strip stage3/linux_init/init_v41
```

결과:

- compile 성공
- `-Wall -Wextra` 기준 신규 경고 없음
- boot image unpack 확인 성공
- ramdisk entries:
  - `.`
  - `init`
- boot image 내부 marker 확인:
  - `A90 Linux init v41`
  - `A90v41`
  - `/cache/native-init.log`
  - `/sys/class/block/%s/dev`

## 실기 검증 결과

검증 상태:

- `native_init_flash.py --from-native`로 native init → TWRP → boot flash → system boot 수행
- TWRP recovery ADB remote SHA256 일치 확인
- `twrp reboot system`으로 native init 부팅
- USB ACM serial bridge (`127.0.0.1:54321`)로 검증
- 결과: **PASS**

Flash 기록:

```text
local image sha256: b2bd3f8dceea4a09048b4d55789db8d754f76226eb05a4dc03e20e9bb2dc9633
remote image sha256: b2bd3f8dceea4a09048b4d55789db8d754f76226eb05a4dc03e20e9bb2dc9633
50634752 bytes copied
```

부팅 확인:

```text
version
A90 Linux init v41
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
[done] version (0ms)
```

로그 경로 확인:

```text
logpath
log: path=/cache/native-init.log ready=yes max=262144
[done] logpath (0ms)

stat /cache/native-init.log
mode=0644 uid=0 gid=0 size=675
[done] stat (1ms)
```

Mount 확인:

```text
mounts
/dev/block/sda31 /cache ext4 rw,relatime,i_version 0 0
[done] mounts (0ms)

mountsystem ro
mountsystem: /mnt/system ready (ro)
[done] mountsystem (7ms)
```

로그 내용 샘플:

```text
[1358ms] boot: A90 Linux init v41 start
[1358ms] boot: base mounts ready
[1358ms] boot: early display/input nodes prepared
[1358ms] boot: cache mounted log=/cache/native-init.log
[1363ms] boot: ACM gadget configured
[1365ms] boot: ttyGS0 ready
[1527ms] boot: display test probe applied
[3530ms] boot: console attached
[3791ms] boot: autohud started refresh=2
[3791ms] boot: entering shell
[22069ms] cmd: start name=cat argc=2 flags=0x0
[22069ms] cmd: end name=cat rc=-2 errno=2 duration=0ms flags=0x0
```

## 다음 작업

- blocking command 취소 정책 통일
- boot readiness timeline을 HUD에도 표시
- `/cache` safe storage map 문서화
- log preservation을 recovery 왕복 후 별도 재확인
