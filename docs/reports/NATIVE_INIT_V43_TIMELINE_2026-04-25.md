# Native Init v43 Boot Timeline Report (2026-04-25)

`A90 Linux init v43`은 v42의 blocking cancel 정책 위에 boot readiness timeline을
추가한 후보이다. 목표는 부팅 중 어떤 커널/디바이스 리소스가 언제 준비됐는지
serial shell과 `/cache/native-init.log` 양쪽에서 확인하는 것이다.

## 산출물

- source: `stage3/linux_init/init_v43.c`
- local binary: `stage3/linux_init/init_v43`
- local ramdisk: `stage3/ramdisk_v43.cpio`
- local boot image: `stage3/boot_linux_v43.img`

SHA256:

```text
cc08cd11dce97c0dfad2350f26366f0e9efe910fe335eba5732e5d408948fdb9  stage3/linux_init/init_v43
041a17914b6fb8f6b591ed2e82c53cdfbd7866962b54f111e7888e5664c217e9  stage3/ramdisk_v43.cpio
ed290154c31bace1b65f4aff912a57f3083627bccc67bc26dfcc668bc1d52355  stage3/boot_linux_v43.img
```

## 구현 내용

- boot timeline ring 추가 (`BOOT_TIMELINE_MAX=32`)
- boot step마다 monotonic timestamp, result code, errno, detail 기록
- `timeline` shell 명령 추가
- `/cache` mount 전 `/tmp`에만 남을 수 있는 초기 timeline을 `/cache` 선택 후 replay
- resource probe 추가:
  - DRM card0
  - input event0
  - input event3
  - battery power supply
  - thermal class

## 로컬 검증

빌드:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v43 stage3/linux_init/init_v43.c
aarch64-linux-gnu-strip stage3/linux_init/init_v43
```

결과:

- compile 성공
- `-Wall -Wextra` 기준 신규 경고 없음
- boot image unpack 확인 성공
- ramdisk entries:
  - `.`
  - `init`
- boot image 내부 marker 확인:
  - `A90 Linux init v43`
  - `A90v43`
  - `timeline`
  - `resource-battery`

## 실기 검증 결과

검증 상태:

- `native_init_flash.py --from-native`로 native init → TWRP → boot flash → system boot 수행
- TWRP recovery ADB remote SHA256 일치 확인
- `twrp reboot system`으로 native init 부팅
- USB ACM serial bridge (`127.0.0.1:54321`)로 검증
- 결과: **PASS**

Flash 기록:

```text
local image sha256: ed290154c31bace1b65f4aff912a57f3083627bccc67bc26dfcc668bc1d52355
remote image sha256: ed290154c31bace1b65f4aff912a57f3083627bccc67bc26dfcc668bc1d52355
50634752 bytes copied
```

부팅 확인:

```text
version
A90 Linux init v43
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
[done] version (1ms)
```

Timeline 확인:

```text
timeline
timeline: count=15 max=32
00     1362ms init-start         rc=0 errno=0 A90 Linux init v43
01     1363ms base-mounts        rc=0 errno=0 proc/sys/dev/tmpfs requested
02     1365ms early-nodes        rc=0 errno=0 display/input/graphics nodes prepared
03     1365ms resource-drm       rc=0 errno=0 /sys/class/drm/card0 ready
04     1365ms resource-input0    rc=0 errno=0 /sys/class/input/event0 ready
05     1365ms resource-input3    rc=0 errno=0 /sys/class/input/event3 ready
06     1365ms resource-battery   rc=0 errno=0 /sys/class/power_supply/battery ready
07     1365ms resource-thermal   rc=0 errno=0 /sys/class/thermal ready
08     1369ms cache-mount        rc=0 errno=0 /cache mounted log=/cache/native-init.log
09     1374ms usb-gadget         rc=0 errno=0 ACM gadget configured
10     1376ms ttyGS0             rc=0 errno=0 /dev/ttyGS0 ready
11     1530ms display-probe      rc=0 errno=0 TEST frame applied
12     3532ms console            rc=0 errno=0 serial console attached
13     3794ms autohud            rc=0 errno=0 started refresh=2
14     3794ms shell              rc=0 errno=0 interactive shell ready
[done] timeline (0ms)
```

Log replay 확인:

```text
logcat
[1369ms] timeline: replay=cache init-start rc=0 errno=0 ms=1362 detail=A90 Linux init v43
[1369ms] timeline: replay=cache base-mounts rc=0 errno=0 ms=1363 detail=proc/sys/dev/tmpfs requested
[1369ms] timeline: replay=cache early-nodes rc=0 errno=0 ms=1365 detail=display/input/graphics nodes prepared
[1369ms] timeline: replay=cache resource-drm rc=0 errno=0 ms=1365 detail=/sys/class/drm/card0 ready
[1369ms] timeline: replay=cache resource-input0 rc=0 errno=0 ms=1365 detail=/sys/class/input/event0 ready
[1369ms] timeline: replay=cache resource-input3 rc=0 errno=0 ms=1365 detail=/sys/class/input/event3 ready
[1369ms] timeline: replay=cache resource-battery rc=0 errno=0 ms=1365 detail=/sys/class/power_supply/battery ready
[1369ms] timeline: replay=cache resource-thermal rc=0 errno=0 ms=1365 detail=/sys/class/thermal ready
```

Status 확인:

```text
status
init: A90 Linux init v43
display: 1080x2400 connector=28 crtc=133 current_buffer=0
autohud: running
[done] status (18ms)
```

## 다음 작업

- HUD boot progress/error 표시
- recovery 왕복 후 `/cache/native-init.log` 보존 확인
- `run` cancel 검증용 static helper 준비
