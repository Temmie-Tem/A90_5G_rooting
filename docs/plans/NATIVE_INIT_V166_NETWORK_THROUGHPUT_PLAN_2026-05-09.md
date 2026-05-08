# Native Init v166 Network Throughput / Impairment Plan (2026-05-09)

## Summary

- target label: `v166 Network Throughput / Impairment`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- 목적은 USB NCM 위에서 host→device/device→host throughput, checksum, reconnect state를 안정성 관점으로 측정하는 것이다.
- 현재 Codex 실행 환경은 host network IP assignment에 필요한 local sudo를 사용할 수 없으므로, v166 실측은 operator-configured NCM 상태에서 재개한다.

## Intended Scope

- NCM device mode enable.
- Host interface `192.168.7.1/24` assignment.
- Device `192.168.7.2/24` reachability check.
- host→device transfer:
  - bounded payload
  - checksum match
  - MB/s
- device→host transfer:
  - bounded payload
  - checksum match
  - MB/s
- tcpctl ping/status/run smoke after transfer.
- optional/manual impairment:
  - host `tc netem` delay/loss/reorder only
  - no device qdisc mutation by default

## Guardrails

- no internet-facing bind.
- no unauthenticated tcpctl or rshell mode.
- no partition write/format/raw block access.
- no host network mutation unless the operator explicitly configures the USB NCM interface.
- impairment must be reversible and documented.

## Required Precondition

Operator must configure the host NCM interface after NCM is enabled:

```bash
sudo ip addr replace 192.168.7.1/24 dev <enx...>
sudo ip link set <enx...> up
ping -c 3 -W 2 192.168.7.2
```

Current automated environment cannot provide the sudo password, so v166 is deferred rather than running a partial throughput test.

## Acceptance

- throughput report includes direction, duration, bytes, MB/s, checksum result, and error count.
- post-transfer `status`, `netservice status`, and tcpctl smoke remain responsive.
- impairment profile, if used, is clearly marked and reverted.
- final state is documented as NCM or ACM-only.

## Next

- Defer v166 throughput execution until host NCM IP assignment is operator-configured.
- Continue with v167 FS Exerciser Mini because it does not require host network mutation.
