# Native Init v44 HUD Boot Summary Report (2026-04-25)

`A90 Linux init v44`는 v43의 boot readiness timeline을 HUD와 shell 상태 출력에
연결한 후보이다. 목표는 화면에 현재 boot 상태가 `BOOT OK ...` 또는
`BOOT ERR ...` 형태로 직접 보이게 하는 것이다.

## 산출물

- source: `stage3/linux_init/init_v44.c`
- local binary: `stage3/linux_init/init_v44`
- local ramdisk: `stage3/ramdisk_v44.cpio`
- local boot image: `stage3/boot_linux_v44.img`

SHA256:

```text
e205962d57e784a6527646f2db89863c701b9295192f1de6289ca0ed7e3904cf  stage3/linux_init/init_v44
b72e214a708e6ad5307425af99611980392b6647909b9ef1d14a7a5148c20188  stage3/ramdisk_v44.cpio
2b77560248835b35a1041aeaf4e59f4ea146d76956374f3ebf0f879b457d4477  stage3/boot_linux_v44.img
```

## 구현 내용

- timeline 기반 boot summary helper 추가
  - 정상: `BOOT OK <last-step> <sec>S`
  - 실패: `BOOT ERR <step> E<errno>`
- HUD 첫 줄과 footer에 boot summary 표시
- `status` 출력에 boot summary 추가
- `bootstatus` shell 명령 추가

## 로컬 검증

빌드:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v44 stage3/linux_init/init_v44.c
aarch64-linux-gnu-strip stage3/linux_init/init_v44
```

결과:

- compile 성공
- `-Wall -Wextra` 기준 신규 경고 없음
- boot image unpack 확인 성공
- boot image marker 확인:
  - `A90 Linux init v44`
  - `A90v44`
  - `BOOT OK`
  - `bootstatus`

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
A90 Linux init v44
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
[done] version (0ms)
```

Boot summary 확인:

```text
bootstatus
boot: BOOT OK shell 3S
timeline_entries: 15/32
[done] bootstatus (0ms)

status
init: A90 Linux init v44
boot: BOOT OK shell 3S
display: 1080x2400 connector=28 crtc=133 current_buffer=0
autohud: running
[done] status (17ms)
```

HUD draw 확인:

```text
statushud
statushud: drawing sensor HUD
statushud: presented framebuffer 1080x2400 on crtc=133
[done] statushud (28ms)

autohud 2
autohud: pid=549 refresh=2s
[done] autohud (0ms)
```

## 다음 작업

- recovery 왕복 후 `/cache/native-init.log` 보존 확인
- `run` cancel 검증용 static helper 준비
- safe storage map report 작성
