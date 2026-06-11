# Native Init V2225 A90 Boot-Window Handoff Runner

## Summary

- Cycle: `V2225`
- Type: rollbackable boot-window handoff runner; default execution is host-only dry-run.
- Decision: `v2225-boot-window-handoff-dry-run-ready`
- Result: `PASS`
- Reason: host-only flash/capture/rollback plan is complete; live execution still requires explicit approval
- Execute mode: `False`
- Evidence: `workspace/private/runs/kernel/v2225-dry-run-final-20260612-071253`

## Images

- Test image: `workspace/private/inputs/boot_images/boot_linux_v2224_a90_boot_window_observer.img`
- Test SHA256: `ad177a775e7c1952e1dba8120066ec9bc3f8814a6f2d6360f83f314bd2c513df`
- Test version: `A90 Linux init 0.9.262 (v2224-a90-boot-window-observer)`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2189_security_p0_stage_fix.img`
- Rollback SHA256: `f54becb2b720ad198413c2a0089912626ca295c79a96f13e0921cf4f05b39f51`
- Rollback version: `A90 Linux init 0.9.261 (v2189-security-p0-stage-fix)`

## Live Contract

- Live mode requires `--execute` plus the exact confirmation token.
- Live sequence: V2222 preflight -> flash V2224 -> collect `/cache/native-init-wifi-test-boot-v2224-*` -> V2220 parser -> rollback V2189 -> selftest fail=0.
- Collection is read-only after boot; it uses `cat` over the native bridge and the helper-owned trace output.

## Safety Scope

- Dry-run does not flash, reboot, write device partitions, scan/connect Wi-Fi, use credentials, configure DHCP/routes, ping, attach BPF, execute `probe_write_user`, or write tracefs controls.
- Live mode flashes only the approved rollbackable V2224 test boot and V2189 rollback image.
- It does not use Wi-Fi HAL scan/connect, credentials, DHCP/routes, external ping, PMIC/GPIO/GDSC/eSoC/PCI paths, platform bind/unbind, or `sda29` writes.

## Dry-Run Command Plan

```json
{
  "preflight": [
    "python3",
    "workspace/public/src/scripts/revalidation/native_kernel_a90_boot_window_preflight_v2222.py"
  ],
  "flash_test_boot": [
    "python3",
    "workspace/public/src/scripts/revalidation/native_init_flash.py",
    "workspace/private/inputs/boot_images/boot_linux_v2224_a90_boot_window_observer.img",
    "--expect-version",
    "A90 Linux init 0.9.262 (v2224-a90-boot-window-observer)",
    "--expect-sha256",
    "ad177a775e7c1952e1dba8120066ec9bc3f8814a6f2d6360f83f314bd2c513df",
    "--verify-protocol",
    "selftest",
    "--bridge-timeout",
    "240",
    "--recovery-timeout",
    "240",
    "--from-native"
  ],
  "collect": [
    [
      "python3",
      "workspace/public/src/scripts/revalidation/a90ctl.py",
      "cat",
      "/cache/native-init-wifi-test-boot-v2224-helper.result"
    ],
    [
      "python3",
      "workspace/public/src/scripts/revalidation/a90ctl.py",
      "cat",
      "/cache/native-init-wifi-test-boot-v2224.summary"
    ],
    [
      "python3",
      "workspace/public/src/scripts/revalidation/a90ctl.py",
      "cat",
      "/cache/native-init-wifi-test-boot-v2224.log"
    ]
  ],
  "parse": [
    "python3",
    "workspace/public/src/scripts/revalidation/a90_kernel_v2220_helper_summary_trace_parser.py"
  ],
  "rollback": [
    "python3",
    "workspace/public/src/scripts/revalidation/native_init_flash.py",
    "workspace/private/inputs/boot_images/boot_linux_v2189_security_p0_stage_fix.img",
    "--expect-version",
    "A90 Linux init 0.9.261 (v2189-security-p0-stage-fix)",
    "--expect-sha256",
    "f54becb2b720ad198413c2a0089912626ca295c79a96f13e0921cf4f05b39f51",
    "--verify-protocol",
    "selftest",
    "--bridge-timeout",
    "240",
    "--recovery-timeout",
    "240",
    "--from-native"
  ],
  "postflight": [
    "python3",
    "workspace/public/src/scripts/revalidation/a90ctl.py",
    "selftest"
  ]
}
```
