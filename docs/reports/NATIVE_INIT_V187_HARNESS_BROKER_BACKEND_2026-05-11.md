# A90 v187 Harness Broker Backend Report

Date: `2026-05-11`
Baseline device build: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v187` host harness broker backend
Device flash: none
Base commit: `1e85d1b`

## Summary

v187 connects the host harness `DeviceClient` to the v186 `A90B1` broker. The
direct `cmdv1` bridge path remains the default and the broker path is opt-in via
`native_test_supervisor.py --device-backend broker`.

The goal is to let observer/supervisor clients use a single host-local broker
instead of each tool writing to the raw serial bridge independently.

## Changes

- `a90harness.device.DeviceClient`
  - adds `backend=direct|broker`
  - keeps direct `run_cmdv1_command()` behavior unchanged
  - adds broker request path over `A90B1` Unix socket
  - records backend/socket/client id metadata for manifests
- `native_test_supervisor.py`
  - adds `--device-backend broker`
  - adds `--broker-runtime-dir`, `--broker-socket-name`, `--broker-socket`
  - records `device_client` metadata in smoke/observe/module/mixed-soak manifests
- `scripts/revalidation/README.md`
  - adds broker-backed supervisor usage example
- task docs
  - mark v187 as started and record live broker-backed smoke/observe results

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/serial_tcp_bridge.py \
  scripts/revalidation/tcpctl_host.py \
  scripts/revalidation/a90_broker.py \
  scripts/revalidation/a90harness/device.py \
  scripts/revalidation/native_test_supervisor.py
python3 scripts/revalidation/a90_broker.py selftest
git diff --check
```

Result: PASS.

Live broker-backed supervisor:

```bash
python3 scripts/revalidation/a90_broker.py serve \
  --backend acm-cmdv1 \
  --runtime-dir tmp/a90-v187-broker.7GzqCq/broker

python3 scripts/revalidation/native_test_supervisor.py \
  --device-backend broker \
  --broker-runtime-dir tmp/a90-v187-broker.7GzqCq/broker \
  smoke \
  --run-dir tmp/a90-v187-broker.7GzqCq/smoke

python3 scripts/revalidation/native_test_supervisor.py \
  --device-backend broker \
  --broker-runtime-dir tmp/a90-v187-broker.7GzqCq/broker \
  observe \
  --max-cycles 1 \
  --duration-sec 60 \
  --interval 1 \
  --run-dir tmp/a90-v187-broker.7GzqCq/observe
```

Result:

- `smoke` PASS
- `observe --max-cycles 1` PASS
- observer samples `7`
- observer failures `0`
- manifests recorded `device_client.backend=broker`

Dry-run:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  --device-backend broker \
  --broker-runtime-dir tmp/a90-broker \
  mixed-soak \
  --dry-run \
  --duration-sec 120 \
  --run-dir tmp/a90-v187-dry.yGivGM/mixed-dry
```

Result: PASS.

## Evidence

- `tmp/a90-v187-broker.7GzqCq/`
- `tmp/a90-v187-dry.yGivGM/`

## Remaining Work

- Add broker backend to additional standalone host collectors where useful.
- Produce broker audit bundle retention/reporting.
- Decide whether v188 should integrate NCM/tcpctl as a broker backend or first
  add a broker-specific concurrent smoke script.

## Conclusion

Recommendation: PASS.

The harness can now use `A90B1` broker as an opt-in device command backend while
keeping the existing direct bridge path as rescue/default.
