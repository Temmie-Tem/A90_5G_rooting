# Native Init V631 Per-Node Sibling-SSCTL Proof Live Report

- date: `2026-05-23 KST`
- status: `classified/rollback-complete`; Wi-Fi external ping is **not** complete
- native test image: `stage3/boot_linux_v631.img`
- rollback image: `stage3/boot_linux_v319.img`
- disabled-smoke evidence: `tmp/wifi/v631-disabled-smoke-20260523-045821/`
- armed-proof evidence: `tmp/wifi/v631-armed-proof-20260523-045943/`
- decision: `v631-cdsp-timeout-adsp-slpi-ok`

## Scope

V631 live validation flashed the V631 boot image, first with the proof flag
absent, then with `/cache/native-init-sibling-ssctl-v631` armed with `run`.

No Wi-Fi HAL, supplicant, hostapd, `boot_wlan`, `qcwlanstate`, scan/connect,
credential use, DHCP, route change, or external ping was executed.

## Disabled-Smoke Result

```text
A90 Linux init 0.9.66 (v631)
boot: BOOT OK shell 4.2s
selftest: pass=11 warn=1 fail=0
```

The disabled boot had no `wifi-v631-ssctl` timeline entry:

```text
16     3898ms console            rc=0 errno=0 serial console attached
17     4160ms autohud            rc=0 errno=0 started refresh=2
18     4160ms shell              rc=0 errno=0 interactive shell ready
```

## Armed-Proof Result

The armed boot returned to cmdv1 and split the V630 hidden timeout into a
per-node map:

```text
17     4198ms wifi-v631-ssctl    rc=0 errno=0 armed one-shot
18     4198ms wifi-v631-ssctl    rc=0 errno=0 adsp start
19     4298ms wifi-v631-ssctl    rc=0 errno=0 adsp status=0x0
20     4298ms wifi-v631-ssctl    rc=0 errno=0 cdsp start
21     9404ms wifi-v631-ssctl    rc=-110 errno=110 cdsp wait failed reaped=1
22     9409ms wifi-v631-ssctl    rc=0 errno=0 slpi start
23     9511ms wifi-v631-ssctl    rc=0 errno=0 slpi status=0x0
24     9511ms wifi-v631-ssctl    rc=-5 errno=1 complete failures=1 timeouts=1
25     9512ms autohud            rc=0 errno=0 started refresh=2
26     9512ms shell              rc=0 errno=0 interactive shell ready
```

Proof log:

```text
FLAG=absent
LOG-BEGIN
node adsp parent start path=/sys/kernel/boot_adsp/boot timeout_ms=5000
node adsp child start path=/sys/kernel/boot_adsp/boot
node adsp write rc=0
node adsp parent rc=0 status=0x0 reaped=1
node cdsp parent start path=/sys/kernel/boot_cdsp/boot timeout_ms=5000
node cdsp child start path=/sys/kernel/boot_cdsp/boot
node cdsp parent rc=-110 status=0x9 reaped=1
node slpi parent start path=/sys/kernel/boot_slpi/boot timeout_ms=5000
node slpi child start path=/sys/kernel/boot_slpi/boot
node slpi write rc=0
node slpi parent rc=0 status=0x0 reaped=1
LOG-END
```

Interpretation:

- one-shot flag removal worked;
- PID1 continued to shell;
- ADSP write returned success;
- CDSP write blocked until timeout, then the child was reaped;
- SLPI write still executed after CDSP timeout and returned success;
- service `74`, WLAN-PD, WLFW/BDF, Wi-Fi link-up, and external ping did not
  advance.

## Rollback Result

Rollback to V319 completed:

```text
remote image sha256: 98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8
boot block prefix sha256: 98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8
A90 Linux init 0.9.61 (v319)
boot: BOOT OK shell 4.3s
selftest: pass=11 warn=1 fail=0
```

## Classification

V631 classified the sibling SSCTL boot-node surface:

| node | result | interpretation |
| --- | --- | --- |
| ADSP | `status=0x0` | safe to write in this post-ACM proof window |
| CDSP | `rc=-110`, reaped | active blocking node |
| SLPI | `status=0x0` | safe to write after CDSP timeout/reap |

The next gate should stop repeating ADSP/SLPI. V632 should focus on why CDSP
boot-node write blocks under native init while Android's early boot reaches
sibling sysmon and service `74`. Candidate directions are host-only first:
compare Android CDSP-related init/property/firmware timing, inspect CDSP sysfs
state before write, and only then design a narrower CDSP-specific proof.

