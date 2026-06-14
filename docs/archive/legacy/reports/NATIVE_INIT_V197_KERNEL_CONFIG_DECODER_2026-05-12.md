# v197 Kernel Config Decoder / Capability Matrix

## Summary

v197 adds host-side decoding of the A90 `/proc/config.gz` into a capability
matrix. This is a host tooling/reporting change only; latest verified native
init remains `A90 Linux init 0.9.59 (v159)`.

## Changes

- Added `scripts/revalidation/a90_kernel_tools.py`.
- Added `scripts/revalidation/kernel_config_decode.py`.
- Generated CONFIG-level capability evidence for firewall/network exposure,
  cgroup/PSI, BPF, pstore/ramoops, tracefs/ftrace, Wi-Fi stack prerequisites,
  and namespace/TUN support.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_kernel_tools.py \
  scripts/revalidation/kernel_config_decode.py
```

Result: PASS.

```bash
python3 scripts/revalidation/kernel_config_decode.py \
  --out tmp/kernel-config/v197-kernel-config.md \
  --json-out tmp/kernel-config/v197-kernel-config.json
```

Result: PASS.

Evidence:

- `tmp/kernel-config/v197-kernel-config.md`
- `tmp/kernel-config/v197-kernel-config.json`

Summary:

- Parsed CONFIG entries: `5724`
- Version match: `A90 Linux init 0.9.59 (v159)` — PASS
- `netfilter_nftables`: present through legacy iptables/conntrack; nftables core is not enabled.
- `cgroup_psi_resource_control`: present, including `CONFIG_PSI=y`.
- `bpf_observability`: present, but `CONFIG_BPF_JIT=n`.
- `pstore_ramoops`: present.
- `tracefs_ftrace_debug`: present, with some dynamic/probe features absent.
- `wifi_wireless_stack`: kernel stack prerequisites are partly present, but this does not override the existing native `wlan/rfkill/module` no-go gate.

## Acceptance

- `/proc/config.gz` is decoded over the existing bridge without device mutation.
- Capability matrix is available as Markdown and JSON.
- No boot image, service lifecycle, mount state, tracing state, or Wi-Fi state was changed.

## Next

v198 should use the CONFIG evidence to inventory netfilter/iptables/nftables
runtime exposure controls before any Wi-Fi or broader network exposure work.
