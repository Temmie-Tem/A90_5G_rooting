# Server-Distro Wi-Fi STA Upstream WSTA2 Runner

- Date: 2026-07-04 KST
- Unit: WSTA2 native `wlan0` materialization runner.
- Scope: source/static validation plus fail-closed live preflight.
- Device mutation: none. No flash, no reboot, no Wi-Fi association, no DHCP, no ping, no public tunnel start.

## Verdict

WSTA2 now has a bounded host runner:

- `workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py`

The runner performs the native live gate only when the required control path exists.  In default mode it probes
an already-running native-init through cmdv1.  With `--flash-v3384`, it may flash the pinned V3384
hardware-contract candidate only through `native_init_flash.py`, and only when either recovery ADB is already
available or native cmdv1 can request recovery.  If the device is already in Debian appliance PID1 and native
cmdv1 is gone, the runner records a blocked result and stops before flash.  If native cmdv1 is present but the
resident build is not V3384, no-flash mode blocks before assuming the hardware-contract command exists.

## Live Preflight Result

The current device was reachable over the local USB/NCM Debian appliance path, and the Debian control plane was
alive.  Native cmdv1 did not return an `A90P1 END` marker in the bounded window, and ADB recovery was not present.

Two private runner results were written:

- `workspace/private/runs/server-distro/wsta2-native-materialization-20260703T171938Z/wsta2_result.json`
  - `decision=wsta2-blocked-native-cmdv1-unavailable`
- `workspace/private/runs/server-distro/wsta2-native-materialization-20260703T171952Z/wsta2_result.json`
  - `decision=wsta2-blocked-no-native-cmdv1-or-recovery-adb`
  - rollback image preconditions were present and SHA-pinned where required

This is a safe block, not a WSTA2 failure.  The current state simply cannot run a native materialization gate
without a native/recovery control path.  No recovery workaround was attempted from Debian, because that would
risk leaving the boot-only flash envelope.

## Runner Gate

When native cmdv1 or recovery ADB is available, run:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
python3 workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py \
  --flash-v3384 \
  --probe-iftype
```

The runner checks:

- V3384 candidate image path, SHA256, and version marker;
- rollback images (`v2321`, `v2237`, `v48`) before any flash request;
- `server-distro hardware-contract` contains `A90DHW next.required=wifi-sta-upstream`;
- `selftest` reports `fail=0`;
- `wifi status` or the bounded `wifi softap iftype-probe` path reaches `wlan0_present=1`;
- process table has no native `wpa_supplicant`, DHCP, AP, DNS, or tunnel worker left running.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py \
  tests/test_server_distro_wsta2_native_materialization.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta2_native_materialization

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py --timeout 5

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py \
  --timeout 5 --flash-timeout 30 --flash-v3384

git diff --check
```

## Safety Boundary

- No boot image was flashed.
- No non-boot partition or raw write path was used.
- No Debian-side recovery/misc/BCB workaround was attempted.
- No Wi-Fi association, DHCP, ping, NAT, AP, or public tunnel command was run.
- No credentials, public URLs, tokens, BSSID/MAC, DHCP leases, or concrete device identifiers are committed.

## Next Gate

WSTA2 live remains pending until native cmdv1 or recovery ADB is available.  Once available, run the WSTA2
runner with `--flash-v3384 --probe-iftype`; if it passes, continue to WSTA3 only with private credentials staged
in the Debian appliance.
