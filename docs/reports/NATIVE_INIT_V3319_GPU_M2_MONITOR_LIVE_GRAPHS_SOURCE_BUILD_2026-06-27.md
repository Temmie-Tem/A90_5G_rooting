# Native Init V3319 GPU M2 Monitor Live Graphs Source Build

## Summary

- Cycle: `V3319`
- Track: GPU rung 3, M2 GPU-accelerated live system-monitor graphs.
- Decision: `v3319-gpu-m2-monitor-live-graphs-source-build-pass`
- Result: PASS
- Device flash: `no` in this build unit.
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3319_gpu_m2_monitor_live_graphs.img`
- Boot SHA256: `4b78660fa1721006ec57f1295a02e65f32546638823f2c537a01dddc30b99fee`
- Base boot: `workspace/private/inputs/boot_images/boot_linux_v3318_gpu_m1_monitor_dashboard.img`
- Init: `A90 Linux init 0.11.90 (v3319-gpu-m2-monitor-live-graphs)`

## Included Delta

- Extends `a90_monitor.c/.h` with a scalar graph series API and mono1 graph-frame renderer for CPU, GPU, memory, and temperature lanes.
- Adds `gpu m2-monitor-live-graph-probe [--frames N] [--interval-ms N] [--timeout-ms N] [--hold-ms N] [--materialize-devnode]`.
- Reuses the proven D3 GPU 2D textured-quad path: CPU builds the live mono1 graph source texture, KGSL samples/scales it to a 960x720 linear target, and KMS presents it.

## M2 Gate

- Command: `gpu m2-monitor-live-graph-probe --frames 12 --interval-ms 200 --timeout-ms 60000 --hold-ms 5000 --materialize-devnode`
- PASS requires `gpu.m2.graph.result=monitor-live-graph-pass`, 12 presented frames, positive graph pixels, semantic match count 64, `present_rc=0`, and `selftest fail=0` after the probe.
- This is a real KGSL submit path (`kgsl_submit_attempted=1`) plus KMS present, with no power/sysfs writes.

## Safety

- Monitor telemetry sources are read-only `/proc` and `/sys` reads.
- Live KGSL validation may use the existing G0 firmware-cache/devnode materialization path; no power/display sysfs write is part of M2.
- No backlight/PWM/PMIC/regulator/GDSC/GPIO write, panel re-init, proprietary blob, Wi-Fi connect, DHCP, or ping.
- Boot partition only through `native_init_flash.py` in the live step.

## Validation

- `py_compile`: V3319 builder and focused source test.
- `unittest`: V3319 M2 source/dispatch/builder contract.
- Compile: focused AArch64 native-init compile with existing baseline warnings only.
- Build: AArch64 helper/native-init compile, preserved-ramdisk overlay, boot image pack, SHA256 capture.
- Marker check: generated boot image contains V3319 identity plus M2 live-graph telemetry.
- Size gate: final boot image must be `<= 67108864` bytes before any flash attempt.

## Metadata

- Helper flags: ``
- Init extra flags: ``
- Node enum baseline: `v3316-gpu-m0-system-monitor-node-enum-pass`
- M0 sampler baseline: `v3317-gpu-m0-monitor-sampler-live-pass`
- M1 dashboard baseline: `v3318-gpu-m1-monitor-dashboard-live-pass`
- Candidate type: `gpu-m2-monitor-live-graphs-candidate`.
