# S22+ Ramoops DTBO + M22 Sysrq Panic Gate Source (2026-07-08)

## Verdict

HOST-ONLY GATE SOURCE PASS. No flash, reboot, Odin live transfer, partition
write, or Android device action was performed.

The M22 retained-console positive control now has a guarded live helper and an
inert AGENTS exception draft. The active policy is intentionally absent, so the
default helper path fails closed before Android/root checks.

## Added

Helper:

`workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py`

Inert policy draft:

`docs/operations/S22PLUS_RAMOOPS_DTBO_M22_SYSRQ_PANIC_AGENTS_EXCEPTION_DRAFT_2026-07-08.md`

The draft is not live authorization while it remains in `docs/operations/`.
It must be explicitly promoted into `AGENTS.md` before any default dry-run or
live run can proceed.

## Intended Future Flow

Once separately authorized, the helper performs exactly this attended sequence:

1. flash the pinned patched DTBO AP;
2. require Android/root to return;
3. require the patched DTBO hash and live `ramoops_region/status=okay`;
4. flash the pinned M22 boot AP;
5. observe ADB/Odin/no-transport after M22 intentionally triggers sysrq-c;
6. roll boot back to the pinned Magisk baseline and collect pstore/last_kmsg;
7. restore the pinned stock DTBO.

M22 is an intentional retained-console positive control. Direct PID1 writes
`S22_NATIVE_INIT_M22_KMSG_SYSRQ_PANIC` to `/dev/kmsg`, enables sysrq, writes
`c` to `/proc/sysrq-trigger`, and only falls back to `reboot("download")` if
sysrq returns.

## Pinned Artifacts

```text
patched_dtbo_ap     4f82663a7c2175a41760ec099c0f662dd04b8932a5ae82ba46b3ecb401a14a00
stock_dtbo_ap       6f397421bee84f4ea0c80a8519be0f6f6af84119794970e8a1faaa05f261caaa
patched_dtbo_raw    1c90b54577cbb42e029818a0c4248e85ec3a0e40903b0887648d6556355c85ab
stock_dtbo_raw      97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c
m22_ap              77c17e9d3fb62319823499e0e8e7fcd485cd180dd730e40d9c2a8112308c4852
m22_boot_img        c79bbe1fb1cee7d7e3c70ff4c249d6e0359760e203cc0bebb1c71d6cc0518802
m22_base_boot       2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
m22_kernel          bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
m22_init            2b711b0fccf6cdd9b4c9beb5ba2f1a095d4e873b42bd03a02eb4655106873831
m22_source          a48818067b6b79578bdc6cd0e327d9e7c316b10bca1be7d838605c7d7e0e6444
magisk_boot_ap      d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock_boot_ap       1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

AP member gates:

```text
DTBO APs: dtbo.img.lz4
Boot APs: boot.img.lz4
```

## Host Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py \
  workspace/public/src/scripts/revalidation/build_s22plus_m22_kmsg_sysrq_panic.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py \
  --print-plan

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py
```

Results:

- `py_compile`: pass.
- `--offline-check`: pass, `rc=0`, verifies DTBO/M22 candidate and rollback
  AP manifests without device action.
- `--print-plan`: pass, `rc=0`, prints the attended live and recovery command
  plan without device action.
- default execution: fail-closed, `rc=1`, before Android/root or device
  access because `AGENTS.md` lacks the M22 retained-console policy markers.

The default missing-marker list included the helper path, M22 AP/boot/init/source
hashes, live and rollback ack tokens, `M22_KMSG_SYSRQ_PANIC`,
`S22_NATIVE_INIT_M22_KMSG_SYSRQ_PANIC`, and the explicit
`intentional kernel crash` / `sysrq-trigger-c` wording.

## Current Gate State

Live flashing is not authorized by this report. The next live-capable sequence
requires:

1. explicit operator approval;
2. promotion of the inert `docs/operations/` exception block into `AGENTS.md`;
3. active-policy readiness/dry-run pass;
4. attended live with `--live --ack S22PLUS-RAMOOPS-DTBO-M22-SYSRQ-PANIC-LIVE-GATE`.

If the M22 candidate exposes no rollback transport, the helper prints the
manual recovery command:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py \
  --rollback-boot-from-download \
  --ack S22PLUS-RAMOOPS-M22-ROLLBACK-BOOT-FROM-DOWNLOAD
```

Stock DTBO cleanup remains separately token-gated through
`S22PLUS-RAMOOPS-RESTORE-STOCK-DTBO`.
