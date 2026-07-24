# S22+ FYG8 P2.56 qnoc MC virtual and Odin observer H0 analysis

Date: 2026-07-24 KST
Tier: H0 host-only
Status: `PASS_P256_QNOC_FOCUSED_HYPOTHESIS_AND_ODIN_OBSERVER_ANALYSIS_H0`
Device contact: none
Build/image/candidate change: none
Live authority: none

## Executive Verdict

P2.55 detail `0xa04` is no longer only an unexplained missing bind. The exact
FYG8 DT, vendor source, shipped module ELF files, candidate plan, retained
result, and stock topology support one strong static causal hypothesis:

```text
dispcc-waipio.ko absent from the direct-PID1 module plan
  -> /soc/clock-controller@af00000 has no driver
  -> strict fw_devlink holds /soc/rsc@af20000 before rpmh_rsc_probe()
  -> rpmh_rsc_probe() cannot populate its bcm_voter child
  -> the "disp" voter is absent from bcm_voters
  -> mc_virt qcom_icc_rpmh_probe() returns -EPROBE_DEFER
  -> /sys/bus/platform/drivers/qnoc-waipio/soc:interconnect@1 stays absent
  -> P2.55 reports 0xa04
```

This is the leading static explanation, not a live root-cause proof. P2.55 did
not read the intermediate display-clock, display-RSC, or display-voter binds,
did not retain the `PART_DISPLAY` subset value, and did not observe the qnoc
probe return code. No candidate containing `dispcc-waipio.ko` has been tested.

The P2.55 post-rollback exception is separate. Durable USBFS receipts prove
that the measured Odin node A was later replaced in the inventory by
post-rollback node B, with all 15 common nodes retaining immutable identity.
Replaying that exact inventory shape through the current observer reproduces:

```text
UsbfsIdentityError: usbfs inventory membership changed during enumeration
OdinTransitionError: measured USB endpoint evidence failed
```

The failed enumeration itself produced no receipt, so the exact in-flight
exception remains inferred rather than directly recorded. The next correction
is observability-only: persist a bounded typed failure receipt and keep all
endpoint acceptance and transfer behavior fail-closed.

## Evidence Baseline

The analysis used:

- exact P2.55 retained classification, generation 77, stage `0x84`, item 9,
  detail `0xa04`;
- exact materialized 59-module P2.54 plan;
- exact FYG8 `vendor_ramdisk00` and the four relevant shipped module ELF
  files extracted from it;
- exact FYG8 vendor DTB containing four concatenated variants;
- stock `Kernel.tar.gz` plus the FYG8 source delta;
- same-build module inventory and dependency edges;
- same-build stock SSUSB supplier topology;
- exact P2.55 USBFS receipts 76, 77, and 78; and
- the current Process v2 Odin transition and USBFS identity code.

Pinned private-input identities were rechecked:

```text
vendor DTB sha256 = 2cd64d43a4f6b89a7c5523f3ef73fbb84dcad92c6d857e649cd1f0baa7c0080e
base source sha256 = 86e2f73412c65fadff0b15bbf0eac9140610f70250514ac0bddbf3b53fb5f7bf
FYG8 delta sha256 = 23ef2b27de8843e271d41405b3c0b1a71bfa668615c8f0f12a1e5c4395ec851a
```

The FYG8 delta does not replace the qnoc, ICC RPMh, BCM voter, RPMh RSC,
display clock, or Waipio DT members used below.

The candidate boot ramdisk does not contain the 59 stock modules. P2.54
composes its custom boot `/init` with the separately pinned stock
`vendor_ramdisk00`. The focused ELF extraction therefore used that exact
vendor ramdisk, not the candidate `boot.img` ramdisk.

## Exact Shipped ELF Cross-Check

The pinned vendor ramdisk decompressed to the previously verified
`63,974,144`-byte newc archive. Four directly relevant modules were extracted
to temporary host storage only:

