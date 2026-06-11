# Native Init V2211 ROPP Stack Recovery Audit

## Decision

- Decision: `v2211-ropp-stack-recovery-blocked-by-canonical-pass-through`
- Reason: Existing stack IPs are canonical/aligned and do not yield a strong callsite or joint-key solution.
- Raw stack IPs: `6`
- All canonical/aligned: `true`
- Candidate slides checked: `37`

## Interpretation

- V2211 keeps stack recovery separate from the V2210 RELA-backed callback-table naming layer.
- `stacktrace.c` only calls `ropp_enable_backtrace()` when a saved LR is outside the kernel range or is misaligned inside the kernel range.
- The existing V2195 stack IPs are all canonical and 4-byte aligned, so an encoded-but-canonical value can pass through undecoded.
- Existing evidence does not produce a strong direct/springboard callsite match or a strong shared XOR-key solution. Exact stack symbolization remains blocked for this capture.

## Source Evidence

- stacktrace_c: `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/arch/arm64/kernel/stacktrace.c`
- instrument_py: `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/scripts/rkp_cfp/instrument.py`
- stacktrace_decode_outside_kernel_range: `True`
- stacktrace_decode_misaligned_kernel_range: `True`
- instrument_eor_lr_key: `True`
- instrument_stp_encoded_lr: `True`
- instrument_ldp_decode: `True`

## Callsite Corpus

- Scan range: `0xffffff8008080060` → `0xffffff8009a03084`
- Return-address candidates: `525592`
- Callsite records: `525592`
- Springboard callsite records: `0`
- Joint-key exhaustive search enabled: `false`
- Strong joint-key slide count: `0`
- Joint-key accepted: `false`
- Joint-key rejection: `joint-key exhaustive search skipped because the callsite corpus is dense; raw frame-slot context is required`

## Top Slide Rows

| Slide | Callsite hits | Unique runtime hits | Direct | Springboard | Best key frames | Best key |
| --- | --- | --- | --- | --- | --- | --- |
| `0xfabf0` | 2 | 1 | 2 | 0 | 0 | - |
| `-0x109720` | 2 | 2 | 2 | 0 | 0 | - |
| `0xdd84` | 1 | 1 | 1 | 0 | 0 | - |
| `0x2e38c` | 1 | 1 | 1 | 0 | 0 | - |
| `0x80000` | 1 | 1 | 1 | 0 | 0 | - |
| `-0x92490` | 1 | 1 | 1 | 0 | 0 | - |
| `-0xa9988` | 1 | 1 | 1 | 0 | 0 | - |
| `0xaba14` | 1 | 1 | 1 | 0 | 0 | - |
| `0xaba78` | 1 | 1 | 1 | 0 | 0 | - |
| `0xb6118` | 1 | 1 | 1 | 0 | 0 | - |
| `0x1cd5bc` | 1 | 1 | 1 | 0 | 0 | - |
| `-0x297c` | 0 | 0 | 0 | 0 | 0 | - |

## Raw Stack IPs

| Index | Runtime | Static under top slide | Nearest symbol | Direct | Springboard |
| --- | --- | --- | --- | --- | --- |
| 0 | `0xffffff8009a42334` | `0xffffff8009947744` | `cfg80211_propagate_radar_detect_wk`0xec | true | false |
| 1 | `0xffffff8009a42334` | `0xffffff8009947744` | `cfg80211_propagate_radar_detect_wk`0xec | true | false |
| 2 | `0xffffff8009a429d8` | `0xffffff8009947de8` | `cfg80211_rfkill_set_block`0x588 | false | false |
| 3 | `0xffffff800819ad8c` | `0xffffff80080a019c` | `arm_iommu_detach_device`0x96c | false | false |
| 4 | `0xffffff800819adf0` | `0xffffff80080a0200` | `arm_iommu_detach_device`0x9d0 | false | false |
| 5 | `0xffffff80081131f4` | `0xffffff8008018604` | `-` | false | false |

## Next

- Do not promote V2195 stack IPs to exact symbol names.
- Next live unit, if stack symbolization is still needed: capture raw frame slots (`fp`, `*(fp)`, `*(fp+8)`) and task/key context with the read-only BPF path, or collect same-boot multi-stack diversity before retrying joint-key solving.
- Keep `probe_write_user`, cgroup attach, flash/reboot, and Wi-Fi actions out of this path.

## Safety

- host_only: `true`
- live_device_access: `false`
- probe_write_user_executed: `false`
- cgroup_attach: `false`
- wifi_action: `false`
- flash_reboot: `false`

## Evidence

- Private result: `workspace/private/runs/kernel/v2211-ropp-stack-recovery-audit/result.json`
- V2197 symbolization: `workspace/private/runs/kernel/v2197-stock-kallsyms/symbolization.json`
- V2198 classifier: `workspace/private/runs/kernel/v2198-jopp-ropp-classifier/result.json`
- Stock raw: `workspace/private/runs/kernel/v2197-stock-kallsyms/kernel.raw`
