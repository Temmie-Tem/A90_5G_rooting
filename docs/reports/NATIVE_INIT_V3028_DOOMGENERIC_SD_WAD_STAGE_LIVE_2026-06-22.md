# Native Init V3028 DOOMGENERIC SD WAD Stage Live

## Summary

- Cycle: `V3028`
- Track: active Video playback / DOOM capstone.
- Decision: `v3028-doomgeneric-sd-wad-stage-live-pass`
- Device action: `sd-write-only-no-flash`
- Boot image written: `0`
- Ramdisk WAD bytes written: `0`
- Public WAD files committed/present: `0`
- Remote SD WAD path: `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- Device WAD bytes: `4196020`
- Device WAD mode: `0600`
- Device WAD SHA256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Device WAD SHA256 match: `1`
- Post-stage selftest fail=0: `1`

## Staging Notes

- The selected private WAD from V3027 was staged onto the SD runtime workspace only.
- The final transfer path used a temporary host HTTP server over the existing NCM link and device-side `busybox wget` into a temporary SD file, then SHA verification, atomic `mv`, `chmod 600`, `sync`, final SHA verification, and `stat`.
- An earlier `netcat` listener transfer attempt did not complete cleanly with this resident userland; its foreground run was cancelled, and no final WAD path was promoted before the successful `wget` path.
- The host NCM profile was temporarily activated to restore host-side NCM reachability. Raw host/device IP, MAC, serial, and SD UUID values are intentionally omitted from this public report.

## Validation

- Bridge wrapper status: managed bridge running and serial candidate present.
- Pre-stage resident health: `version` ok; `status` ok; `selftest verbose` reported `fail=0`.
- Pre-stage storage: SD present, mounted, expected, and read/write.
- Device-side tmp SHA matched the selected V3027 SHA before promotion.
- Final staged WAD SHA matched the selected V3027 SHA after promotion and sync.
- Final staged WAD stat: mode `0600`, size `4196020`.
- Post-stage resident health: `status` ok; `selftest verbose` reported `fail=0`; storage remained SD read/write.
- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_init_frontier_select.py tests/test_native_init_frontier_select.py`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_init_frontier_select`: PASS
- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_init_frontier_select.py --json`: PASS
- `git diff --check`: PASS

## Safety

- No flash, boot image build, boot image write, rollback write, ramdisk write, Wi-Fi action, sysfs write, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path was touched.
- WAD/IWAD bytes remain out of public paths, committed artifacts, ramdisk, and boot image.
- The WAD now persists only on the device SD runtime workspace and under the existing private host input path.

## Next Unit

- Run ID: `V3029`
- Type: `host-only WAD-backed doomgeneric command implementation`
- Summary: Wire bounded verify/play command handling around the SD-staged private WAD hash and path, still keeping WAD bytes out of public, ramdisk, and boot image.
