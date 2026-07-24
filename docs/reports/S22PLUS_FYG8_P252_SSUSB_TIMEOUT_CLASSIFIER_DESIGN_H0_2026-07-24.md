# S22+ FYG8 P2.52 SSUSB Timeout Classifier Design (H0)

Date: 2026-07-24 KST
Tier: H0 host-only
Status: `DESIGN_COMPLETE_IMPLEMENTATION_PENDING`

## Scope

P2.50 reached `gcc-waipio` and then recorded `ETIMEDOUT` at the existing
`a600000.ssusb` gate:

```text
stage=0x84 item_index=9 detail=110
```

P2.51 and P2.51b narrowed that timeout to a bounded runtime discriminator.
P2.52 will implement that discriminator without adding a module, checkpoint
stage, retained-record field, policy layer, or device action.

This design changes no source, kernel, image, candidate, or live authority. It
defines the implementation and validation closure for the next H0 unit.

## Preserved Contract

The following are invariants:

- the P2.48 80-step sequence is byte-for-byte unchanged;
- SSUSB remains stage `0x84`, item and gate index `9`;
- terminal success remains `0x8f`;
- the 59-module plan and 12 bind gates are unchanged;
- the original 20-second deadline remains one global gate-loop deadline;
- `0x001..0x7ff`, `0x800..0x8ff`, and `0x900..0x9ff` retain their P2.48
  errno, prior-regression, and read-error meanings;
- generation remains monotonic and no failure is written at an earlier stage;
- retained record layout and CRC behavior remain unchanged; and
- P2.48 `generate()` output and decoder policy behavior remain byte-exact.

The central selector registry necessarily changes to register P2.52. That
registry growth must not alter the output or behavior of selecting P2.45 or
P2.48, but the selector file itself is not claimed to remain byte-identical.

P2.52 is a new versioned source contract. It delegates the P2.48 step
descriptor and adds an exact classifier-detail whitelist only for stage
`0x84`.

## Single Source Of Truth

The P2.52 contract specification will define each executable classifier item
once:

```text
ClassifierDetail(
    value,
    name,
    category,
    path,
    expected_symlink_basename,
)
```

The same descriptors generate:

1. the userspace runtime bind-check table;
2. the userspace checkpoint detail whitelist;
3. the kernel retained-writer detail whitelist;
4. the host decoder's accepted values and semantic names; and
5. exhaustive and mutation-test expectations.

There must be no separate handwritten range such as `0xa00..0xaff`, no
independent upper-bound constant, and no duplicate path-to-detail map.

The P2.52 executable map must equal the P2.51/P2.51b audit output exactly. The
audits remain evidence inputs; P2.52 becomes the execution source of truth.

Two P2.48 validation orders must be replaced, not merely appended:

1. its checkpoint failure wrapper currently rejects every positive detail above
   `0x9ff` before `publish()`, so no `0xaXX` value can reach the validator;
2. its detail validator applies the low-byte gate-count check before range
   dispatch, so it would misread `0xa30` as gate index 48.

P2.52 preserves negative errno normalization to `0x001..0x7ff`. Positive
structured detail is passed to the generated exact validator instead of a
broad maximum check. The validator first dispatches by detail band, applies
low-byte gate-index rules only to `0x800..0x9ff`, and compares `0xaXX` only
against the generated stage/detail whitelist.

## Exact Detail Map

All values below are accepted only as failure detail at stage `0x84`, item 9.
Every other value in `0xa00..0xfff`, including `0xa00`, remains rejected.

| Priority | Detail | Meaning at classification instant |
|---:|---:|---|
| 1 | `0xa01` | exact USB3 GDSC bind absent |
| 2 | `0xa02` | exact PDC bind absent |
| 3 | `0xa03` | qnoc aggre1 bind absent |
| 4 | `0xa04` | qnoc MC virtual bind absent |
| 5 | `0xa05` | qnoc config bind absent |
| 6 | `0xa06` | qnoc GEM bind absent |
| 7 | `0xa07` | EUD bind absent |
| 8 | `0xa08` | Waipio TLMM bind absent |
| 9 | `0xa09` | SS PHY `vdd` RPMh `ldob1` wrapper bind absent |
| 10 | `0xa0a` | SS PHY `core` RPMh `ldob6` wrapper bind absent |
| 11 | `0xa0b` | HS PHY `vdd` RPMh `ldob5` wrapper bind absent |
| 12 | `0xa0c` | HS PHY `vdda18` RPMh `ldoc1` wrapper bind absent |
| 13 | `0xa0d` | HS PHY `vdda33` RPMh `ldob2` wrapper bind absent |
| 14 | `0xa20` | exact HS PHY bind absent |
| 15 | `0xa21` | exact SS PHY bind absent |
| 16 | `0xa10` | all enumerated binds present, but `waiting_for_supplier=1` |
| 17 | `0xa30` | all enumerated dependencies pass entry/exit snapshots; parent stays absent through grace |

