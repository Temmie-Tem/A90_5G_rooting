# Native Init v263 CNSS Warning Disposition Plan

## Summary

- target: v263 CNSS warning disposition model
- baseline evidence: v261/v262 clean start-only and QRTR/QMI no-scan outputs
- boot image change: none
- daemon start: not executed
- new host tool: `scripts/revalidation/wifi_cnss_warning_disposition.py`
- expected output: `tmp/wifi/v263-cnss-warning-disposition/`

V257/V261 start-only evidence consistently reports three warnings:

- `perfd-client-unavailable`
- `kmsg-write-denied`
- `shell-quote-noise`

V259 showed these are Android runtime/logging surface gaps and not helper cleanup
bugs. v263 turns that into an explicit disposition artifact: which warnings are
accepted for start-only, which remain blockers for broader Wi-Fi, and which
changes would require a new opt-in shim rather than silent behavior changes.

## References

- Android `logwrapper -k` uses kernel logging as an explicit logging target:
  <https://android.googlesource.com/platform/system/core/+/pie-dev/logwrapper/logwrapper.c>
- Android libcutils `klog.cpp` writes through `/dev/kmsg` when kernel logging is
  selected:
  <https://chromium.googlesource.com/aosp/platform/system/core/libcutils/+/refs/heads/stabilize-15964.9.B/klog.cpp>
- Android init documentation notes `stdio_to_kmsg` and warns that launching init
  services manually is hard because init sets environment, groups, labels, and
  capabilities:
  <https://chromium.googlesource.com/aosp/platform/system/core/+/refs/heads/master/init/>

## Scope

- Consume a prior live evidence analyzer manifest.
- Run the existing read-only `wifi_cnss_warning_surface_probe.py` classification
  with that manifest as prerequisite input.
- Produce warning dispositions:
  - accepted start-only warning
  - broader-Wi-Fi blocker
  - opt-in shim candidate
  - duplicate/noise coalesced with another warning
- Keep all Wi-Fi control actions out of scope.

## Guardrails

v263 must not:

- run `cnss-daemon`, `cnss_diag`, HAL, supplicant, wificond, hostapd, or DHCP
- mutate `/dev/kmsg`, property service, `/dev/socket/perfd`, or `/data/vendor/wifi`
- send QRTR/QMI requests
- scan/connect/link-up Wi-Fi
- bind/unbind ICNSS, unblock rfkill, write Android partitions, or reboot

## Implementation

Add `scripts/revalidation/wifi_cnss_warning_disposition.py`:

- Inputs:
  - `--analysis-manifest` from a prior `wifi_cnss_live_evidence_analyzer.py` run
  - optional `--surface-out-dir`
- Calls existing read-only `wifi_cnss_warning_surface_probe.classify()`.
- Writes:
  - `manifest.json`
  - `summary.md`
  - embedded surface manifest under `surface/`
- Decision labels:
  - `cnss-warning-disposition-ready`
  - `cnss-warning-disposition-incomplete`
  - `cnss-warning-disposition-blocked`

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_cnss_warning_disposition.py \
  scripts/revalidation/wifi_cnss_warning_surface_probe.py \
  scripts/revalidation/wifi_cnss_live_evidence_analyzer.py
git diff --check
```

Live read-only disposition:

```bash
python3 scripts/revalidation/wifi_cnss_warning_disposition.py \
  --analysis-manifest tmp/wifi/v261-cnss-live-evidence-analysis-final-20260519-085902/manifest.json \
  --out-dir tmp/wifi/v263-cnss-warning-disposition
```

Post-check:

```bash
python3 scripts/revalidation/wifi_cnss_zombie_audit.py \
  --out-dir tmp/wifi/v263-cnss-zombie-audit-post-warning-disposition
```

## Acceptance

- Decision is `cnss-warning-disposition-ready`.
- Critical checks from the input live analyzer and surface probe pass.
- `perfd-client-unavailable` is recorded as accepted for start-only but still a
  broader-Wi-Fi runtime service gap.
- `kmsg-write-denied` and `shell-quote-noise` are coalesced as logging-path
  noise, not helper cleanup failure.
- No daemon is started and CNSS process audit remains clean.

## Assumptions

- v263 is host tooling/evidence only; no native init version bump or boot image
  flash is needed.
- Any future `/dev/kmsg` or perfd shim must be opt-in and separately approved,
  because it changes the private Android namespace semantics.
