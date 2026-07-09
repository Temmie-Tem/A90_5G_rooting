# V3411 S22+ O3 Minimal-ACM Root And Risk Design

## Verdict

`HOST DESIGN PASS`. O3 now has a pinned, evidence-backed module-root profile and
explicit risk policy. No direct-PID1 binary or boot image was built in this
unit. No reboot, flash, module insertion, sysfs/configfs write, or partition
write occurred.

## Why The 44-Module Plan Was Rejected

Adding only the M31B watchdog root to the O2 default plan produced 44 modules:
the O2 42 plus `qcom_wdt_core.ko` and `gh_virt_wdt.ko`. That plan respected
`modules.dep` and `modules.softdep`, but omitted the DT/devlink supplier roots
already identified by M34 S9:

```text
pinctrl-msm.ko
pinctrl-waipio.ko
icc-rpmh.ko
icc-bcm-voter.ko
clk-rpmh.ko
rpmh-regulator.ko
qnoc-waipio.ko
arm_smmu.ko
qcom-pdc.ko
```

Those relationships are not represented completely by symbol dependencies.
Building O3 from 44 modules would repeat a known omission and depend on the
functional gates to rediscover it live. V3411 rejects that path before build.

## Pinned O3 Profile

`s22plus_o2_module_plan.py --profile o3-minimal-acm` selects these roots:

```text
clk-qcom.ko
pinctrl-msm.ko
qcom_rpmh.ko
icc-rpmh.ko
icc-bcm-voter.ko
gcc-waipio.ko
pinctrl-waipio.ko
clk-rpmh.ko
rpmh-regulator.ko
gdsc-regulator.ko
qnoc-waipio.ko
arm_smmu.ko
qcom-pdc.ko
dwc3-msm.ko
gh_virt_wdt.ko
```

The first thirteen are the evidence-backed Waipio provider set, `dwc3-msm.ko`
is the selected USB leaf, and `gh_virt_wdt.ko` carries the M31B survival root.
The O2 planner adds every recursive hard and soft dependency and produces:

```text
module_count=59
module_plan_tsv_sha256=a34ebbad3b5d770f133e37a450cc3007e4a84ab831788484680e88aad6b3d534
generated_header_sha256=45727cff30952096d9604682a3ba3d284807a75e6622ed4c8ae57bc153d5b863
functional_bind_gates_sha256=952496134adb496c49a7a7b4a5dd0c46ed418ffe8161641ebe066ff5790f5e9c
```

Private generated output:

```text
workspace/private/outputs/s22plus_native_init/o3_minimal_acm_plan_v0_2
```

The planner pins both the count and full TSV SHA for this profile.

## One Narrow Softdep Correction

FYG8 metadata contains:

```text
softdep pinctrl_waipio pre: qcom_tlmm_vm_irqchip
```

`qcom_tlmm_vm_irqchip` is absent from the 441-module vendor DB. Read-only stock
Android evidence also shows no loaded module or platform-driver path by that
name, while `pinctrl_waipio` is loaded and its Waipio driver is bound. The stock
loader therefore tolerates this unavailable softdep edge.

V3411 adds exactly one allowlisted unresolved edge:

```text
pinctrl-waipio.ko -> pre:qcom_tlmm_vm_irqchip
```

It is emitted in `selection.tolerated_unresolved_softdeps`. The other four
unresolved FYG8 edges remain fatal if their target enters a selected plan. A
fixture test proves that an unrelated missing softdep is still rejected.

## Explicit Risk Model

The 59-module closure contains:

```text
abc.ko
sec_debug.ko
minidump.ko
eud.ko
qc_usb_audio.ko
qcom_wdt_core.ko
gh_virt_wdt.ko
```

They are not optional decoration:

- `abc`, `sec_debug`, `minidump`, and `qc_usb_audio` enter through stock hard
  dependencies needed by the Samsung DWC3 path.
- `eud` is the pinned stock `dwc3_msm pre:` soft dependency.
- `qcom_wdt_core` and `gh_virt_wdt` are the M31B survival-proven watchdog
  dependency closure.

O3 may load only these exact modules as dependency/survival inputs. It must not
write `/sys/module/eud/parameters/enable`, trigger sec_debug/sysrq, configure
audio, change charge current, drive VBUS/OTG boost, or perform regulator/GDSC/
GPIO/raw-PMIC writes. Removing a hard/soft edge merely to reduce the list is
also prohibited; a different root model requires a new named discriminator.

## Candidate Behavior Contract

The next host build must implement this sequence:

1. Direct PID1 mounts only the minimum volatile proc/sys/dev/configfs views.
2. Execute the generated 59-module plan with the O2 fail-stop core.
3. Stream `/proc/modules` through EOF and require all 59 runtime names.
4. Require the eight O2 functional gates in order: hwspinlock, SMEM, cmd-db,
   RPMH, GCC, ssusb, DWC3 core, and UDC.
5. Create one generic built-in configfs function `acm.usb0`, one configuration,
   and no other function.
6. Set only `a600000.ssusb/mode=peripheral` and bind only
   `a600000.dwc3`.
7. Expose an O0-compatible framed request/response service plus a device-reported
   bind-state bundle over the same ACM control plane.
8. Keep PID1 alive after the bounded proof. On any earlier failure, emit
   retained kmsg/pmsg diagnostics and park without cascading behavior.

The candidate must not create Samsung `ss_acm`, MTP, ADB, FunctionFS, NCM,
max77705/charger/altmode behavior, a full stock composite, a Download beacon,
or Android/Magisk handoff.

## Validation

The O2/O3 planner and C core suites now pass 16 tests. New coverage pins the
59-module O3 identity and proves that only the exact Waipio unresolved softdep
is tolerated. No active O3 exception exists. The operator's earlier generic
live-approval intent is noted but is not an artifact-specific live gate and was
not consumed.

Next is the direct-PID1 source and boot-only host build. Only after exact boot,
init, plan, daemon, and AP hashes plus rollback pins pass review should a fresh
one-shot live exception be considered.
