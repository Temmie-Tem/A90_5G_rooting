# S22+ FYG8 R4W1-C Connected Source Host GO

Date: 2026-07-20 KST

Verdict: `GO_TO_SEPARATE_R4W1C_CONNECTED_POLICY_BINDING`

Scope: host-only implementation, static validation, and independent review of
the R4W1-C connected read-only qualification gate. No device contact, USB
enumeration, reboot, Download transition, Odin transfer, flash, partition write,
or live authorization occurred.

## Contract

The helper exposes only `--offline-check` and
`--connected-read-only-dry-run`. It has no candidate transfer, rollback, or
partition-write surface. The connected mode requires a complete ACTIVE clause
in `AGENTS.md` plus the fresh exact acknowledgement
`S22PLUS-FYG8-R4W1C-CONNECTED-READ-ONLY-DRY-RUN`.

The proposed clause authorizes one successful bounded read-only qualification.
It binds the R4W1-C watchdog carrier, Magisk and stock cleanup artifacts, full
FYG8 firmware evidence, hardened Odin transition core, Odin binary, helper,
test, inactive draft, and the complete clause identity. A connected PASS cannot
activate a live candidate exception.

## Final Sources

```text
workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1c_connected_gate.py
  size    54734
  SHA256  fa4e9b0a77032fbb8b17affb2ae985b80c990b6e4b07c0ee095328cfd80516b9

tests/test_s22plus_fyg8_r4w1c_connected_gate.py
  size    32764
  SHA256  98938da61fc6a3f95389a31f019950fa00b3e6575687aab8d1edf5d070240251

docs/operations/S22PLUS_FYG8_R4W1C_CONNECTED_EXCEPTION_DRAFT_2026-07-20.md
  size    5774
  SHA256  e1ff33327385b22e25e27ebd541b4103a2ce6b39408148d9e3318052c3eb2af2

docs/operations/S22PLUS_FYG8_R4W1C_CONNECTED_BINDING_CLAUSE_2026-07-20.md
  size    7186
  SHA256  f472bfdb2a94f9c269281cd2b5db7330caaaa5bf7d882ddf9f121a39657e1661
```

The exact fenced policy payload SHA256 is
`35f1d2cf8b9a4b25bac108832fb3f9ec9fd37e05c1b03f9fa34eeb5367c17ffa`.
It contains one ACTIVE sentinel, no INACTIVE or RETIRED sentinel, all 16 values
required by the helper's policy parser, and the exact inactive-draft pin.

## Evidence Closure

The connected wrapper holds the PID/thread-bound Odin transaction lease across
initial clean-empty enumeration, Android and retained-log collection, final
identity and boot-ID continuity checks, final clean-empty enumeration, durable
evidence publication, PASS creation, and complete PASS reopening. Every Odin
snapshot, phase receipt, index segment, observer, stderr file, preflight,
timeline, result, and PASS record is reopened by direct path, size, SHA256, and
stable bytes. Parent-component symlinks are rejected for both run evidence and
the canonical private state path.

The device-side operation set is read-only. The helper requires exact FYG8
Android and Magisk identity, stock `vendor_boot`/DTBO/recovery identities, live
`sec_log_buf`, exact platform bind, pstore console absence, a complete bounded
`/proc/ap_klog` capture, and two complete byte-identical `/proc/last_kmsg`
captures with a clean R4W1-B marker namespace.

## Validation

```text
R4W1-C connected focused tests and relevant cores   140 passed
py_compile                                           PASS
ResourceWarning-as-error                             PASS
git diff --check                                     PASS
full 9.68 GB offline artifact gate                   PASS
offline verdict                                      PASS_R4W1C_CONNECTED_GATE_OFFLINE_CHECK
```

The offline result reported no device contact, device write, reboot, Download
transition, Odin transfer, or flash. The connected PASS path was absent and the
policy was inactive, as required before binding.

Five independent read-only review rounds closed four successive findings sets:
policy continuity, whole-transaction evidence closure, prepared-phase
semantics, result and parent run-directory symlinks, and canonical PASS parent
symlinks. The final delta review found no HIGH or MEDIUM issue and returned:

```text
Source commit: GO
Separate connected policy activation: GO
```

## Next Gate

Commit this source packet first. Then copy the reviewed fenced block
byte-for-byte into `AGENTS.md` in a separate policy-binding commit and rerun the
complete host validation. Only after that commit may the attending operator
supply the exact connected acknowledgement. Generic approval is insufficient.
This report grants no device contact or live authority.
