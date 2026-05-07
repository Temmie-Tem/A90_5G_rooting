# Native Init v156 Thermal/Power Sensor Map Plan (2026-05-08)

## Summary

- target build: `A90 Linux init 0.9.56 (v156)`
- marker: `0.9.56 v156 THERMAL POWER MAP`
- 목적은 장시간 안정성 판단에 필요한 thermal zone, cooling device, power_supply 속성을 read-only로 매핑하는 것이다.
- v156은 커널/센서 관찰 기능 추가이며, thermal governor, charger, watchdog, tracefs, partition 상태를 변경하지 않는다.

## Scope

- `a90_sensormap.c/h`를 추가한다.
- shell command `sensormap [summary|thermal|power|full|paths]`를 추가한다.
- `status`와 `bootstatus`에 compact sensor summary를 추가한다.
- host collector `scripts/revalidation/sensor_map_collect.py`를 추가한다.
- README/task queue 최신 기준을 v156으로 갱신한다.

## Read-only Rules

- 허용: `/sys/class/thermal`, `/sys/class/power_supply`의 readable attribute 수집.
- 허용: thermal zone type/temp/trip, cooling device type/cur/max, power_supply 핵심 속성 출력.
- 금지: trip point/cooling state/charger 속성 write.
- 금지: stress, reboot, mount 변경, watchdog open, tracefs enable.

## Device Command Contract

```text
sensormap
sensormap summary
sensormap thermal
sensormap power
sensormap full
sensormap paths
```

- `summary`: count와 최대 온도 후보를 한 줄로 출력한다.
- `thermal`: thermal zone과 cooling device 상세를 출력한다.
- `power`: power_supply별 주요 속성을 출력한다.
- `full`: thermal + power를 모두 출력한다.
- `paths`: 수집 기준 sysfs 경로와 count를 출력한다.

## Validation

- local static ARM64 build.
- `strings` marker 확인.
- `git diff --check`.
- host Python `py_compile`.
- real-device flash with `native_init_flash.py --verify-protocol auto`.
- `sensormap`, `sensormap thermal`, `sensormap power`, `sensormap paths`.
- `sensor_map_collect.py --expect-version "A90 Linux init 0.9.56 (v156)"`.
- `native_integrated_validate.py --expect-version "A90 Linux init 0.9.56 (v156)"`.

## Acceptance

- known-good A90에서 `sensormap` rc=0.
- thermal/power output이 장시간 안정성 판단에 쓸 수 있을 만큼 구체적이다.
- host collector output은 private file handling을 유지한다.
- 기존 v155 kernel diagnostics, shell, HUD/menu, storage, selftest 회귀가 없다.

