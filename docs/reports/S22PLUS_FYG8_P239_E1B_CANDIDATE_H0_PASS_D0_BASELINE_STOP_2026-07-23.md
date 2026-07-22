# S22+ FYG8 P2.39 E1B candidate H0 pass and D0 baseline stop

Date: 2026-07-23 KST
Tier: H0 complete; connected D0 stopped read-only
Status: `PASS_P239_E1B_CANDIDATE_H0_D0_BASELINE_NOT_CLEAN`
Live authority: none

## Verdict

P2.39 completed the profile-2 E1B candidate pipeline. Two clean Full-LTO
builds, deterministic boot-only packaging, independent effective-rootfs
reconstruction, the common Process v2 offline contract, 142 focused tests, and
an independent safety review passed.

Connected D0 did not produce a prepared binding. Its first bounded
`/proc/last_kmsg` read found the valid terminal-success E1A record retained
from P2.37 and stopped before a journal, approval, Odin session, reboot, or
device write. F1 remains inactive.

## Profile-Driven Candidate

The P2.34 implementation is now profile-driven without changing the E1A
identity domain. E1B uses a distinct profile-2 run identity, kernel config,
userspace compile definition, terminal stage `0x3f`, and exact five-module
contract. Candidate construction still creates one boot-only AP member named
`boot.img.lz4`; no module binary is added to the boot ramdisk.

The E1B userspace contract requires the stock modules in this order:

```text
smem
minidump
qcom_scm
qcom_wdt_core
gh_virt_wdt
```

Each successful `finit_module()` transition is checkpointed, followed by an
exact `/proc/modules` verification and E1B terminal success. The source and
static contracts reject reordered or additional modules, `sec_log_buf.ko`,
shell, USB, block-write, and reboot authority.

## Build And Artifact Closure

Two clean Full-LTO builds ran sequentially on the dedicated builder. The output
tree was removed between builds. Both build wrappers passed their clean-output,
exclusive-root, source, config, module, kernel-banner, witness, and linked
cache-flush gates.

The following final artifacts were byte identical across both builds:

- `Image`;
- `vmlinux`;
- `.config`;
- `System.map`;
- `vmlinux.symvers`; and
- `abi.xml`.

Two independent candidate package runs then produced byte-identical boot
images, compressed members, AP archives, and artifact results. Independent
reconstruction verified the fixed boot-v4 kernel interval, exact `/init` and
child binaries, LZ4 round trip, MagiskBoot unpack, one-member AP inventory, and
writer exclusion.

## Effective Rootfs And Offline Evidence

The checker composes the candidate generic ramdisk with the pinned stock
`vendor_boot` layers in boot order. It rejects duplicate or overriding paths
and requires the exact five FYG8 module files, metadata rows, dependency order,
ELF identities, and stock `vendor_boot` identity. This proves the modules are
available to E1B without expanding the boot-only AP.

The exact candidate was promoted into the three Process v2 evidence payloads.
The common typed verifier accepted their E1B profile, run identity, decoder,
terminal `0x3f`, candidate AP, source contract, effective rootfs, and safety
closure.

That replay exposed one E1A-specific constant in the common verifier: it
expected `32769` reachable slot variants for every profile. The actual E1B
contract correctly enumerates `57345` variants because E1B has six additional
nonterminal module stages. The verifier now derives the count from each pinned
profile sequence while requiring its terminal exactly once at the end. E1A
remains `32769`; E1B is `57345`.

## Validation And Review

- 142 focused model, source, build, packaging, evidence, D0, and F1 adapter
  tests passed.
- Python compilation and `git diff --check` passed.
- The independent review returned GO with no actionable finding.
- The reviewer separately replayed the actual P2.39 E1B evidence, rejected a
  coherently repinned E1B count downgrade and an unsupported profile, replayed
  the P2.37 E1A bundle successfully, and passed 70 related tests.

## Connected D0 Stop

The fresh connected D0 attempt performed one bounded read-only observer read.
It found one valid P2.37 E1A record at terminal stage `0x2f`, with two valid A/B
slots and terminal-success semantics. It did not find the current E1B identity.
The clean-baseline gate therefore rejected preparation as designed.

No candidate or rollback AP was transferred. Odin was not invoked. The device
was not rebooted or written. The stopped manifest and run directory are kept as
private evidence and will not be reused for a later binding.

## Next Gate

One separately approved D1 normal Android reboot may rotate out the historical
retained record. After Android returns healthy, create a fresh manifest and run
directory and repeat connected D0. Only a clean baseline and a complete D0
prepared binding permit requesting one exact E1B F1 approval.

E1B live module insertion, watchdog registration, driver bind, platform bind,
UDC, ACM bytes, NCM, shell, and Debian remain unproved.
