# F026. Metrics refactor breaks older init source builds

## Metadata

| field | value |
|---|---|
| finding_id | `fa50097a3e1c81918944778437e4ef5c` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/fa50097a3e1c81918944778437e4ef5c |
| severity | `informational` |
| status | `new` |
| detected_at | `2026-05-02T19:56:11.593304Z` |
| committed_at | `2026-05-02 01:57:46 +0900` |
| commit_hash | `556c33d1545d4683b813da1eb3875c1bf32cab42` |
| relevant_paths | `stage3/linux_init/a90_hud.h | stage3/linux_init/a90_metrics.h | stage3/linux_init/v89/60_shell_basic_commands.inc.c | stage3/linux_init/v89/40_menu_apps.inc.c` |
| has_patch | `false` |

## CSV Description

This commit moves status metric types and helpers from a90_hud.* to a90_metrics.* and updates v90 callsites. However, older versioned sources still present in the repository, such as v89, include the shared a90_hud.h and still refer to struct a90_hud_status_snapshot, a90_hud_read_status_snapshot(), and a90_hud_read_sysfs_long(). Because the shared HUD header no longer defines or declares those compatibility symbols, rebuilding init_v89.c now fails with unknown storage size and implicit declaration errors. This is not an exploitable security vulnerability in the v90 runtime, but it is a reproducibility/rollback availability regression for retained historical sources. A safe fix would be to keep backward-compatible typedefs/wrappers in a90_hud.h/c, vendor version-specific headers with older source trees, or update the preserved v88/v89 source snapshots to use a90_metrics.*.

## Codex Cloud Detail

Metrics refactor breaks older init source builds
Link: https://chatgpt.com/codex/cloud/security/findings/fa50097a3e1c81918944778437e4ef5c?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=&page=2
Criticality: informational (attack path: ignore)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 556c33d
Author: shs02140@gmail.com
Created: 2026. 5. 3. 오전 4:56:11
Assignee: Unassigned
Signals: Validated, Attack-path

# Summary
Introduced a non-security build regression affecting older retained init source versions. v90 itself uses the new metrics API, but v89 and older sources still reference the removed HUD metrics API.
This commit moves status metric types and helpers from a90_hud.* to a90_metrics.* and updates v90 callsites. However, older versioned sources still present in the repository, such as v89, include the shared a90_hud.h and still refer to struct a90_hud_status_snapshot, a90_hud_read_status_snapshot(), and a90_hud_read_sysfs_long(). Because the shared HUD header no longer defines or declares those compatibility symbols, rebuilding init_v89.c now fails with unknown storage size and implicit declaration errors. This is not an exploitable security vulnerability in the v90 runtime, but it is a reproducibility/rollback availability regression for retained historical sources. A safe fix would be to keep backward-compatible typedefs/wrappers in a90_hud.h/c, vendor version-specific headers with older source trees, or update the preserved v88/v89 source snapshots to use a90_metrics.*.

# Validation
## Rubric
- [x] Confirm the checked-out commit and inspect the metrics-extraction changes to a90_hud.h/c and a90_metrics.h/c.
- [x] Verify older retained source snapshots still include the shared HUD header and reference removed HUD metric symbols.
- [x] Attempt a direct debug-style compile of the affected real target, init_v89.c, and capture compiler diagnostics.
- [x] Run a positive control by compiling/linking v90 with the new metrics API to show the environment and replacement API are usable.
- [x] Attempt runtime-oriented validation methods as far as applicable: direct run/crash is impossible because compilation fails first; valgrind is unavailable; LLDB was used non-interactively to run GCC and confirm the same failure path.
## Report
Validated the finding as a compile-time build/reproducibility regression, not a runtime security crash. Current commit is 556c33d1545d4683b813da1eb3875c1bf32cab42. Evidence: git diff for stage3/linux_init/a90_hud.h shows removal of struct a90_hud_status_snapshot, a90_hud_read_sysfs_long(), and a90_hud_read_status_snapshot(), while adding only #include "a90_metrics.h". Current stage3/linux_init/a90_hud.h:8-24 exposes HUD rendering APIs and no old HUD metric compatibility symbols; stage3/linux_init/a90_metrics.h:6-24 defines replacement struct a90_metrics_snapshot and a90_metrics_* helpers. v89 still includes ../a90_hud.h via stage3/linux_init/v89/00_prelude.inc.c:30-42 and still uses removed symbols at stage3/linux_init/v89/40_menu_apps.inc.c:148,152,3350,3383 and stage3/linux_init/v89/60_shell_basic_commands.inc.c:123,127. Direct rebuild check: `gcc -std=gnu11 -D_GNU_SOURCE -Wall -O0 -g -Istage3/linux_init -c stage3/linux_init/init_v89.c -o /tmp/init_v89.o` fails with `implicit declaration of function 'a90_hud_read_sysfs_long'`, `storage size of 'snapshot' isn't known`, and `implicit declaration of function 'a90_hud_read_status_snapshot'`. Positive control: the same compile command for stage3/linux_init/init_v90.c succeeds and creates /tmp/init_v90.o; selected-dependency host link for v90 also succeeds. v88 was also checked and fails similarly, supporting the 'v89 and older retained sources' portion. A minimal PoC using only a90_hud.h and the old API fails with the same unknown struct and implicit declaration errors. Runtime crash testing is inapplicable because the defect prevents producing an executable for the legacy source. Valgrind was attempted but is not installed. LLDB was used non-interactively to launch GCC against the PoC and confirmed GCC exits with status 1 on the same compile errors.

