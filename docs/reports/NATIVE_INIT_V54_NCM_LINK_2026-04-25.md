# Native Init V54 NCM Link Validation

Date: `2026-04-25`

## Summary

`A90 Linux init v53` 상태에서 code change 없이 USB NCM persistent mode를 실기 검증했다.
ACM serial 제어 채널을 유지한 채 host에는 `cdc_ncm`, device에는 `ncm0`가 생성됐고,
IPv4 ping, IPv6 link-local ping, host → device `toybox netcat` TCP payload 전달까지 확인했다.

이 결과는 다음 개발 단계를 `v54` 코드 변경으로 보기보다,
**v53 runtime 위에서 서버형 접근 경로가 처음 열린 검증 단계**로 본다.

## Starting State

- native init: `A90 Linux init v53`
- control: USB ACM serial bridge `127.0.0.1:54321`
- USB state before test: ACM-only
- helper: `/cache/bin/a90_usbnet`
- userland: `/cache/bin/toybox`

Initial helper status:

```text
functions: acm.usb0
config b.1: f1,strings,bmAttributes,MaxPower
f1: ../../../../usb_gadget/g1/functions/acm.usb0
f2: <readlink:No such file or directory>
```

## Commands

Enable persistent NCM:

```bash
printf 'run /cache/bin/a90_usbnet ncm\n' | nc -w 15 127.0.0.1 54321
```

Check device state:

```bash
printf 'run /cache/bin/a90_usbnet status\n' | nc -w 10 127.0.0.1 54321
printf 'run /cache/bin/toybox ifconfig -a\n' | nc -w 10 127.0.0.1 54321
```

Set device IPv4:

```bash
printf 'run /cache/bin/toybox ifconfig ncm0 192.168.7.2 netmask 255.255.255.0 up\n' \
  | nc -w 10 127.0.0.1 54321
```

Host IPv4 setup requires root:

```bash
sudo ip addr add 192.168.7.1/24 dev enx6e0617d3b2a3
sudo ip link set enx6e0617d3b2a3 up
ping -c 3 192.168.7.2
```

## Observed USB State

Host:

```text
Bus 002 Device 036: ID 04e8:6861 Samsung Electronics Co., Ltd SAMSUNG_Android
If 0: cdc_acm
If 1: cdc_acm
If 2: cdc_ncm
If 3: cdc_ncm
```

Host network interface:

```text
enx6e0617d3b2a3  UP  6e:06:17:d3:b2:a3 <BROADCAST,MULTICAST,UP,LOWER_UP>
```

Device helper:

```text
functions: ncm.usb0,acm.usb0
config b.1: f2,f1,strings,bmAttributes,MaxPower
f1: ../../../../usb_gadget/g1/functions/acm.usb0
f2: ../../../../usb_gadget/g1/functions/ncm.usb0
ncm.ifname: ncm0
ncm.dev_addr: fa:3d:4b:0f:b5:83
ncm.host_addr: 6e:06:17:d3:b2:a3
```

Device `ncm0` after IPv4 setup:

```text
ncm0 Link encap:Ethernet HWaddr fa:3d:4b:0f:b5:83
inet addr:192.168.7.2 Bcast:192.168.7.255 Mask:255.255.255.0
inet6 addr: fe80::f83d:4bff:fe0f:b583/64 Scope: Link
UP BROADCAST RUNNING MULTICAST MTU:8178
```

## Link Tests

### IPv4

Device-side IPv4 setup succeeded.

Host-side IPv4 setup without sudo failed as expected:

```text
RTNETLINK answers: Operation not permitted
```

After user ran the host sudo commands, host IPv4 was configured:

```text
enx6e0617d3b2a3 UP 192.168.7.1/24 fe80::48eb:a02f:cda3:aa18/64
```

IPv4 ping:

```text
PING 192.168.7.2 (192.168.7.2) 56(84) bytes of data.
64 bytes from 192.168.7.2: icmp_seq=1 ttl=64 time=1.52 ms
64 bytes from 192.168.7.2: icmp_seq=2 ttl=64 time=1.49 ms
64 bytes from 192.168.7.2: icmp_seq=3 ttl=64 time=1.47 ms

--- 192.168.7.2 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss
```

### IPv6 Link-local

Host → device IPv6 link-local ping got a response:

```text
64 bytes from fe80::f83d:4bff:fe0f:b583%enx6e0617d3b2a3: icmp_seq=1 ttl=64 time=3.09 ms
```

The run observed `1/3` replies. This is enough to prove L3 reachability, but repeated ping
stability should be retested after host IPv4 is configured or NetworkManager behavior is pinned down.

### TCP / Netcat

Device listener:

```bash
printf 'run /cache/bin/toybox netcat -l -p 2323\n' | nc -w 25 127.0.0.1 54321
```

Host client:

```bash
printf 'hello-from-host-over-ncm-ipv6\n' \
  | nc -6 -w 5 'fe80::f83d:4bff:fe0f:b583%enx6e0617d3b2a3' 2323
```

Device serial output:

```text
hello-from-host-over-ncm-ipv6
[exit 0]
[done] run (9012ms)
```

This confirms host → device TCP payload delivery over USB NCM.

## Notes

- ACM serial remained usable after NCM persistent mode.
- USB re-enumeration produced a stray `AT` command on the serial shell once. This is probably host-side modem probing and should be filtered or ignored in a future shell hardening pass.
- `a90_usbnet ncm` attempted to write configured MAC addresses before bind, but configfs returned `No such device`; the kernel still assigned working random MACs.
- The current host interface name is MAC-derived and may change: always re-read `ncm.host_addr` or `ip -br link`.

## Current State After Test

- Device is still in NCM + ACM composite mode.
- Device `ncm0` has `192.168.7.2/24` and IPv6 link-local.
- Host `enx6e0617d3b2a3` is UP with `192.168.7.1/24` and IPv6 link-local.

Rollback if needed:

```bash
printf 'run /cache/bin/a90_usbnet off\n' | nc -w 12 127.0.0.1 54321
sleep 3
printf 'version\n' | nc -w 5 127.0.0.1 54321
```

## Next Work

1. Add a small host helper script for NCM interface detection and IP setup.
2. Test device → host netcat and longer-lived TCP sessions.
3. Add a shell filter for unsolicited host modem-probe `AT` noise.
4. Decide whether `a90_usbnet` should set MAC addresses after unbind or accept kernel-assigned addresses.
5. Build a persistent TCP control service or evaluate static dropbear after NCM stays stable.
