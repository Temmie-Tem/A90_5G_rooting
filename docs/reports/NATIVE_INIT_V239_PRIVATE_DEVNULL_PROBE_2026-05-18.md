# Native Init v239 Private Devnull Probe

## Summary

- Goal: validate the v238 conclusion by providing `/dev/null` inside the
  private Android execution namespace and rerunning the bounded linker-list
  matrix.
- Result: PASS / `android-linker-devnull-early-abort-cleared`.
- No PID1 boot image update, Android daemon execution, Wi-Fi scan/connect,
  rfkill write, credential handling, DHCP, routing, or Android partition write
  was used.

## Implementation

Updated helper:

- `stage3/linux_init/helpers/a90_android_execns_probe.c`
- version: `a90_android_execns_probe v6`
- SHA-256: `822608844d89ea8d888c7f16000256acc0dc9a2583d1a330c74f32c323fd6438`

New helper option:

```text
--null-device-mode none|dev-null|dev-null-selinux
```

Behavior:

- `none`: preserves v236 behavior.
- `dev-null`: creates private `<root>/dev/null` as char device `1:3`, mode
  `0666`, before `chroot()`/exec.
- `dev-null-selinux`: additionally creates private
  `<root>/sys/fs/selinux/null` as char device `1:3`, mode `0666`.

Updated host probe:

- `scripts/revalidation/wifi_linker_crash_capture_probe.py`
- passes `--null-device-mode` to the helper;
- records crash fault address per matrix row;
- classifies v239 PASS when fault address `0xa1` no longer appears.

## Validation

Local validation:

```bash
python3 -m py_compile scripts/revalidation/wifi_linker_crash_capture_probe.py
scripts/revalidation/build_android_execns_probe_helper.sh
python3 scripts/revalidation/wifi_linker_crash_capture_probe.py \
  --out-dir tmp/wifi/v239-plan-smoke \
  --null-device-mode dev-null \
  plan
```

Helper deploy used existing NCM transfer path:

```text
/cache/bin/a90_android_execns_probe
sha256=822608844d89ea8d888c7f16000256acc0dc9a2583d1a330c74f32c323fd6438
```

Real linkerconfig support files were reinstalled from v233 host evidence because
they were absent on the live device:

| file | SHA-256 |
| --- | --- |
| `/cache/bin/a90_real_ld.config.txt` | `1ab340f0ee1e5f6d7c43e372dfe3bc9164d34b348dd9c716ded1b4e56e079f1a` |
| `/cache/bin/a90_real_apex.libraries.config.txt` | `5419adf6ed8f74c480d79096681a19a8570470ab8359c6e8c0be110da434f16e` |

Live probe command:

```bash
python3 scripts/revalidation/wifi_linker_crash_capture_probe.py \
  --out-dir tmp/wifi/v239-devnull-linker-capture-live \
  --null-device-mode dev-null \
  probe
```

Live result:

```json
{
  "decision": "android-linker-devnull-early-abort-cleared",
  "pass": true,
  "reason": "null-device materialization cleared the 0xa1 early-abort signature in the selected matrix",
  "null_device_mode": "dev-null"
}
```

Evidence directory:

```text
tmp/wifi/v239-devnull-linker-capture-live/
```

## Matrix Result

| linker | target | signal | exit | fault | stdout | stderr | conclusion |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| `system-linker` | `system-toybox` | `0` | `0` | none | `926` | `0` | linker list passed |
| `system-linker` | `apex-linker64-self` | `0` | `0` | none | `41` | `276` | linker list completed with config warning |
| `system-linker` | `cnss-daemon` | `0` | `1` | none | `41` | `222` | dependency/runtime namespace blocker |
| `apex-linker` | `system-toybox` | `0` | `0` | none | `926` | `0` | linker list passed |
| `apex-linker` | `apex-linker64-self` | `0` | `0` | none | `41` | `276` | linker list completed with config warning |
| `apex-linker` | `cnss-daemon` | `0` | `1` | none | `41` | `258` | dependency/runtime namespace blocker |

The v236/v237/v238 fault address `0xa1` no longer appears in any matrix row.
No selected case crashed with `SIGSEGV(11)` after `dev-null` materialization.

## New Blocker

The blocker moved from early abort to normal linker dependency resolution for
`cnss-daemon`:

```text
CANNOT LINK EXECUTABLE "/system/bin/linker64": library "libcutils.so" not found: needed by main executable
CANNOT LINK EXECUTABLE "/apex/com.android.runtime/bin/linker64": library "libcutils.so" not found: needed by main executable
```

Baseline `system-toybox` resolves `libcutils.so` from `/system/lib64`, which
means the private root now supports at least one normal Android linker-list path.
The remaining issue is target/namespace-specific library visibility or namespace
configuration for the vendor target path, not the stdio null-device abort.

## Interpretation

v239 closes the v238 hypothesis: the generic linker crash was caused by missing
null-device context in the private Android execution namespace.  Providing only
`/dev/null` is sufficient to clear the `0xa1` early-abort signature; the
`/sys/fs/selinux/null` fallback was not needed in this run.

Wi-Fi daemon start remains blocked.  The next safe step is another read-only
linker-list investigation focused on why `cnss-daemon` cannot resolve
`libcutils.so` even though baseline system binaries can.

## Guardrails

- No `cnss-daemon` entrypoint execution.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.
- No rfkill write.
- No global bind mount or persistent Android partition write.
- Helper is restricted to `linker64 --list` inside a private namespace.