# Evidence
stage3/linux_init/a90_hud.h (L8 to 17)
  Note: The shared HUD header now includes a90_metrics.h and exposes only HUD rendering/storage APIs; the old a90_hud_status_snapshot type and a90_hud_read_* metric helper declarations used by older versioned sources are gone.
```
#include "a90_kms.h"
#include "a90_metrics.h"

struct a90_hud_storage_status {
    const char *backend;
    const char *root;
    const char *warning;
};

void a90_hud_boot_splash_set_line(size_t index, const char *fmt, ...);
```

stage3/linux_init/a90_metrics.h (L6 to 24)
  Note: The replacement metric snapshot type and helper functions are defined under new a90_metrics_* names, but only v90 callsites were updated.
```
struct a90_metrics_snapshot {
    char battery_status[64];
    char battery_pct[32];
    char battery_temp[32];
    char battery_voltage[32];
    char cpu_temp[32];
    char cpu_usage[16];
    char gpu_temp[32];
    char gpu_usage[16];
    char memory[64];
    char loadavg[32];
    char uptime[32];
    char power_now[32];
    char power_avg[32];
};

int a90_metrics_read_sysfs_long(const char *path, long *value_out);
void a90_metrics_read_snapshot(struct a90_metrics_snapshot *snapshot);
void a90_metrics_read_cpu_freq_label(unsigned int cpu, char *out, size_t out_size);
```

stage3/linux_init/v89/40_menu_apps.inc.c (L140 to 152)
  Note: v89 CPU frequency helper still calls the removed a90_hud_read_sysfs_long() symbol.
```
    long khz;

    snprintf(out, out_size, "?");
    if (snprintf(path, sizeof(path),
                 "/sys/devices/system/cpu/cpu%u/cpufreq/scaling_cur_freq",
                 cpu) >= (int)sizeof(path)) {
        return;
    }
    if (a90_hud_read_sysfs_long(path, &khz) < 0) {
        if (snprintf(path, sizeof(path),
                     "/sys/devices/system/cpu/cpu%u/cpufreq/cpuinfo_cur_freq",
                     cpu) >= (int)sizeof(path) ||
            a90_hud_read_sysfs_long(path, &khz) < 0) {
```

stage3/linux_init/v89/40_menu_apps.inc.c (L3345 to 3383)
  Note: The v89 CPU stress screen still uses the removed HUD status snapshot type and reader, causing compilation failure after the shared API removal.
```
static int draw_screen_cpu_stress_app(bool running,
                                      bool done,
                                      bool failed,
                                      long remaining_ms,
                                      long duration_ms) {
    struct a90_hud_status_snapshot snapshot;
    char online[64];
    char present[64];
    char freq0[32];
    char freq1[32];
    char freq2[32];
    char freq3[32];
    char freq4[32];
    char freq5[32];
    char freq6[32];
    char freq7[32];
    char lines[8][160];
    const char *status_word;
    uint32_t scale;
    uint32_t title_scale;
    uint32_t x;
    uint32_t y;
    uint32_t card_w;
    uint32_t line_h;
    size_t index;

    duration_ms = clamp_stress_duration_ms(duration_ms);

    if (failed) {
        status_word = "FAILED";
    } else if (running) {
        status_word = "RUNNING";
    } else if (done) {
        status_word = "DONE";
    } else {
        status_word = "READY";
    }

    a90_hud_read_status_snapshot(&snapshot);
```

