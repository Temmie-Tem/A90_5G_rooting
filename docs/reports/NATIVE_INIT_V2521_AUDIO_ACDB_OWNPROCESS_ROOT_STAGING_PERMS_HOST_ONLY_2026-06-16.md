# NATIVE_INIT_V2521_AUDIO_ACDB_OWNPROCESS_ROOT_STAGING_PERMS_HOST_ONLY_2026-06-16

## Scope

- Unit: V2521 host-only staging hardening for the V2490 own-process ACDB live runner.
- Trigger: V2520 correctly quotes multi-line `su -c` scripts, which means setup/collection commands will actually run as root on the next live run.
- Goal: prevent the fixed root execution path from breaking `adb push` and `adb pull` by leaving the staging directory or artifacts root-only.

## Change

- `setup_command()` now creates the remote staging directory under `su`, then attempts:
  - `chown shell:shell /data/local/tmp/a90-acdb-ownget /data/local/tmp/a90-acdb-ownget/delta`
  - `chmod 700` on both directories
- This preserves shell writability for subsequent `adb push` while root can still access/execute the helper.
- `collect_prepare_command()` now makes pulled artifacts readable after collection:
  - `chmod 755 .`
  - `find . -maxdepth 1 -type f -exec chmod 644 {} \;`
  - `chmod 755 ./delta`

## Safety Boundary

- Host-only unit; no device run.
- No HAL injection, Magisk module install, HAL restart, AudioTrack/playback, native speaker write, or `/dev/msm_audio_cal` SET ioctl.
- No raw/proprietary artifacts are committed.
- The permission changes apply only to the transient Android temp directory that the runner removes during cleanup.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_audio_acdb_ownprocess_get_live_handoff_v2490.py tests/test_native_audio_acdb_ownprocess_get_live_handoff_v2490.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests/test_native_audio_acdb_ownprocess_get_live_handoff_v2490.py`
  - Result: `17` tests passed.
- V2490 dry-run with the V2512 helper:
  - `ok=true`
  - `live_ready=true`
  - command safety `ok=true`
  - dry-run command plan includes the shell ownership handoff and artifact-readability chmod.

## Next Unit

- V2522 can rerun the hardened V2490 live path.
- Expected first check: `ownget-run-context.txt` should now show root/Magisk context instead of shell.
- If root context is confirmed but `/dev/msm_audio_cal` still denies, the next gate is the SELinux/domain or group policy around `audio_device`, not the adb/su transport.

