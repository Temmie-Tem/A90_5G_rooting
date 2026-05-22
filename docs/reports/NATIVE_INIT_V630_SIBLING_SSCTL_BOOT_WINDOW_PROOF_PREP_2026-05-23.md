# Native Init V630 Sibling-SSCTL Boot-Window Proof Prep Report

- date: `2026-05-23 KST`
- status: `local-build-pass`; live flash not yet executed in this report
- native build: `A90 Linux init 0.9.65 (v630)`
- builder: `scripts/revalidation/build_native_init_boot_v630.py`
- local boot image: `stage3/boot_linux_v630.img`
- rollback image: `stage3/boot_linux_v319.img`

## Scope

This prep step implements and locally validates the V630 boot-image proof. It
does not flash the device, reboot the device, arm the proof flag, start Wi-Fi
daemons, start Wi-Fi HAL, scan/connect, use credentials, run DHCP, change
routes, or ping externally.

## Implementation

V630 adds a post-ACM one-shot sibling SSCTL proof to
`stage3/linux_init/v630/90_main.inc.c`.

The proof is disabled unless `/cache/native-init-sibling-ssctl-v630` exists
with exact content `run`. If armed, V630 removes the flag first, then forks a
child that writes `1` once to:

- `/sys/kernel/boot_adsp/boot`
- `/sys/kernel/boot_cdsp/boot`
- `/sys/kernel/boot_slpi/boot`

PID1 waits up to `5000ms`, kills the child on timeout, records timeline/kmsg/log
evidence, and continues to the normal shell path. This directly addresses the
V572 failure mode: no helper runs before ACM, and a stuck child should not hold
PID1 indefinitely.

## Local Validation

```text
python3 -m py_compile scripts/revalidation/build_native_init_boot_v630.py
python3 scripts/revalidation/build_native_init_boot_v630.py
```

Result:

```text
markers: pass
init_sha256=63f273b953e0fb16b5de0154dc78f5425cfafe24f056f2eb934d8a0db3384ef1
ramdisk_sha256=0173390254283ae0d5239fbc03fe59fb1cfd66404a46e7c83b08c3f4b9bab706
boot_sha256=5759e01723a53bd5958478ddf2dd4ef11c05327d8d325eea2eb16f20f18f87bc
```

The builder verified these boot-image markers:

- `A90 Linux init 0.9.65 (v630)`
- `A90v630: sibling ssctl proof armed`
- `native-init-sibling-ssctl-v630`

## Safety Notes

- The proof is one-shot and flag-gated.
- The flag is unlinked before sysfs writes.
- The sysfs writes are isolated in a child process.
- PID1 has a bounded wait and continues to shell on child error/timeout.
- V630 still does not touch `boot_wlan`, `qcwlanstate`, Wi-Fi HAL,
  scan/connect, credentials, DHCP, routes, or external ping.

## Next Step

Proceed to live V630 validation:

1. flash `stage3/boot_linux_v630.img` with the arm flag absent;
2. verify disabled-smoke boot and cmdv1 reachability;
3. arm `/cache/native-init-sibling-ssctl-v630` with `run`;
4. reboot once, collect markers, and roll back to `stage3/boot_linux_v319.img`;
5. classify whether service `74`, WLAN-PD, WLFW/BDF, or only sibling sysmon
   advanced.