| Module | Size | SHA256 | P2.54 closure |
|---|---:|---|---|
| `dispcc-waipio.ko` | `116,168` | `7e4c404e639996982bdbcc08350139a09ab13b24de90cade81f8cfc8d71dacc5` | omitted from plan |
| `icc-bcm-voter.ko` | `23,432` | `7164f3d8851d2b1d0a132f7dde621cfba5150946e4bd9946dfd6da071e693e3f` | exact match |
| `icc-rpmh.ko` | `29,352` | `5c68e9b5328acffdad2a94d73f482f7d64a095693f85d8ed3b6736bfd9288bfc` | exact match |
| `qnoc-waipio.ko` | `201,496` | `d2792c954fdd9c85d40bdd1fc726d554914573a6ecb5057af675ecd62765cb40` | exact match |

All four are non-stripped AArch64 relocatable ELF objects. Their symbols and
relocations independently match the source-level chain:

- `qnoc_probe()` calls `qcom_icc_rpmh_probe()` and returns its error;
- `waipio_aggre1_noc` has one voter, whose relocation resolves to `hlos`;
- `waipio_mc_virt` has two voters, whose relocations resolve to `hlos` and
  `disp`;
- `qcom_icc_rpmh_probe()` calls `of_bcm_voter_get()` and returns an error
  pointer unchanged;
- `of_bcm_voter_get()` materializes `-517`, Linux `-EPROBE_DEFER`, when no
  matching voter is present in the global list;
- `qcom_icc_bcm_voter_probe()` is the code that adds the voter to that list;
  and
- the shipped display-clock ELF contains `disp_cc_waipio_probe()`, driver name
  `disp_cc-waipio`, and the call to `qcom_cc_really_probe()`.

The exact candidate config has `CONFIG_COMMON_CLK_QCOM` and
`CONFIG_INTERCONNECT_QCOM` unset. These providers are therefore not hidden
built-ins in the candidate kernel; they must come from the stock modules.

## Analysis Ledger

### A1: The expected qnoc bind path might be wrong

Basis:

- `0xa04` only proves that one exact sysfs path was absent.
- A wrong device basename or wrong driver name would produce the same result.

Checks:

- all four exact DTBs use `/soc/interconnect@1` with compatible
  `qcom,waipio-mc_virt`;
- exact `waipio.c` maps that compatible to `waipio_mc_virt`;
- the platform driver name is `qnoc-waipio`;
- the earlier `0xa03` predicate proved another node bound to that same driver;
  and
- same-build stock topology exposes
  `supplier:platform:soc:interconnect@1` to SSUSB.

Decision:

`RULED_OUT`. The expected driver and device basename are correct.

### A2: qnoc module registration might have failed

Basis:

- module insertion success alone would not prove platform bind.

Checks:

- the exact plan includes `icc-bcm-voter.ko`, `socinfo.ko`, `icc-rpmh.ko`, and
  `qnoc-waipio.ko` in dependency-valid order;
- P2.55 passed qnoc aggre1 at classifier priority 3 before failing mc_virt at
  priority 4; and
- aggre1 and mc_virt are entries in the same qnoc driver's match table.

Decision:

`RULED_OUT`. The qnoc driver registered and bound at least one Waipio node.

### A3: mc_virt might have a different DT dependency on the shipping variants

Checks against all four exact FYG8 DTBs produced the same result:

```text
compatible:       qcom,waipio-mc_virt
voter names:      hlos, disp
voter phandles:   /soc/rsc@17a00000/bcm_voter
                   /soc/rsc@af20000/bcm_voter
status:           okay by default
display clock:    /soc/clock-controller@af00000, clock id 0x48
```

All 11 exact DTBO entries reference `mc_virt` as a consumer phandle. They do
not target or replace the mc_virt parent. Their display-RSC fragments add
children but do not change the RSC parent's clock dependency.

Decision:

`VERIFIED`. Variant or overlay selection does not remove the display voter
requirement.

### A4: A missing display voter might not stop qnoc probe

Exact source order, independently matched by the shipped ELF relocations and
error constants:

1. the mc_virt descriptor declares voters `hlos` and `disp`;
2. `qcom_icc_rpmh_probe()` calls `of_bcm_voter_get()` for every enabled voter;
3. it immediately returns `PTR_ERR()` for any missing voter;
4. `of_bcm_voter_get()` initializes its result to `-EPROBE_DEFER`; and
5. it returns a voter only after the matching DT node has been inserted into
   the global `bcm_voters` list by `qcom_icc_bcm_voter_probe()`.

Decision:

