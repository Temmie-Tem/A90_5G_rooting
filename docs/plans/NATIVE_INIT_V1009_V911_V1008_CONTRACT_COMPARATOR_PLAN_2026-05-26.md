# V1009 V911/V1008 Contract Comparator Plan

## Goal

Classify why the V911 reduced `mdm_helper` runtime-contract path observes
`/dev/esoc-0`, while the V1008 full Android service-window path does not.

## Scope

1. Compare V911 and V1008 manifests host-only.
2. Compare the two helper transcripts for:
   - `mdm_helper` uid/gid/groups/preexec contract;
   - target and actual SELinux execution context;
   - `per_mgr` / `per_mgr_light` liveness;
   - `/dev/esoc-0` fd visibility;
   - service-window actor set and fd-poll coverage.
3. Select the next live gate without starting any new device process.

## Guardrails

V1009 is host-only.

Forbidden:

- serial device command;
- Android boot or ADB command;
- daemon, service-manager, HAL, or `mdm_helper` start;
- `/dev/esoc-0`, `/dev/subsys_esoc0`, eSoC ioctl, GPIO, sysfs, or debugfs access;
- Wi-Fi scan/connect/link-up;
- credential use;
- DHCP/routes;
- external ping;
- boot image, partition, firmware, or filesystem mutation.

## Success Criteria

V1009 passes if it records a classified route based on current evidence:

- V911 fd-positive reduced route vs V1008 fd-negative full service-window route;
- shared property and device surfaces;
- exact `mdm_helper` identity/context deltas;
- `per_mgr` lifecycle delta;
- no forbidden actions.

A pass is not the final Wi-Fi objective. It only selects the next lower gate
toward native Wi-Fi connect and external ping.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v911_v1008_contract_comparator_v1009.py
python3 scripts/revalidation/native_wifi_v911_v1008_contract_comparator_v1009.py
```
