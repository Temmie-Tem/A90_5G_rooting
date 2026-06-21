# Native Init V3024 DOOMGENERIC Private Integration Build

## Summary

- Decision: `v3024-doomgeneric-private-full-engine-link-pass`
- Device action: `none` in this host-only unit.
- Track: active Video playback / DOOM capstone.
- Build scope: full private doomgeneric engine source link with a native A90 bridge adapter.
- Private doomgeneric source pinned: `1`
- Private source clean: `1`
- V3023 policy ready: `1`
- Private engine source files compiled: `80`
- Private engine object count: `81`
- AArch64 static engine linked: `1`
- Marker check pass: `1`
- Public WAD files committed/present: `0`
- Private WAD files currently present: `0`
- Safe next host-only unit: `1`

## Source Pin

- Source URL: `https://github.com/ozkl/doomgeneric`
- Private source root: `workspace/private/demo-assets/doom/doomgeneric-v3020`
- Pinned commit: `dcb7a8dbc7a16ce3dda29382ac9aae9d77d21284`
- Current commit: `dcb7a8dbc7a16ce3dda29382ac9aae9d77d21284`
- Commit date: `2026-04-12`
- Commit subject: `boolean fix`
- LICENSE SHA256: `8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643`
- Source makefile: `workspace/private/demo-assets/doom/doomgeneric-v3020/doomgeneric/Makefile.soso`
- Engine source count from makefile: `80`
- Excluded backend: `doomgeneric_soso.c`

## Private Build Artifact

- Adapter source: `workspace/private/builds/native-init/v3024-doomgeneric-private-integration/a90_doomgeneric_native_bridge_v3024.c`
- Adapter source SHA256: `d420ef86b6ceeed41f5cbe4db60e5b2d8b688f2809881d64b7274b3bd9e0019c`
- Engine binary: `workspace/private/builds/native-init/v3024-doomgeneric-private-integration/a90_doomgeneric_private_engine_v3024`
- Engine binary SHA256: `8b6630498b7ff217e6ad9b27593f89644ba73eb7cbbf11361838972f15581735`
- Engine binary bytes: `597960`
- Engine object total bytes: `1320240`
- Compile stdout non-empty count: `35`
- `file`: `/home/temmie/dev/A90_5G_rooting/workspace/private/builds/native-init/v3024-doomgeneric-private-integration/a90_doomgeneric_private_engine_v3024: ELF 64-bit LSB executable, ARM aarch64, version 1 (GNU/Linux), statically linked, BuildID[sha1]=d3a30d5527a4b1499a97deb18e4d89e3c19dd2a1, for GNU/Linux 3.7.0, stripped`
- `size`: `text	   data	    bss	    dec	    hex	filename |  537528	  21548	1046304	1605380	 187f04	/home/temmie/dev/A90_5G_rooting/workspace/private/builds/native-init/v3024-doomgeneric-private-integration/a90_doomgeneric_private_engine_v3024`

## Size Gate

- V3021 init binary bytes: `1330256`
- V3021 boot image bytes: `61046784`
- Engine-only object total within V3023 2 MiB cap: `1`
- Boot-image delta: `not-produced` because V3024 deliberately stops at private engine link, before ramdisk/boot integration.

## Runtime Policy

- Runtime WAD root: `/cache/a90-runtime/pkg/doom/v3024/`
- Runtime WAD path marker: `/cache/a90-runtime/pkg/doom/v3024/DOOM1.WAD`
- WAD/IWAD data is not committed, copied, embedded, or staged by this build.
- Sound remains disabled for the first native engine link path (`-nosound -nomusic`).
- Input path remains serial doompad state to `DG_GetKey`; no OTG, touch, evdev injection, or uinput is required.
- Render target marker remains `DG_DrawFrame` to native KMS/pageflip; this private link artifact does not touch DRM/KMS.

## Safety

- Host-only private-source link; no flash, serial command, WAD copy, Wi-Fi action, sysfs write, boot image write, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.
- The public tree records only scripts, tests, and metadata; generated objects/binaries remain private.

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doomgeneric_engine_integration_build_v3024.py tests/test_native_doomgeneric_private_integration_build_v3024.py workspace/public/src/scripts/revalidation/native_init_frontier_select.py tests/test_native_init_frontier_select.py`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doomgeneric_private_integration_build_v3024 tests.test_native_init_frontier_select`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doomgeneric_engine_integration_build_v3024.py`: PASS
- `file workspace/private/builds/native-init/v3024-doomgeneric-private-integration/a90_doomgeneric_private_engine_v3024`: PASS (AArch64 static ELF)
- `git diff --check`: PASS

## Next Unit

- Run ID: `V3025`
- Type: `native-init command/boot integration candidate`
- Summary: Wire the V3024 private engine link result into a native-init candidate command surface, still without WAD data in public, ramdisk, or boot image.
