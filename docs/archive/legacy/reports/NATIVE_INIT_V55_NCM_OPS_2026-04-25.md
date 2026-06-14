# Native Init V55 NCM Operations Helper

Date: `2026-04-25`

## Summary

`A90 Linux init v53` 위에서 검증된 USB NCM 경로를 반복 운용하기 위한 host/device
helper를 추가하고 실기 검증했다. 목표는 사람이 매번 host interface 이름을 찾고 IP를
수동 설정하지 않아도, ACM serial bridge를 통해 NCM을 켜고 `192.168.7.1/24` ↔
`192.168.7.2/24` 링크를 재현 가능하게 만드는 것이다.

이 단계는 새 boot image가 아니라 **운영 자동화와 TCP 검증 도구 추가**로 본다.

## Live Validation Result

Starting state:

- native init: `A90 Linux init v53`
- bridge: `127.0.0.1:54321`
- host interface: `enx6e0617d3b2a3`
- device interface: `ncm0`

Device NCM state:

```text
ncm.ifname: ncm0
ncm.dev_addr: fa:3d:4b:0f:b5:83
ncm.host_addr: 6e:06:17:d3:b2:a3
```

Host address was set by the user because this agent could not use interactive sudo:

```bash
sudo ip addr replace 192.168.7.1/24 dev enx6e0617d3b2a3
sudo ip link set enx6e0617d3b2a3 up
```

`ncm_host_setup.py status` parsed the helper output and matched the host interface:

```text
[ncm] host interface: enx6e0617d3b2a3 (6e:06:17:d3:b2:a3)
```

`ncm_host_setup.py ping` passed:

```text
3 packets transmitted, 3 received, 0% packet loss
rtt min/avg/max/mdev = 1.482/1.526/1.553/0.031 ms
```

Short stability ping passed:

```text
30 packets transmitted, 30 received, 0% packet loss
rtt min/avg/max/mdev = 1.445/1.502/1.754/0.077 ms
```

ACM bridge remained alive after NCM traffic:

```text
A90 Linux init v53
[done] version (0ms)
```

Device `ncm0` counters after tests:

```text
RX packets:5861 errors:0 dropped:0 overruns:0 frame:0
TX packets:230 errors:0 dropped:0 overruns:0 carrier:0
```

## Added Tools

### Host NCM setup helper

Path:

```bash
scripts/revalidation/ncm_host_setup.py
```

Commands:

```bash
python3 scripts/revalidation/ncm_host_setup.py setup
python3 scripts/revalidation/ncm_host_setup.py status
python3 scripts/revalidation/ncm_host_setup.py ping
python3 scripts/revalidation/ncm_host_setup.py off
```

Default behavior:

- bridge: `127.0.0.1:54321`
- device helper: `/cache/bin/a90_usbnet`
- toybox: `/cache/bin/toybox`
- device IP: `192.168.7.2/24`
- host IP: `192.168.7.1/24`
- host interface detection: parse `ncm.host_addr` from `a90_usbnet status`, then match
  `/sys/class/net/*/address`

`setup` sequence:

1. `run /cache/bin/a90_usbnet ncm`
2. `run /cache/bin/a90_usbnet status`
3. `run /cache/bin/toybox ifconfig ncm0 192.168.7.2 netmask 255.255.255.0 up`
4. host MAC based interface detection
5. `sudo ip addr replace 192.168.7.1/24 dev <iface>`
6. `sudo ip link set <iface> up`
7. `ping -c 3 -W 2 192.168.7.2`

The helper handles v53 menu busy state by sending `hide` and retrying before running
blocking `run ...` commands.

### Device TCP nettest helper

Source:

```bash
stage3/linux_init/a90_nettest.c
```

Build:

```bash
./scripts/revalidation/build_nettest_helper.sh
```

Current local artifact:

```text
external_tools/userland/bin/a90_nettest-aarch64-static
sha256 765c1976521970000314295f32925dad680af4b2537b7226298283a18821776b
```

Device install target:

```bash
/cache/bin/a90_nettest
```

