# Native Init V48 USB Reattach / NCM Probe Report

Date: `2026-04-25`

## Summary

`init_v48`은 USB gadget rebind 이후 device-side `/dev/ttyGS0` 콘솔 fd가 stale 상태로 남는 문제를 줄이기 위한 안정화 버전이다.

결론:

- `stage3/boot_linux_v48.img` 플래시 및 부팅 확인 — PASS
- `usbacmreset` 내장 명령으로 ACM rebind 후 serial shell 복구 — PASS
- 외부 helper `run /cache/bin/a90_usbnet off` 후 serial shell 복구 — PASS
- `probe-ncm`으로 ACM + NCM composite gadget 임시 열거 — PASS
- host에 NCM interface 생성 확인 — PASS
- device에 `ncm0` interface 생성 확인 — PASS
- IP 설정/패킷 통신 검증은 다음 단계

## Artifacts

- init source: `stage3/linux_init/init_v48.c`
- local init binary: `stage3/linux_init/init_v48`
- local ramdisk: `stage3/ramdisk_v48.cpio`
- local boot image: `stage3/boot_linux_v48.img`
- USB helper source: `stage3/linux_init/a90_usbnet.c`
- USB helper build script: `scripts/revalidation/build_usbnet_helper.sh`
- bridge script: `scripts/revalidation/serial_tcp_bridge.py`

SHA256:

```text
2b967a730b8fd58c7c66d455ccb1196610b3cc373c9bcdfe20d57d841270441e  stage3/linux_init/init_v48
261fbe85a847f142908d84e0bdd3634aa198d605760743aa55c6cd06f75b6357  stage3/ramdisk_v48.cpio
1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042  stage3/boot_linux_v48.img
ed54c840f44f97834fed5ba7e7b34d38d602bf50ac2e4a8b9fdf2754ae9b8304  /cache/bin/a90_usbnet
```

## Problem

`init_v47`에서 USB gadget을 외부 helper로 unbind/bind하면 host에는 `/dev/ttyACM0`가 다시 생기지만,
native init PID 1은 기존 `/dev/ttyGS0` file descriptor에 묶여 있었다.

증상:

- host `lsusb`와 `/dev/ttyACM0`는 복구됨
- `serial_tcp_bridge.py`를 재시작해도 TCP `version` 응답 없음
- 원인은 host bridge stale fd가 아니라 device-side native init console fd stale 문제로 판단

## V48 Changes

`stage3/linux_init/init_v48.c`:

- `INIT_VERSION`을 `v48`로 갱신
- `read_line()`을 blocking `read()` 중심에서 `poll()` 기반으로 변경
- `POLLHUP`/`POLLERR`/`POLLNVAL`, read error/eof 시 console reattach 시도
- idle timeout 기반 조용한 console reattach 추가
- `reattach` 명령 추가
- `usbacmreset` 명령 추가
- `startadbd`/`stopadbd` rebind 뒤 `reattach_console()` 호출

`scripts/revalidation/serial_tcp_bridge.py`:

- serial device inode/rdev identity 추적 추가
- USB re-enumeration으로 `/dev/ttyACM0`가 새 노드가 되면 기존 fd를 닫고 재연결

`stage3/linux_init/a90_usbnet.c`:

- `status|ncm|rndis|probe-ncm|probe-rndis|off` 지원
- `probe-*`는 child process로 분리해 일정 시간 후 ACM-only rollback
- UDC unbind는 newline write, 일반 configfs 속성은 newline 없이 write
- `/cache/usbnet.log`에 진행 기록

## Local Build

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/init_v48 stage3/linux_init/init_v48.c
aarch64-linux-gnu-strip stage3/linux_init/init_v48
```

USB helper:

```bash
./scripts/revalidation/build_usbnet_helper.sh
```

Result:

- `init_v48` compile 성공
- `a90_usbnet` compile 성공
- static ELF 확인: no `INTERP`, no dynamic section
- boot image marker 확인:
  - `A90 Linux init v48`
  - `A90v48`
  - `usbacmreset`
  - `reattach`

## Flash Validation

Command:

```bash
python3 ./scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v48.img \
  --expect-version "A90 Linux init v48" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

Result:

```text
local image sha256: 1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042
remote image sha256: 1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042
A90 Linux init v48
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
[done] version (0ms)
```

## ACM Rebind Validation

Built-in `usbacmreset`:

```text
usbacmreset
usbacmreset: rebinding ACM, serial may reconnect

# serial console reattached: usbacmreset
[done] usbacmreset (1061ms)
```

Post-reset bridge check:

```text
A90 Linux init v48
[done] version (0ms)
```

External helper `off`:

```text
run /cache/bin/a90_usbnet off
mode: off
saved udc: a600000.dwc3
udc: unbind
```

Recovery:

```text
A90 Linux init v48
[done] version (0ms)
helper_off_bridge_ok_at=3s
```

Host after helper rebind:

```text
Bus 002 Device 029: ID 04e8:6861 Samsung Electronics Co., Ltd SAMSUNG_Android
/dev/ttyACM0
```

## NCM Probe

Command:

```text
run /cache/bin/a90_usbnet probe-ncm
```

Helper result:

```text
probe: detached pid=550 mode=ncm seconds=15
a90_usbnet: rc=0
```

During probe, host saw ACM + NCM composite interfaces on the phone:

```text
Bus 002 Device 030: ID 04e8:6861 Samsung Electronics Co., Ltd SAMSUNG_Android
If 0, Class=Communications, Driver=cdc_acm
If 1, Class=CDC Data, Driver=cdc_acm
If 2, Class=Communications, Driver=cdc_ncm
If 3, Class=CDC Data, Driver=cdc_ncm
```

Host network interface:

```text
enx26eaa7b343d7  DOWN  26:ea:a7:b3:43:d7 <NO-CARRIER,BROADCAST,MULTICAST,UP>
```

During a later probe:

```text
enx425f6b65a0cb  DOWN  42:5f:6b:65:a0:cb <NO-CARRIER,BROADCAST,MULTICAST,UP>
```

Device-side toybox saw:

```text
ncm0      Link encap:Ethernet  HWaddr 9e:0b:bb:b2:b9:7a
          BROADCAST MULTICAST  MTU:8178
```

After rollback:

```text
Bus 002 Device 031: ID 04e8:6861 Samsung Electronics Co., Ltd SAMSUNG_Android
If 0, Class=Communications, Driver=cdc_acm
If 1, Class=CDC Data, Driver=cdc_acm
A90 Linux init v48
[done] version (0ms)
```

## Current Limitations

- `ncm.usb0` configfs attrs often return `No such device` when read/written directly.
- NCM still enumerates and creates `ncm0`, so the attr errors are not an immediate blocker for enumeration.
- Host NCM interface is `DOWN`/`NO-CARRIER` until IP/link setup is attempted.
- Host-side IP assignment needs root privileges.
- `probe-ncm` rolls back after 15 seconds; persistent `ncm` mode should be used only after recovery confidence remains high.

## Next Step

Recommended next task:

1. Add a safer USB network setup helper command:
   - persistent `ncm`
   - `ncm-off`
   - optional device IP setup for `ncm0`
2. During persistent NCM mode:
   - device: `ifconfig ncm0 192.168.7.2 netmask 255.255.255.0 up`
   - host: `sudo ip addr add 192.168.7.1/24 dev <enx...>`
   - host: `sudo ip link set <enx...> up`
3. Validate:
   - host ↔ device ping
   - toybox `netcat`
   - serial bridge survival during network rebind

ADB remains lower priority than serial + NCM because v48 now gives a recoverable serial rescue path.
