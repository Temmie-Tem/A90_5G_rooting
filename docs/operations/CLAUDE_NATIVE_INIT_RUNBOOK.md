# Claude / Agent Native Init Operations Runbook

Date: `2026-04-25`

이 문서는 Claude나 다른 에이전트가 이 저장소에서 같은 실수를 반복하지 않도록 남기는
운영 설명서다. 핵심은 **브릿지로 현재 상태를 먼저 확인하고, TWRP/boot image/serial rescue
경로를 잃지 않는 것**이다.

## 0. 현재 기준점

현재 기준:

- device: `Samsung Galaxy A90 5G SM-A908N`
- recovery: TWRP 사용 가능
- latest verified native init: `A90 Linux init v48`
- latest source: `stage3/linux_init/init_v48.c`
- latest boot image: `stage3/boot_linux_v48.img`
- primary control channel: USB CDC ACM serial
- host bridge: `127.0.0.1:54321`
- bridge script: `scripts/revalidation/serial_tcp_bridge.py`
- safe persistent area: `/cache`
- toybox on device: `/cache/bin/toybox`
- USB helper on device: `/cache/bin/a90_usbnet`

중요한 v48 개선:

- USB ACM rebind 후 native init이 `/dev/ttyGS0`를 다시 attach한다.
- `usbacmreset` 명령이 있다.
- `a90_usbnet probe-ncm`으로 host `cdc_ncm`, device `ncm0` 확인 완료.
- ADB는 후순위다. 기본 제어 채널은 serial bridge다.

v49 주의:

- `stage3/boot_linux_v49.img`는 local marker와 boot partition prefix readback은 맞았지만
  system boot 후 Android `/system/bin/init second_stage`로 진입했다.
- 현재 v49는 격리된 실패 실험이다.
- 새 실험 버전은 v48에서 최소 diff로 시작하되, 번호는 v50 이상을 사용한다.
- Claude는 v49를 stable이나 다음 기준으로 삼으면 안 된다.

## 1. 절대 원칙

### 하지 말 것

- `boot`, `recovery`, `vbmeta`, `efs`, `sec_efs`, modem, persist, key/security 계열 파티션을 추측으로 쓰지 말 것.
- `userdata`를 포맷하거나 마운트 rw로 쓰지 말 것.
- host에 `/dev/ttyACM0`가 보인다고 native init shell이 살아 있다고 단정하지 말 것.
- bridge 응답이 없다고 곧바로 다시 flash하지 말 것.
- USB gadget rebind 실험을 v47 이하에서 오래 반복하지 말 것. v48 이후를 기준으로 한다.
- ADB를 먼저 살리려고 시간을 쓰지 말 것. 현재는 serial + NCM이 더 현실적인 경로다.

### 먼저 할 것

1. `git status --short`로 기존 변경사항을 확인한다.
2. bridge `version`을 확인한다.
3. 안 되면 host USB 상태와 TWRP ADB 상태를 확인한다.
4. flash가 필요하면 반드시 TWRP ADB에서 local/remote SHA256을 확인한다.
5. 실험 후에는 `/cache/native-init.log`, `/cache/usbnet.log`를 확인한다.

## 2. Bridge 사용법

브릿지는 사용자가 보통 sudo로 실행한다.

```bash
sudo python3 ./scripts/revalidation/serial_tcp_bridge.py --port 54321
```

에이전트가 sudo를 직접 못 쓰는 환경이면 사용자에게 재시작을 요청한다.

```bash
sudo pkill -f serial_tcp_bridge.py
sudo python3 ./scripts/revalidation/serial_tcp_bridge.py --port 54321
```

기본 확인:

```bash
printf 'version\n' | nc -w 3 127.0.0.1 54321
```

정상 예:

```text
A90 Linux init v48
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
[done] version (0ms)
```

명령은 가능한 한 짧게 보낸다.

```bash
printf 'status\n' | nc -w 5 127.0.0.1 54321
printf 'logcat\n' | nc -w 5 127.0.0.1 54321
printf 'run /cache/bin/toybox ifconfig -a\n' | nc -w 8 127.0.0.1 54321
```

여러 명령을 한 번에 보낼 수는 있지만, USB rebind나 blocking command 뒤에는 첫 명령이 유실될 수 있다.
그럴 때는 1~3초 후 `version`을 다시 보낸다.

```bash
for i in $(seq 1 5); do
  printf 'version\n' | nc -w 3 127.0.0.1 54321 || true
  sleep 1
done
```