`VERIFIED WITH CONDITION`. When the display voter is enabled, its absence
deterministically defers mc_virt before provider registration. The condition
is the target's runtime `PART_DISPLAY` subset value.

### A5: The display BCM voter might exist without display-RSC bind

Exact `rpmh_rsc_probe()` creates its DT child platform devices only at its last
step:

```c
return devm_of_platform_populate(&pdev->dev);
```

The generic OF implementation confirms that this call walks the parent node
and creates child platform devices. The display BCM voter is one such child.

Decision:

`RULED_OUT`. The child cannot bind before the display RSC reaches its final
populate step.

### A6: Why the display RSC does not reach that step

The exact display RSC has a required clock from
`/soc/clock-controller@af00000`. The matching stock driver is
`dispcc-waipio.ko`.

P2.43 already established:

- the exact kernel defaults `fw_devlink` to strict/on;
- a missing DT clock supplier can defer the consumer before its probe;
- no relevant boot-argument override exists; and
- `dispcc-waipio.ko` has four hard module dependencies:
  `clk-qcom.ko`, `debug-regulator.ko`, `gdsc-regulator.ko`, and
  `proxy-consumer.ko`.

The exact P2.54 plan contains all four dependencies but omits
`dispcc-waipio.ko`. Its other DT inputs are already in the passed apps-RSC
chain: the RPMh clock and `mxlvl` regulator.

Decision:

`STRONG_STATIC_CAUSAL_HYPOTHESIS`. The exact candidate has no built-in QCOM
clock provider, the plan omits the only matching stock module, and the module's
four hard dependencies are already present. If the display voter is enabled,
the omitted module prevents the display-clock provider, which prevents
display-RSC child population and leaves that voter absent.

### A7: Could this still be only a late timing problem?

No later userspace event can load a module that is absent from the candidate
plan. The stock module bytes exist in the pinned vendor ramdisk, but the
direct-PID1 runtime loads only the materialized plan. Deferred probing can
retry, but that missing provider cannot appear during the candidate runtime.

Decision:

`RULED_DOWN FOR THIS BRANCH`. Scheduling may change when the failure appears,
but cannot close the missing-module branch in the current candidate.

### A8: Could SoC subset handling legitimately disable the display voter?

`icc-rpmh.c` skips the `disp` voter when
`socinfo_get_part_info(PART_DISPLAY)` reports a no-display subset. This is the
one material branch around the causal chain.

Evidence against that branch on this target:

- the target has a working display;
- same-build stock state loads `dispcc_waipio` and `qnoc_waipio`;
- stock SSUSB is linked to `soc:interconnect@1`; and
- the source comment describes the branch as disabling BCMs for no-display
  parts.

Residual limitation:

P2.55 did not retain the actual `PART_DISPLAY` subset value. Therefore this
branch is `STRONGLY_RULED_DOWN`, not directly live-measured.

### A9: Could mc_virt have failed after voter acquisition?

Yes. The retained classifier observed only an absent bind symlink, not the
driver's return code. If `PART_DISPLAY` disables the display voter, or if both
voters were present, a later failure in regmap, clock, provider registration,
or node initialization could produce the same absent bind.

Decision:

`OPEN BUT SECONDARY`. The exact aggre1-success/mc_virt-failure split, the
two-voter versus one-voter ELF difference, and the omitted display-clock
module make the display-voter branch the strongest explanation. They do not
turn the bind absence into a retained `-EPROBE_DEFER` observation.

## Reasoning Transitions

This unit did not start by assuming the display module was the answer:

1. **Hypothesis: the `0xa04` path was wrong.** All four DTBs, the qnoc match
   table, stock supplier topology, and the earlier same-driver aggre1 success
   agreed on the path, so that branch was rejected.
2. **Hypothesis: qnoc module registration failed.** The live aggre1 bind proved
   the same driver registered and probed, so analysis moved from module load to
   descriptor-specific dependencies.
3. **Hypothesis: mc_virt differed only by timing.** Source inspection exposed
   its additional `disp` voter. That redirected the analysis to the display
   BCM voter and its parent display RSC.
4. **Prior conclusion challenged:** P2.43 had correctly removed the display
   RSC from the direct apps-RSC/GCC sequence and then generalized too far that
   it was irrelevant to USB. The newly observed mc_virt frontier revealed an
   indirect dependency, so only that broader conclusion was retired.
