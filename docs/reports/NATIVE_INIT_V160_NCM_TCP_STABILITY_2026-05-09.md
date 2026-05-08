# Native Init v160 NCM/TCP Stability Report (2026-05-09)

## Result

- status: PASS
- label: `v160 NCM/TCP Stability`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- device build was not bumped for this validation-only step.
- objective: prove USB NCM + token-authenticated `a90_tcpctl` remains stable under a 1-hour repeated host/device control loop.

## Implemented

- Added `scripts/revalidation/ncm_tcp_stability_report.py`.
- Added `docs/plans/NATIVE_INIT_V160_NCM_TCP_STABILITY_PLAN_2026-05-09.md`.
- Linked v160 in the task queue and next-work plan.

## Evidence Paths

```text
tmp/soak/v159-ncm-tcp-20260508-232721/ncm-setup.txt
tmp/soak/v159-ncm-tcp-20260509-001148/tcpctl-soak.txt
tmp/soak/v159-ncm-tcp-20260509-001148/native-long-soak-report.md
tmp/soak/v159-ncm-tcp-20260509-001148/native-long-soak-report.json
tmp/soak/v159-ncm-tcp-20260509-001148/ncm-tcp-stability-report.md
tmp/soak/v159-ncm-tcp-20260509-001148/ncm-tcp-stability-report.json
```

## NCM/TCP Soak

```text
duration: 3602.5s
cycles: 360
tcp ping pass: 360
status pass: 120
run pass: 120
host ping pass: 360
failures: 0
```

Final NCM ping:

```text
3 packets transmitted, 3 received, 0% packet loss
rtt min/avg/max/mdev = 1.478/1.503/1.540/0.026 ms
```

Serial/tcpctl shutdown evidence:

```text
tcpctl: served=602 stop=1
[exit 0]
[done] run (3600541ms)
```

## Longsoak Correlation

```text
result: PASS
host events: 7
host failures: 0
device samples: 428
device seq contiguous: True
device ts monotonic: True
device uptime monotonic: True
```

Selected trends:

| Metric | First | Last | Min | Max | Delta |
|---|---:|---:|---:|---:|---:|
| `uptime_sec` | `59215.250` | `65629.730` | `59215.250` | `65629.730` | `6414.480` |
| `battery_pct` | `100.000` | `100.000` | `100.000` | `100.000` | `0.000` |
| `battery_temp_c` | `31.400` | `31.300` | `31.300` | `31.700` | `-0.100` |
| `cpu_temp_c` | `35.900` | `35.500` | `35.500` | `38.200` | `-0.400` |
| `gpu_temp_c` | `37.000` | `36.300` | `36.300` | `39.700` | `-0.700` |
| `mem_used_mb` | `267.000` | `268.000` | `267.000` | `269.000` | `1.000` |
| `load1` | `2.520` | `2.000` | `2.000` | `2.790` | `-0.520` |

## Post-Test Control Checks

```text
version: PASS A90 Linux init 0.9.59 (v159)
status: PASS selftest pass=11 warn=1 fail=0, longsoak health=ok, runtime backend=sd
selftest verbose: PASS pass=11 warn=1 fail=0
netservice status: PASS ncm0=present tcpctl=stopped token=present
longsoak status verbose: PASS running=yes samples=424+ health=ok
```

## Static Validation

```text
python3 -m py_compile scripts/revalidation/ncm_tcp_stability_report.py scripts/revalidation/tcpctl_host.py scripts/revalidation/ncm_host_setup.py
git diff --check
```

Result: PASS.

## Notes

- The NCM setup transcript did not include the helper's stderr-only final `NCM setup complete` line because the original run used `| tee` without `2>&1`.
- The v160 reporter accepts this case only when `ncm.ifname: ncm0`, successful `ifconfig ncm0`, and zero-loss NCM ping are all present.
- Device longsoak remained running after the export/correlation step.
- This validates the USB-local network control path but does not widen exposure beyond USB NCM.

## Next

- v161: Storage I/O Integrity under `/mnt/sdext/a90/test-*`.