Numeric order does not define evaluation order. In particular, PHY checks run
before `0xa10` so a known missing PHY is not collapsed into an unknown supplier
result.

The executable bind map is:

```text
0xa01 /sys/bus/platform/drivers/gdsc/149004.qcom,gdsc
0xa02 /sys/bus/platform/drivers/qcom-pdc/b220000.interrupt-controller
0xa03 /sys/bus/platform/drivers/qnoc-waipio/16e0000.interconnect
0xa04 /sys/bus/platform/drivers/qnoc-waipio/soc:interconnect@1
0xa05 /sys/bus/platform/drivers/qnoc-waipio/1500000.interconnect
0xa06 /sys/bus/platform/drivers/qnoc-waipio/19100000.interconnect
0xa07 /sys/bus/platform/drivers/msm-eud/88e0000.qcom,msm-eud
0xa08 /sys/bus/platform/drivers/waipio-pinctrl/f000000.pinctrl
0xa09 /sys/bus/platform/drivers/qcom,rpmh-regulator/17a00000.rsc:rpmh-regulator-ldob1
0xa0a /sys/bus/platform/drivers/qcom,rpmh-regulator/17a00000.rsc:rpmh-regulator-ldob6
0xa0b /sys/bus/platform/drivers/qcom,rpmh-regulator/17a00000.rsc:rpmh-regulator-ldob5
0xa0c /sys/bus/platform/drivers/qcom,rpmh-regulator/17a00000.rsc:rpmh-regulator-ldoc1
0xa0d /sys/bus/platform/drivers/qcom,rpmh-regulator/17a00000.rsc:rpmh-regulator-ldob2
0xa20 /sys/bus/platform/drivers/msm-usb-hsphy/88e3000.hsphy
0xa21 /sys/bus/platform/drivers/msm-usb-ssphy-qmp/88e8000.ssphy
```

For each row, `expected_symlink_basename` is the final path component.

Each bind check uses `newfstatat(..., AT_SYMLINK_NOFOLLOW)` plus bounded
`readlinkat()`. A path counts as present only when it is a symlink and its
target basename equals the descriptor's exact expected device basename.
`ENOENT`, a non-symlink, or a wrong target is the mapped absent result. Other
read or validation failures use the existing frontier read-error detail
`0x909`.

## Waiting Attribute

The exact source creates:

```text
/sys/devices/platform/soc/a600000.ssusb/waiting_for_supplier
```

before driver bind under strict `fw_devlink`, emits exactly `0\n` or `1\n`,
and removes the attribute after successful bind.

The runtime therefore:

- reads at most three bytes;
- accepts only exact `0\n` or `1\n` followed by EOF;
- treats truncation, extra data, malformed content, or non-`ENOENT` I/O error
  as `0x909`; and
- never treats attribute `ENOENT` alone as supplier-ready.

If the attribute disappears, the runtime immediately rechecks the exact SSUSB
driver symlink. A now-bound parent advances stage `0x84`; an absent parent plus
an absent attribute records `0x909`.

## Classifier Algorithm

The classifier runs only when the existing global deadline expires with
`completed == 9`.

```text
1. Revalidate previously completed gates 0..8 in ascending order.
2. Recheck the exact SSUSB parent bind.
   - bound: publish normal progress at 0x84 and continue;
   - unexpected read error: fail at 0x84 with 0x909.
3. Read waiting_for_supplier exactly.
4. Check the 15 descriptor bind paths in priority order.
   - first absent path: propose that path's detail;
   - unexpected read error: propose 0x909.
5. Recheck the parent.
6. Re-read waiting_for_supplier to close the scan race.
   - value 1: propose 0xa10;
   - value 0: enter the one allowed grace;
   - absent/malformed/error: propose 0x909.
```

Every terminal classifier result passes through one common finalizer:

```text
1. revalidate gates 0..8 in ascending order;
2. if one regressed or failed validation, emit its existing 0x8XX/0x9XX detail;
3. recheck the SSUSB parent;
4. if bound, publish normal 0x84 progress;
5. otherwise publish the proposed classifier detail.
```

This preserves P2.48's earliest-regression priority even if a prior gate
changes during classification. The parent recheck then wins over the proposed
classifier failure, preventing a concurrent successful bind from being
reported as a missing supplier.

The classifier reports state at a bounded observation instant. A path that
binds after an `0xa01..0xa21` record does not invalidate that observation and
does not turn it into proof of a permanent root cause.

## Five-Second Grace

Grace is entered only after the global deadline when:

