# v134 Plan: Network Exposure Guardrail

## Summary

v134 targets `A90 Linux init 0.9.34 (v134)` / `0.9.34 v134 EXPOSURE GUARDRAIL`.
The goal is not to add a new remote-access feature. The goal is to make the
current USB/NCM/root-control exposure boundary explicit, machine-checkable, and
visible from shell/diag output before any Wi-Fi or broader network work resumes.

The current security baseline is:

- imported F001-F031 findings dispositioned as 29 mitigated and 2 accepted
  trusted-lab-boundary items;
- local targeted v133 rescan result `PASS=12`, `WARN=1`, `FAIL=0`;
- remaining warning is intentional USB ACM/local serial bridge root control,
  not a new blocker.

v134 should preserve the current trusted-lab model:

- USB ACM serial shell remains the local rescue/control channel;
- host serial bridge remains localhost by default;
- NCM `tcpctl` and `rshell` remain opt-in and token-gated;
- no Wi-Fi bring-up, rfkill write, module load/unload, partition writes, or
  broader network exposure is introduced.

## Key Changes

- Copy v133 into `init_v134.c` and `v134/*.inc.c`.
- Bump metadata in `a90_config.h` to `0.9.34` / `v134` and add changelog text
  `0.9.34 v134 EXPOSURE GUARDRAIL`.
- Add a small exposure status API, preferably `a90_exposure.c/h`:
  - `a90_exposure_collect()`
  - `a90_exposure_summary()`
  - `a90_exposure_print()`
  - optional `a90_exposure_guardrail_ok()`
- Exposure snapshot should summarize these surfaces:
  - USB ACM serial shell: present, trusted-lab-only, physical/local boundary;
  - host bridge policy: expected localhost bridge and Samsung by-id identity
    pinning are host-side requirements;
  - NCM interface: present/running state, bind address, device IP;
  - `tcpctl`: running state, pid, bind address, port, token path present,
    `auth=required` expectation;
  - `rshell`: enabled/running state, bind address, port, token file mode,
    token value hidden;
  - service flags: `netservice` and `rshell` opt-in flags present/absent;
  - accepted boundary: F021/F030 remain accepted only while the channel is
    USB-local/localhost-only.
- Add shell command `exposure [status|verbose|guard]`:
  - `exposure` / `exposure status`: concise operator summary;
  - `exposure verbose`: per-surface detail and guardrail evidence;
  - `exposure guard`: return non-zero if a guardrail fails.
- Add exposure summary to existing diagnostics:
  - `status` should show a compact `exposure:` line;
  - `bootstatus` or `selftest verbose` may include a short exposure summary;
  - `diag full` should include an `[exposure]` section;
  - `local_security_rescan.py` should remain host-side and may be referenced
    from the report, not embedded into PID1.
- Do not print live token values in `status`, `diag`, or `exposure` output.
  Only print `present/missing`, mode, owner-only status, and token path.

## Guardrails

- No automatic start of `netservice`, `tcpctl`, or `rshell` beyond existing
  opt-in semantics.
- No change to accepted USB ACM local shell behavior in v134.
- No new listener, no port change, no bind-address expansion.
- No Wi-Fi enablement, rfkill write, kernel module load/unload, firmware write,
  or Android/vendor mutation.
- If exposure guard detects a bind address outside the intended USB NCM address,
  missing token requirement, non-private token mode, or unexpected running
  service, it reports `warn/fail` but must not hard-stop PID1 boot.
- Destructive commands remain blocked by current menu busy policy.

## Test Plan

- Local build:
  - build `init_v134.c` with all shared modules plus new `a90_exposure.c`;
  - check `strings` for `A90 Linux init 0.9.34 (v134)`, `A90v134`, and
    `0.9.34 v134 EXPOSURE GUARDRAIL`.
- Static checks:
  - `git diff --check`;
  - host Python `py_compile` including `local_security_rescan.py`;
  - `rg` stale marker scan for v133 markers in v134 active files;
  - `rg` check that `exposure` command is registered in v134 shell table.
- Device validation:
  - flash `stage3/boot_linux_v134.img` through native bridge/TWRP;
  - verify `version`, `status`, `bootstatus`, `selftest verbose`;
  - run `exposure`, `exposure verbose`, `exposure guard`;
  - run `diag full` and confirm `[exposure]` section exists without token
    values.
- Network/security regression:
  - default boot: `netservice` disabled, `tcpctl` stopped, `rshell` disabled;
  - `netservice start`: NCM ping works, `tcpctl` bind is `192.168.7.2`, token
    is required, `exposure guard` stays acceptable;
  - `rshell start`: rshell bind is `192.168.7.2`, token mode is private,
    invalid-token rejection still works;
  - rollback: `rshell stop`, `netservice stop`, ACM bridge recovers;
  - `local_security_rescan.py` rerun reports `FAIL=0`.
- UI/menu regression:
  - `screenmenu`, menu-visible busy gate, `hide`, post-hide `run`, and quick
    `native_soak_validate.py` continue to pass.

## Docs And Acceptance

- Add report `docs/reports/NATIVE_INIT_V134_NETWORK_EXPOSURE_GUARDRAIL_2026-05-07.md` after implementation.
- Update README/latest verified only after real-device flash and exposure guard
  validation pass.
- Update security closure/rescan docs only if the new v134 output changes the
  current disposition.
- Acceptance criteria:
  - no new network surface;
  - no token value leakage in diagnostics;
  - `exposure guard` catches policy drift;
  - v133 local security scan pattern families remain passing;
  - F021/F030 accepted-lab-boundary remains explicitly documented.

## Assumptions

- v134 is a guardrail/observability release, not a Wi-Fi or remote-access
  feature release.
- `a90_exposure` may depend on service, netservice, runtime, diag-safe helpers,
  config, log, and util, but it should not start/stop services by itself.
- The shell command only reads state; service lifecycle remains owned by
  `netservice`, `rshell`, and `service` commands.
- Codex Cloud fresh scan may arrive later; v134 should provide better evidence
  for responding to any future network-exposure finding.
