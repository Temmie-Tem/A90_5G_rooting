# Native Init V3316 GPU M0 System Monitor Node Enum

## Summary

- Cycle: `V3316`
- Track: GPU rung ③, M0 system-monitor data layer pre-implementation node enumeration.
- Artifact: none. This was a read-only device enumeration pass on the current V3315 resident.
- Init under test: `A90 Linux init 0.11.87 (v3315-gpu-2d-d3-video-semantic-edge-tolerance)`
- Result: PASS. The real CPU, GPU, thermal, memory, load, and battery nodes needed by the M0 sampler are readable without
  writes. CPU clusters can be derived from `cpufreq/related_cpus` and max frequency, so the sampler must not hardcode CPU
  IDs.

## Safety

- No boot image was built.
- No flash was run.
- No forbidden partition, power, PMIC, GPIO, regulator, GDSC, panel-init, backlight, or cooling-device write was attempted.
- Device interaction was limited to serial control health checks and read-only `/proc` + `/sys` file reads.
- Wi-Fi connect/DHCP/ping were not run.

## Preflight

- Managed serial bridge probe: connected and running on the selected ACM device.
- `a90ctl version`: `A90 Linux init 0.11.87 (v3315-gpu-2d-d3-video-semantic-edge-tolerance)`
- `a90ctl status`: resident reachable, display path present, SD mounted, selftest `pass=12 warn=1 fail=0`.
- `a90ctl selftest verbose`: `pass=12 warn=1 fail=0`.

## CPU Nodes

Readable CPU topology and frequency paths:

- `/sys/devices/system/cpu/online=0-7`
- `/sys/devices/system/cpu/present=0-7`
- `/sys/devices/system/cpu/cpu*/topology/{physical_package_id,core_id,thread_siblings_list,core_siblings_list}`
- `/sys/devices/system/cpu/cpu*/cpufreq/{related_cpus,affected_cpus,scaling_cur_freq,scaling_min_freq,scaling_max_freq,cpuinfo_min_freq,cpuinfo_max_freq,scaling_available_frequencies}`

Derived cluster map from the device, using `related_cpus` plus `cpuinfo_max_freq`:

| Label | CPUs | related_cpus | min kHz | max kHz | Example current kHz |
| --- | --- | --- | ---: | ---: | ---: |
| Silver | `0 1 2 3` | `0 1 2 3` | `300000` | `1785600` | `1785600` |
| Gold | `4 5 6` | `4 5 6` | `710400` | `2419200` | `2419200` |
| Prime | `7` | `7` | `825600` | `2841600` | `2841600` |

Implementation note: labels are assigned by sorting discovered clusters by max frequency. The CPU IDs above are evidence
from this device, not constants to bake into the sampler.

## Proc Nodes

Readable process/kernel aggregate paths:

- `/proc/stat`: aggregate `cpu` plus `cpu0` through `cpu7` lines present.
- `/proc/loadavg`: readable.
- `/proc/uptime`: readable.
- `/proc/meminfo`: readable; sample included `MemTotal=5504940 kB`, `MemFree=5054840 kB`,
  `MemAvailable=5216660 kB`.

M0 sampler implication: keep two or more `/proc/stat` snapshots in a ring and compute per-core usage from deltas, while
storing memory and load snapshots directly.

## GPU Nodes

Readable KGSL paths:

- `/sys/class/kgsl/kgsl-3d0/gpu_model=Adreno640v2`
- `/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage=0 %`
- `/sys/class/kgsl/kgsl-3d0/gpubusy=0 0`
- `/sys/class/kgsl/kgsl-3d0/temp=43200`
- `/sys/class/kgsl/kgsl-3d0/gpuclk=257000000`
- `/sys/class/kgsl/kgsl-3d0/max_gpuclk=585000000`
- `/sys/class/kgsl/kgsl-3d0/devfreq/cur_freq=257000000`
- `/sys/class/kgsl/kgsl-3d0/devfreq/min_freq=257000000`
- `/sys/class/kgsl/kgsl-3d0/devfreq/max_freq=585000000`
- `/sys/class/kgsl/kgsl-3d0/devfreq/available_frequencies=257000000 345000000 427000000 499200000 585000000`
- `/sys/class/kgsl/kgsl-3d0/devfreq/governor=msm-adreno-tz`

All listed GPU paths were read-only. No devfreq governor, min, max, power, reset, or KGSL control write was attempted.

## Thermal Nodes

Readable thermal zones include CPU, GPU, DDR, PMIC, USB, AC, and battery sensors. The pass found `thermal_zone0` through
`thermal_zone78`; some modem1/mmwave zones report an empty `temp`, which the sampler should tolerate.

High-signal examples:

- `cpu-0-0-usr=45900`, `cpu-0-1-usr=44800`, `cpu-0-2-usr=43600`, `cpu-0-3-usr=44400`
- `cpu-1-0-usr=44400`, `cpu-1-1-usr=45500`, `cpu-1-2-usr=45500`, `cpu-1-7-usr=45100`
- `gpuss-0-usr=41700`, `gpuss-1-usr=43200`, `gpuss-max-step=43200`
- `ddr-usr=45900`, `pm8150_tz=41999`, `pm8150l_tz=43329`
- `usb-therm=36300`, `ac=38300`, `battery=36300`

Cooling devices were enumerated read-only for context only. `panel0-backlight` appeared as a cooling device, but M0/M1/M2
must never write it.

## Power Supply Nodes

Readable power-supply paths:

- `battery`: `status=Full`, `capacity=100`, `temp=363`, `voltage_now=4322000`, `current_now=5`,
  `power_now=478`, `charge_counter=4400000`, `health=Good`, `present=1`
- `usb`: `online=1`
- `ac`: `online=0`, `temp=385`
- `otg`: `online=0`
- `wireless`: `present=0`, `online=0`

Implementation note: battery temperature is tenths of a degree C in the power-supply path, while many thermal zones are
millidegrees C. The sampler should normalize units before rendering.

## M0 Implementation Requirements

- Enumerate CPU directories dynamically from `present`/`online` and existing `cpuN` sysfs directories.
- Build unique clusters from `cpufreq/related_cpus`; fall back to sibling lists or singleton cores only if `related_cpus`
  is absent.
- Label clusters by sorted max frequency: lowest = Silver, middle = Gold, highest = Prime for this 3-cluster SD855 layout.
- Keep fixed-size history rings for CPU usage, CPU frequency, GPU busy/frequency/temp, memory, load, battery, and selected
  thermals.
- Treat missing, empty, or permission-denied nodes as absent values, not fatal errors.
- Export a bounded probe command that prints structured `gpu.m0.monitor.*` telemetry before M1 starts rendering.

## Conclusion

The M0 data-source condition is closed: the system monitor can be built from real device nodes with read-only access, and
the SD855 Prime/Gold/Silver topology is discoverable from sysfs rather than hardcoded. Next step is the M0 sampler and ring
buffer implementation, followed by a source/build/live probe under a new boot artifact if native-init changes are needed.