- the SSUSB parent is still absent;
- all 15 exact bind checks pass; and
- the second exact `waiting_for_supplier` read is `0`.

The grace rules are:

- derive one deadline from `CLOCK_MONOTONIC` with checked arithmetic;
- add exactly five seconds;
- never reset, extend, or re-enter that deadline;
- retain the existing 100 ms maximum poll interval;
- revalidate prior gates 0..8 in ascending order on each poll;
- check only the SSUSB parent as the forward gate during grace; and
- preserve the earliest prior-gate regression at current frontier `0x84`.

If SSUSB binds, publish ordinary progress for `0x84` and resume the existing
gate loop. The original global deadline is not reset, so downstream gates do
not inherit a new five-second budget.

At grace expiry, revalidate prior gates and run the full classifier again:

- parent bound: publish progress;
- newly absent known path: emit its exact detail;
- `waiting_for_supplier=1`: emit `0xa10`;
- all enumerated dependencies still ready with parent absent: emit `0xa30`;
- malformed or unreadable state: emit `0x909`.

This final rescan prevents a provider that disappears during grace from being
misreported as `0xa30`.

## Versioned Implementation Closure

Implementation should add only:

- `s22plus_fyg8_p252_contract_spec.py`;
- `s22plus_fyg8_p252_e1_decoder.py`;
- `s22plus_fyg8_p252_source_contract.py`;
- focused P2.52 tests; and
- one P2.52 registration in `s22plus_fyg8_source_contracts.py`.

The source adapter starts from `p248.generate()` and performs bounded,
count-checked transforms. It materializes a new P2.52 runtime and checkpoint
client while leaving the P2.44 plan header unchanged.

Do not edit P2.48 contract behavior in place. Do not copy the full P2.48
adapter. P2.52 should delegate unchanged generation, linked-audit helpers, and
layout behavior where their contracts still apply.

The P2.52 decoder keeps the raw `active` slot shape unchanged and adds semantic
classification separately. This avoids breaking generic Process v2 evidence
code that compares the raw active slot.

## Static Validation Gate

Implementation is complete only when host-only validation proves:

1. P2.48 generated outputs and historical decoder behavior are unchanged.
2. P2.52 step sequence, item indices, module plan, and terminal stage equal
   P2.48 exactly.
3. Only the 17 exact classifier details are newly accepted, only at `0x84`.
4. Every other `0xa00..0xfff` value is rejected at every stage.
5. P2.51/P2.51b path, priority, and detail output equals the P2.52 descriptor.
6. Runtime, checkpoint validator, kernel validator, and decoder derive from the
   same descriptor.
7. Global timeout remains 20 seconds and grace is one-shot and at most five
   seconds.
8. Attribute disappearance always causes a parent recheck.
9. Prior-gate regression checks remain active during grace.
10. Grace expiry performs a full final rescan before `0xa30`.
11. The userspace output cross-compiles as static AArch64 and two links are
    byte-identical.
12. The kernel patch applies cleanly, with no image or kernel build required.
13. Reachable-record enumeration includes all 17 new details and no reserved
    neighbor.
14. Mutations to one path, basename, detail, priority, waiting parser, grace
    duration, final rescan, or whitelist are rejected.
15. Positive `0xaXX` detail reaches `publish()` while unknown positive values
    remain rejected.
16. `0xa30` is accepted as a classifier value and is never interpreted as gate
    index 48; low-byte gate-index checks remain exclusive to `0x8XX/0x9XX`.
17. Every `0xaXX`/`0x909` terminal path crosses the common prior-gate and parent
    finalizer; mutations that bypass it are rejected.

A later final candidate build must additionally prove linked whitelist-table
bytes and validator dataflow in `vmlinux`. Full-LTO belongs to that candidate
unit, not this implementation loop.

## Non-Goals

P2.52 does not add:

- `debugfs/devices_deferred` parsing;
- probe-entry instrumentation or printk dependency;
- per-provider checkpoint stages;
- more USB modules;
- SMMU checks before the SSUSB parent frontier;
- configfs, gadget, UDC, ACM, shell, NCM, or Debian behavior; or
- device authority.

## Proof Limit

The implementation can make one future observation discriminate the known
branches. It cannot identify the current live root cause without a later
authorized candidate run.

`0xa30` will mean that all enumerated dependencies passed both the grace-entry
and grace-exit snapshots while the parent stayed absent at every grace poll.
It does not prove that every nested bind remained continuously present between
the two snapshots. It will narrow the next H0 unit to probe-internal/deferred
behavior, but it will not by itself identify a specific return site inside
`dwc3_msm_probe()`.

## Decision

`GO` for bounded P2.52 implementation under H0.

No candidate build, connected read, device action, or F1 authorization follows
from this design.
