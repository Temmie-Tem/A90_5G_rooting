# Native Init V630 Sibling-SSCTL Boot-Window Proof Live Report

- date: `2026-05-23 KST`
- status: `classified/rollback-complete`; Wi-Fi external ping is **not** complete
- native test image: `stage3/boot_linux_v630.img`
- rollback image: `stage3/boot_linux_v319.img`
- disabled-smoke evidence: `tmp/wifi/v630-disabled-smoke-20260523-044657/`
- armed-proof evidence: `tmp/wifi/v630-armed-proof-20260523-044912/`
- decision: `v630-boot-window-timeout-after-adsp`

## Scope

V630 live validation flashed the V630 boot image, first with the proof flag
absent, then with `/cache/native-init-sibling-ssctl-v630` armed with `run`.

No Wi-Fi HAL, supplicant, hostapd, `boot_wlan`, `qcwlanstate`, scan/connect,
credential use, DHCP, route change, or external ping was executed.

## Disabled-Smoke Result

```text
A90 Linux init 0.9.65 (v630)
boot: BOOT OK shell 4.1s
selftest: pass=11 warn=1 fail=0
```

The disabled boot had no `wifi-v630-ssctl` timeline entry:

```text
16     3862ms console            rc=0 errno=0 serial console attached
17     4124ms autohud            rc=0 errno=0 started refresh=2
18     4124ms shell              rc=0 errno=0 interactive shell ready
```

The arm flag and proof log were absent:

```text
FLAG=absent
LOG=absent
```

This proves V630 does not repeat the V572 pre-ACM bootloop behavior when the
proof is not explicitly armed.

## Armed-Proof Result

The armed boot returned to cmdv1, but the proof hit the child timeout:

```text
boot: BOOT ERR wifi-v630- E110
reaper: total=1 last_pid=548 last=signal=9
```

Timeline:

```text
16     3915ms console            rc=0 errno=0 serial console attached
17     4200ms wifi-v630-ssctl    rc=0 errno=0 armed one-shot
18     9206ms wifi-v630-ssctl    rc=-110 errno=110 wait failed
19     9206ms autohud            rc=0 errno=0 started refresh=2
20     9207ms shell              rc=0 errno=0 interactive shell ready
```

Proof log:

```text
FLAG=absent
LOG-BEGIN
v630 sibling ssctl child start
write /sys/kernel/boot_adsp/boot rc=0
LOG-END
```

Interpretation:

- the one-shot flag removal worked;
- the fork/timeout safety path worked;
- PID1 continued to shell after timeout;
- ADSP boot-node write returned success;
- the child did not reach a logged CDSP or SLPI result before timeout;
- no service `74`, WLAN-PD, WLFW/BDF, or Wi-Fi link-up evidence advanced.

## Rollback Result

Rollback to V319 completed:

```text
remote image sha256: 98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8
boot block prefix sha256: 98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8
A90 Linux init 0.9.61 (v319)
boot: BOOT OK shell 4.1s
selftest: pass=11 warn=1 fail=0
```

## Classification

V630 is useful but not sufficient:

- `disabled-smoke`: pass
- `armed proof`: bounded failure after ADSP
- `rollback`: pass
- `service74`: not advanced
- `wlan_pd`: not advanced
- `wifi_bringup`: not attempted
- `external_ping`: not attempted

The correct next gate is V631: split ADSP/CDSP/SLPI into separately bounded
per-node child attempts so one blocking node cannot hide the others. V631
should keep the post-ACM one-shot design and rollback path, but run one child
per node with independent timeout and explicit per-node result logging.

