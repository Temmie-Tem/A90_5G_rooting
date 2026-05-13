# v228 Report: Controlled CNSS Start-Only Plan

## Summary

v228 implements a host-side controlled CNSS start-only planner. It does not run
`cnss-daemon`, `cnss_diag`, or any live Wi-Fi command. It consumes v216/v221/v222
/v223/v224/v225/v227 evidence and emits a concrete allowlist, start plan,
rollback policy, and exposure boundary for a later v229 opt-in execution step.

Final result:

- v228: PASS, decision `cnss-start-plan-ready`
- live daemon execution: none
- active Wi-Fi operation: none
- next step: v229 controlled CNSS start planner/runner with explicit operator
  confirmation

## Implemented

- Added `scripts/revalidation/wifi_cnss_start_plan.py`.
- Generated private evidence under `tmp/wifi/v228-controlled-cnss-start-plan`.
- Kept v228 as a planner-only step.

## Command

```bash
python3 scripts/revalidation/wifi_cnss_start_plan.py \
  --out-dir tmp/wifi/v228-controlled-cnss-start-plan
```

Result:

```text
PASS out_dir=/home/temmie/dev/A90_5G_rooting/tmp/wifi/v228-controlled-cnss-start-plan decision=cnss-start-plan-ready reason=controlled CNSS start-only plan is ready; no daemon execution performed
```

## Input Decisions

| evidence | expected | actual |
| --- | --- | --- |
| v216 | `replay-model-ready` | `replay-model-ready` |
| v221 | `elf-evidence-ready` | `elf-evidence-ready` |
| v222 | `vendor-root-ready` | `vendor-root-ready` |
| v223 | `reboot-recovery-accepted` | `reboot-recovery-accepted` |
| v224 | `shim-dryrun-ready` | `shim-dryrun-ready` |
| v225 | `cnss-start-plan-approved` | `cnss-start-plan-approved` |
| v227 | `system-root-ready` | `system-root-ready` |

## Service Model

| service | phase | binary | args | capability notes |
| --- | --- | --- | --- | --- |
| `cnss-daemon` | phase1 primary | `/system/vendor/bin/cnss-daemon` | `-n -l` | requires explicit `NET_ADMIN` in evidence |
| `cnss_diag` | phase2 optional diagnostic | `/system/vendor/bin/cnss_diag` | `-q -f -t HELIUM` | must not run before phase1 passes |

Service checks passed:

- `cnss-daemon-present`
- `cnss-daemon-args`
- `cnss-daemon-net-admin-explicit`
- `cnss-daemon-elf-closed`
- `cnss-diag-present`
- `cnss-diag-phase2-only`
- `cnss-diag-elf-closed`

## Output Files

```text
tmp/wifi/v228-controlled-cnss-start-plan/manifest.json
tmp/wifi/v228-controlled-cnss-start-plan/start-plan.json
tmp/wifi/v228-controlled-cnss-start-plan/command-allowlist.json
tmp/wifi/v228-controlled-cnss-start-plan/rollback-policy.json
tmp/wifi/v228-controlled-cnss-start-plan/exposure-boundary.json
tmp/wifi/v228-controlled-cnss-start-plan/summary.md
```

Permissions:

```text
0o700 tmp/wifi/v228-controlled-cnss-start-plan
0o600 tmp/wifi/v228-controlled-cnss-start-plan/manifest.json
0o600 tmp/wifi/v228-controlled-cnss-start-plan/start-plan.json
0o600 tmp/wifi/v228-controlled-cnss-start-plan/command-allowlist.json
0o600 tmp/wifi/v228-controlled-cnss-start-plan/rollback-policy.json
0o600 tmp/wifi/v228-controlled-cnss-start-plan/exposure-boundary.json
0o600 tmp/wifi/v228-controlled-cnss-start-plan/summary.md
```

## Guardrails

- v228 performs no live device commands.
- No CNSS daemon execution in v228.
- No rfkill write, link-up, scan, connect, DHCP, routing, NAT, or DNS changes.
- No credential path access.
- No persistent system/vendor/data writes.
- Future v229 execution must use explicit operator confirmation.
- Reboot remains the only accepted recovery primitive if state cannot be
  restored.

## Artifact Hashes

```text
3ea7c6c746a650eb619b1cc99c1e204e1d45e70f78684b360ce7e16373c212df  tmp/wifi/v228-controlled-cnss-start-plan/manifest.json
6d9e67708733d2c4d43e0eb00d78b0d94b06df05c903fed66e7ba7d8c3cb622e  tmp/wifi/v228-controlled-cnss-start-plan/start-plan.json
0e928c807d2d4b5449ed6defb3999cfd4a300a120949ac35492b27084b8f9e68  tmp/wifi/v228-controlled-cnss-start-plan/command-allowlist.json
32ce7ca5dea60f2665a22d527d5bdfa04052b90613ce596b39a28028c3beb53f  tmp/wifi/v228-controlled-cnss-start-plan/rollback-policy.json
35b1ebee101093a299aa9ab647f8082e08efa2528bbf82e91c81245857fbd3fb  tmp/wifi/v228-controlled-cnss-start-plan/exposure-boundary.json
a403d7f596b6819aa23372749257a1fe32bf423788679f58b5add18ed2fa312c  tmp/wifi/v228-controlled-cnss-start-plan/summary.md
```

## Next Step

v229 can implement the controlled CNSS start planner/runner, but execution must
remain opt-in behind an explicit confirmation flag. v229 should start only
`cnss-daemon` first, observe bounded state, stop/reap, and keep scan/connect and
credentials out of scope.
