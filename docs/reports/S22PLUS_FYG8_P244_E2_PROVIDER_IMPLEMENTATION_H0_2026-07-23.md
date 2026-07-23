# S22+ FYG8 P2.44 E2 provider implementation

Date: 2026-07-23 KST
Tier: H0 host-only
Status: `PASS_P244_E2_PROVIDER_IMPLEMENTATION_HOST_ONLY`
Device contact: none
Live authority: none

## Verdict

P2.44 implements the P2.43 replacement contract without changing the exact
59-module E2 plan or adding the unrelated display clock module. The generated
runtime now observes 12 ordered read-only predicates:

```text
hwspinlock -> smem -> cmd-db
  -> psci-domain -> apps-rsc -> apps-rpmh-clock
  -> apps-rpmh-cxlvl -> apps-rpmh-mxlvl -> gcc-waipio
  -> ssusb -> dwc3-core -> udc
```

The 59 module stages remain `0x40..0x7a`. Gate stages are `0x7b..0x86`, and
terminal success remains `0x8f`. The profile-3 kernel sequence therefore has
80 entries and 323,585 reachable record variants.

This closes source implementation and static validation only. It does not
prove that the P2.42 timeout was caused by the missing display-clock supplier,
nor that any replacement provider, GCC, SSUSB, DWC3, UDC, or host USB state
binds under direct PID 1.

## Implementation Shape

The historical P2.41/P2.42 inputs remain byte-identical. A host-only adapter
loads four exact SHA-pinned files and applies count-checked transformations:

- the plan replaces the historical eight-gate table with the exact 12-gate
  table;
- the runtime changes the gate count and terminal gate stage, makes the
  driver-gate/UDC split depend on the table length, and emits 11 exact driver
  basenames;
- the checkpoint transition model extends the final E2 gate from `0x82` to
  `0x86`; and
- the kernel patch extends the profile-3 sequence tail through `0x86` while
  preserving success at `0x8f`.

Every replacement checks its expected source cardinality. Any historical
input drift or generated-output drift fails closed. The generated identities
are pinned independently of the historical source identities.

The adapter and checker are:

```text
workspace/public/src/scripts/revalidation/
  s22plus_fyg8_p244_e2_provider_sources.py
  s22plus_fyg8_p244_e2_static_checker.py
```

No generated C/header/patch copy is tracked. P2.45 candidate construction must
materialize the four verified outputs from this adapter rather than editing
or copying the historical P2.41 files by hand.

## Exact Provider Contract

| Full gate order | Gate | Read-only predicate |
|---:|---|---|
| 1 | `hwspinlock` | `/sys/bus/platform/drivers/qcom_hwspinlock/soc:hwlock` |
| 2 | `smem` | `/sys/bus/platform/drivers/qcom-smem/soc:qcom,smem` |
| 3 | `cmd-db` | `/sys/bus/platform/drivers/cmd-db/80860000.aop_cmd_db_region` |
| 4 | `psci-domain` | `/sys/bus/platform/drivers/psci-cpuidle-domain/soc:psci` |
| 5 | `apps-rsc` | `/sys/bus/platform/drivers/rpmh/17a00000.rsc` |
| 6 | `apps-rpmh-clock` | `/sys/bus/platform/drivers/clk-rpmh/17a00000.rsc:qcom,rpmhclk` |
| 7 | `apps-rpmh-cxlvl` | `/sys/bus/platform/drivers/qcom,rpmh-regulator/17a00000.rsc:rpmh-regulator-cxlvl` |
| 8 | `apps-rpmh-mxlvl` | `/sys/bus/platform/drivers/qcom,rpmh-regulator/17a00000.rsc:rpmh-regulator-mxlvl` |
| 9 | `gcc-waipio` | `/sys/bus/platform/drivers/gcc-waipio/100000.clock-controller` |
| 10 | `ssusb` | `/sys/bus/platform/drivers/msm-dwc3/a600000.ssusb` |
| 11 | `dwc3-core` | `/sys/bus/platform/drivers/dwc3/a600000.dwc3` |
| 12 | `udc` | `/sys/class/udc/a600000.dwc3` |

`af20000.rsc` and `dispcc-waipio.ko` are absent from the generated plan,
runtime, checkpoint, and linked executable.

## Static Closure

The checker proves:

- all four historical input SHA256 identities and all four generated output
  SHA256 identities;
- the unchanged 59-module order and all 210 module constraints;
- exactly 12 gate rows and 11 driver basenames;
- clean application of the generated kernel patch to the exact private FYG8
  source tree;
- exact profile-3 sequence length 80 and terminal `0x8f`;
- 323,585 reachable profile-3 record variants;
- unchanged 90,114 E1A/E1B reachable record variants after the temporary
  profile-3 model is restored;
- two byte-identical static AArch64 links;
- no interpreter, dynamic segment, or undefined symbol;
- the exact run ID once and every gate path once in the linked executable;
- the existing child checkpoint ABI and QEMU exit/token contract;
- the exact 59 vendor module bytes and absence of `sec_log_buf.ko`; and
- no device, build, image, manifest, Odin, flash, sysfs-write, configfs-write,
  or live-authority action.

The generated static AArch64 `/init` identity during validation was:

```text
sha256=b5ae9f1c643cc557f1a5efb0ef36ef22d7adf42e6056b7dacd84f4c4daaca154
size=69360
```

That file was a temporary host validation output, not a candidate artifact.

Validation passed:

```text
py_compile: 3 files
P2.44 focused tests: 11/11
P2.41-P2.44 focused regression tests: 42/42
source generator verdict: PASS_P244_E2_PROVIDER_SOURCES_HOST_ONLY
static checker verdict: PASS_P244_E2_PROVIDER_IMPLEMENTATION_HOST_ONLY
```

The first independent review returned `NO-GO` because the checker derived the
six preserved gates from the same generator table. A first fix derived their
IDs, kinds, and paths from the SHA-pinned P2.41 table plus the independently
audited P2.43 provider chain. A second review then found that driver basenames
still came only from the generator table. The final fix derives all 11
basenames from the independently verified gate paths and compares that result
with the generated runtime table. Public-input tests exercise this relation
without requiring private FYG8 artifacts. Final independent re-review passed
with no remaining finding.

## Evidence Limits

`VERIFIED`:

- P2.44 implements the exact P2.43 source contract;
- the historical module plan and earlier evidence artifacts are unchanged;
- stage capacity and record exhaustiveness cover the expanded gate range; and
- implementation authority remains H0.

`NOT PROVEN`:

- P2.42's live runtime supplier state or exact root cause;
- direct-PID1 bind of any newly observed provider;
- GCC, SSUSB, DWC3, or UDC success with this implementation;
- USB enumeration or transport; and
- candidate build, packaging, D0 qualification, F1 readiness, or live
  authority.

## Next Unit

P2.45 is a separate H0 candidate-construction unit. It must materialize the
P2.44 generated sources, perform reproducible final Full-LTO builds, create
one deterministic boot-only AP, close the effective rootfs and artifact
identities, and prepare an offline Process v2 manifest.

No device contact or live approval follows from this report. Connected D0 and
fresh exact F1 approval remain later, separate steps.