5. **Hypothesis: source and shipped modules might differ.** Exact modules were
   extracted from the P2.54-pinned vendor ramdisk. Their hashes, symbols,
   descriptor relocations, and error constants matched the source chain, so
   source drift was ruled down.
6. **Hypothesis: a built-in provider could replace the omitted module.** The
   exact candidate config has the QCOM clock/interconnect families unset, so
   the module omission remains material.
7. **Remaining discriminator:** runtime `PART_DISPLAY` was never retained. It
   can bypass the display-voter lookup, so the conclusion stops at a strong
   static causal hypothesis rather than claiming the live root cause.
8. **Separate observer issue:** the generic post-rollback error initially did
   not identify its inner cause. Durable before/after receipts reproduced one
   exact failure shape, but the failed in-flight reads were never persisted;
   the reconstruction is therefore explicitly inferred.

## P2.43 Scope Correction

P2.43 correctly removed `/sys/bus/platform/drivers/rpmh/af20000.rsc` as a
direct gate on the apps-RSC/GCC chain. Its stronger conclusion that
`dispcc-waipio.ko` was irrelevant to USB is retired.

The later evidence exposes an indirect dependency:

```text
USB -> mc_virt -> disp BCM voter -> display RSC -> display clock
```

This does not restore the old display-RSC gate at its former early position.
It means the display-clock/RSC/voter closure belongs immediately before the
qnoc mc_virt predicate.

## Bounded Next Candidate Design

The next unit is design-only before any build:

1. add the exact stock `dispcc-waipio.ko` to the module plan after its existing
   dependencies and before `qnoc-waipio.ko`;
2. do not add DRM, panel, DSI, SDE, backlight, or a display userspace stack;
3. do not patch qnoc to ignore or fake the display voter;
4. add ordered classifier coordinates before mc_virt:
   `/sys/bus/platform/drivers/disp_cc-waipio/af00000.clock-controller`,
   `/sys/bus/platform/drivers/rpmh/af20000.rsc`, and
   `/sys/bus/platform/drivers/bcm_voter/af20000.rsc:bcm_voter`; and
5. retain the existing terminal SSUSB/DWC3/UDC proof requirement.

Those basenames are derived from the exact DT node names, exact driver names,
and the source-matched `of_device_make_bus_id()` algorithm. They remain
candidate-side predicates until a later live result observes them.

`dispcc-waipio.ko` is a stock clock driver, but its probe is not observational:
it maps display-clock registers, configures two PLLs, and enables clock
gating. That bounded stock side effect must be included in the next execution
closure and independent safety review.

No new Full-LTO build is justified until the module order, exact diagnostic
paths, source contract, and observer change below pass H0 validation.

## Odin Observer Reconstruction

### Confirmed durable facts

- receipts 76 and 77 both contain sole live Odin node A with one immutable
  identity;
- rollback transfer returned `odin_transfer_completed` once;
- the journal reached `ROLLBACK_FLASHED` before final verification;
- the failed observation created no receipt;
- recovery's first successful receipt reused sequence 78;
- receipt 78 has no Odin-live node and its inventory contains post-rollback
  node B, not node A;
- the 15 paths common to receipts 77 and 78 have zero immutable changes; and
- recovery performed no transfer and closed final Android health.

### Why the inner cause was lost

`enumerate_odin()` constructs complete measured endpoint evidence before it
returns an `OdinSnapshot`. It catches every `OSError` or
`UsbfsIdentityError` from the final evidence step and replaces the message
with:

```text
measured USB endpoint evidence failed
```

`_snapshot_and_record()` persists only after `enumerate_odin()` returns.
Therefore an evidence-construction failure has neither a snapshot receipt nor
a durable inner exception. The Python exception cause exists only in the
failed process.

### Exact-shape replay

Feeding receipt 77's inventory as the observer baseline and receipt 78's
inventory as its next read produces:

```text
observer: UsbfsIdentityError
          usbfs inventory membership changed during enumeration
core:     OdinTransitionError
          measured USB endpoint evidence failed
cause:    UsbfsIdentityError
          usbfs inventory membership changed during enumeration
```

This proves that the durable before/after shape is sufficient to reproduce the
observed outer error. It does not prove that the original in-flight reads had
that exact shape; they were not persisted.