## 3. Bridge가 안 될 때 판단 순서

### 1단계: host USB 확인

```bash
lsusb | rg 'Samsung|04e8|6861|6860' || true
ls -l /dev/ttyACM* 2>/dev/null || true
ls -l /dev/serial/by-id 2>/dev/null || true
adb devices
```

판단:

- `04e8:6861` + `/dev/ttyACM0` 있음: USB ACM은 host에 보인다.
- bridge만 응답 없음: bridge 재시작 또는 native init console stale 가능성.
- `adb devices`가 `recovery`: TWRP 상태다.
- 아무것도 안 보임: USB gadget이 죽었거나 물리 재부팅이 필요할 수 있다.

### 2단계: v48이면 `usbacmreset`

bridge가 살아 있을 때만:

```bash
printf 'usbacmreset\n' | nc -w 12 127.0.0.1 54321
```

정상 예:

```text
usbacmreset: rebinding ACM, serial may reconnect
# serial console reattached: usbacmreset
[done] usbacmreset
```

### 3단계: TWRP로 복구

native init shell이 살아 있으면:

```bash
printf 'recovery\n' | nc -w 3 127.0.0.1 54321
```

TWRP에 들어간 뒤:

```bash
adb devices
```

`RFCM90CFWXA recovery`가 보여야 한다.

## 4. TWRP에서 system/native init으로 부팅

현재 TWRP `twrp reboot` help에는 `system` target이 없고,
실기에서 `twrp reboot system`은 no-op처럼 TWRP에 머무는 경우가 확인됐다.
system/native init으로 나갈 때는 `twrp reboot` 무인자를 사용한다.

```bash
adb -s RFCM90CFWXA shell 'twrp reboot'
```

그 후 bridge로 확인:

```bash
python3 ./scripts/revalidation/native_init_flash.py \
  --verify-only \
  --expect-version "A90 Linux init v48" \
  --bridge-timeout 180
```

주의:

- `twrp reboot system`은 이 기기의 TWRP CLI에서 신뢰하지 않는다.
- `adb reboot` 또는 `adb shell reboot`는 recovery로 되돌아올 수 있다.
- `adb shell 'twrp reboot'` 후 USB 재열거와 bridge `version`을 관찰한다.

## 5. Custom init 수정 흐름

새 버전 예시가 v50이라면:

```bash
cp stage3/linux_init/init_v48.c stage3/linux_init/init_v50.c
```

반드시 바꿀 것:

- `#define INIT_VERSION "v50"`
- `A90v48` kmsg marker를 `A90v50`로 변경
- v49 번호는 재사용하지 않는다.
- `mark_step("..._v48\n")` 계열을 새 버전으로 변경
- README/docs의 latest 기준점은 실기 검증 뒤에만 갱신

검색:

```bash
rg -n 'v48|A90v48|init_v48|boot_linux_v48|ramdisk_v48' stage3/linux_init/init_v50.c
```

빌드:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v50 stage3/linux_init/init_v50.c
aarch64-linux-gnu-strip stage3/linux_init/init_v50
file stage3/linux_init/init_v50
sha256sum stage3/linux_init/init_v50
strings stage3/linux_init/init_v50 | rg 'A90 Linux init v50|A90v50'
```

컴파일 경고를 무시하지 말 것.

## 6. Boot image 만들기

검증된 이전 boot image에서 kernel/header 인자를 재사용하고 ramdisk만 바꾼다.

```bash
rm -rf /tmp/a90_boot_v48_unpack
mkdir -p /tmp/a90_boot_v48_unpack
python3 mkbootimg/unpack_bootimg.py \
  --boot_img stage3/boot_linux_v48.img \
  --out /tmp/a90_boot_v48_unpack \
  --format=mkbootimg \
  > /tmp/a90_boot_v48_mkbootimg_args.txt
```

ramdisk 생성:

```bash
rm -rf stage3/ramdisk_v50
mkdir -p stage3/ramdisk_v50/bin
cp stage3/linux_init/init_v50 stage3/ramdisk_v50/init
cp stage3/linux_init/a90_sleep stage3/ramdisk_v50/bin/a90sleep
chmod 755 stage3/ramdisk_v50/init stage3/ramdisk_v50/bin/a90sleep
(
  cd stage3/ramdisk_v50
  find . | LC_ALL=C sort | cpio -o -H newc > ../ramdisk_v50.cpio
)
```

boot image 생성:

```bash
python3 - <<'PY'
from pathlib import Path
import shlex
import subprocess

