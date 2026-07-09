# NATIVE_INIT V3403 — S22+ O0 stock USB control live proof

Date: 2026-07-10 03:34 KST / 2026-07-09 18:34 UTC

## Verdict

PASS. The known-good Android/Magisk USB stack carried a bidirectional framed
control protocol between device `/dev/ttyGS0` and host `/dev/ttyACM0` without a
flash, reboot, gadget reconfiguration, configfs/sysfs write, or module load.

The successful bounded run completed all 128 requests with:

```text
requested=128
completed=128
payload_equality=true
sequence_continuity=true
host_reopen_at=64
host_reopen_completed=true
payload_bytes_each_direction=7383
daemon_invalid=0
daemon_crc_errors=0
daemon_seq_errors=0
daemon_io_reopens=0
```

Latency:

```text
min_ms=0.183291
p50_ms=0.314189
p95_ms=0.610990
p99_ms=1.138363
max_ms=2.977764
```

This proves the O0 host protocol, stock CDC ACM transport, device tty, and
clean host close/reopen behavior. It does not prove direct native PID1 or native
DWC3/configfs bring-up.

## Root Cause Found During O0

The first bounded attempt did not receive a response. The device helper started,
but host sequence 0 timed out. Post-run read-only inspection showed that stock
service `DR-daemon` (`/system/bin/ddexe`, SELinux domain `u:r:ddexe:s0`) already
held `/dev/ttyGS0`. The original helper and `ddexe` were competing readers on one
tty queue; `ddexe` consumed the host request.

The final harness therefore treats stock tty ownership as an explicit reversible
gate:

1. require `init.svc.DR-daemon=running` and one `ddexe` ttyGS0 owner;
2. request `ctl.stop DR-daemon` and require stopped/no owner;
3. run the temporary O0 daemon and framed proof;
4. stop/delete the temporary daemon;
5. request `ctl.start DR-daemon` and require running/one ttyGS0 owner.

Final ownership evidence:

```text
before:  state=running pid_present=true  tty_owner_count=1
handoff: state=stopped pid_present=false tty_owner_count=0
after:   state=running pid_present=true  tty_owner_count=1
remote temporary daemon=absent
```

The active gadget remained connected throughout. The udev observer recorded no
USB re-enumeration event, which is expected because O0 changed the tty consumer,
not the gadget or UDC.

## Protocol

The fixed binary frame is:

```text
magic[4]="S2O0"
version:u8=1
type:u8=request(1)|response(2)
payload_len:u16le
seq:u32le
crc32:u32le
payload[0..1024]
```

CRC32 covers the first 12 header bytes and payload. The device response preserves
the request sequence and payload while changing only the frame type and CRC.

Tracked implementation:

- `workspace/public/src/android/s22plus_o0_tty_echo.c`
- `workspace/public/src/scripts/revalidation/s22plus_o0_stock_usb_control.py`
- `tests/test_s22plus_o0_stock_usb_control.py`

Generated AArch64 daemon metadata:

```text
sha256=a82cd32f83afc20d40fc74a9402896ae07378811f259913ed6df7cbc540f858c
size=708176
file=ELF 64-bit LSB executable, ARM aarch64, statically linked
```

The compiled binary remains under `workspace/private/` and is not committed.

## Run Evidence

Initial ownership-conflict run:

```text
workspace/private/runs/s22plus_o0_stock_usb_control_20260709T183026Z
result=fail
error=serial read timeout after 0/16 bytes
state_unchanged=all true
cleanup_rc=0
```

Successful run:

```text
workspace/private/runs/s22plus_o0_stock_usb_control_20260709T183327Z
result=pass
rc=0
daemon_rc=0
cleanup_rc=0
```

The timeline uses only the canonical single-object shape:

```json
{"events":[{"name":"o0_session_start","timestamp_utc":"..."}]}
```

It records staging, observer start, stock-service handoff, daemon readiness,
roundtrip start/end, host tty reopen start/end, cleanup, stock-service restore,
observer end, and session end. Flash phases are intentionally absent because O0
performed no candidate or rollback flash.

Postflight equality was true for boot SHA256, model/device/incremental, ttyGS0,
active UDC, and `sys.usb.config`. The known-good Magisk boot remained
`2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`.

## Validation

```text
python py_compile: PASS
AArch64 static -Wall -Wextra -Werror build: PASS
unit tests: Ran 13, OK
offline safety contract: ready=true
live O0 result: PASS
```

Safety contract:

```text
flash=false
reboot=false
configfs_write=false
sysfs_write=false
active_gadget_change=false
module_load=false
magisk_install=false
temporary_data_local_tmp_only=true
stock_tty_service_stop_start_restored=true
```

## Next

O0 is closed. The next active unit is O1 host-only design/build: preserve the
stock first-stage module loader and use a Magisk boot `overlay.d` rc/service to
start the O0-proven daemon at the earliest safe trigger. O1 must account for
stock `DR-daemon` ownership rather than starting a second ttyGS0 reader. No O1
live boot flash is authorized by this result.
