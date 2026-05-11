# F045-F046 Fresh Local Security Rescan

Date: 2026-05-11
Baseline: active v159 native-init plus post-v184 host harness security patches
Git HEAD: `8edda96`
Scope: active native-init source, shared modules, current revalidation host tools, F001-F046 local guardrails, and known root-control surfaces.

This is a local targeted rescan, not a Codex Cloud scanner replacement. It checks the imported F001-F046 pattern families, exposure guardrails, and controller policy matrix wiring against the current repository state.

## Summary

- PASS: 29
- WARN: 1
- FAIL: 0
- New implementation blocker from this local scan: `0`

## Results

| id | status | check | evidence | note |
|---|---|---|---|---|
| S001 | PASS | tcpctl and rshell bind to the USB NCM device address, not INADDR_ANY | `stage3/linux_init/a90_config.h` binds both services to `NETSERVICE_DEVICE_IP`; active network files have no `INADDR_ANY`/`0.0.0.0` match. | Reduces F001/F003/F005/F030-style broad network exposure. |
| S002 | PASS | tcpctl requires token auth when launched by netservice | `a90_tcpctl.c` gates `run` behind `auth`; `a90_netservice.c` passes `NETSERVICE_TCP_TOKEN_PATH` and logs `auth=required`. | Covers previous unauthenticated tcpctl findings. |
| S003 | PASS | netservice and rshell token files are private no-follow writes | Token writers use `O_NOFOLLOW` and `0600`; diagnostics hide token value. | Token display commands remain operator-only dangerous controls over the trusted local shell. |
| S004 | PASS | dangerous service commands remain blocked by menu busy gate | `service` is registered `CMD_DANGEROUS`; controller only allows read-only `service list/status` while menu is active. | Covers F010/F023-style dangerous-command bypasses. |
| S005 | PASS | runtime helper preference requires a valid manifest SHA-256 match | `a90_helper.c` only prefers runtime helpers when SHA-256 is present, checked, and matched; otherwise fallback is selected. | Covers helper manifest arbitrary-exec findings. |
| S006 | PASS | logs, runtime probes, storage probes, and diagnostics use no-follow private writes | `a90_log.c`, `a90_runtime.c`, `a90_storage.c`, and `a90_diag.c` retain `O_NOFOLLOW`, `0600`, and private-dir guardrails. | Covers SD symlink/log/diagnostic disclosure findings. |
| S007 | PASS | host boot-image archive extraction validates entries before extractall | `mkbootimg/gki/certify_bootimg.py` uses tar/zip validators and `safe_unpack_archive`; `shutil.unpack_archive` is absent. | Covers unsafe archive extraction finding. |
| S008 | PASS | host subprocess helpers pin repo-relative paths and cwd where needed | `native_soak_validate.py` resolves `a90ctl.py` from `__file__` and runs with `cwd=REPO_ROOT`; diagnostics collector does the same. | Covers untrusted-CWD helper execution findings. |
| S009 | PASS | serial bridge defaults to localhost and pins Samsung by-id serial identity | `serial_tcp_bridge.py` defaults to `127.0.0.1`, uses Samsung by-id auto discovery, refuses ambiguous matches by default, and tracks realpath identity. | F021/F030 remain accepted trusted-lab local control boundaries. |
| S010 | PASS | diagnostic bundles are private and redact log tails by default | Host diag output chmods `0700/0600`; device diag defaults redact log tails and token value. | Covers diagnostic disclosure findings. |
| S011 | PASS | active host scripts do not set known root SSH credentials | No active `scripts/revalidation` or `mkbootimg/gki/certify_bootimg.py` match for default root SSH credential patterns. | Legacy archived docs/scripts are excluded from active v153 runtime/tooling scope. |
| S012 | PASS | tcpctl host installer writes temp path, verifies hash, then moves into place | `tcpctl_host.py install` uses a per-run temp target, verifies SHA-256 before `mv`, and cleans the temp path on exceptions. | Covers tcpctl install race/poisoning follow-up guardrails. |
| S013 | PASS | volume hold repeat timer clears when a screen cannot consume repeats | Retained v131-v153 auto-HUD loops clear `menu_hold_code` and `menu_hold_next_ms` when a timed repeat is not consumed. | Covers F032 zero-timeout poll/redraw spin in non-repeat screens. |
| S014 | PASS | menu-visible mountsd requires explicit status subcommand | `a90_controller.c` allows `mountsd status` during menu-active operation, but no longer allows bare `mountsd`. | Covers F033 mountsd side effects through absent-subcommand menu policy. |
| S015 | PASS | exposure guardrail command and diagnostics are wired | `exposure [status|verbose|guard]`, `status`/`bootstatus` summaries, and `diag` exposure output are present without token values. | Provides machine-checkable evidence before broader network or Wi-Fi work. |
| S016 | PASS | controller policy matrix covers menu-visible side-effect boundaries | `policycheck` is registered and the matrix names representative storage/network/service/process/power side-effect cases. | Covers absent-subcommand and command-policy drift before new network work. |
| S017 | PASS | integrated validation harness covers core safety gates | `native_integrated_validate.py` covers selftest, pid1guard, exposure, policycheck, service/network status, and UI nonblocking checks. | Provides one host gate before Wi-Fi/network-facing changes or large controller refactors. |
| S018 | PASS | longsoak host export is bounded and does not cat device-provided paths | `native_long_soak.py` collects recorder data through `longsoak export` with line/byte caps and no longer issues generic `cat <device_path>`. | Covers F034 unvalidated device path and unbounded host cat. |
| S019 | PASS | longsoak helper opens root logs with no-follow private regular-file handling | `helpers/a90_longsoak.c` uses `open(...O_NOFOLLOW, 0600)`, verifies a regular file with `fstat`, and applies `fchmod` on the fd. | Covers F035 helper symlink-following root log writes. |
| S020 | PASS | longsoak status/tail/export reject display sentinels and unsafe paths | `a90_longsoak.c` validates owned JSONL paths, rejects `-`, and routes status scan, tail, and export through the no-follow safe opener. | Covers F036 and the device-owned half of F034. |
| S021 | PASS | longsoak bundle uses private no-follow output handling | `native_long_soak_bundle.py` forces `0700/0600`, rejects symlink destinations, and avoids `copy2`/`Path.write_text` for bundle outputs. | Covers F037 private evidence and symlink-clobber handling. |
| S023 | PASS | storage and filesystem exercisers enforce confined device paths | `path_safety.py` centralizes safe components/path-boundary/raw-arg checks; storage/fs tests no longer rely on weak string-prefix guards. | Covers F038 and F041 path escape / raw serial command injection findings. |
| S024 | PASS | CPU/memory stability validator does not opt into unsafe replay | `cpu_mem_thermal_stability.py` no longer marks `dd`, `rm`, `longsoak start`, `ps`, or cpustress `run` commands as retry-unsafe replayable. | Covers F040 replay of privileged non-idempotent commands. |
| S025 | PASS | unlimited observer uses counters instead of retaining all samples | `a90harness/observer.py` streams JSONL and keeps counters plus a bounded recent-failure ring. | Covers F043 host memory growth during unlimited observer runs. |
| S026 | PASS | NCM/TCP stability report requires authenticated tcpctl evidence | `ncm_tcp_stability_report.py` now requires `auth=required`, authenticated request flow, and absence of `auth=none`. | Covers F042 false PASS for unauthenticated tcpctl transcripts. |
| S027 | PASS | NCM/TCP preflight matches tcpctl smoke output and checks auth | `ncm_tcp_preflight.py` no longer waits for a stale marker and verifies the authenticated smoke transcript. | Covers F044 false failure of the NCM/TCP preflight wrapper. |
| S028 | PASS | NCM resume docs prefer explicit host interface pinning | The v166 deferred throughput resume path recommends `--interface`; auto-interface is documented as diagnostic fallback only. | Covers F039 unsafe operational bypass of host NIC pinning. |
| S029 | PASS | CPU/memory profiles use private unpredictable device temp directories | `cpu_memory_profiles.py` now creates a random root-owned `/tmp/a90-cpumem.*` directory before `dd` writes and cleans that directory. | Covers F045 predictable shared `/tmp` root `dd` target overwrite. |
| S030 | PASS | NCM preflight refuses untrusted cache tcpctl fallback | `ncm_tcp_preflight.py` only selects the ramdisk `/bin/a90_tcpctl`; it no longer executes `/cache/bin/a90_tcpctl` after a plain stat. | Covers F046 untrusted persistent tcpctl helper fallback. |
| S022 | WARN | accepted local root-control channels remain intentionally present | USB ACM root shell and localhost serial bridge are still present by design. | Matches F021/F030 accepted-lab-boundary; do not expose bridge or ACM control over LAN/Wi-Fi without new auth. |

## Interpretation

The local targeted scan found no new implementation blocker in the active code path. The remaining warning is the already accepted trusted-lab boundary for physical USB ACM/local serial bridge control.

Before any Wi-Fi or broader network exposure, rerun this local scan and a Codex Cloud security scan, then revisit F021/F030 if the control channel is no longer USB-local/localhost-only.

## Reproduction

```bash
python3 scripts/revalidation/local_security_rescan.py --out docs/security/SECURITY_FRESH_SCAN_V196_2026-05-11.md
git diff --check
```
