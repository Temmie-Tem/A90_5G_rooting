# A90 Native Init V60 Netservice Reconnect Report

Date: `2026-04-26`

## Summary

`A90 Linux init v60`에서 `netservice stop/start`로 USB gadget을 재열거한 뒤
ACM serial, USB NCM, IPv4 ping, TCP control이 다시 살아나는지 검증했다.

결론:

- software UDC re-enumeration path: PASS
- serial bridge recovery: PASS
- NCM host interface recreation: PASS
- IPv4 ping: PASS
- `a90_tcpctl` ping/status/run: PASS
- final rollback to ACM-only: PASS
- physical unplug/replug soak: not tested yet

## Important Observation

NCM 재열거마다 host interface 이름이 바뀔 수 있다.
따라서 이전에 성공했던 `enx...` 이름을 재사용하면 안 된다.

이번 관찰:

- 이전 interface 예: `enx0a2eb7a94b2f`
- 이번 interface: `enxba06f3efab0f`
- stale interface에 `ip addr`를 넣으면 `Cannot find device`가 정상적으로 발생한다.

현재 interface는 device helper의 `ncm.host_addr` MAC 또는 `ip -br link`로 매번 다시 확인해야 한다.

## Tooling

새 helper:

```bash
scripts/revalidation/netservice_reconnect_soak.py
```

용도:

- `status`: bridge, `netservice status`, `a90_usbnet status` 확인
- `once`: `netservice stop` → `netservice start` → NCM/TCP 검증 → final stop
- `soak`: stop/start 검증을 여러 cycle 반복

sudo 제약이 있는 환경에서는 다음 옵션을 사용한다.

```bash
python3 scripts/revalidation/netservice_reconnect_soak.py once --manual-host-config
```

이 옵션은 현재 새로 생긴 `enx...`에 대한 명령을 출력하고,
사용자가 다른 터미널에서 host IP를 설정할 때까지 기다린다.

## Validation Log

초기 상태:

```text
netservice: flag=/cache/native-init-netservice enabled=no
netservice: ncm0=absent tcpctl=stopped
```

`netservice start` 후:

```text
netservice: flag=/cache/native-init-netservice enabled=no
netservice: ncm0=present tcpctl=running pid=598
```

host interface:

```text
enxba06f3efab0f
```

host IP 설정:

```bash
sudo ip addr replace 192.168.7.1/24 dev enxba06f3efab0f
sudo ip link set enxba06f3efab0f up
```

ping:

```text
PING 192.168.7.2 (192.168.7.2) 56(84) bytes of data.
64 bytes from 192.168.7.2: icmp_seq=1 ttl=64 time=3.10 ms
64 bytes from 192.168.7.2: icmp_seq=2 ttl=64 time=1.48 ms
64 bytes from 192.168.7.2: icmp_seq=3 ttl=64 time=1.47 ms

3 packets transmitted, 3 received, 0% packet loss
rtt min/avg/max/mdev = 1.470/2.013/3.095/0.764 ms
```

TCP control:

```text
a90_tcpctl v1 ready
pong
OK
```

`status`:

```text
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 #2 SMP PREEMPT Thu Jan 12 18:53:40 KST 2023 aarch64
uptime: 2485
load: 2.00 2.00 1.92
mem: 4775/5375 MB free/total
OK
```

`run /cache/bin/toybox uptime`:

```text
[pid 619]
10:38:59 up 41 min,  0 users,  load average: 2.00, 2.00, 1.92
[exit 0]
OK
```

final host ping:

```text
3 packets transmitted, 3 received, 0% packet loss
rtt min/avg/max/mdev = 1.484/1.496/1.514/0.013 ms
```

final rollback:

```text
A90 Linux init v60
netservice: flag=/cache/native-init-netservice enabled=no
netservice: ncm0=absent tcpctl=stopped
```

## Issues Found

During USB re-enumeration, host modem probing can still leak fragmented serial lines such as:

```text
A
ATATAT
```

v59/v60 already ignore common full `AT`, `ATE0`, `AT+...`, `ATQ0 ...` lines,
but a single `A` fragment can still produce `unknown command: A`.

Impact:

- It did not break final NCM/TCP validation.
- It can pollute automation output if bridge commands are sent during USB rebind.

Follow-up:

- V61 candidate: harden native init serial noise filter for short `A` fragments and repeated `ATAT...` lines.
- Host automation should also avoid batching commands immediately after USB re-enumeration.

## Current Safe State

After validation:

- native init: `A90 Linux init v60`
- netservice flag: disabled
- `ncm0`: absent
- `tcpctl`: stopped
- host NCM interface: removed
- serial bridge: alive

## Remaining Work

1. Physical USB unplug/replug manual soak
2. V61 serial noise hardening for fragmented modem probes
3. Longer `netservice_reconnect_soak.py soak --cycles N` run from a terminal with sudo access
