# Native Init V3299 GPU Compute C0 Reference Recon

Date: 2026-06-26

## Scope

Host-only C0 recon for the active GPU compute demo ladder.

No native-init source behavior changed, no boot artifact was built, and no flash was run.

## Result

`native_gpu_compute_c0_reference_v3299.py --json` passed the C0 reference recon.

Confirmed from the operator-staged Mesa reference under `/tmp/a90-mesa-gpu-src/`:

- Ordered compute dispatch envelope:
  `cs_restore` -> `SP_CS_*` program -> `CP_LOAD_STATE6 ST6_SHADER` -> constants -> UAV bind ->
  `CP_SET_MARKER RM6_COMPUTE` -> `SP_CS_NDRANGE_0..6` + kernel group -> `CP_EXEC_CS` -> WFI/readback.
- A640 compute register offsets match local `a6xx.xml`, including `SP_CS_CONFIG=0xa9bb`,
  `SP_CS_UAV_BASE=0xa9f2`, `SP_CS_NDRANGE_0=0xb990`, and `SP_UPDATE_CNTL=0xbb08`.
- PM4 opcode/enum values match local `adreno_pm4.xml`, including `CP_EXEC_CS=0x33`,
  `CP_SET_MARKER=0x65`, `SB6_CS_SHADER=0x0d`, `ST6_UAV=3`, and `RM6_COMPUTE=8`.
- C1 kernel contract for `kern_invocationid.asm` is fixed:
  local size `32,1,1`, one 32-word UAV, `@invocationid(r0.x)`, and expected readback `buf[i] == i`
  for words `0..31`.

## Source Identity

```text
a6xx_compute_dispatch_reference.txt 09214c7edf3e41e367a855121f68a8abb09eb55527c7bd5e4285780ad1ba1126
a6xx.xml                            142f225bc4ae56a910c910f1d233cc7890587c74fbdec8c390466ffbdf5e0faa
adreno_pm4.xml                      f8137e5d31a3cfce27cba0a8bc269e460067dca9ccb95e620404b7fc752913fb
comp_a6xx.cc                        06d4a0045aededca6f8d901e23b186de77d73abf3e922acf00ff8181e1b8c627
comp_fd6_compute.cc                 139ee4354cc05813201a8154d24b9580bb4f27d7db906eacafab6fcc7bfd8361
kern_invocationid.asm               1e0187f2917ab504602a22f30f475716ea8ec7f7123481d371cc87b908c1a97a
```

## C1 Gate

C1 live dispatch is not ready yet because the shader bytes are not materialized or disassembled.

Current host tool state:

- `/tmp/a90-mesa-h3-build-ir3/src/freedreno/isa/ir3-disasm` exists and is usable for byte verification.
- `computerator` is a target in `/tmp/a90-mesa-h3-build-ir3/build.ninja`, but no executable exists.
- `/tmp/a90-mesa-h3-build-ir3/src/compiler/nir/libnir.a` contains only `nir_stub.c.o`
  (`sha256=42e7f6e94cb4d9d3db31d91521a14e5f0e034b757f06b45ebae9ee5df6e2aea6`), so assembler targets cannot
  resolve full NIR symbols.
- A direct assembler-only probe and the Meson `src/freedreno/ir3/ir3_disasm` target both fail at link time with
  unresolved NIR symbols such as `nir_intrinsic_infos`, `nir_serialize`, and `nir_alu_instr_create`.

Decision: do not flash C1 until `kern_invocationid.asm` has verified A640 CS shader words. The next bounded unit is
either a full-NIR Mesa assembler build or manual hand-encoding verified by the existing `ir3-disasm`.

## Validation

```text
PYTHONPYCACHEPREFIX=tmp/pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_gpu_compute_c0_reference_v3299.py \
  tests/test_native_gpu_compute_c0_reference_v3299.py
```

Result: pass.

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_native_gpu_compute_c0_reference_v3299.py'
```

Result: `Ran 7 tests ... OK`.

```text
python3 workspace/public/src/scripts/revalidation/native_gpu_compute_c0_reference_v3299.py --json
```

Result: `passed=true`, `c0_reference_recon_passed=true`, `kernel_bytes_verified=false`,
`ready_for_c1_live=false`.
