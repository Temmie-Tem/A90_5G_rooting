# Native Init V455 Wi-Fi Strict Post-route Semantics Plan

Date: 2026-05-20

## Goal

V455 proves the strict return-code semantics introduced by V454.  The generated
V454 scripts must not hide post-route/proof failures when V447 succeeds, and
must preserve the V447 return code when V447 itself fails.

## Scope

Allowed:

- read latest V454 packet and generated scripts;
- audit scripts for strict post-route markers;
- run a local shell return-code matrix that mirrors the V454 strict block;
- recommend the V454 host preflight script after proof passes.

Not allowed:

- read Wi-Fi secret env values;
- execute generated operator scripts;
- run V447/V449/V450/V452 success paths;
- boot/flash Android, enable Wi-Fi, scan, connect, or mutate the device;
- expose any server listener.

## Implementation

- Proof: `scripts/revalidation/wifi_strict_postroute_semantics_v455.py`
  - `plan`: records proof plan;
  - `run`: audits V454 script markers and executes a shell return-code matrix.

## Validation Plan

```text
python3 -m py_compile scripts/revalidation/wifi_strict_postroute_semantics_v455.py

python3 scripts/revalidation/wifi_strict_postroute_semantics_v455.py \
  --out-dir tmp/wifi/v455-strict-postroute-semantics-plan-<ts> \
  plan

python3 scripts/revalidation/wifi_strict_postroute_semantics_v455.py \
  --out-dir tmp/wifi/v455-strict-postroute-semantics-run-<ts> \
  run

git diff --check
```

## Matrix Cases

- V447 succeeds and all route/proof commands pass: return 0.
- V447 succeeds and router fails: return router failure.
- V447 succeeds and later proof fails: return later proof failure.
- V447 fails and route/proof passes: preserve V447 failure.
- V447 fails and route/proof fails: preserve V447 failure.
- Live cancellation exits before route/proof: preserve cancellation return code.

## Expected Decisions

- `v455-strict-postroute-semantics-plan-ready`
- `v455-strict-postroute-semantics-needs-v454`
- `v455-strict-postroute-semantics-v454-not-ready`
- `v455-strict-postroute-semantics-marker-failed`
- `v455-strict-postroute-semantics-matrix-failed`
- `v455-strict-postroute-semantics-pass`

## Pass Criteria

V455 passes only when:

- latest V454 packet exists and passed;
- generated host preflight/live scripts contain all strict post-route markers;
- the return-code matrix passes every case;
- no generated operator script or device command is executed.

## Next Gate

Run the V454 host preflight strict-route script and enter Wi-Fi values locally.
After preflight, use routed evidence to decide whether to run the V454 live
strict-proof script.

Server exposure remains blocked.
