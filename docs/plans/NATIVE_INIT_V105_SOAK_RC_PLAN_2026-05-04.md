# Native Init v105 Soak RC Plan

Date: `2026-05-04`

## Summary

- v105 target: `A90 Linux init 0.9.5 (v105)` / `0.9.5 v105 SOAK RC`.
- Baseline: v104 Wi-Fi feasibility gate, verified in `docs/reports/NATIVE_INIT_V104_WIFI_FEASIBILITY_2026-05-04.md`.
- Goal: promote the v96-v104 module/runtime/network stack into a recovery-friendly release-candidate baseline by proving repeated operation, recovery, and diagnostics behavior.
- Scope is intentionally conservative: v105 should not introduce risky hardware enablement or partition mutation.
- Wi-Fi bring-up remains blocked because v104 gate returned `baseline-required` in default native state and `no-go` after read-only `mountsystem ro`.

## Key Changes

- Copy v104 into `stage3/linux_init/init_v105.c` and `stage3/linux_init/v105/*.inc.c`.
- Update `stage3/linux_init/a90_config.h`, kmsg marker, ABOUT/changelog to:
  - `A90 Linux init 0.9.5 (v105)`
  - `0.9.5 v105 SOAK RC`
  - `A90v105`
- Preserve v104 device behavior unless validation finds a blocking stability defect.
- Add a host-side validation helper `scripts/revalidation/native_soak_validate.py`.
  - It should use the existing serial bridge/a90ctl control path.
  - It should run bounded cycles of non-destructive commands.
  - It should save a text log and return nonzero on failed command, wrong version, selftest failure, or diagnostic mismatch.
- Do not add Wi-Fi enablement, rfkill writes, module load/unload, firmware/vendor mutation, or partition formatting.

## Host Soak Helper Scope

`native_soak_validate.py` should support:

- `--cycles N` default small value for quick validation.
- `--sleep SEC` delay between cycles.
- `--expect-version "A90 Linux init 0.9.5 (v105)"`.
- `--out PATH` to store a transcript.
- Default command cycle:
  - `version`
  - `status`
  - `bootstatus`
  - `selftest verbose`
  - `runtime`
  - `storage`
  - `service list`
  - `diag`
  - `wififeas gate`
- Optional non-destructive UI/network checks:
  - `statushud`
  - `autohud 2`
  - `screenmenu`
  - `hide`
  - `netservice status`
- Dangerous/raw-control checks such as `recovery`, `reboot`, `poweroff`, `netservice start|stop`, `usbacmreset` must be opt-in and not part of the default quick soak.

## Build Plan

- Build static ARM64 init with the same compiled modules as v104:
  - `init_v105.c`
  - `a90_util.c/h`
  - `a90_log.c/h`
  - `a90_timeline.c/h`
  - `a90_console.c/h`
  - `a90_cmdproto.c/h`
  - `a90_run.c/h`
  - `a90_service.c/h`
  - `a90_kms.c/h`
  - `a90_draw.c/h`
  - `a90_input.c/h`
  - `a90_hud.c/h`
  - `a90_menu.c/h`
  - `a90_metrics.c/h`
  - `a90_shell.c/h`
  - `a90_controller.c/h`
  - `a90_storage.c/h`
  - `a90_selftest.c/h`
  - `a90_usb_gadget.c/h`
  - `a90_netservice.c/h`
  - `a90_runtime.c/h`
  - `a90_helper.c/h`
  - `a90_userland.c/h`
  - `a90_diag.c/h`
  - `a90_wifiinv.c/h`
  - `a90_wififeas.c/h`
- Generate `stage3/ramdisk_v105.cpio` with:
  - `/init`
  - `/bin/a90sleep`
  - `/bin/a90_cpustress`
  - `/bin/a90_rshell`
- Generate `stage3/boot_linux_v105.img` by reusing v104 boot image header/kernel/cmdline and replacing only ramdisk.

## Static Validation

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` build — required.
- `strings` marker check:
  - `A90 Linux init 0.9.5 (v105)`
  - `A90v105`
  - `0.9.5 v105 SOAK RC`
- `git diff --check` — required.
- Host Python `py_compile`:
  - `scripts/revalidation/a90ctl.py`
  - `scripts/revalidation/native_init_flash.py`
  - `scripts/revalidation/diag_collect.py`
  - `scripts/revalidation/wifi_inventory_collect.py`
  - `scripts/revalidation/native_soak_validate.py`
- Stale marker scan for v104 strings in v105 source tree — required.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v105.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.5 (v105)" \
  --verify-protocol auto
```

Required command checks:

- `version`
- `status`
- `bootstatus`
- `selftest verbose`
- `diag`
- `runtime`
- `storage`
- `mountsd status`
- `service list`
- `netservice status`
- `wifiinv`
- `wififeas gate`
- `statushud`
- `autohud 2`
- `screenmenu`
- `hide`
- `cpustress 3 2`

Required host soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 10 \
  --sleep 2 \
  --expect-version "A90 Linux init 0.9.5 (v105)" \
  --out tmp/soak/v105-quick-soak.txt
```

Optional/manual soak after quick validation:

- Longer idle soak with HUD/menu hidden and visible states.
- USB cable reconnect check.
- NCM/tcpctl/remote shell soak only if explicitly enabled.
- Recovery/TWRP/native-init transition check if the operator is ready to babysit reboots.

## Acceptance Criteria

- v105 boots and verifies with `cmdv1 version/status`.
- Boot selftest remains `fail=0`.
- `native_soak_validate.py` completes all cycles without failed command or wrong version.
- No obvious zombie/orphan accumulation appears in `status`, `service list`, or diagnostics output.
- Serial bridge remains responsive after UI commands and CPU stress.
- `wififeas gate` still blocks Wi-Fi bring-up unless kernel-facing prerequisites become visible.
- Latest verified docs and report are updated only after flash and real-device validation pass.

## Report And Docs

- Write `docs/reports/NATIVE_INIT_V105_SOAK_RC_2026-05-04.md` after validation.
- Update:
  - `README.md`
  - `docs/README.md`
  - `docs/overview/VERSIONING.md`
  - `docs/overview/PROJECT_STATUS.md`
  - `docs/plans/NATIVE_INIT_NEXT_WORK_2026-04-25.md`
  - `docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md`
  - `docs/plans/NATIVE_INIT_LONG_TERM_ROADMAP_2026-05-03.md`
- Artifact retention after success: keep `v105` latest, `v104` rollback, and `v48` known-good fallback.

## Assumptions

- v105 is a stabilization/release-candidate cycle, not a new hardware feature cycle.
- The v104 Wi-Fi feasibility result means direct native Wi-Fi enablement is not attempted in v105.
- USB ACM serial remains the primary rescue/control path.
- NCM/tcpctl/remote shell remain optional services; default quick soak must not require them to be enabled.
