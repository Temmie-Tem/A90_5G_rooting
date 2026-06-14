# A90 Native Init V60 Netservice Report

Date: `2026-04-26`

## Summary

`A90 Linux init v60`은 USB NCM과 `a90_tcpctl`을 boot-time service로 켤 수 있게 만든 버전이다.
기본값은 안전하게 OFF이며, `/cache/native-init-netservice` flag가 있을 때만 부팅 중 자동 시작한다.

최종 실기 상태는 rollback까지 확인된 상태다.

- latest native init: `A90 Linux init v60`
- source: `stage3/linux_init/init_v60.c`
- boot image: `stage3/boot_linux_v60.img`
- fallback: `stage3/boot_linux_v48.img`
- final netservice state: disabled

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v60` | `4a274b02f793be79872c4ff164dcead332b33e4f7cf281c35f1d59625774dd09` |
| `stage3/ramdisk_v60.cpio` | `f8b153804c561e26c784c713668a6e8e3dfb0cb10b83a9a72c659f1d8c46285c` |
| `stage3/boot_linux_v60.img` | `c57fbf4645790826fbd5e804ff605c25b95cffb4c5eb0ff9076202581e6e828a` |

## Implementation

`init_v60.c`에 `netservice` 명령을 추가했다.

```text
netservice [status|start|stop|enable|disable]
```

동작 정책:

- `status`: flag, helper 존재 여부, `ncm0`, `tcpctl` pid, log path 출력
- `start`: `/cache/bin/a90_usbnet ncm` → console reattach → `ncm0` 대기 → device IP 설정 → `a90_tcpctl` 시작
- `stop`: tracked `a90_tcpctl` 종료 → `/cache/bin/a90_usbnet off` → console reattach
- `enable`: `/cache/native-init-netservice` flag 생성 후 `start`
- `disable`: flag 제거 후 `stop`

boot path:

- flag가 없으면 아무것도 시작하지 않는다.
- flag가 있으면 `netservice_start()`를 호출한다.
- 성공 시 timeline과 log에 netservice 준비 상태를 남긴다.

사용 경로:

- USB helper: `/cache/bin/a90_usbnet`
- TCP helper: `/cache/bin/a90_tcpctl`
- toybox: `/cache/bin/toybox`
- device interface: `ncm0`
- device IP: `192.168.7.2/24`
- host IP: `192.168.7.1/24`
- TCP control: `192.168.7.2:2325`
- netservice log: `/cache/native-init-netservice.log`

## Host Helper Change

`scripts/revalidation/ncm_host_setup.py`도 같이 조정했다.

이전에는 `setup`이 항상 device에서 `a90_usbnet ncm`을 다시 실행했다.
v60 boot netservice처럼 NCM이 이미 켜져 있으면 다음 순서로 동작한다.

1. bridge에서 `a90_usbnet status` 확인
2. `ncm.ifname`과 `ncm.host_addr`가 이미 있으면 `a90_usbnet ncm` 재실행 생략
3. device IP 설정
4. `ncm.host_addr` 기준 host `enx...` 자동 탐지
5. host IP와 ping 검증

이로써 boot-time NCM이 이미 active인 상태에서도 host setup helper가 덮어쓰기식 재바인딩을 피한다.

## Validation

### Default OFF

v60 boot 직후 기본 상태:

```text
netservice: flag=/cache/native-init-netservice enabled=no
netservice: ncm0=absent tcpctl=stopped
```

판정:

- default OFF — PASS
- ACM serial bridge 유지 — PASS

### Enable + Boot Auto-start

`netservice enable`로 flag 생성 후 v60으로 다시 부팅했다.

boot-time 상태:

```text
netservice: flag=/cache/native-init-netservice enabled=yes
netservice: if=ncm0 ip=192.168.7.2/255.255.255.0 tcp=2325 idle=3600s max_clients=0
netservice: helpers usbnet=yes tcpctl=yes toybox=yes
netservice: ncm0=present tcpctl=running pid=544
```

판정:

- flag 감지 — PASS
- NCM composite 유지 — PASS
- `ncm0` 생성 — PASS
- `a90_tcpctl` boot-time spawn — PASS

### Host NCM

host interface:

```text
enx0a2eb7a94b2f
```

host 설정:

```bash
sudo ip addr replace 192.168.7.1/24 dev enx0a2eb7a94b2f
sudo ip link set enx0a2eb7a94b2f up
ping -c 3 -W 2 192.168.7.2
```

결과:

```text
3 packets transmitted, 3 received, 0% packet loss
```

판정:

- host interface 감지 — PASS
- IPv4 ping 3/3 — PASS

### TCP Control

host에서 `tcpctl_host.py`로 확인했다.

```bash
python3 scripts/revalidation/tcpctl_host.py ping
python3 scripts/revalidation/tcpctl_host.py status
python3 scripts/revalidation/tcpctl_host.py run /cache/bin/toybox uptime
```

결과:

- TCP `ping` → `pong OK`
- TCP `status` → kernel/uptime/load/mem 응답
- TCP `run /cache/bin/toybox uptime` → `[exit 0] OK`

판정:

- boot-time TCP control — PASS

### Netservice Log

최종 성공 boot의 `/cache/native-init-netservice.log` 핵심 line:

```text
tcpctl: listening port=2325 idle_timeout=3600s max_clients=0
```

초기 구현에서 `86400s` timeout을 사용했을 때는 다음 오류가 발생했다.

```text
listen: invalid port or timeout
```

원인:

- `a90_tcpctl`의 idle timeout 상한이 `3600s`였다.

수정:

- `NETSERVICE_TCP_IDLE_SECONDS`를 `3600`으로 고정했다.

판정:

- 실패 원인 확인 — PASS
- 최종 timeout 값 수정 — PASS

### Rollback

실험 종료 후:

```text
netservice disable
```

최종 상태:

```text
netservice: flag=/cache/native-init-netservice enabled=no
netservice: ncm0=absent tcpctl=stopped
```

bridge 상태:

```text
A90 Linux init v60
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
```

판정:

- flag 제거 — PASS
- NCM rollback — PASS
- tcpctl 종료 — PASS
- serial bridge 유지 — PASS

## Current Safe State

현재 최종 기준 상태는 다음과 같다.

- boot image: `stage3/boot_linux_v60.img`
- native init: `A90 Linux init v60`
- netservice: disabled
- `ncm0`: absent
- `a90_tcpctl`: stopped
- serial bridge: alive

NCM/TCP control을 다시 켤 때:

```bash
printf 'netservice enable\n' | nc -w 20 127.0.0.1 54321
python3 scripts/revalidation/ncm_host_setup.py setup
python3 scripts/revalidation/tcpctl_host.py ping
```

실험 후 rollback:

```bash
printf 'netservice disable\n' | nc -w 20 127.0.0.1 54321
```

## Next Work

1. USB 물리 재연결/UDC reset 이후 `netservice`와 NCM/tcpctl 복구 확인
2. Wi-Fi 드라이버/펌웨어/vendor daemon read-only 인벤토리
3. 장기 저장소 후보(`/userdata`/별도 partition) 결정
4. TCP control 인증/제한 정책 검토
