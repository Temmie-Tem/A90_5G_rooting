# Native Init V490 SELinux Policy Load Ready

- Date: 2026-05-21 KST
- Scope: V490 readiness after helper v48 deployment and preflight
- Result: `v490-selinux-policy-load-proof-preflight-ready`
- Pass meaning: policy-load proof is ready to run under explicit approval; native-init Wi-Fi connect and external ping are still not achieved

## Current State

- Latest code commit: `863faa2 Prepare native SELinux policy load proof`
- Deployed helper: `a90_android_execns_probe v48`
- Remote helper SHA-256: `5bc491c7ed0c4da498c6ee16568004dd886df577edd5f8cbebd50fb0740db10c`
- V490 runner status: preflight-ready
- Live policy-load status: not executed

## Evidence

- Helper deploy evidence: `tmp/wifi/v490-helper-deploy-20260521-062803/manifest.json`
- V490 preflight-ready evidence: `tmp/wifi/v490-policy-load-preflight-ready-20260521-063431/manifest.json`
- Approval guard evidence: `tmp/wifi/v490-policy-load-approval-guard-20260521-063545/manifest.json`
- Current status evidence: `tmp/wifi/v490-readiness-status-20260521-063534.json`
- Plan: `docs/plans/NATIVE_INIT_V490_SELINUX_POLICY_LOAD_PROOF_PLAN_2026-05-21.md`

## Checks

| item | value |
|---|---:|
| helper deploy decision | `execns-helper-v48-deploy-pass` |
| policy-load preflight decision | `v490-selinux-policy-load-proof-preflight-ready` |
| approval guard decision | `v490-selinux-policy-load-proof-approval-required` |
| policy load executed | `false` |
| init reexec executed | `false` |
| daemon start executed | `false` |
| Wi-Fi HAL start executed | `false` |
| Wi-Fi bring-up executed | `false` |
| final selftest | `pass=11 warn=1 fail=0` |

## Required Approval

The next live action writes a compiled Android SELinux policy to `/sys/fs/selinux/load`. It is a global kernel SELinux policy mutation and has no in-place rollback contract. The practical rollback remains rebooting into the known-good native init path if policy side effects appear.

Required phrase:

```text
approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up
```

## Execution Boundary

V490 live run is allowed to:

- compile split policy using the V489-proven `secilc` argument set
- write the compiled policy blob once to `/sys/fs/selinux/load`
- capture pre/post current context, enforcing state, policy version, loaded bytes, and loaded hash

V490 live run is not allowed to:

- reexec PID1
- start service-manager or hwservicemanager
- start CNSS or Wi-Fi HAL
- start supplicant or wificond
- scan, connect, DHCP, route, or ping externally

## Next Work

1. Run V490 policy-load proof only after explicit approval.
2. If V490 passes, write the live report and plan V491 post-load domain-transition proof.
3. If V491 proves domain transition, retry service-manager/HAL registration.
4. Continue toward Wi-Fi scan/connect/link-up, DHCP/routing, and external ping.
