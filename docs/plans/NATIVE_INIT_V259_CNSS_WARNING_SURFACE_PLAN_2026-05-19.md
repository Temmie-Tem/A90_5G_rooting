# Native Init V259 CNSS Warning Surface Plan

## Summary

- V259 classifies the non-fatal warnings discovered by V258 without starting `cnss-daemon` again.
- Scope is read-only: perfd availability, Android property service surface, `/dev/kmsg` permissions, and init/service references.
- Wi-Fi scan/connect/link-up/credential/DHCP/routing remain blocked.

## Input Context

V258 classified V257 live evidence as `cnss-start-only-evidence-classified` and found three warnings:

- `perfd-client-unavailable`
- `kmsg-write-denied`
- `shell-quote-noise`

These warnings did not block start-only lifecycle, but they need classification before broader live operations.

## Implementation

- Add `scripts/revalidation/wifi_cnss_warning_surface_probe.py`.
- Use `EvidenceStore` and `a90_kernel_tools.run_capture()`.
- Read prerequisite V258 manifest.
- Collect read-only device evidence:
  - `pidof cnss-daemon`
  - `stat /dev/kmsg`
  - `stat /dev/socket/property_service`
  - `stat /dev/__properties__`
  - `stat /dev/socket/perfd`
  - `stat /mnt/system/vendor/bin/perfd`
  - `grep -R -n -i perfd|dev/kmsg|cnss-daemon` across mounted init/vendor config roots
  - `find /mnt/system -name '*perfd*'` with a bounded maxdepth
- Classify:
  - perfd binary/config present or absent
  - perfd runtime socket present or absent
  - property service socket/area present or absent
  - `/dev/kmsg` current mode/owner and whether write denial is expected for uid 1000
  - shell quote noise as daemon/logging-command artifact unless helper source contains matching kmsg shell construction

## Validation

- Static:
  - `python3 -m py_compile scripts/revalidation/wifi_cnss_warning_surface_probe.py`
  - `git diff --check`
- Device read-only:
  - run probe against current v159 native state
  - confirm `pidof cnss-daemon` rc=1
  - confirm no daemon start, no scan/connect/link-up commands, no rfkill or ICNSS writes

## Acceptance

- Output decision should distinguish warning-only gaps from blockers.
- If perfd/property/kmsg warnings are expected Android-service gaps, next work can move to QRTR/QMI interaction or a dedicated property/perfd shim plan.
- If evidence shows a helper instrumentation bug, fix instrumentation before broader live operations.
