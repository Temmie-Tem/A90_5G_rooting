# Native Init V3020 DOOMGENERIC Port Probe

## Summary

- Decision: `v3020-doomgeneric-private-source-build-probe-pass`
- Device action: `none` in this host-only unit.
- Track: active Video playback / DOOM capstone.
- Private doomgeneric source pinned: `1`
- Private source clean: `1`
- AArch64 probe linked: `1`
- Public WAD files committed/present: `0`
- Private WAD files currently present: `0`
- Safe next unit: `1`

## Source Pin

- Source URL: `https://github.com/ozkl/doomgeneric`
- Private source root: `workspace/private/demo-assets/doom/doomgeneric-v3020`
- Pinned commit: `dcb7a8dbc7a16ce3dda29382ac9aae9d77d21284`
- Current commit: `dcb7a8dbc7a16ce3dda29382ac9aae9d77d21284`
- Commit date: `2026-04-12`
- Commit subject: `boolean fix`
- Source file count: `202`
- LICENSE SHA256: `8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643`
- `doomgeneric.h` SHA256: `d24861dd7aa75d283226724f710ae4226839898bc61b986a0602df7df19df148`
- `doomkeys.h` SHA256: `9bacfdc85b2003913b8a571c0762226d07e5e303dbdaa6c64887a194a4279ba2`

## Build Probe

- Adapter source: `workspace/private/builds/native-init/v3020-doomgeneric-port-probe/a90_doomgeneric_port_probe_v3020.c`
- Adapter source SHA256: `cf1ef6923992783eda4722fa940824754f0863c59e33251f9b784f09519b9acb`
- Adapter object: `workspace/private/builds/native-init/v3020-doomgeneric-port-probe/a90_doomgeneric_port_probe_v3020.o`
- Adapter object SHA256: `784ef8495943a3908015680870f2f9b21eda707baae559b60683337035754391`
- doomgeneric object: `workspace/private/builds/native-init/v3020-doomgeneric-port-probe/doomgeneric_v3020.o`
- doomgeneric object SHA256: `a2da05d74b0119efb189f38541a19ffa72661147e10c0772e99d919941839147`
- Probe binary: `workspace/private/builds/native-init/v3020-doomgeneric-port-probe/a90_doomgeneric_port_probe_v3020`
- Probe binary SHA256: `7c09f86ed4b3ffdfbd68a70e078f1faeb9824ed594ba0cf58d47843c5440dbe3`
- `file`: `/home/temmie/dev/A90_5G_rooting/workspace/private/builds/native-init/v3020-doomgeneric-port-probe/a90_doomgeneric_port_probe_v3020: ELF 64-bit LSB executable, ARM aarch64, version 1 (GNU/Linux), statically linked, BuildID[sha1]=44cef9a8980c9309c291c84d5c6719be502f0034, for GNU/Linux 3.7.0, not stripped`

## Port Mapping

- Frame path: DG_DrawFrame -> private probe framebuffer copy; native target will call a90_kms_present.
- Input path: doompad snapshot edges -> DG_GetKey queue.
- Time path: DG_SleepMs/DG_GetTicksMs bounded monotonic shim.
- Sound path: not enabled in first WAD-backed unit.

## Asset Policy

- WAD/IWAD data must not be committed.
- WAD/IWAD data must not be embedded into the boot image for the first real engine unit.
- Runtime staging root for the next WAD unit: `/cache/a90-runtime/pkg/doom/v3021/`.
- Private source/asset root: `workspace/private/demo-assets/doom/`.

## Safety

- Host-only source/build probe; no flash, serial command, evdev open, input injection, sysfs write, Wi-Fi action, audio/video playback, WAD copy, boot image write, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.
- The generated adapter C and AArch64 probe binary are private build artifacts only.
- A later live unit still needs explicit rollback-gated boot-image build and device validation.

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doomgeneric_port_probe_v3020.py tests/test_native_doomgeneric_port_probe_v3020.py`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doomgeneric_port_probe_v3020`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doomgeneric_port_probe_v3020.py`: PASS
- `file workspace/private/builds/native-init/v3020-doomgeneric-port-probe/a90_doomgeneric_port_probe_v3020`: PASS (AArch64 static ELF)
- `git diff --check`: PASS

## Next Unit

- Run ID: `V3021`
- Type: `source-integration-plan-or-build`
- Summary: Choose whether to vendor the pinned doomgeneric source publicly with GPL/NOTICE handling or keep source private for one more build-only integration probe; WAD remains runtime-private.
