# Native Init v160 NCM/TCP Stability Plan (2026-05-09)

## Summary

- target label: `v160 NCM/TCP Stability`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- 목적은 Wi-Fi 작업 전에 USB NCM과 token-authenticated `a90_tcpctl` 경로를 장시간 반복 검증하는 것이다.
- v160은 먼저 host-side stability evidence/report 경로를 고정한다. device boot image bump는 NCM/TCP 안정성 검증에 필요한 device-side 변경이 생길 때만 별도 판단한다.

## Scope

- `scripts/revalidation/tcpctl_host.py soak`를 공식 NCM/TCP stability loop로 사용한다.
- `scripts/revalidation/ncm_host_setup.py setup` 출력, `tcpctl_host.py soak` 출력, optional longsoak report JSON을 하나의 PASS/FAIL report로 묶는다.
- `scripts/revalidation/ncm_tcp_stability_report.py`를 추가해 다음 조건을 기계적으로 검증한다.
  - tcpctl ready banner 확인
  - NCM ping zero packet loss 확인
  - tcpctl ping/status/run pass count 확인
  - final serial bridge recovery 확인
  - optional longsoak trend pass 확인
- helper mismatch는 `tcpctl_host.py smoke/soak`의 ready/version output과 local expected helper path/hash 점검으로 잡는다.

## Recommended Run

```bash
RUN_ID=v160-ncm-tcp-$(date +%Y%m%d-%H%M%S)
mkdir -p tmp/soak/$RUN_ID
umask 077

python3 scripts/revalidation/a90ctl.py longsoak start 15

python3 scripts/revalidation/ncm_host_setup.py setup --allow-auto-interface \
  2>&1 | tee tmp/soak/$RUN_ID/ncm-setup.txt

python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /bin/a90_tcpctl \
  --toybox /cache/bin/toybox \
  soak \
  --duration 3600 \
  --interval 10 \
  --status-every 3 \
  --run-every 3 \
  --ping-every 1 \
  --ping-count 1 \
  --stop-on-failure \
  2>&1 | tee tmp/soak/$RUN_ID/tcpctl-soak.txt
```

After the device longsoak is exported/correlated:

```bash
python3 scripts/revalidation/ncm_tcp_stability_report.py \
  --tcpctl-soak tmp/soak/$RUN_ID/tcpctl-soak.txt \
  --ncm-setup tmp/soak/$RUN_ID/ncm-setup.txt \
  --longsoak-report-json tmp/soak/$RUN_ID/native-long-soak-report.json \
  --expect-version "A90 Linux init 0.9.59 (v159)" \
  --min-duration 3600 \
  --min-cycles 300 \
  --out-md tmp/soak/$RUN_ID/ncm-tcp-stability-report.md \
  --out-json tmp/soak/$RUN_ID/ncm-tcp-stability-report.json
```

If no longsoak report is available yet, run the same command without
`--longsoak-report-json` and mark the report as host/NCM-only evidence.

## Validation

- `git diff --check`
- `python3 -m py_compile scripts/revalidation/ncm_tcp_stability_report.py scripts/revalidation/tcpctl_host.py scripts/revalidation/ncm_host_setup.py`
- `ncm_host_setup.py setup`: host interface configured and `192.168.7.2` ping PASS.
- `tcpctl_host.py soak`: `failures: 0`, repeated tcpctl ping/status/run PASS, final NCM ping PASS.
- `ncm_tcp_stability_report.py`: report result PASS with private output files.
- post-test bridge checks:
  - `python3 scripts/revalidation/a90ctl.py version`
  - `python3 scripts/revalidation/a90ctl.py status`
  - `python3 scripts/revalidation/a90ctl.py selftest verbose`
  - `python3 scripts/revalidation/a90ctl.py netservice status`
  - `python3 scripts/revalidation/a90ctl.py longsoak status verbose`

## Acceptance

- NCM ping loss is `0%`.
- tcpctl ping/status/run pass counts match transcript summary.
- tcpctl `failures: 0`.
- serial bridge recovers and `version/status/selftest/netservice` still answer.
- Any longsoak evidence used by the report has `host_failures=0`, contiguous device sequence, and monotonic uptime.
- All generated host evidence is private-output friendly (`umask 077`, report writer `0700/0600`, symlink refusal).

## Next

- If v160 passes, proceed to v161 Storage I/O Integrity.
- If v160 fails, classify whether the failure is host interface setup, tcpctl helper mismatch, token auth, NCM packet loss, serial recovery, or device runtime degradation before moving on.
