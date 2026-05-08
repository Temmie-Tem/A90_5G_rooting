# A90 v178 Host Harness Baseline on Native Init v159

Date: `2026-05-09`
Device build under test: `A90 Linux init 0.9.59 (v159)`
Plan: `docs/plans/NATIVE_INIT_V178_POST_SECURITY_BASELINE_PLAN_2026-05-09.md`
Roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

Result: `PASS`

No `v178` native-init source or boot image exists in this cycle. `v178` is a
host-harness validation/report label, not a device firmware version. The live
phone remains on `A90 Linux init 0.9.59 (v159)`; `native_init_flash.py
--verify-only` confirmed that existing v159 boot, then the post-security host
harness baseline was tested against that live device.

This report promotes the patched host harness from F038-F044 remediation into the
baseline for v179 mixed-soak scheduler work.

## Device Version / Flash State

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  --verify-only \
  --expect-version "A90 Linux init 0.9.59 (v159)" \
  --verify-protocol auto
```

Result:

- `cmdv1 verify passed`
- `version rc=0 status=ok`
- `status rc=0 status=ok`
- boot image/source used by the device: `stage3/boot_linux_v159.img`, `stage3/linux_init/init_v159.c`
- no v178 native-init boot image was built or flashed
- action: reflash skipped; this v178 report validates host tooling against the existing v159 device

## Device Smoke

Commands:

```bash
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py selftest verbose
python3 scripts/revalidation/a90ctl.py storage
python3 scripts/revalidation/a90ctl.py mountsd status
python3 scripts/revalidation/a90ctl.py exposure guard
python3 scripts/revalidation/a90ctl.py policycheck run
python3 scripts/revalidation/a90ctl.py longsoak status verbose
```

Results:

- `status`: PASS, `rc=0`, `duration_ms=32`
- `bootstatus`: PASS, `rc=0`, `duration_ms=13`
- `selftest verbose`: PASS, `pass=11 warn=1 fail=0`
- `storage`: PASS, SD backend active, fallback `no`, writable `yes`
- `mountsd status`: PASS, SD UUID matched expected value
- `exposure guard`: PASS, `guard=ok warn=0 fail=0`, NCM absent, tcpctl stopped, rshell stopped, boundary `usb-local`
- `policycheck run`: PASS, `cases=96 pass=96 fail=0`
- `longsoak status verbose`: PASS, `health=ok`, running `yes`, samples `1195`

Expected warning retained:

- helper manifest warning remains accepted for this baseline: `helpers warn=1 manifest=no`

## Host Security Baseline

Command:

```bash
python3 scripts/revalidation/local_security_rescan.py --out /tmp/a90-v178-security-rescan.md
```

Result:

- local targeted scan: PASS
- no `S0xx FAIL` rows detected
- accepted warning remains the trusted USB ACM/local serial root-control boundary

Negative safety checks were re-run and failed before device contact:

```bash
python3 scripts/revalidation/storage_iotest.py --run-id . run --sizes 4096
python3 scripts/revalidation/storage_iotest.py --run-id '..' run --sizes 4096
python3 scripts/revalidation/storage_iotest.py --run-id $'ok\nwritefile /cache/native-init-netservice 1\n#' run --sizes 4096
python3 scripts/revalidation/fs_exerciser_mini.py --run-id .
python3 scripts/revalidation/fs_exerciser_mini.py --test-root /mnt/sdext/a90/test-fsx-other
```

Result:

- all negative checks rejected invalid input before any live device operation

## Observer Smoke

Command:

```bash
python3 scripts/revalidation/native_test_supervisor.py observe \
  --duration-sec unlimited \
  --max-cycles 2 \
  --interval 2 \
  --run-dir tmp/soak/harness/v178-post-security-observe-20260509-042523
```

Result:

- PASS
- cycles: `2`
- samples: `14`
- failures: `0`
- stop_reason: `max-cycles`
- evidence: `tmp/soak/harness/v178-post-security-observe-20260509-042523/`

## Filesystem Smoke

Command:

```bash
python3 scripts/revalidation/fs_exerciser_mini.py \
  --run-id v178-fsx-smoke-20260509-042552 \
  --ops 16 \
  --out-dir tmp/soak/fs-exerciser
```

Result:

- PASS
- duration: `11.932s`
- records: `20`
- cleanup_ok: `True`
- failed records: `0`
- evidence: `tmp/soak/fs-exerciser/v178-fsx-smoke-20260509-042552/`

## NCM/TCP Preflight

Command:

```bash
python3 scripts/revalidation/native_test_supervisor.py run ncm-tcp-preflight \
  --allow-ncm \
  --run-dir tmp/soak/harness/v178-ncm-preflight-20260509-042552
```

Result:

- PASS as structured SKIP
- reason: host NCM path `192.168.7.2` was not reachable; no sudo or USB rebind attempted
- evidence: `tmp/soak/harness/v178-ncm-preflight-20260509-042552/`

This is an expected environment-dependent defer because current device state is
ACM-only with `netservice=disabled` and `ncm=absent`.

## Acceptance Check

| Gate | Result | Evidence |
|---|---|---|
| Baseline v159 device verified | PASS | `native_init_flash.py --verify-only` |
| Local F038-F044 security rescan | PASS | `/tmp/a90-v178-security-rescan.md` |
| Negative path/raw-input checks | PASS | rejected before device contact |
| Real-device core smoke | PASS | status/bootstatus/selftest/storage/exposure/policycheck |
| Observer bounded accounting | PASS | `samples=14 failures=0` |
| FS exerciser patched path guard smoke | PASS | `failed records=0 cleanup_ok=True` |
| NCM preflight environment handling | PASS/SKIP | structured skip, no sudo/rebind |

## Decision

v178 post-security harness baseline is accepted.

Next execution item:

- v179 Mixed Soak Scheduler Foundation

Pre-v178 v160-v177 evidence remains useful historical evidence, but v179-v184
readiness decisions should use post-v178 harness output.
