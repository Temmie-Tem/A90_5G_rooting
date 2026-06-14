# Native Init V57 TCP Control Host Wrapper

Date: `2026-04-26`

## Summary

`a90_tcpctl`을 사람이 직접 `nc` 조합으로 다루지 않아도 되도록 host wrapper를 추가하고
실기 검증했다. 이 단계의 목표는 NCM 위 TCP 제어 채널을 `install`, `start`, `call`,
`run`, `stop`, `smoke` 같은 반복 가능한 host 명령으로 감싸는 것이다.

## Added Tool

Path:

```bash
scripts/revalidation/tcpctl_host.py
```

Default endpoints:

- serial bridge: `127.0.0.1:54321`
- tcpctl target: `192.168.7.2:2325`
- device binary: `/cache/bin/a90_tcpctl`
- toybox: `/cache/bin/toybox`

Commands:

```bash
python3 scripts/revalidation/tcpctl_host.py install
python3 scripts/revalidation/tcpctl_host.py start
python3 scripts/revalidation/tcpctl_host.py call status
python3 scripts/revalidation/tcpctl_host.py ping
python3 scripts/revalidation/tcpctl_host.py version
python3 scripts/revalidation/tcpctl_host.py status
python3 scripts/revalidation/tcpctl_host.py run /cache/bin/toybox uname -a
python3 scripts/revalidation/tcpctl_host.py stop
python3 scripts/revalidation/tcpctl_host.py smoke
```

Behavior:

- `start` launches `run /cache/bin/a90_tcpctl listen ...` through the serial bridge and streams
  the serial-side server log.
- `call`, `ping`, `version`, `status`, `run`, and `stop` talk directly to `192.168.7.2:2325`.
- `install` transfers the static helper over NCM with toybox `netcat` + `dd`, then verifies SHA256.
- `smoke` starts the service, runs representative TCP commands, sends `shutdown`, verifies the
  serial `run` command exits, then checks serial `version` and NCM ping.
- The wrapper sends a best-effort `hide` first, so v53 menu-active state does not block `run`.

## Validation

Syntax/help checks:

```text
python3 -m py_compile scripts/revalidation/tcpctl_host.py
python3 scripts/revalidation/tcpctl_host.py --help
```

Live smoke command:

```bash
python3 scripts/revalidation/tcpctl_host.py smoke
```

Smoke result:

```text
--- ping ---
a90_tcpctl v1 ready
pong
OK

--- version ---
a90_tcpctl v1 ready
a90_tcpctl v1
OK

--- status ---
a90_tcpctl v1 ready
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 #2 SMP PREEMPT Thu Jan 12 18:53:40 KST 2023 aarch64
uptime: 62921
load: 2.00 2.00 2.00
mem: 4767/5375 MB free/total
OK

--- run-uname ---
[exit 0]
OK

--- run-ifconfig ---
ncm0 ... inet addr:192.168.7.2 ... [exit 0]
OK

--- shutdown ---
OK shutdown
```

Serial-side server result:

```text
tcpctl: listening port=2325 idle_timeout=60s max_clients=8
tcpctl: served=7 stop=1
[exit 0]
[done] run (602ms)
```

Post-smoke checks:

```text
serial bridge version -> A90 Linux init v53
NCM ping 192.168.7.2 -> 3/3 PASS, 0% packet loss
```

## Notes

- First smoke attempt exposed a wrapper bug: the TCP service had stopped cleanly, but the host
  thread waited for socket EOF instead of the serial `[done] run` marker.
- `BridgeRunThread` now exits when it sees `[done] run`, `[err] run`, or `[busy]`.
- The wrapper still treats `a90_tcpctl` as a lab-only unauthenticated USB/NCM control channel.
- Next work is longer stability testing and deciding whether NCM/tcpctl should become a boot-time
  service.
