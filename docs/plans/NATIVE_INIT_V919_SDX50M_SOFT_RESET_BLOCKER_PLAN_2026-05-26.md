# Native Init V919 SDX50M Soft Reset Blocker Plan

## Context

V918 proved that the native path can now reach the real SDX50M power-up path:

```text
/dev/subsys_esoc0 open
  -> subsys_device_open
    -> __subsystem_get
      -> mdm_subsys_powerup
        -> mdm_cmd_exe
          -> mdm4x_do_first_power_on
            -> sdx50m_toggle_soft_reset
```

The trigger child entered uninterruptible sleep at `sdx50m_toggle_soft_reset`, `mdm3` remained `OFFLINING`, and no MHI/KS/WLFW/BDF/wlan0 progression appeared. Cleanup reboot restored native health.

## Goal

Classify the missing precondition that makes Android pass `sdx50m_toggle_soft_reset` while native init blocks there.

## Scope

V919 is host-only/read-only unless a later plan explicitly promotes a bounded live check. It should use existing V913/V914 Android evidence, V918 live evidence, OSRC/DTS, and local source/artifact analysis.

## Hard Guardrails

- Do not open `/dev/subsys_esoc0` again in V919.
- Do not run `mdm_helper`, `pm-service`, `pm_proxy_helper`, service-manager, CNSS daemon, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.
- Do not write boot image, partitions, firmware, GPIO, sysfs, debugfs, rfkill, module bind/unbind, or kernel parameters.
- Do not repeat live trigger until the missing reset/status precondition is classified.

## Inputs

- `tmp/wifi/v918-mdm-helper-subsys-trigger-capture-live/manifest.json`.
- `tmp/wifi/v918-mdm-helper-subsys-trigger-capture-live/native/mdm-helper-subsys-trigger.txt`.
- `tmp/wifi/v913-android-esoc-gpio-timeline-handoff-live/` and V914 reclassifier evidence.
- OSRC DTS/source files for SDX50M/eSoC nodes and PMIC/GPIO reset/status wiring.
- `docs/overview/MDM3_ESOC_SDX50M_BRINGUP_RESEARCH_2026-05-25.md`.
- `docs/overview/ESOC_PERIPHERAL_MANAGER_BRINGUP_RESEARCH_2026-05-25.md`.

## Questions

1. Which GPIO/PMIC/status line does `sdx50m_toggle_soft_reset` wait on or manipulate?
2. Does Android assert AP2MDM/status or PMIC GPIO9 before `subsys_esoc0` open?
3. Does Android use `pm-service`, `mdm_helper`, vendor properties, or peripheral-manager state changes before the soft-reset path?
4. Is the native failure caused by missing property state, missing controller actor, missing power rail/GPIO state, or missing timing after Android-style provider startup?
5. What is the next bounded live action that does not fake `ESOC_NOTIFY` or `BOOT_DONE`?

## Method

1. Extract V918 blocker facts into a compact host-only manifest: wchan, syscall, stack, mdm3 state, MHI/KS/WLFW/BDF/wlan0 counters, cleanup health.
2. Extract Android positive timeline around SDX50M/eSoC/GPIO/peripheral-manager markers from existing V913/V914 evidence.
3. Search OSRC/DTS for `qcom,ext-sdx50m`, AP2MDM/MDM2AP GPIOs, PMIC GPIO soft reset, `ssctl-instance-id`, and `sysmon-id`.
4. Compare Android-vs-native ordering and identify the first missing precondition before `sdx50m_toggle_soft_reset` returns.
5. Produce a decision table with safe next gate candidates.

## Success Criteria

- A V919 report states whether the likely blocker is GPIO/PMIC state, peripheral-manager property sequencing, missing controller actor, timing, or an unobservable proprietary driver condition.
- The report names one next live gate or explicitly rejects live retry until more Android evidence is captured.
- No device mutation or live actor start occurs in V919.

## Failure Criteria

- Existing evidence lacks Android markers around the relevant reset/status window.
- OSRC lacks the proprietary eSoC driver logic needed to infer the missing precondition.
- The only remaining candidates require direct GPIO writes, fake notify/BOOT_DONE, or repeated D-state trigger opens without new evidence.

## Next

If V919 can identify an Android-only precondition, V920 should implement the smallest bounded proof for that precondition. If not, V920 should be an Android recapture focused specifically on SDX50M reset/status/GPIO/peripheral-manager ordering.
