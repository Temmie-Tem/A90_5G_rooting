# Native Init v238 Linker Early-Abort Call-Site Map Plan

## Summary

- v238 continues from v237 without changing the PID1 boot image.
- Goal: map captured fault address `0xa1` / abort code `161` to the exact
  `__early_abort` caller in the matching Samsung `linker64` ELF.
- Scope is host-side evidence tooling and documentation only; no Android daemon
  start, Wi-Fi scan/connect, rfkill write, credential handling, or partition
  write.

## Inputs

- v237 ELF evidence: `tmp/wifi/v237-linker-offset-symbolize-live/files/linker64`.
- v237 manifest: `tmp/wifi/v237-linker-offset-symbolize-live/manifest.json`.
- v236/v237 crash fact: `fault_addr=0xa1` and file offset `0x1002f4` inside
  `__dl__ZL13__early_aborti+0x14`.
- Reference source pattern: AOSP bionic `libc_init_common.cpp` shows
  `__early_abort(line)` deliberately writes through the line/abort-code address,
  and `__nullify_closed_stdio()` falls back from `/dev/null` to
  `/sys/fs/selinux/null` before aborting.

## Implementation

- Add `scripts/revalidation/wifi_linker_early_abort_map.py`.
- Modes:
  - `plan`: write private plan-only evidence.
  - `analyze`: disassemble local linker64, find all calls to
    `__dl__ZL13__early_aborti`, recover the previous `mov w0, #imm`, and match
    that constant against the captured fault address.
- Capture host evidence:
  - full `objdump -d` output;
  - `strings -a -tx` output;
  - bounded per-call disassembly context;
  - `manifest.json` and `summary.md`.

## Analysis Rules

1. Parse v237 manifest for captured `fault_addr` unless `--fault-addr` overrides
   it.
2. Run host `objdump -d` on the local `linker64` ELF.
3. Locate every `bl ... <__dl__ZL13__early_aborti>` instruction.
4. Scan backward within the same function for the nearest `mov w0, #imm` and
   record that immediate as the abort code.
5. Select the call site whose abort code equals the captured fault address.
6. Use local strings evidence to correlate `/dev/null`, `/sys/fs/selinux/null`,
   `__dl_libc_init_common.cpp`, and `__libc_init_AT_SECURE`.

## Test Plan

```bash
python3 -m py_compile scripts/revalidation/wifi_linker_early_abort_map.py
python3 scripts/revalidation/wifi_linker_early_abort_map.py \
  --out-dir tmp/wifi/v238-plan-smoke plan
python3 scripts/revalidation/wifi_linker_early_abort_map.py \
  --out-dir tmp/wifi/v238-linker-early-abort-map-live analyze
git diff --check
```

## Acceptance

- PASS when abort code `0xa1` maps to one `__early_abort` caller.
- PASS reason must distinguish the result from Wi-Fi daemon behavior: this is a
  generic Android linker/private namespace abort, not a `cnss-daemon` specific
  crash.
- Next step must remain bounded to private namespace repair, starting with
  `/dev/null` materialization, before any Wi-Fi daemon start/scan/connect.

## Guardrails

- Host-side ELF/disassembly analysis only.
- No device command execution.
- No Android daemon execution.
- No Wi-Fi scan/connect.
- No rfkill write.
- No credential collection.
- No system/vendor write.
