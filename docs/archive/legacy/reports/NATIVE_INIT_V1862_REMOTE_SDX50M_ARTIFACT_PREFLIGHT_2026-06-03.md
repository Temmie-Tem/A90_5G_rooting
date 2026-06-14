# Native Init V1862 Remote SDX50M Artifact Preflight

## Summary

- Cycle: `V1862`
- Type: live read-only remote artifact preflight for the SDX50M bridge path
- Decision: `v1862-remote-sdx50m-artifact-ready-host-pass`
- Label: `remote-sdx50m-artifact-ready`
- Result: PASS
- Reason: Remote private SDX50M cnss-daemon artifact exists and its SHA matches the local V1857 artifact; the next bridge unit can focus on v356 private-mount integration
- Evidence: `tmp/wifi/v1862-remote-sdx50m-artifact-preflight`

## Input

- V1861: `v1861-direct-prereq-pre-wifi-gap-confirmed-host-pass` / `direct-prereq-pre-wifi-gap-confirmed` / pass `True`
- V1857 local artifact: `v1857-artifact-plumbing-dry-run-ready-host-pass` / `artifact-plumbing-dry-run-ready` / pass `True`

## Artifact State

- local artifact: `tmp/wifi/v1220-cnss-daemon-sdx50m-patch/artifacts/cnss-daemon.sdx50m` exists `True` size `95112` sha `784fd7bd9b602d8e1f94c9ceef977845909f452611025c40fda589d0e57de5fd`
- expected local size/SHA: `95112` / `784fd7bd9b602d8e1f94c9ceef977845909f452611025c40fda589d0e57de5fd`
- remote artifact: `/cache/bin/cnss-daemon.sdx50m` stat_ok `True` sha_ok `True` missing `False` sha `784fd7bd9b602d8e1f94c9ceef977845909f452611025c40fda589d0e57de5fd`
- remote SHA matches local: `True`
- remote toybox ok: `True`
- hide retry count: `0`
- git clean: `True`

## Commands

| name | command | host rc | protocol | terminal |
| --- | --- | ---: | --- | --- |
| toybox-stat | `stat /cache/bin/toybox` | `0` | `ok/0` | `True` |
| remote-artifact-stat | `stat /cache/bin/cnss-daemon.sdx50m` | `0` | `ok/0` | `True` |
| remote-artifact-sha256 | `run /cache/bin/toybox sha256sum /cache/bin/cnss-daemon.sdx50m` | `0` | `ok/0` | `True` |

## Safety Scope

This preflight used only read-only bridge observations: `stat` and `toybox sha256sum` on the remote target. It did not write or execute the remote artifact, start a serial bridge, flash, reboot, stage properties, start actors, open `/dev/subsys_esoc0`, start `boot_wlan`, issue restart-PD request, force RC1, fake ONLINE state, write PMIC/GPIO/GDSC controls, perform eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, or external ping.

## Next

- Do not proceed to Wi-Fi HAL/scan/connect unless WLFW service 69 and `wlan0` are present.
- If remote artifact is missing or mismatched, run a separate deploy-only cache-write gate before any private-mount bridge live unit.
- If remote artifact is ready, the next useful unit is v356 private-mount bridge integration under the existing rollback and lower-publication guardrails.
