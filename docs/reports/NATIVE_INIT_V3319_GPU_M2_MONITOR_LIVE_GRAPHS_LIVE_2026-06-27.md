# Native Init V3319 GPU M2 Monitor Live Graphs Live

## Summary

- Cycle: `V3319`
- Track: GPU rung 3, M2 GPU-accelerated live system-monitor graphs.
- Candidate: `workspace/private/inputs/boot_images/boot_linux_v3319_gpu_m2_monitor_live_graphs.img`
- Candidate SHA256: `4b78660fa1721006ec57f1295a02e65f32546638823f2c537a01dddc30b99fee`
- Init after flash: `A90 Linux init 0.11.90 (v3319-gpu-m2-monitor-live-graphs)`
- Result: PASS. The M2 probe rendered live CPU/GPU/memory/temperature graph lanes as a mono1 source texture, submitted
  the proven D3 textured-quad KGSL path, copied the GPU output to KMS, and presented 12/12 frames with `present_rc=0`.
- Next: M3 polish plus extraction of the shared KGSL submit/fence/buffer/texture/present layer.

## Flash Gate

- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Local candidate SHA256: `4b78660fa1721006ec57f1295a02e65f32546638823f2c537a01dddc30b99fee`
- Remote staged image SHA256 matched the local candidate.
- Boot block prefix readback SHA256 matched the local candidate.
- Rollback image verified before flash:
  `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
  SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Deeper fallback verified before flash:
  `workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img`
  SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- Final fallback verified before flash:
  `workspace/private/inputs/boot_images/boot_linux_v48.img`
  SHA256 `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
- Recovery/TWRP image verified before flash:
  `workspace/private/inputs/firmware/twrp/recovery.img`
  SHA256 `b1ef377a52ec8ab43b49a5fcc7a0b27e8efff91bf2d8cccdc565ecadadcc646c`

## Health

- Pre-flash resident: `A90 Linux init 0.11.89 (v3318-gpu-m1-monitor-dashboard)`
- Pre-flash `selftest`: `pass=12 warn=1 fail=0`
- Flash-helper post-boot verification reached V3319 and reported `status` with `selftest pass=12 warn=1 fail=0`.
- Standalone post-flash health:
  - `version`: `0.11.90`, build `v3319-gpu-m2-monitor-live-graphs`
  - `selftest`: `pass=12 warn=1 fail=0`
- Post-probe `selftest`: `pass=12 warn=1 fail=0`

## M2 Probe

Command:

```text
gpu m2-monitor-live-graph-probe --frames 12 --interval-ms 200 --timeout-ms 60000 --hold-ms 5000 --materialize-devnode
```

Key telemetry:

- `gpu.m2.graph.scope=gpu-m2-live-monitor-graphs-textured-2d`
- `gpu.m2.graph.texture_source=live-monitor-mono1-graph-cpu-gpu-mem-temp`
- `gpu.m2.graph.blit_mode=kgsl-textured-quad-scale-to-960x720-linear-readback-kms-copy`
- `gpu.m2.graph.source=480x360 mono1 stride=60`
- `gpu.m2.graph.target=960x720 stride=3840`
- `gpu.m2.graph.shader_sha256=4e8ad0a934d236149af999619a1fe99690e7b732d2e4ca69a2b345100d8d04a3`
- `gpu.m2.graph.power_write_attempted=0`
- `gpu.m2.graph.proprietary_blob_attempted=0`
- `gpu.m2.graph.kgsl_submit_attempted=1`
- `gpu.m2.graph.kms_present_attempted=1`
- `gpu.m2.graph.materialize_rc=0`
- `gpu.m2.graph.result=monitor-live-graph-pass`
- `gpu.m2.graph.timed_out=0`
- `gpu.m2.graph.child_status=0x0`
- `gpu.m2.graph.result_rc=0`
- `gpu.m2.graph.gpu_create_rc=0`
- `gpu.m2.graph.kms_begin_rc=0`
- `gpu.m2.graph.present_rc=0`
- `gpu.m2.graph.presented=12`
- `gpu.m2.graph.graph_points=13`
- `gpu.m2.graph.graph_pixels_set=2724`
- `gpu.m2.graph.cpu.count=8`
- `gpu.m2.graph.cluster.count=3`
- `gpu.m2.graph.gpu.model=Adreno640v2`
- `gpu.m2.graph.pm4_dwords=409`
- `gpu.m2.graph.elapsed_ns=2202390364`
- `gpu.m2.graph.fps_milli=5448`
- `gpu.m2.graph.timing.sample.avg_us=19378`
- `gpu.m2.graph.timing.graph.avg_us=39`
- `gpu.m2.graph.timing.texture.avg_us=2889`
- `gpu.m2.graph.timing.gpu_wait.avg_us=5550`
- `gpu.m2.graph.timing.copy.avg_us=41353`
- `gpu.m2.graph.timing.present.avg_us=1995`
- `gpu.m2.graph.timing.total.avg_us=183528`
- `gpu.m2.graph.changed_total=8294400`
- `gpu.m2.graph.semantic.sample_count=64`
- `gpu.m2.graph.semantic.match_count=64`
- `gpu.m2.graph.semantic.exact_match_count=64`
- `gpu.m2.graph.semantic.mismatch_count=0`
- `gpu.m2.graph.semantic.output_other_count=0`
- `A90P1 END seq=6 cmd=gpu rc=0 errno=0 duration_ms=7469 flags=0x0 status=ok`

## Safety Result

- The M2 monitor sampler reads `/proc` and `/sys` telemetry and does not write power/display control nodes.
- The live graph path used the existing G0 firmware-cache/devnode materialization and D3 KGSL textured-quad path.
- No backlight, PWM, PMIC, regulator, GDSC, GPIO, panel re-init, forbidden partition, Wi-Fi connect, DHCP, or ping action
  was performed.
- No rollback was needed.

## Conclusion

M2 is closed. The monitor now has a real continuous GPU-accelerated 2D consumer: live system telemetry is rendered into a
source graph texture, sampled/scaled through KGSL, and presented through KMS with semantic output validation and clean
post-probe health. The next rung is M3: polish plus extraction of the shared GPU path.
