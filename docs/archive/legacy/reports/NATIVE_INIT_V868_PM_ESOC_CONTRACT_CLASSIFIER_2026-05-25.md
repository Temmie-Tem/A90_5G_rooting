# V868 PM/eSoC Contract Classifier Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| classifier | `tmp/wifi/v868-pm-esoc-contract-classifier/manifest.json` | `v868-esoc-req-eng-precondition-selected` |
| summary | `tmp/wifi/v868-pm-esoc-contract-classifier/summary.md` | host-only PASS |

V868 did not contact the device and did not start any live actor. It classified
V867's residual `pm_proxy_helper` D-state against the local A90 Samsung OSRC
eSoC contract.

## Key Findings

| Item | Finding |
| --- | --- |
| V867 blocker | `pm_proxy_helper` remained `Ds` and could not be killed during the bounded cleanup window |
| local UAPI | `ESOC_REG_REQ_ENG=7`, `ESOC_REG_CMD_ENG=8`, `ESOC_CMD_EXE=1`, `ESOC_PWR_ON=1` |
| Samsung SSR source | `subsystem_restart.c` contains the `pm_proxy_helper` eSoC shutdown dependency exception |
| research doc | A90-local ioctl note is present and stale public ioctl offsets are absent |

## Interpretation

`pm_proxy_helper` should not be retried alone. The current best explanation is
that Android first establishes the `/dev/esoc-0` control side with CMD/REQ
engine registration, then lets `pm_proxy_helper` hold `/dev/subsys_esoc0`. V867
started only the latter side, so the helper entered the same D-state class as
the earlier raw `/dev/subsys_esoc0` experiments.

The next implementation target is not Wi-Fi HAL or scan/connect. It is the
native eSoC control preflight around `/dev/esoc-0`, using the local A90 OSRC
UAPI values rather than generic public mdm-helper examples.

## Guardrails

- No bridge/device contact.
- No daemon start, no `mdm_helper`, no `ks`, no Wi-Fi HAL.
- No scan/connect, credentials, DHCP/routes, or external ping.
- No GPIO/sysfs/debugfs/subsystem state write, module load/unload, boot image
  write, or partition write.

## Next

V869 should be source/build-only helper work for an A90 eSoC control preflight.
It should add observability and static guardrails first; live `ESOC_PWR_ON`,
`mdm_helper`, `ks`, `pm_proxy_helper`, CNSS, HAL, scan/connect, credentials,
DHCP/routes, and external ping stay blocked until later gates.
