# v197 Plan: Kernel Config Decoder / Capability Matrix

## Summary

v197 adds a host-side, read-only decoder for the A90 kernel `/proc/config.gz`.
The goal is to move from broad kernel inventory facts to `CONFIG_*` level
evidence before deciding firewall, cgroup/PSI, BPF, tracefs, pstore, or Wi-Fi
next steps.

## Scope

- Add `scripts/revalidation/a90_kernel_tools.py` for shared private-output and
  bridge capture helpers.
- Add `scripts/revalidation/kernel_config_decode.py`.
- Fetch `/proc/config.gz` through `toybox zcat` over the existing `cmdv1 run`
  path, or parse a local decompressed config with `--config-file`.
- Produce a Markdown and JSON capability matrix for:
  - netfilter/nftables/iptables/conntrack
  - cgroup/PSI resource control
  - BPF observability
  - pstore/ramoops
  - tracefs/ftrace/debugfs/usbmon
  - Wi-Fi wireless stack prerequisites
  - namespaces/TUN/VETH support

## Non-Goals

- Do not flash a new boot image.
- Do not mount pstore, tracefs, debugfs, cgroup, or cgroup2.
- Do not enable Wi-Fi, rfkill, tracing, BPF programs, or firewall rules.
- Do not change device-side PID1 code.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_kernel_tools.py \
  scripts/revalidation/kernel_config_decode.py

python3 scripts/revalidation/kernel_config_decode.py \
  --out tmp/kernel-config/v197-kernel-config.md \
  --json-out tmp/kernel-config/v197-kernel-config.json
```

## Acceptance

- `/proc/config.gz` is decoded successfully from the v159 device.
- The report includes a CONFIG-level capability matrix.
- Host output is written with private/no-follow helpers.
- Result is read-only and does not mutate kernel/device state.