## Smallest Safe Odin Change

Do not relax endpoint identity or treat a simultaneous disappearance/arrival
as successful absence yet.

The bounded correction is:

1. introduce a typed, bounded inventory-membership exception containing only
   sorted `removed` and `added` path sets;
2. persist a separate sealed diagnostic-failure receipt from
   `_snapshot_and_record()` with attempted sequence, stage, exception class,
   and bounded delta;
3. keep it outside the successful snapshot sequence and generation tracker;
4. do not issue a ticket, advance a state transition, accept endpoint absence,
   repeat a candidate/rollback transfer, or change recovery behavior; and
5. re-raise the same fail-closed error.

Focused replay must cover:

- exact Odin-node removal plus post-rollback-node arrival;
- immutable replacement;
- unrelated arrival;
- an I/O failure;
- exclusive and bounded failure-receipt creation; and
- recovery from durable `ROLLBACK_FLASHED` with zero transfer calls.

Because this touches the F1 runner/recovery evidence closure, AGENTS.md
requires one independent safety review before another F1.

## Validation

- The exact P2.43 dependency audit reran against current pinned private inputs
  and returned `PASS_P243_RPMH_DEPENDENCY_AUDIT_HOST_ONLY`.
- The exact P2.51 SSUSB audit reran and returned
  `PASS_P251_SSUSB_DEPENDENCY_AUDIT_HOST_ONLY`.
- The four focused P2.43, P2.51, USBFS identity, and Odin transition test
  modules ran 106 tests with zero failures.
- The extracted ELF sizes and hashes match the tracked module inventory and
  P2.54 module closure.
- Independent H0 review classified the qnoc conclusion as a strong static
  causal hypothesis rather than deterministic live proof; that limit is
  incorporated above.
- Independent H0 review of the Odin path confirmed the durable/inferred split
  and the separate diagnostic-failure receipt as the smallest fail-closed
  correction.
- `git diff --check` passes.

## Proof Classification

`VERIFIED`:

- exact qnoc path identity and driver registration;
- all four DTB variants' mc_virt voters;
- candidate omission of `dispcc-waipio.ko`;
- all four hard module dependencies already present;
- qnoc and BCM-voter error semantics;
- RSC child-population boundary;
- stock SSUSB dependence on `soc:interconnect@1`;
- receipt 77 to 78 inventory delta; and
- current observer's loss of inner error detail.

`STRONG_STATIC_CAUSAL_HYPOTHESIS`:

- if the display voter is enabled, missing `dispcc-waipio.ko` prevents its
  creation and causes persistent mc_virt `-EPROBE_DEFER`.

`OPEN UNTIL A LATER LIVE RUNG`:

- direct retained evidence for display-clock, display-RSC, and display-voter
  binds;
- the P2.55 candidate's actual `PART_DISPLAY` subset value;
- successful mc_virt bind after adding the stock clock module; and
- every downstream SSUSB, DWC3, UDC, and host USB result.

`INFERRED, NOT RECORDED`:

- the original failed USBFS enumeration observed the same compound node-A to
  node-B inventory transition reconstructed from durable receipts.

## External Cross-Check

The exact FYG8 vendor source is the primary evidence. Generic behavior was
cross-checked against:

- Android common
  [`drivers/of/platform.c`](https://android.googlesource.com/kernel/common/+/ab522e1478e3191114535f454a1c41ba3b2d1cb9/drivers/of/platform.c),
  where `devm_of_platform_populate()` creates child platform devices; and
- the Linux kernel
  [device-link documentation](https://kernel.org/doc/html/latest/driver-api/device_link.html),
  which documents that managed supplier dependencies can defer consumer
  probing.

No external source overrides the exact FYG8 DT, source, module, and live
evidence above.

## Boundary And Next Unit

This unit contacted no device, built no kernel, created no image or candidate,
and grants no D0, D1, or F1 authority.

P2.57 is two independent H0 subunits, not one coupled redesign:

1. add the one-module qnoc dependency closure and exact intermediate
   classifier coordinates through the existing source contract; then
2. add the observability-only Odin failure receipt plus focused replay and one
   independent safety review before any later F1.

Only after that closure passes should one final Full-LTO candidate be
qualified. A later F1 still requires connected D0 preparation and a fresh
exact approval.
