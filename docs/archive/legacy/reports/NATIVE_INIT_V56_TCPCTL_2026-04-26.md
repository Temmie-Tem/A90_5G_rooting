# Native Init V56 TCP Control Service

Date: `2026-04-26`

## Summary

`A90 Linux init v53` + USB NCM 위에서 작은 TCP command service helper를 구현하고
실기 검증했다. 이 단계의 목표는 serial bridge를 rescue/control fallback으로 남겨둔 채,
NCM 링크 `192.168.7.2:<port>`로 빠른 명령/응답 채널을 여는 것이다.

이 단계도 새 boot image가 아니라 **static userland helper 추가와 runtime 검증**이다.

## Added Tool

Source:

```bash
stage3/linux_init/a90_tcpctl.c
```

Build:

```bash
./scripts/revalidation/build_tcpctl_helper.sh
```

Current local artifact:

```text
external_tools/userland/bin/a90_tcpctl-aarch64-static
sha256 997a5d717c235c2d3cd8757223e68003ce6b68cffee73f06681d1bee16519faf
```

Device install target:

```bash
/cache/bin/a90_tcpctl
```

Usage:

```bash
run /cache/bin/a90_tcpctl listen <port> <idle_timeout_sec> [max_clients]
```

Protocol:

- one TCP connection handles one line command
- every connection starts with `a90_tcpctl v1 ready`
- successful commands end with `OK`
- failed commands end with `ERR ...`
- `shutdown` stops the server and returns control to the serial `run` command

Commands:

```text
help
ping
version
status
run <absolute-path> [args...]
quit
shutdown
```

`run` is intentionally minimal:

- absolute executable path required
- stdin is `/dev/null`
- stdout/stderr are captured and returned over TCP
- default child timeout is 10 seconds
- output is capped at 128 KiB

## Local Validation

Host-native build of the same source was used to validate the protocol shape before device
testing:

```text
ping -> pong / OK
status -> kernel, uptime, load, memory / OK
run /bin/echo hello-tcpctl -> [exit 0] / OK
shutdown -> OK shutdown
```

Static ARM64 build validation:

```text
ELF 64-bit LSB executable, ARM aarch64, statically linked
There is no dynamic section in this file.
```

## Device Install Result

The helper was transferred over NCM using the same netcat/dd path as V55:

```bash
printf 'run /cache/bin/toybox netcat -l -p 18083 /cache/bin/toybox dd of=/cache/bin/a90_tcpctl bs=4096\n' \
  | nc -w 80 127.0.0.1 54321
cat external_tools/userland/bin/a90_tcpctl-aarch64-static | nc -w 10 192.168.7.2 18083
```

Device receive result:

```text
161+4 records in
161+4 records out
663568 bytes (648 K) copied, 10.013 s, 65 K/s
[exit 0]
```

Device SHA256 matched the host artifact:

```text
997a5d717c235c2d3cd8757223e68003ce6b68cffee73f06681d1bee16519faf  /cache/bin/a90_tcpctl
```

## Live TCP Validation

Server launch through serial bridge:

```bash
printf 'run /cache/bin/a90_tcpctl listen 2325 60 8\n' | nc -w 90 127.0.0.1 54321
```

Host TCP commands:

```bash
printf 'ping\n' | nc -w 5 192.168.7.2 2325
printf 'version\n' | nc -w 5 192.168.7.2 2325
printf 'status\n' | nc -w 5 192.168.7.2 2325
printf 'run /cache/bin/toybox uname -a\n' | nc -w 5 192.168.7.2 2325
printf 'run /cache/bin/toybox ifconfig ncm0\n' | nc -w 5 192.168.7.2 2325
printf 'shutdown\n' | nc -w 5 192.168.7.2 2325
```

Results:

```text
a90_tcpctl v1 ready
pong
OK
```

```text
a90_tcpctl v1 ready
a90_tcpctl v1
OK
```

```text
a90_tcpctl v1 ready
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 #2 SMP PREEMPT Thu Jan 12 18:53:40 KST 2023 aarch64
uptime: 62261
load: 2.00 2.03 2.00
mem: 4767/5375 MB free/total
OK
```

```text
a90_tcpctl v1 ready
[pid 1572]
Linux (none) 4.14.190-25818860-abA908NKSU5EWA3 #2 SMP PREEMPT Thu Jan 12 18:53:40 KST 2023 aarch64 Toybox
[exit 0]
OK
```

`ifconfig ncm0` over TCP returned the expected `192.168.7.2` interface details and `[exit 0]`.

Server serial log:

```text
tcpctl: listening port=2325 idle_timeout=60s max_clients=8
tcpctl: served=6 stop=1
[exit 0]
[done] run (2103ms)
```

Post-test checks:

```text
serial bridge version -> A90 Linux init v53
final ping 192.168.7.2 -> 3/3 PASS, 0% packet loss
```

## Notes

- This is not SSH and has no authentication. Treat it as a USB/NCM lab control port only.
- Serial bridge remains the rescue channel. If tcpctl is stuck, cancel the serial `run` command
  with `q` or let the idle timeout expire.
- `shutdown` is the clean stop path for the helper.
- Next useful step is to wrap tcpctl launch/client commands in a host helper, then decide whether
  to evolve this into a boot-time service or replace it with dropbear/SSH later.