stage3/linux_init/v89/60_shell_basic_commands.inc.c (L122 to 128)
  Note: v89 still declares struct a90_hud_status_snapshot and calls a90_hud_read_status_snapshot(), which are no longer provided by the shared header/API.
```
static void cmd_status(void) {
    struct a90_hud_status_snapshot snapshot;
    char boot_summary[64];
    struct a90_kms_info kms_info;

    a90_hud_read_status_snapshot(&snapshot);
    a90_timeline_boot_summary(boot_summary, sizeof(boot_summary));
```

# Attack-path analysis
Final: ignore | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
The scanner's low characterization as a build/reproducibility regression is supported, but for security triage it should be ignored rather than treated as a vulnerability. Evidence shows removed HUD metrics symbols in a90_hud.h and stale v89/v88 references causing compile failure. However, the threat model's relevant attack surfaces are privileged runtime command channels, flashing workflows, helper persistence, and host tooling; this issue is a local compile-time incompatibility with no attacker-controlled input, no exposed network surface, no identity/secret handling, and no deployed runtime. Probability of security exploitation is therefore none, and security impact is none.
## Likelihood
ignore - There is no realistic attacker exploitation path. Triggering the issue requires a developer/operator to build legacy sources from the checkout; it is not reachable over USB, TCP, cloud identity, public network, or untrusted data input.
## Impact
ignore - Impact is limited to local build/reproducibility and rollback availability for older retained source snapshots. There is no demonstrated confidentiality loss, integrity compromise, privilege escalation, code execution, or attacker-triggerable runtime denial of service.
## Assumptions
- Analysis is limited to repository artifacts in /workspace/A90_5G_rooting and did not use cloud APIs.
- The reported issue is the metrics refactor breaking older retained native-init source builds such as v88/v89.
- A security vulnerability requires an attacker-reachable path or a meaningful confidentiality, integrity, identity, privilege, or runtime availability impact in the project threat model.
- An operator or developer attempts to rebuild retained legacy init sources such as stage3/linux_init/init_v89.c from this checkout.
- The legacy source still includes the shared a90_hud.h header after the commit removed the old HUD metrics compatibility API.
## Path
Local build of init_v89.c
  -> v89 includes shared a90_hud.h
  -> old HUD metrics API no longer exists
  -> compile failure; no deployed runtime/security boundary crossed
## Path evidence
- `stage3/linux_init/a90_hud.h:8-24` - Current shared HUD header includes a90_metrics.h and exposes HUD rendering/storage APIs, but no longer declares struct a90_hud_status_snapshot, a90_hud_read_status_snapshot(), or a90_hud_read_sysfs_long().
- `stage3/linux_init/a90_metrics.h:6-24` - Replacement metric snapshot and helper APIs exist under a90_metrics_* names.
- `stage3/linux_init/v89/00_prelude.inc.c:30-42` - v89 includes the shared ../a90_hud.h header, so it observes the post-refactor API surface.
- `stage3/linux_init/v89/40_menu_apps.inc.c:148-152` - v89 still calls removed a90_hud_read_sysfs_long(), producing an implicit declaration diagnostic.
- `stage3/linux_init/v89/40_menu_apps.inc.c:3350-3383` - v89 still declares struct a90_hud_status_snapshot and calls removed a90_hud_read_status_snapshot(), producing compile errors.
- `stage3/linux_init/v89/60_shell_basic_commands.inc.c:123-127` - v89 shell status command still uses the removed HUD snapshot type and reader.
## Narrative
The finding is a real source-level regression: a90_hud.h no longer declares the old HUD metrics snapshot and helper functions, while v88/v89 still reference them. A direct v89 compile fails with unknown storage size for a90_hud_status_snapshot and implicit declarations for a90_hud_read_* helpers, while v90 compiles successfully with the new a90_metrics API. This supports the low availability/reproducibility finding but does not establish a security vulnerability: no attacker controls the input, no service is exposed, no secret or identity boundary is affected, and the failure happens before any legacy runtime can be deployed.
## Controls
- No public ingress, load balancer, or listening port is associated with this finding.
- No secret references or cloud identities are involved.
- The affected path fails at compile time before a legacy runtime can expose PID1/root behavior.
- Current v90 source compiles successfully with the new metrics API, limiting the regression to retained legacy sources.
## Blindspots
- Static-only review did not execute on-device runtime paths, but the affected legacy target fails before runtime.
- The repository may contain undocumented workflows that depend on v88/v89 rollback builds, which would affect operational availability but not create an attacker-reachable security path.
- A full build matrix was not exhaustively enumerated for every historical init version.
