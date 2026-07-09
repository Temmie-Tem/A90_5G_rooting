# NATIVE_INIT V3406 — S22+ O1 live result

Date: 2026-07-10 04:12 KST / 2026-07-09 19:12 UTC

## Verdict

O1 CANDIDATE FAIL, ROLLBACK PASS.

The exact O1 boot-only candidate booted normal Android and exposed the stock
Samsung CDC ACM tty. The first framed host request failed with `EIO`, so O1 did
not prove any framed payload roundtrip. Retained kernel log evidence identifies
the exact blocker: Android init rejected the injected service because it had no
SELinux transition from init to an executable domain.

The pinned Magisk boot-only AP was restored. Current Android, Magisk root, boot
SHA, and stock `DR-daemon` tty ownership are healthy.

## Live Evidence

Run:

```text
workspace/private/runs/s22plus_o1_stock_first_stage_control_live_gate_20260709T190500Z
```

Result:

```text
result=candidate-fail-rollback-pass
rc=1
candidate_ap_sha256=388d35c12e9f5024f053837444da46254db6a6177c046400549148e24eaeec29
candidate_boot_sha256=df7a166752f78aa07bea10aef53de1ba2737abf43bb041fe01738cce36113070
candidate_error=OSError errno=5 Input/output error
roundtrip=null
rollback_target=magisk
```

Candidate transfer completed and the original Odin endpoint disconnected. The
stock Android USB gadget returned as `04e8:6860`, with `/dev/ttyACM0` using the
`cdc_acm` driver. The helper recorded `candidate_boot_ready`, then failed at
`candidate_protocol_start` before sequence 0 completed.

Before rollback, a bounded read-only check showed:

```text
boot=df7a166752f78aa07bea10aef53de1ba2737abf43bb041fe01738cce36113070
O1 marker=0
O1 service state=<absent>
O1 status=<absent>
DR-daemon=running
ddexe=<present>
```

This proved the candidate image itself was running while the O1 wrapper had not
started. It did not yet distinguish rc injection from service-start rejection.

## Root Cause

After rollback, `/proc/last_kmsg` from the candidate boot was collected to:

```text
workspace/private/runs/s22plus_o1_stock_first_stage_control_live_gate_20260709T190500Z/postrollback_candidate_last_kmsg.bin
bytes=2097136
```

The retained log proves the overlay was injected and the property action ran:

```text
init: processing action (sys.usb.configured=configured)
  from (/system/etc/init/hw/init.rc:3411)
init: Command 'start s22plus_o1_control'
  action=sys.usb.configured=configured (/system/etc/init/hw/init.rc:3412)
  failed: File /debug_ramdisk/s22plus_o1_service.sh
  (labeled "u:object_r:system_file:s0") has incorrect label or no domain
  transition from u:r:init:s0 to another SELinux domain defined
```

The same rejection appears at approximately 18.226s, 22.226s, 22.663s, and
62.324s. Therefore:

- Magisk `overlay.d` packaging worked;
- `${MAGISKTMP}` became `/debug_ramdisk`;
- the O1 property trigger worked;
- service execution failed before the wrapper could create marker/status or
  stop `DR-daemon`;
- stock `ddexe` remained present, so the host did not reach the O0 daemon and
  the `EIO` is downstream of this service-start failure, not an O0 protocol
  verdict.

This supersedes the initial live-window inference that the rc might not have
been registered.

## Rollback

The helper's first `adb reboot download` request after the candidate failure hit
a transient reconnect error:

```text
candidate_adb_reboot_download_rc=1
error: closed
```

Android re-enumerated normally. After the operator explicitly requested that
the host issue the software Download transition, the second bounded
`adb reboot download` returned 0. The helper detected Download and flashed the
pinned Magisk rollback AP.

Postrollback:

```text
boot_sha256=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
boot_completed=1
su=uid=0(root) context=u:r:magisk:s0
3 stability samples=PASS, uptime strictly increasing
DR-daemon=running
ddexe=present and tty owner
O1 status=absent (expected after rollback reboot)
```

Timeline uses the canonical single `events` schema and contains:

```text
live_session_start
candidate_flash_start
candidate_flash_done
candidate_boot_ready
rollback_flash_start
rollback_flash_done
rollback_boot_ready
live_session_end
```

## Interpretation And Next

The next candidate must change one discriminator only: add
`seclabel u:r:magisk:s0` to the existing O1 service stanza. Android init defines
`seclabel` as the explicit process context used before service exec, and the
same Magisk boot already runs Magisk's injected init actions in
`u:r:magisk:s0`. References:

- [AOSP init service `seclabel` contract](https://android.googlesource.com/platform/system/core/+/refs/heads/android15-qpr2-s9-release/init/README.md)
- [Magisk root directory overlay guide](https://topjohnwu.github.io/Magisk/guides.html)
- Magisk v30.7 source `native/src/init/rootdir.rs`, which injects Magisk exec
  actions with `u:r:magisk:s0`

O1.1 host work should preserve the exact trigger, wrapper, daemon, request
count, tty handoff, kernel, and Magisk `/init`. The live helper should also add a
bounded ADB Download retry after reconnect and collect `/proc/last_kmsg`
automatically after rollback. A new O1.1 live flash requires a fresh pinned
exception and new explicit operator approval.
