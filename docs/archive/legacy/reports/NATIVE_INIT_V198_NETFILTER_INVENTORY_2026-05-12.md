# v198 Netfilter / Nftables Exposure Inventory

## Summary

v198 inventories A90 firewall/exposure control capability without changing
rules, sysctls, modules, interfaces, or listeners. This is a host tooling
change only; latest verified native init remains `A90 Linux init 0.9.59 (v159)`.

## Changes

- Added `scripts/revalidation/netfilter_inventory.py`.
- Reused v197 config decoding helpers from `scripts/revalidation/a90_kernel_tools.py`.
- Produced a runtime and CONFIG matrix for netfilter, conntrack, nftables,
  legacy iptables, and userland firewall tool availability.

## Validation

```bash
python3 -m py_compile scripts/revalidation/netfilter_inventory.py
```

Result: PASS.

```bash
python3 scripts/revalidation/netfilter_inventory.py \
  --out tmp/netfilter/v198-netfilter.md \
  --json-out tmp/netfilter/v198-netfilter.json
```

Result: PASS.

Evidence:

- `tmp/netfilter/v198-netfilter.md`
- `tmp/netfilter/v198-netfilter.json`

Summary:

- Decision: `legacy-iptables-runtime-present`
- IPv4 tables: `security`, `raw`, `nat`, `mangle`, `filter`
- IPv6 tables: `nat`, `raw`, `mangle`, `filter`
- Conntrack runtime: present, count `0`, max `262144`
- `CONFIG_NF_TABLES=n`, so nftables should not be treated as the default path.
- Legacy iptables kernel path is available, but common userland tools were not
  found in the checked cache/system paths.

## Acceptance

- Kernel and runtime netfilter evidence is captured read-only.
- The next network exposure work should plan around legacy iptables capability
  unless userland tools are added explicitly.
- No firewall rule, sysctl, interface, module, or Wi-Fi state was changed.

## Next

v199 should inventory cgroup/PSI resource-control feasibility for service
isolation before long-running server-style workloads.
