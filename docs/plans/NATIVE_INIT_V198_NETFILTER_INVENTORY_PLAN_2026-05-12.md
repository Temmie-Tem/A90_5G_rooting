# v198 Plan: Netfilter / Nftables Exposure Inventory

## Summary

v198 adds a host-side, read-only inventory for A90 firewall and network exposure
controls. It combines v197 `CONFIG_*` evidence with runtime `/proc/net` and
`/proc/sys/net/netfilter` state before any Wi-Fi or broader network exposure.

## Scope

- Add `scripts/revalidation/netfilter_inventory.py`.
- Decode `/proc/config.gz` and extract netfilter, conntrack, nftables, iptables,
  NAT, mangle, raw, and bridge netfilter flags.
- Read runtime table names, matches, targets, conntrack count/max, and netfilter
  proc/sys nodes.
- Check whether common userland firewall tools exist in cache/system paths.

## Non-Goals

- Do not install `iptables`, `nft`, or `conntrack`.
- Do not write firewall rules.
- Do not write sysctl values.
- Do not load modules or change network interfaces.
- Do not enable Wi-Fi or public listeners.

## Validation

```bash
python3 -m py_compile scripts/revalidation/netfilter_inventory.py

python3 scripts/revalidation/netfilter_inventory.py \
  --out tmp/netfilter/v198-netfilter.md \
  --json-out tmp/netfilter/v198-netfilter.json
```

## Acceptance

- Kernel config and runtime netfilter state are captured.
- The report classifies whether nftables or legacy iptables is the viable path.
- Output is private/no-follow and read-only.
