# NATIVE_INIT_V3193 GPU G2 mmap probe live validation

- Date: 2026-06-25
- Track: GPU G2b KGSL GPU object mmap/munmap probe
- Source/build commit under test: `96b2d240` (`Build V3192 GPU G2 mmap probe`)
- Boot artifact: `workspace/private/inputs/boot_images/boot_linux_v3192_gpu_g2_mmap_probe.img`
- Boot SHA256: `26e9cb8f294c4fe0dd343d4d3d51677cf5b2d57e2e99e9b0c01c6e0bf763409f`
- Native init: `0.11.24` / `v3192-gpu-g2-mmap-probe`

## Flash

`native_init_flash.py --from-native` passed the checked flash path:

- local image marker, size, and SHA matched
- recovery ADB gate passed
- remote pushed image SHA matched
- boot write/readback SHA matched
- rebooted to system and native-init verify passed
- no rollback needed

Rollback gate before flash:

- v2321 rollback SHA matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- v2237 fallback SHA matched `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- v48 fallback image present
- recovery/TWRP path exercised by the checked helper

## Health

Post-flash resident:

```text
A90 Linux init 0.11.24 (v3192-gpu-g2-mmap-probe)
selftest: pass=12 warn=1 fail=0
```

Post-probe health stayed clean:

```text
selftest: pass=12 warn=1 fail=0
```

## Validation Note

The first post-flash G0 attempt used slow serial input and did not reach the GPU
probe because the command text was corrupted before dispatch. The actual
functional validation used normal cmdv1 input with `--hide-on-busy`, which
produced clean command framing.

## G0 Prepare

Command:

```bash
python3 workspace/public/src/scripts/revalidation/a90ctl.py --hide-on-busy --timeout 30 \
  gpu g0-fwclass-prepare
```

Result:

```text
gpu.g0.fwclass_prepare.verify_a630_sqe.size=32304
gpu.g0.fwclass_prepare.verify_a640_gmu.size=37680
gpu.g0.fwclass_prepare.fwpath.readback=/cache/a90-runtime/pkg/gpu-g0-fw
gpu.g0.fwclass_prepare.result=ok
```

## G1 Recheck

Command:

```bash
python3 workspace/public/src/scripts/revalidation/a90ctl.py --hide-on-busy --timeout 40 \
  gpu g1-context-probe --timeout-ms 5000 --materialize-devnode
```

Result:

```text
gpu.g1.context.result=created-destroyed
gpu.g1.context.timed_out=0
gpu.g1.context.open_elapsed_ms=26
gpu.g1.context.create_rc=0
gpu.g1.context.context_id=1
gpu.g1.context.flags_in=0x140012
gpu.g1.context.flags_out=0x148052
gpu.g1.context.destroy_attempted=1
gpu.g1.context.destroy_rc=0
gpu.g1.context.total_elapsed_ms=28
```

The inherited G1 reporting still showed `child_reaped=0` because it uses the
older immediate nonblocking reap path. This is the same hygiene issue documented
in V3189/V3191 and did not affect the G2b run.

## G2b Probe

Command:

```bash
python3 workspace/public/src/scripts/revalidation/a90ctl.py --hide-on-busy --timeout 40 \
  gpu g2-mmap-probe --timeout-ms 5000 --materialize-devnode
```

Result:

```text
gpu.g2.gpuobj.parent_enters_open=0
gpu.g2.gpuobj.parent_enters_ioctl=0
gpu.g2.gpuobj.ioctl_allowlist=drawctxt_create,gpuobj_alloc,gpuobj_free,drawctxt_destroy
gpu.g2.gpuobj.alloc_size=4096
gpu.g2.gpuobj.alloc_flags=0x0
gpu.g2.gpuobj.mmap_attempted=1
gpu.g2.gpuobj.mmap_offset_rule=id_times_4096
gpu.g2.gpuobj.mmap_access_attempted=0
gpu.g2.gpuobj.submit_attempted=0
gpu.g2.gpuobj.power_write_attempted=0
gpu.g2.gpuobj.result=mapped-unmapped
gpu.g2.gpuobj.timed_out=0
gpu.g2.gpuobj.child_killed=0
gpu.g2.gpuobj.child_reaped=1
gpu.g2.gpuobj.open_elapsed_ms=6
gpu.g2.gpuobj.open_rc=0
gpu.g2.gpuobj.create_rc=0
gpu.g2.gpuobj.context_id=1
gpu.g2.gpuobj.context_flags_in=0x140012
gpu.g2.gpuobj.context_flags_out=0x148052
gpu.g2.gpuobj.alloc_rc=0
gpu.g2.gpuobj.alloc_size_in=4096
gpu.g2.gpuobj.alloc_size_out=4096
gpu.g2.gpuobj.alloc_flags_in=0x0
gpu.g2.gpuobj.alloc_flags_out=0xc0000
gpu.g2.gpuobj.alloc_va_len=0
gpu.g2.gpuobj.alloc_mmapsize=4096
gpu.g2.gpuobj.gpuobj_id=2
gpu.g2.gpuobj.mmap_len=4096
gpu.g2.gpuobj.mmap_offset=8192
gpu.g2.gpuobj.mmap_rc=0
gpu.g2.gpuobj.mmap_nonnull=1
gpu.g2.gpuobj.munmap_attempted=1
gpu.g2.gpuobj.munmap_rc=0
gpu.g2.gpuobj.free_attempted=1
gpu.g2.gpuobj.free_rc=0
gpu.g2.gpuobj.destroy_attempted=1
gpu.g2.gpuobj.destroy_rc=0
gpu.g2.gpuobj.close_rc=0
gpu.g2.gpuobj.total_elapsed_ms=8
```

The full command duration was 12 ms. The object mmap used the kernel-backed
`id * 4096` offset rule and returned a non-null mapping, then immediately
munmapped it before freeing the object and destroying the context. No mapped
memory read/write, command submit, freedreno rendering, or power write was
attempted.

## Kernel Log Filter

GPU-related dmesg filtering after the probe showed normal boot-time KGSL/GMU/SMMU
inventory plus the expected ZAP load/reset transition:

```text
gpu_cc_gmu_clk_src: set OPP pair(...)
arm-smmu 2ca0000.kgsl-smmu: non-coherent table walk
iommu: Adding device 2c6a000.qcom,gmu:gmu_user to group ...
iommu: Adding device 2ca0000.qcom,kgsl-iommu:gfx3d_user to group ...
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: loading from ...
subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: Brought out of reset
```

No KGSL/Adreno/GMU fault, oops, panic, hang, or GPU timeout was observed in the
bounded G2b validation. The only timeout lines in the broad filter belonged to
modem/wlan firmware loading and were unrelated to the KGSL probe.

## Conclusion

G2b is live-proven at the narrow mmap/munmap rung:

- G0 firmware-class prepare passed.
- G1 context create/destroy still passed.
- KGSL GPUOBJ allocation of 4096 bytes returned success.
- KGSL mmap with offset `gpuobj_id * 4096` returned success.
- KGSL munmap, GPUOBJ free, context destroy, and close returned success.
- No mapped-memory access, command submit, freedreno rendering, or power write
  was attempted.
- Post-probe health remained `pass=12 warn=1 fail=0`.

Next safe rung is design-only first: confirm a read-only mapping touch is safe
from KGSL source semantics before adding any bounded child-only mapped-memory
read probe. Writes, command submit, rendering, and power-control writes remain
out of scope.