args = shlex.split(Path('/tmp/a90_boot_v48_mkbootimg_args.txt').read_text())
for i, item in enumerate(args):
    if item == '--ramdisk':
        args[i + 1] = 'stage3/ramdisk_v50.cpio'
        break
else:
    raise SystemExit('missing --ramdisk')

cmd = ['python3', 'mkbootimg/mkbootimg.py', *args, '--output', 'stage3/boot_linux_v50.img']
print(shlex.join(cmd))
subprocess.run(cmd, check=True)
PY
```

검증:

```bash
ls -lh stage3/ramdisk_v50.cpio stage3/boot_linux_v50.img
sha256sum stage3/linux_init/init_v50 stage3/ramdisk_v50.cpio stage3/boot_linux_v50.img
strings stage3/boot_linux_v50.img | rg 'A90 Linux init v50|A90v50'
```

## 7. Boot image 플래시

TWRP 상태에서만 실행한다.

```bash
adb devices
```

`recovery` 확인 후:

```bash
python3 ./scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v50.img \
  --expect-version "A90 Linux init v50" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

이 스크립트가 하는 일:

1. local image 존재/정렬/SHA256/expected marker 확인
2. TWRP ADB 대기
3. `/tmp/native_init_boot.img`로 push
4. remote SHA256 확인
5. `dd if=... of=/dev/block/by-name/boot bs=4M conv=fsync && sync`
6. boot partition prefix SHA256 readback 확인
7. `adb shell 'twrp reboot'`
8. bridge `version` 확인

수동으로 `dd`를 직접 치기 전에 이 스크립트를 우선한다.

## 8. Toybox 사용법

빌드:

```bash
./scripts/revalidation/build_static_toybox.sh
```

TWRP에서 배치:

```bash
adb -s RFCM90CFWXA shell 'mkdir -p /cache/bin && chmod 755 /cache/bin'
adb -s RFCM90CFWXA push external_tools/userland/bin/toybox-aarch64-static-0.8.13 /cache/bin/toybox
adb -s RFCM90CFWXA shell 'chmod 755 /cache/bin/toybox && sync && sha256sum /cache/bin/toybox'
```

native init에서 사용:

```bash
printf 'run /cache/bin/toybox --help\n' | nc -w 8 127.0.0.1 54321
printf 'run /cache/bin/toybox ifconfig -a\n' | nc -w 8 127.0.0.1 54321
printf 'run /cache/bin/toybox ps -A\n' | nc -w 8 127.0.0.1 54321
```

주의:

- `ps` 단독은 `rc=1`일 수 있다. `ps -A` 또는 `ps -ef` 사용.
- `netcat -h`는 실패할 수 있다. `netcat --help` 사용.
- `ip link`는 출력 후 `No such device`와 `rc=1`이 나올 수 있다.

## 9. USB helper / NCM 사용법

빌드:

```bash
./scripts/revalidation/build_usbnet_helper.sh
```

TWRP에서 배치:

```bash
adb -s RFCM90CFWXA push external_tools/userland/bin/a90_usbnet-aarch64-static /cache/bin/a90_usbnet
adb -s RFCM90CFWXA shell 'chmod 755 /cache/bin/a90_usbnet && sync && sha256sum /cache/bin/a90_usbnet'
```

native init에서 상태 확인:

```bash
printf 'run /cache/bin/a90_usbnet status\n' | nc -w 8 127.0.0.1 54321
```

ACM-only rebind:

```bash
printf 'run /cache/bin/a90_usbnet off\n' | nc -w 12 127.0.0.1 54321
```

v48 기준 정상이라면 1~3초 뒤 `version`이 돌아온다.

NCM 임시 probe:

```bash
printf 'run /cache/bin/a90_usbnet probe-ncm\n' | nc -w 8 127.0.0.1 54321
```

host 관찰:

```bash
lsusb -t
ip -br link
```

정상 관찰:

- phone device에 `cdc_acm` + `cdc_ncm` composite interface
- host에 `enx...` 형태 NCM interface
- device에 `ncm0`

device 관찰:

```bash
printf 'run /cache/bin/toybox ifconfig -a\n' | nc -w 10 127.0.0.1 54321
```

주의:

- `probe-ncm`은 약 15초 후 ACM-only로 rollback한다.
- persistent `ncm`은 다음 단계에서 IP/link 검증을 할 때만 사용한다.
- host IP 설정은 root 권한이 필요하다.

