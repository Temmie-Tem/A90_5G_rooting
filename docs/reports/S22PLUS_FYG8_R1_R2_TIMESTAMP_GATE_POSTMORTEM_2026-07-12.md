# S22+ FYG8 R1/R2 Timestamp Gate Postmortem

Date: 2026-07-12 KST  
Target: `SM-S906N/g0q/S906NKSS7FYG8`  
Scope: host-only build-evidence correction; no device or packaging action

## Corrected Verdict

`R1_FULL_LTO_BUILDABILITY_PROVED_R1_REPRODUCIBILITY_AND_R2_REOPENED`

The FX-8300 run still proves that the unchanged Full-LTO source traverses the
complete GKI, vendor/external module, provider-closure, and output path within
32 GiB physical RAM. It does not close reproducible output identity or strict
R2 stock-equivalence because its generated Linux banner has the wrong build
timestamp.

The prior R2 v1 PASS is superseded. R3 remains blocked until a clean R1 v3 run
and R2 v2 exact-banner audit pass.

## Evidence

The archived R1/R2 output records pin this generated banner:

```text
Linux version 5.10.226-android12-9-30958166-abS906NKSS7FYG8 ...
#1 SMP PREEMPT Sun Jul 12 07:16:46 UTC 2026
```

The exact FYG8 stock baseline pins:

```text
Linux version 5.10.226-android12-9-30958166-abS906NKSS7FYG8 ...
#1 SMP PREEMPT Fri Aug 1 05:55:56 UTC 2025
```

Release, build user/host, compiler, and linker identity match. The timestamp
does not. A direct archived-result versus stock-baseline comparison returns
`exact_banner_match=false`.

## Root Cause

The host wrapper correctly exported:

```text
SOURCE_DATE_EPOCH=1754027756
KBUILD_BUILD_TIMESTAMP=Fri Aug 1 05:55:56 UTC 2025
```

Samsung `kernel_platform/build/_setup_env.sh` then unconditionally replaced
both values:

```sh
export SOURCE_DATE_EPOCH=$(git -C ${ROOT_DIR}/${KERNEL_DIR} log -1 --pretty=%ct)
export KBUILD_BUILD_TIMESTAMP="$(date -d @${SOURCE_DATE_EPOCH})"
```

The source archive has no owned kernel Git history and the wrapper deliberately
isolates it from the unrelated parent repository. The `git log` therefore does
not provide the pinned stock epoch, the timestamp becomes unusable/empty, and
Kbuild falls back to the current compile time.

The preflight reported the intended environment but did not verify that the
Samsung setup script preserved it. The old R2 v1 audit checked release and a
compiler substring, not the full stock Linux banner. Those two omissions let
the mismatch pass.

## Corrective Gate

Build schema v3 now:

1. verifies the exact two-line Samsung override before build;
2. temporarily replaces only those lines with preserve-preseeded-value forms;
3. executes the build with the stock epoch/timestamp already exported;
4. restores and rehashes `_setup_env.sh` after the build;
5. rejects R1 if the generated `Image` lacks the exact stock timestamp, release,
   build-user/host, or compiler markers.

R2 schema v2 now loads the complete `linux_banner` from the pinned stock
baseline and requires byte-for-byte banner equality. It also requires an R1 v3
result with a verified banner gate and restored timestamp-control script.

No kernel C source, config, security feature, boot image, or device state is
changed by this correction.

## Re-Close Requirements

1. Transfer the v3 wrapper and v2 auditor to the FX-8300 host.
2. Build from a separate clean reconstructed source tree.
3. Require R1 v3 zero return and exact stock banner gate.
4. Require R2 v2 zero return, exact banner, Full-LTO config, 25,864/25,864 CRC
   closure, and unchanged boot-capacity result.
5. Compare relative-path artifact/module/symvers/provider identities rather
   than whole JSON SHA, because result JSON includes absolute paths and live
   resource measurements.
6. Retrieve and independently hash the R3-operational artifact set locally.

Until then, the old R1/R2 hashes remain historical evidence only and cannot
authorize R3 artifact implementation.
