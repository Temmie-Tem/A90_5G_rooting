# Native Init V58 TCP Control Soak

Date: `2026-04-26`

## Summary

`tcpctl_host.py`에 timed soak 검증 명령을 추가하고, 현재 USB NCM + `a90_tcpctl`
경로가 5분 동안 반복 명령과 ping을 버티는지 실기 확인했다.

이 단계의 의미는 “한 번 명령이 되는가”에서 한 단계 올라가,
NCM을 기본 서버형 제어망으로 써도 되는지 판단할 최소 지속성 기준을 확보하는 것이다.

## Added Tool Mode

Path:

```bash
scripts/revalidation/tcpctl_host.py
```

New command:

```bash
python3 scripts/revalidation/tcpctl_host.py soak
```

Default soak behavior:

- bridge로 `/cache/bin/a90_tcpctl listen 2325 60 0` 실행
- `max_clients=0`으로 client count 제한 없이 반복 검증
- 300초 동안 10초 간격으로 TCP `ping`
- 매 6사이클마다 TCP `status`와 `run /cache/bin/toybox uptime`
- 매 사이클 host `ping 192.168.7.2`
- 종료 시 TCP `shutdown`, serial `[done] run`, bridge `version`, final NCM ping 확인

Useful options:

```bash
python3 scripts/revalidation/tcpctl_host.py soak --duration 600 --interval 10
python3 scripts/revalidation/tcpctl_host.py soak --duration 300 --stop-on-failure
python3 scripts/revalidation/tcpctl_host.py soak --install-first
```

## Validation

Syntax/help checks:

```text
python3 -m py_compile scripts/revalidation/tcpctl_host.py
python3 scripts/revalidation/tcpctl_host.py soak --help
```

Short live check:

```text
python3 scripts/revalidation/tcpctl_host.py soak --duration 20 --interval 5 --status-every 2 --run-every 2
```

Short result:

```text
duration: 22.2s
cycles: 4
tcp ping pass: 4
status pass: 2
run pass: 2
host ping pass: 4
failures: 0
```

Main live check:

```text
python3 scripts/revalidation/tcpctl_host.py soak --duration 300 --interval 10
```

Main result:

```text
tcpctl: listening port=2325 idle_timeout=60s max_clients=0
tcpctl: served=42 stop=1
[exit 0]
[done] run (300509ms)

duration: 302.2s
cycles: 30
tcp ping pass: 30
status pass: 5
run pass: 5
host ping pass: 30
failures: 0
```

Post-soak checks:

```text
serial bridge version -> A90 Linux init v53
NCM ping 192.168.7.2 -> 3/3 PASS, 0% packet loss
rtt min/avg/max/mdev = 1.470/1.484/1.511/0.019 ms
```

## Current Conclusion

- USB NCM + `a90_tcpctl` is stable enough for short interactive development sessions.
- Serial bridge remains the rescue/control channel for launching and recovery.
- TCP control is still unauthenticated and should stay restricted to the lab USB/NCM link.
- Physical USB unplug/replug or host network-manager reconnect behavior is not covered by this soak.

## Next Work

- Filter or ignore unsolicited `AT` serial noise from host modem probing.
- Decide whether NCM/tcpctl should become an automatic boot-time service.
- Add a separate USB re-enumeration/reconnect soak if cable or gadget reset stability becomes important.