Commands:

```bash
run /cache/bin/a90_nettest listen <port> <timeout_sec> <expect>
run /cache/bin/a90_nettest send <host_ipv4> <port> <payload>
```

The helper intentionally avoids stdin-driven interactive behavior. This keeps TCP tests
separate from native init's serial cancel path, where toybox `netcat` can otherwise compete
with the shell for serial input.

## Device Install Result

Initial `wget` transfer over NCM reached the host HTTP server but failed on the device with
`wget: response 0`, so the tested transfer path used toybox `netcat` with a device-side
`dd` child:

```bash
printf 'run /cache/bin/toybox netcat -l -p 18082 /cache/bin/toybox dd of=/cache/bin/a90_nettest bs=4096\n' \
  | nc -w 70 127.0.0.1 54321
cat external_tools/userland/bin/a90_nettest-aarch64-static | nc -w 10 192.168.7.2 18082
```

Device receive result:

```text
158+6 records in
158+6 records out
663568 bytes (648 K) copied, 10.013 s, 65 K/s
[exit 0]
```

Device SHA256 matched the host artifact:

```text
765c1976521970000314295f32925dad680af4b2537b7226298283a18821776b  /cache/bin/a90_nettest
```

Helper usage check returned the expected usage and `rc=2`.

## Validation Flow

Host setup:

```bash
python3 scripts/revalidation/ncm_host_setup.py setup
```

Expected:

- `a90_usbnet status` shows `f1 -> acm.usb0`, `f2 -> ncm.usb0`
- `ncm.ifname: ncm0`
- host interface is found by `ncm.host_addr`
- host gets `192.168.7.1/24`
- device `192.168.7.2` ping passes

Host → device TCP:

```bash
( printf 'run /cache/bin/a90_nettest listen 2323 10 hello-from-host\n' \
    | nc -w 15 127.0.0.1 54321 ) &
sleep 1
printf 'hello-from-host\n' | nc -w 5 192.168.7.2 2323
wait
```

Expected device output:

```text
PASS listen received expected payload
```

Actual result:

```text
listen: port=2323 timeout_ms=15000 expect=hello-from-host
received: hello-from-host
PASS listen received expected payload
[exit 0]
[done] run (2103ms)
```

Device → host TCP:

```bash
rm -f /tmp/a90-ncm-device-to-host.txt
( nc -l -p 2324 > /tmp/a90-ncm-device-to-host.txt ) &
listener_pid=$!
sleep 1
printf 'run /cache/bin/a90_nettest send 192.168.7.1 2324 hello-from-device\n' \
  | nc -w 10 127.0.0.1 54321
wait "${listener_pid}"
cat /tmp/a90-ncm-device-to-host.txt
```

Expected host output:

```text
hello-from-device
```

Expected device output:

```text
PASS send delivered payload
```

Actual device result:

```text
send: host=192.168.7.1 port=2324 payload=hello-from-device
PASS send delivered payload
[exit 0]
[done] run (100ms)
```

Actual host payload:

```text
hello-from-device
```

Rollback:

```bash
python3 scripts/revalidation/ncm_host_setup.py off
printf 'version\n' | nc -w 5 127.0.0.1 54321
```

Expected:

- USB network function is removed
- ACM serial bridge responds with `A90 Linux init v53`

This rollback command was not executed during the final validation pass so the working NCM
link would remain active for follow-up work.

## Notes

- `a90_usbnet` MAC attr write warnings are not a blocker for V55. The host helper relies on
  the actual `ncm.host_addr` reported by configfs after enumeration.
- `ncm_host_setup.py setup` still requires interactive sudo for host IP assignment unless it
  is run as root or with cached sudo credentials. In this validation pass, the host IP was set
  manually by the user and `status`/`ping` were verified through the helper.
- Wi-Fi driver/firmware extraction stays out of this step. NCM remains the stable rescue and
  development link before wireless work begins.
- The unsolicited serial `AT` noise observed during USB re-enumeration is still a V56 shell
  hardening candidate.