## 10. 다음 NCM IP 검증 절차

아직 다음 단계다. 진행 시 권장 순서:

1. `probe-ncm`으로 enumeration 재확인
2. persistent NCM 켜기

```bash
printf 'run /cache/bin/a90_usbnet ncm\n' | nc -w 12 127.0.0.1 54321
```

3. device IP 설정

```bash
printf 'run /cache/bin/toybox ifconfig ncm0 192.168.7.2 netmask 255.255.255.0 up\n' | nc -w 8 127.0.0.1 54321
```

4. host interface 이름 확인

```bash
ip -br link
```

5. 사용자에게 host sudo 명령 요청

```bash
sudo ip addr add 192.168.7.1/24 dev <enx...>
sudo ip link set <enx...> up
ping -c 3 192.168.7.2
```

6. rollback

```bash
printf 'run /cache/bin/a90_usbnet off\n' | nc -w 12 127.0.0.1 54321
```

## 11. 로그 확인

native init log:

```bash
printf 'logcat\n' | nc -w 8 127.0.0.1 54321
```

USB helper log:

```bash
printf 'cat /cache/usbnet.log\n' | nc -w 8 127.0.0.1 54321
```

TWRP에서 직접:

```bash
adb -s RFCM90CFWXA shell 'tail -160 /cache/native-init.log 2>/dev/null || true'
adb -s RFCM90CFWXA shell 'tail -160 /cache/usbnet.log 2>/dev/null || true'
```

## 12. 커밋 전 확인

```bash
git status --short
git diff --check
python3 -m py_compile scripts/revalidation/serial_tcp_bridge.py scripts/revalidation/native_init_flash.py
bash -n scripts/revalidation/build_static_toybox.sh scripts/revalidation/build_usbnet_helper.sh
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -o /tmp/a90_init_check stage3/linux_init/init_v50.c
```

`stage3/boot_linux_v*.img`, `stage3/ramdisk_v*.cpio`, compiled binaries는 `.gitignore` 대상이다.
커밋에는 보통 source, script, docs만 넣는다.

## 13. 자주 틀리는 지점

### `screen`이 바로 종료됨

브릿지가 이미 `/dev/ttyACM0`를 잡고 있거나 권한 문제일 수 있다. 이 프로젝트에서는 직접 `screen`보다
`serial_tcp_bridge.py` + `nc`를 우선한다.

### `adb devices`가 비어 있음

native init 상태에서는 ADB가 기본 제어 채널이 아니다. 정상일 수 있다.
TWRP 상태에서만 `recovery`로 잡히는 것을 기대한다.

### host에 `/dev/ttyACM0`가 있는데 bridge 응답이 없음

v47 이하라면 device-side console fd stale 가능성이 크다. v48 이상으로 올린다.
v48 이상이면 bridge 재시작 후 `version`을 여러 번 시도한다.

### `run /cache/bin/a90_usbnet probe-ncm` 뒤 첫 `version`이 비어 있음

USB rollback 직후 첫 입력이 유실될 수 있다. 1~3초 후 다시 `version`.

### TWRP에서 `twrp reboot`가 애매하게 동작함

system/native init으로 나갈 때는 `adb shell 'twrp reboot'`을 사용한다.
`twrp reboot system`은 현재 TWRP CLI에서 no-op처럼 남을 수 있다.
`adb reboot` 또는 `adb shell reboot`는 recovery로 되돌아올 수 있다.

### NCM interface 이름이 매번 다름

host의 `enx...` 이름은 MAC 기반이라 probe마다 바뀔 수 있다. 매번 `ip -br link`로 확인한다.

## 14. 작업 인계 요약

새 에이전트는 다음 순서만 기억하면 된다.

```text
git status 확인
  -> bridge version 확인
  -> 안 되면 host USB/TWRP ADB 확인
  -> 코드 수정은 init_v48에서 복사해 새 버전으로
  -> static build
  -> ramdisk/boot image 생성
  -> TWRP에서 native_init_flash.py로 flash
  -> version 검증
  -> usbacmreset / helper off로 rebind 안전성 확인
  -> NCM은 probe부터, persistent는 IP 검증 때만
```

복구 기준:

- TWRP가 있으면 boot image를 다시 flash할 수 있다.
- `backups/baseline_a_20260423_030309/boot.img`는 stock 쪽 복구 기준점이다.
- native init에서 위험해지면 `recovery`로 돌아간다.
