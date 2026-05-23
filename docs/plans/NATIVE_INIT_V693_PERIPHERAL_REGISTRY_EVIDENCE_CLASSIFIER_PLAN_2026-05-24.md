# Native Init V693 Peripheral Registry Evidence Classifier Plan

## Objective

V693 classifies the V692 registry snapshot evidence without running new device
commands. V692 captured five provider-adjacent registry phases, but Binder
debugfs was unavailable and the provider pair still exited. The goal is to
decide whether V692 proves provider registration or only proves an
observability gap.

## Scope

- Parse the top-level V692 manifest and arm manifest.
- Parse `companion-start-only-with-holder.txt` with null-safe decoding.
- Extract:
  - `pm-service`, `pm-proxy`, `cnss-daemon` retry, and `vndservicemanager`
    child status;
  - fd counts and Binder/vndbinder fd presence;
  - SELinux exec context decisions;
  - registry snapshot completeness;
  - `/dev/socket` entries per phase;
  - Binder debugfs availability;
  - WLFW/BDF/`wlan0` marker counts.
- Classify whether the next gate should query vndservicemanager directly
  before any Wi-Fi HAL, scan/connect, DHCP, or external ping attempt.

## Guardrails

- no device command;
- no helper deploy;
- no daemon or service start;
- no Wi-Fi HAL, `wificond`, supplicant, or hostapd start;
- no scan/connect/link-up;
- no credential, DHCP, route change, or external ping;
- no sysfs subsystem state write;
- no `esoc0` open or hold;
- no boot image or partition write.

## Success Criteria

- V692 evidence is present and has decision
  `v692-provider-registration-snapshot-captured`;
- registry snapshot phases are complete;
- classifier records whether Binder debugfs provided usable registry content;
- classifier records provider fd/exit behavior;
- output selects a concrete next gate without running live actions.

## Validation Commands

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_peripheral_registry_evidence_classifier_v693.py

python3 scripts/revalidation/native_wifi_peripheral_registry_evidence_classifier_v693.py \
  --out-dir tmp/wifi/v693-peripheral-registry-evidence-classifier-plan \
  plan

python3 scripts/revalidation/native_wifi_peripheral_registry_evidence_classifier_v693.py \
  --out-dir tmp/wifi/v693-peripheral-registry-evidence-classifier \
  run

git diff --check
```

## Next Gate

If V693 reports a provider registration observability gap, V694 should add a
bounded service-query proof against the private `vndservicemanager` namespace.
That query must remain below Wi-Fi HAL start and must not scan/connect, run
DHCP, use credentials, change routes, or ping externally.
