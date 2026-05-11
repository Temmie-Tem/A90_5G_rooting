# v202 Plan: Kernel Capability Summary View

## Summary

v202 adds one host-side summary view for v197-v200 kernel capability evidence.
The goal is to make the next Wi-Fi/network/debug decision from a single report
instead of reading four separate artifacts.

## Scope

- Add `scripts/revalidation/kernel_capability_summary.py`.
- Merge these inputs:
  - v197 kernel config decoder
  - v198 netfilter inventory
  - v199 cgroup/PSI inventory
  - v200 debug observability plan
  - live `wififeas gate`
- Support both existing JSON inputs and `--refresh` mode that reruns v197-v200
  collectors before summary generation.

## Non-Goals

- Do not enable Wi-Fi.
- Do not write firewall rules.
- Do not mount cgroup, tracefs, debugfs, or pstore.
- Do not change native-init PID1 or boot images.

## Validation

```bash
python3 -m py_compile scripts/revalidation/kernel_capability_summary.py

python3 scripts/revalidation/kernel_capability_summary.py \
  --out tmp/kernel-capability/v202-kernel-capability.md \
  --json-out tmp/kernel-capability/v202-kernel-capability.json

python3 scripts/revalidation/kernel_capability_summary.py \
  --refresh \
  --config-json tmp/kernel-config/v202-kernel-config.json \
  --netfilter-json tmp/netfilter/v202-netfilter.json \
  --cgroup-json tmp/cgroup-psi/v202-cgroup-psi.json \
  --debug-json tmp/debug-observability/v202-debug-observability.json \
  --out tmp/kernel-capability/v202-kernel-capability-refresh.md \
  --json-out tmp/kernel-capability/v202-kernel-capability-refresh.json
```

## Acceptance

- Summary output includes config, netfilter, cgroup/PSI, tracefs/pstore, and
  Wi-Fi gate rows.
- `--refresh` mode regenerates source evidence and still passes.
- Report is private/no-follow and read-only.
