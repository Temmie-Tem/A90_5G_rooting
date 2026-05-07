# Native Init v156 Thermal/Power Sensor Map Report (2026-05-08)

## Result

- status: PASS
- build: `A90 Linux init 0.9.56 (v156)`
- marker: `0.9.56 v156 THERMAL POWER MAP`
- boot image: `stage3/boot_linux_v156.img`

## Artifacts

```text
8746c1b3cbf7901bc28f6b6f2f775a46cf6a1ef46fb4b10dcc6ee87925b267ac  stage3/linux_init/init_v156
ca6f86781caec181657cec75456659cd56d00a18ca46346ad82f17823fcab642  stage3/ramdisk_v156.cpio
d0760ee5365b83fd48e1c93dd26f8eb9b4200066853f3c483d0c2ddabfc7c239  stage3/boot_linux_v156.img
```

## Implemented

- Added `stage3/linux_init/a90_sensormap.c`.
- Added `stage3/linux_init/a90_sensormap.h`.
- Added `sensormap [summary|thermal|power|full|paths]`.
- Added sensor summary to `status` and `bootstatus`.
- Added `scripts/revalidation/sensor_map_collect.py`.
- Updated latest verified docs to v156.

## Device Evidence

```text
sensormap=thermal=78 readable=64 cooling=15 max=lmh-dcvs-01:75.000C power=10 batteries=1 chargers=3
```

Observed examples:

- thermal zones: 78
- readable thermal temps: 64
- cooling devices: 15
- power supplies: 10
- battery: present, capacity 100%, health Good
- chargers/supplies include `ac`, `usb`, `wireless`, `max77705-charger`, `sec-direct-charger`, `pca9468-charger`

## Validation

```text
native_init_flash.py stage3/boot_linux_v156.img --from-native --expect-version "A90 Linux init 0.9.56 (v156)" --verify-protocol auto
cmdv1 version/status: PASS
sensormap: PASS
sensormap thermal: PASS
sensormap power: PASS
sensormap paths: PASS
sensor_map_collect.py: PASS failed_commands=0
native_integrated_validate.py: PASS commands=25
git diff --check: PASS
python3 -m py_compile: PASS
```

## Notes

- v156 is read-only. It does not modify thermal governors, charger state, cooling device state, watchdog, tracefs, mount state, or partitions.
- Some modem thermal zones expose no readable temperature in native init. This is recorded as missing temp, not a failure.
- `lmh-dcvs-*` reports 75C while CPU/GPU user-facing zones stay around low 30C in this sample, so future trend logic should keep per-zone names instead of relying on one global thermal number.

## Next

- v157: Pstore/Ramoops Feasibility.
- v158: Watchdog Read-only Feasibility.
- v159: Tracefs/Ftrace Feasibility.

