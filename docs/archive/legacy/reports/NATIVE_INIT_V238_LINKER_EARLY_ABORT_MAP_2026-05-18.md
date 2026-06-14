# Native Init v238 Linker Early-Abort Map

## Summary

- Goal: map v236/v237 captured fault address `0xa1` to the exact bionic linker
  `__early_abort` caller.
- Result: PASS / `linker-early-abort-dev-null-open-failed`.
- No PID1 boot image update, device command, Android daemon execution, Wi-Fi
  scan/connect, rfkill write, credential handling, or partition write was used.

## Implementation

Added host tool:

- `scripts/revalidation/wifi_linker_early_abort_map.py`

Added plan:

- `docs/plans/NATIVE_INIT_V238_LINKER_EARLY_ABORT_MAP_PLAN_2026-05-18.md`

Tool modes:

- `plan`: writes private plan-only evidence without device or ELF analysis.
- `analyze`: scans local linker64 disassembly, finds all
  `__dl__ZL13__early_aborti` call sites, recovers each abort-code immediate, and
  matches it to the captured fault address.

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/wifi_linker_early_abort_map.py
python3 scripts/revalidation/wifi_linker_early_abort_map.py \
  --out-dir tmp/wifi/v238-plan-smoke plan
python3 scripts/revalidation/wifi_linker_early_abort_map.py \
  --out-dir tmp/wifi/v238-linker-early-abort-map-live analyze
```

Live host-side result:

```json
{
  "decision": "linker-early-abort-dev-null-open-failed",
  "pass": true,
  "fault_addr": "0xa1",
  "selected_call": {
    "call_site": "0x1000b8",
    "function": "__dl__Z21__libc_init_AT_SECUREPPc",
    "function_delta": "0xa0",
    "abort_code": "0xa1",
    "abort_code_dec": 161,
    "mov_site": "0x1000b4"
  }
}
```

Evidence directory:

```text
tmp/wifi/v238-linker-early-abort-map-live/
```

## Call-Site Map

| call | function | delta | abort code | decimal | mov site |
| --- | --- | --- | --- | --- | --- |
| `0x1000b8` | `__dl__Z21__libc_init_AT_SECUREPPc` | `0xa0` | `0xa1` | `161` | `0x1000b4` |
| `0x1001b8` | `__dl__Z21__libc_init_AT_SECUREPPc` | `0x1a0` | `0xba` | `186` | `0x1001b4` |
| `0x1002cc` | `__dl__Z21__libc_init_AT_SECUREPPc` | `0x2b4` | `0xbd` | `189` | `0x1002c8` |
| `0x1002d4` | `__dl__Z21__libc_init_AT_SECUREPPc` | `0x2bc` | `0x14f` | `335` | `0x1002d0` |
| `0x1002dc` | `__dl__Z21__libc_init_AT_SECUREPPc` | `0x2c4` | `0xc4` | `196` | `0x1002d8` |

Selected caller context:

```text
100064: d0fff857  adrp x23, a000
100068: 91231ef7  add  x23, x23, #0x8c7
100070: aa1703e0  mov  x0, x23
100074: 940001fb  bl   100860 <__dl___open_2>
...
10008c: 90fff857  adrp x23, 8000
100090: 9125a6f7  add  x23, x23, #0x969
100098: aa1703e0  mov  x0, x23
10009c: 940001f1  bl   100860 <__dl___open_2>
...
1000b4: 52801420  mov  w0, #0xa1
1000b8: 9400008a  bl   1002e0 <__dl__ZL13__early_aborti>
```

String context from the same ELF:

```text
0xa8c7 /dev/null
0x8969 /sys/fs/selinux/null
0x4fd9 failed to open /dev/null
0xc72f expected /dev/null fd to be 0, actually %d
0x181ef4 __dl_libc_init_common.cpp
0x19249a __dl__Z21__libc_init_AT_SECUREPPc
```

The disassembly string references line up with the selected caller: first open
uses the string at `0xa8c7` (`/dev/null`), fallback open uses `0x8969`
(`/sys/fs/selinux/null`), then abort code `0xa1` is passed when both paths fail
or stdio cannot be nullified as expected.

## Source Correlation

AOSP bionic `libc_init_common.cpp` documents the same pattern:

- `__early_abort(size_t line)` intentionally crashes by writing through the
  supplied line/abort-code address because stdio may not be safe yet.
- `__nullify_closed_stdio()` opens `/dev/null`, falls back to
  `/sys/fs/selinux/null`, and calls `__early_abort(__LINE__)` if stdio cannot be
  safely associated with one of those null devices.
- `__libc_init_AT_SECURE()` calls that stdio nullification path when the process
  is not PID 1 or `AT_SECURE` is set.

Reference: <https://android.googlesource.com/platform/bionic/+/master/libc/bionic/libc_init_common.cpp>

Samsung's exact line numbers differ from AOSP `master`, so the source match is
used as a structural correlation, not as an exact source-line claim.

## Interpretation

v237 proved the crash instruction is `__early_abort+0x14` / `str wzr, [x8]`.
v238 proves the captured fault address `0xa1` maps to the earlier caller at
`0x1000b8` inside `__libc_init_AT_SECURE`.

The current blocker is therefore narrower than "Android linker crashes": the
private Android execution namespace is missing the null-device context bionic
expects before it will run even `linker64 --list` safely.  This is still a
generic linker process-context blocker, not a Wi-Fi daemon specific blocker.

## Next Step

Recommended v239:

1. update the private namespace helper to create or bind a minimal `/dev/null`
   inside the temporary Android execution root before `chroot`/exec;
2. optionally materialize `/sys/fs/selinux/null` only if `/dev/null` alone does
   not satisfy the linker;
3. rerun the same `linker64 --list` matrix before considering any daemon start.

Wi-Fi daemon start, scan, connect, credentials, DHCP, routing, and rfkill writes
remain blocked until linker list mode gets past this early abort.

## Guardrails

- Host-side ELF/disassembly analysis only.
- No device command execution.
- No Android daemon execution.
- No Wi-Fi scan/connect.
- No rfkill write.
- No credential collection.
- No system/vendor write.
- Host output directories/files are private.
