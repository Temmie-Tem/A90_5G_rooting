# NATIVE_INIT_V3189 GPU G1 context probe live validation

- Date: 2026-06-25
- Track: GPU G1 KGSL context-create probe
- Source/build commit under test: `76efa1be` (`Build V3188 GPU G1 context probe`)
- Boot artifact: `workspace/private/inputs/boot_images/boot_linux_v3188_gpu_g1_context_probe.img`
- Boot SHA256: `9969d849f81e870650c32b78589df94e63df93364a28089e94f36abc22410170`
- Native init: `0.11.22` / `v3188-gpu-g1-context-probe`

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
A90 Linux init 0.11.22 (v3188-gpu-g1-context-probe)
selftest: pass=12 warn=1 fail=0
```

The first post-flash command attempt lost A90P1 framing. A standalone `version`
with `--input-mode slow` resynchronized cleanly, and subsequent commands were
stable. This matched the earlier host transport artifact and did not affect
device health.

## G0 Prepare

Before G1, the required G0 firmware-class step was re-run:

```text
gpu.g0.fwclass_prepare.verify_a630_sqe.size=32304
gpu.g0.fwclass_prepare.verify_a640_gmu.size=37680
gpu.g0.fwclass_prepare.fwpath.readback=/cache/a90-runtime/pkg/gpu-g0-fw
gpu.g0.fwclass_prepare.result=ok
```

## G1 Probe

Command:

```bash
python3 workspace/public/src/scripts/revalidation/a90ctl.py --input-mode slow \
  gpu g1-context-probe --timeout-ms 5000 --materialize-devnode
```

Result:

```text
gpu.g1.context.parent_enters_open=0
gpu.g1.context.parent_enters_ioctl=0
gpu.g1.context.ioctl_allowlist=drawctxt_create,drawctxt_destroy
gpu.g1.context.mmap_attempted=0
gpu.g1.context.gpuobj_alloc_attempted=0
gpu.g1.context.submit_attempted=0
gpu.g1.context.power_write_attempted=0
gpu.g1.context.requested_flags=0x140012
gpu.g1.context.result=created-destroyed
gpu.g1.context.timed_out=0
gpu.g1.context.open_elapsed_ms=25
gpu.g1.context.open_rc=0
gpu.g1.context.create_elapsed_ms=0
gpu.g1.context.create_rc=0
gpu.g1.context.context_id=1
gpu.g1.context.flags_in=0x140012
gpu.g1.context.flags_out=0x148052
gpu.g1.context.destroy_attempted=1
gpu.g1.context.destroy_rc=0
gpu.g1.context.close_rc=0
gpu.g1.context.total_elapsed_ms=27
```

The full command duration was 29 ms. Post-probe health stayed clean:

```text
selftest: pass=12 warn=1 fail=0
```

The child wrote its result before the immediate nonblocking `waitpid()` observed
reaping, so `child_reaped=0` was reported. The native reaper later recorded the
child as exited with status 0; this is report hygiene, not a functional failure.

## Kernel Log Tail

Post-probe dmesg tail:

```text
[   60.749087] subsys-restart: __subsystem_get(): __subsystem_get: a640_zap count:0
[   60.750094] subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: loading from ...
[   60.764065] subsys-pil-tz soc:qcom,kgsl-hyp: a640_zap: Brought out of reset
[   64.480120] firmware modem.mdt: _request_firmware_load: firmware state wait timeout: rc = -110
[   64.480216] subsys-pil-tz 4080000.qcom,mss: modem: Failed to locate modem.mdt(rc:-11)
[   64.480440] subsys-restart: __subsystem_get(): __subsystem_get: modem count:0
[   65.480764] subsys-restart: __subsystem_get(): __subsystem_get: modem count:1
```

As in V3187, the modem timeout appears as the recurring boot-side background
event. The G1 probe completed successfully before/around this window and did not
introduce a selftest regression.

## Conclusion

G1 is live-proven at the narrow context rung:

- G0 firmware-class prepare passed.
- KGSL context create returned context id 1.
- KGSL context destroy returned success.
- No mmap, GPU object allocation, command submit, freedreno rendering, or power
  write was attempted.
- Post-probe health remained `pass=12 warn=1 fail=0`.

Next safe rung is G2 design only: bounded allocation/free of the smallest KGSL
GPU object, with mmap and command submit still explicitly out of scope until G2
is separately live-proven and health-checked.
