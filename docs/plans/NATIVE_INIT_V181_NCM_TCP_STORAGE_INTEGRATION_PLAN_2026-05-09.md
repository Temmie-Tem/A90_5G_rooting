# A90 v181 NCM/TCP + Storage Workload Integration Plan

Date: `2026-05-09`
Device build baseline: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v181` host harness, not a native-init boot image
Roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

v181 integrates NCM/TCP and SD storage workloads into the v179 mixed-soak
scheduler. The main risk is that `tcpctl_host.py` and `storage_iotest.py` are
external host tools that open their own bridge connections. When the observer is
running concurrently, those tools must not race the observer for the serial
bridge.

## Scope

- Mark NCM/TCP and storage modules as `external_bridge_client`.
- Add an `external-bridge` resource lock to mixed-soak schedules.
- Add a `DeviceClient.exclusive()` context so the scheduler can block observer
  serial commands while an external bridge-using workload runs.
- Keep `--allow-ncm` as the explicit gate for NCM/TCP and storage workloads.
- Validate ACM-only behavior as structured blocked/skipped, not failure.
- Validate full NCM/TCP + storage only after the operator configures host NCM.

## Non-Goals

- No host sudo automation beyond existing `ncm_host_setup.py`.
- No USB rebind unless explicitly requested by operator.
- No public network listener widening.
- No native-init boot image change.

## Validation Plan

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

ACM-only gate:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 30 \
  --observer-interval 5 \
  --seed 181
```

Full NCM run after operator setup:

```bash
ip -br link | grep enx
python3 scripts/revalidation/ncm_host_setup.py setup \
  --interface <known-usb-ncm-ifname> \
  --manual-host-config \
  --sudo "sudo -n"
ping -c 3 -W 2 192.168.7.2
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 3600 \
  --observer-interval 15 \
  --seed 181 \
  --allow-ncm \
  --workload-profile quick
```

`--allow-auto-interface` is a diagnostic fallback only. Prefer pinning the
current USB/NCM interface with `--interface`.

## Acceptance

- Schedule shows `external-bridge` lock for `ncm-tcp-preflight` and `storage-io`.
- Without `--allow-ncm`, NCM/TCP and storage workloads are blocked/skipped and the
  run remains PASS.
- With host NCM configured and `--allow-ncm`, NCM/TCP and storage workloads PASS.
- Observer failures remain `0`.
- Storage cleanup and final verify PASS.
- Evidence remains private (`0700` dirs, `0600` files).
