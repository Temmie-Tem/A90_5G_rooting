# Native Init V2204 File-Operations Slide Anchor

## Decision

- Decision: `v2204-file-ops-anchor-exact-slide`
- Pass: `true`
- Exact slide: `true`
- Best slide: `0x8179c`
- Reason: at least two known file_operations anchors agree

## Method

- Opens `/dev/null`, `/dev/zero`, and `/proc/version` read-only in the helper process.
- Uses `sched:sched_switch` plus `bpf_get_current_task()` filtered to the helper pid.
- Reads `task->files->fdt->fd[]->file->f_op` with `bpf_probe_read` only.
- Compares runtime f_op pointers against the bit-exact stock `System.map` recovered in V2197.

## Result

- Samples: `160`
- Read errors: `0`
- task/files/fdt: `0xffffffc080cbcd80` / `0xffffffc080c1f000` / `0xffffffc080c1f028`

| Field | Runtime f_op | Candidate slides |
| --- | --- | --- |
| `fd0_fop` | `0xffffff8009bfbbb0` | `null_fops` 0x8179c |
| `fd1_fop` | `0xffffff8009bfbca0` | `zero_fops` 0x8179c |
| `fd2_fop` | `0xffffff8009aa5180` | `version_proc_fops` 0x7b884, `proc_reg_file_ops` 0x7ecf4, `proc_reg_file_ops_no_compat` 0x7ee4c |

## Safety

- read_only_bpf: `true`
- probe_write_user_executed: `false`
- cgroup_attach: `false`
- wifi_action: `false`
- flash_reboot: `false`

## Evidence

- Private run: `workspace/private/runs/kernel/v2204-file-ops-anchor-20260612-012852`
- System.map: `workspace/private/runs/kernel/v2197-stock-kallsyms/System.map`
- Helper SHA-256: `3b3418c5ea0c1c4dc912de17454d6af25641d15b06f4b0fc9f62a8ed46b07d9e`
- Selftest fail=0: `true`
