# Native Init V3326 GPU Z2 Imported Scanout Pass Gate Source Build

- Cycle: `V3326`
- Decision: `v3326-gpu-z2-imported-scanout-pass-gate-source-build-pass`
- Init: `A90 Linux init 0.11.94 (v3326-gpu-z2-imported-scanout-pass-gate)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3326_gpu_z2_imported_scanout_pass_gate.img`
- Boot SHA256: `9a63d1f1c8c2ad8aac6cdf63232d71466b2bcf97b5bec5ad7fb62f45601d39d4`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3325_gpu_z2_imported_scanout_target.img`

## Change

- Fixes the V3325 Z2 imported-target pass gate by removing the self-reference on `summary.result_rc` before the child assigns the final result.
- The render path remains the same: DRM msm scanout GEM -> PRIME fd -> KGSL dma-buf import -> M3 textured monitor graph render -> readback semantic validation, with no KMS copy and no KMS present.

## V3325 Evidence Behind This Fix

- V3325 live telemetry already showed the functional proof passed: `ADDFB2=0`, KGSL import/info `0`, `render_rc=0`, `changed_count=691200`, semantic match `64/64`, output-other `0`, and cleanup `0`.
- The only failing field was `gpu.z2.import.result=z2-imported-scanout-render-target-failed` because the pass predicate required `summary.result_rc == 0` while `result_rc` was still initialized to `-EIO`.

## Validation Contract

- Command: `gpu z2-imported-scanout-target-probe --timeout-ms 60000 --materialize-devnode`
- PASS requires `gpu.z2.import.result=z2-imported-scanout-render-target-pass`, `changed_count>0`, semantic match count `64`, semantic output-other count `0`, KGSL import success, KMS `ADDFB2` success, no KMS copy, no KMS present, and post-probe `selftest fail=0`.
- No PMIC/GDSC/regulator/GPIO/backlight write, proprietary blob, EGL/GLES/OpenCL, forbidden partition, or raw flash path is introduced.

## Static Validation

- `py_compile`: V3326 builder and focused source test.
- Unit tests: V3326 focused source contract, V3325 source contract, and V3321 M3 regression contract.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3326 identity plus Z2 imported scanout target telemetry.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Candidate type: `gpu-z2-imported-scanout-pass-gate-candidate`.
