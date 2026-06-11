# Native Init V2222 Boot-Window Preflight Contract

## Result

- decision: `v2222-boot-window-preflight-ready-approval-required`
- pass: `true`
- runner: `workspace/public/src/scripts/revalidation/native_kernel_a90_boot_window_preflight_v2222.py`
- evidence: `workspace/private/runs/kernel/v2222-boot-window-preflight-20260612-065709/`
- contract: `workspace/private/runs/kernel/v2222-boot-window-preflight-20260612-065709/boot_window_contract.json`
- selftest: `fail=0`

## What Ran

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_kernel_a90_boot_window_preflight_v2222.py
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/native_kernel_a90_boot_window_preflight_v2222.py
```

The runner is preflight-only. It checked bridge state, native version, helper
inventory, selftest, and the V2221 current-window collector-parser contract.

It did not reboot, flash, create or enable tracefs events, attach BPF, execute
`probe_write_user`, scan/connect Wi-Fi, change routes, or write partitions.

## Evidence Summary

| Signal | Value |
| --- | ---: |
| bridge ready | `true` |
| native init | `0.9.261 build=v2189-security-p0-stage-fix` |
| `/bin/a90_android_execns_probe` | `v427` |
| `/cache/bin/a90_android_execns_probe` | `v286` |
| `a90*` events present | `21` |
| `a90*` events enabled | `21` |
| current-window hits | `0` |
| V2221 contract pass | `true` |
| selftest | `fail=0` |

Helper inventory:

| Path | Version | SHA-256 |
| --- | --- | --- |
| `/bin/a90_android_execns_probe` | `v427` | `a4ef028aee167ab6a66b17389ade37427e85647d18e45270634f666b8efe1a44` |
| `/cache/bin/a90_android_execns_probe` | `v286` | `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f` |

## Contract

The generated boot-window contract marks the next live capture as approval
required. It allows only:

1. rollbackable test-boot or an already-active helper-owned boot window;
2. helper-owned `a90*` trace_uprobe registration and collection;
3. V2220 parser postprocess;
4. stock BPF only for static kernel tracepoints, if separately required.

It explicitly keeps these blocked without new approval:

1. BPF attach to dynamic `a90*` trace_uprobe events;
2. `probe_write_user`;
3. cgroup-BPF attach;
4. Wi-Fi scan/connect/credentials/DHCP/routes/external ping;
5. PMIC/GPIO/GDSC/eSoC/PCI rescan/platform bind/unbind;
6. partition writes or `sda29` writes.

The expected boot-window sequence remains:

```text
a90cnss:wlfw_start
→ a90cnss:wlfw_service_request
→ a90cnss:wlfw_cap_qmi
→ a90cnss:wlfw_bdf_entry
```

## Interpretation

V2222 does not claim a new boot-window observation. It establishes that the
current state is ready for an approved boot-window run:

- bridge and native command transport are live;
- native init is on the current `0.9.261` baseline;
- the active helper in `/bin` is `v427`, while `/cache/bin` remains an older
  `v286` artifact and should not be treated as current truth;
- V2221 can still collect and postprocess the current no-hit window;
- selftest remains `fail=0`.

The next blocker is procedural, not technical: actual boot-window capture needs
explicit approval because it requires a reboot/test-boot or equivalent early
helper window.

## Next

V2223 should execute the approved boot-window capture only after explicit user
approval. It should reuse this contract and immediately feed the helper summary
or collector summary into the V2220 parser.
