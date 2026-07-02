# Native Init V3363 Init Hot-Reload Source Build

- Cycle: `V3363`
- Decision: `v3363-init-hot-reload-source-build`
- Init: `A90 Linux init 0.11.124 (v3363-init-hot-reload)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3363_init_hot_reload.img`
- Boot SHA256: `394ab12f0b156304d34b6be3e3bac190e4551010f64466b55efd55b2c3380b7e`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3335_gpu_z3_primary_setcrtc.img`

## Change

- Adds `reload INIT-RELOAD-EXECVE <staged-init-path> <expected-sha256>` (a90_init_reload.c): replaces PID1 in place via execve() with NO reboot, to shorten the research flash cycle for init-only changes.
- The USB gadget/configfs kernel state persists across execve (native-init gadget setup is idempotent and never unbinds the UDC), so the host serial link stays up and the new init comes straight back to a shell without a reboot or USB re-enumeration.
- Token-gated, requires the candidate in the approved SD staging root, validates a caller-pinned SHA-256 and ELF magic before execve. A failed execve leaves the old init running. Registered `CMD_DANGEROUS | CMD_NO_DONE`.
- Existing self-dd F0/F1/F2/F3 commands are preserved.

## Validation Contract

- Static PASS requires the V3363 version strings plus the reload markers (`A90RELOAD`, `INIT-RELOAD-EXECVE`, usage) to be present while preserving the prior command surface.
- Live H0 PASS, separately gated, will require: flash V3363, stage its own init ELF, `reload` it, prove the serial device never re-enumerates (no reboot), native-init uptime resets (init restarted), `selftest fail=0`, and the reload completes far under a reboot.
- No live re-exec is claimed by this source-build report.

## Metadata

- Helper flags: `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- Init extra flags: ``
- Candidate type: `init-hot-reload`.
