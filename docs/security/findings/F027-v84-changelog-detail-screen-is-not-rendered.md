# F027. v84 changelog detail screen is not rendered

## Metadata

| field | value |
|---|---|
| finding_id | `dfb9953b79848191ba79be7453344bb3` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/dfb9953b79848191ba79be7453344bb3 |
| severity | `informational` |
| status | `new` |
| detected_at | `2026-04-29T17:03:24.447320Z` |
| committed_at | `2026-04-30 01:17:25 +0900` |
| commit_hash | `fbf8b66c21394da1cb07eb7f7bbb6faa05f86b34` |
| relevant_paths | `stage3/linux_init/v84/40_menu_apps.inc.c` |
| has_patch | `false` |

## CSV Description

Selecting the newly added 0.8.15 v84 changelog item maps to SCREEN_APP_CHANGELOG_0815, but draw_screen_about_app() only dispatches changelog detail screens starting at SCREEN_APP_CHANGELOG_0814. The auto HUD draw loop has the same omission in its active_app predicate. As a result, the latest changelog entry can be selected but its detail screen is blank/not drawn, while older changelog entries continue to work. This is a functional regression introduced by the commit, not a security vulnerability.

## Codex Cloud Detail

v84 changelog detail screen is not rendered
Link: https://chatgpt.com/codex/cloud/security/findings/dfb9953b79848191ba79be7453344bb3?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=&page=2
Criticality: informational (attack path: ignore)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: fbf8b66
Author: shs02140@gmail.com
Created: 2026. 4. 30. 오전 2:03:24
Assignee: Unassigned
Signals: Validated, Attack-path

# Summary
A low-impact UI regression was introduced. I did not find an introduced security vulnerability in the cmdproto extraction itself; the cmdv1x bounds checks and decoding behavior appear equivalent to v83.
Selecting the newly added 0.8.15 v84 changelog item maps to SCREEN_APP_CHANGELOG_0815, but draw_screen_about_app() only dispatches changelog detail screens starting at SCREEN_APP_CHANGELOG_0814. The auto HUD draw loop has the same omission in its active_app predicate. As a result, the latest changelog entry can be selected but its detail screen is blank/not drawn, while older changelog entries continue to work. This is a functional regression introduced by the commit, not a security vulnerability.

# Validation
## Rubric
- [x] Confirm the new 0.8.15 v84 changelog entry is present and selectable.
- [x] Confirm selecting it maps to SCREEN_APP_CHANGELOG_0815.
- [x] Confirm draw_screen_about_app() omits SCREEN_APP_CHANGELOG_0815 while handling older changelog ids.
- [x] Confirm a 0815 detail renderer exists, making the omission unintended rather than unsupported functionality.
- [x] Confirm the auto-HUD active_app routing also omits SCREEN_APP_CHANGELOG_0815 and that dynamic execution reproduces silent non-rendering rather than a security crash.
## Report
Validated the suspected low-impact UI regression. Code review of the touched v84 file shows the 0.8.15 v84 changelog menu item is selectable at stage3/linux_init/v84/40_menu_apps.inc.c:214-216 and maps through screen_menu_about_app() to SCREEN_APP_CHANGELOG_0815 at lines 351-360. However, draw_screen_about_app() handles changelog detail screens starting at SCREEN_APP_CHANGELOG_0814 and falls through to default return 0 for unhandled ids at lines 424-463. The auto-HUD draw predicate similarly starts at SCREEN_APP_CHANGELOG_0814 and omits 0815 at lines 617-649. A real renderer for 0815 does exist in draw_screen_changelog_detail() at lines 4598-4601, confirming the dispatch omission is unintended. Dynamic PoC: I compiled a small harness that includes the real init_v84.c translation unit and calls the actual static menu/render dispatch functions. Run output: map_0815=6 expected=6; map_0814=7 expected=7; draw_screen_about_app(0815) rc=0 errno=0; draw_screen_about_app(0814) rc=-2 errno=2; direct draw_screen_changelog_detail(0815) rc=-2 errno=2; omission_detected=yes. In this container, KMS rendering fails with ENOENT because there is no DRM device, but that is useful differential evidence: the direct 0815 renderer and neighboring 0814 path attempt rendering and fail, while draw_screen_about_app(0815) silently returns success without attempting any render. ASan/UBSan run reproduced the same logic result with no sanitizer crash, supporting that this is functional/UI, not memory-corruption. LLDB non-interactive trace stopped in draw_screen_about_app(app_id=SCREEN_APP_CHANGELOG_0815) at 40_menu_apps.inc.c:425, showing the real dispatch path receives the new app id.

# Evidence
stage3/linux_init/v84/40_menu_apps.inc.c (L214 to 216)
  Note: The commit adds a selectable 0.8.15 v84 changelog item.
```
static const struct screen_menu_item screen_menu_changelog_items[] = {
    { "0.8.15 v84", "CMDPROTO API",       SCREEN_MENU_CHANGELOG_0815, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.14 v83", "CONSOLE API",        SCREEN_MENU_CHANGELOG_0814, SCREEN_MENU_PAGE_CHANGELOG },
```

stage3/linux_init/v84/40_menu_apps.inc.c (L351 to 361)
  Note: Selecting that menu action maps it to SCREEN_APP_CHANGELOG_0815.
```
static enum screen_app_id screen_menu_about_app(enum screen_menu_action action) {
    switch (action) {
    case SCREEN_MENU_ABOUT_VERSION:
        return SCREEN_APP_ABOUT_VERSION;
    case SCREEN_MENU_ABOUT_CHANGELOG:
        return SCREEN_APP_ABOUT_CHANGELOG;
    case SCREEN_MENU_ABOUT_CREDITS:
        return SCREEN_APP_ABOUT_CREDITS;
    case SCREEN_MENU_CHANGELOG_0815:
        return SCREEN_APP_CHANGELOG_0815;
    case SCREEN_MENU_CHANGELOG_0814:
```

stage3/linux_init/v84/40_menu_apps.inc.c (L424 to 433)
  Note: draw_screen_about_app() omits SCREEN_APP_CHANGELOG_0815 and starts handling changelog detail ids at 0814, so the new item falls through to the default path.
```
static int draw_screen_about_app(enum screen_app_id app_id) {
    switch (app_id) {
    case SCREEN_APP_ABOUT_VERSION:
        return draw_screen_about_version();
    case SCREEN_APP_ABOUT_CHANGELOG:
        return draw_screen_about_changelog();
    case SCREEN_APP_ABOUT_CREDITS:
        return draw_screen_about_credits();
    case SCREEN_APP_CHANGELOG_0814:
    case SCREEN_APP_CHANGELOG_0813:
```

stage3/linux_init/v84/40_menu_apps.inc.c (L4598 to 4602)
  Note: A renderer for SCREEN_APP_CHANGELOG_0815 exists, confirming the omission in the dispatch paths is unintended.
```
static int draw_screen_changelog_detail(enum screen_app_id app_id) {
    switch (app_id) {
    case SCREEN_APP_CHANGELOG_0815:
        return draw_screen_changelog_v0815();
    case SCREEN_APP_CHANGELOG_0814:
```

stage3/linux_init/v84/40_menu_apps.inc.c (L617 to 649)
  Note: The auto HUD draw predicate also omits SCREEN_APP_CHANGELOG_0815, so an active 0815 changelog app is not routed to draw_screen_about_app().
```
        } else if (active_app == SCREEN_APP_ABOUT_VERSION ||
                   active_app == SCREEN_APP_ABOUT_CHANGELOG ||
                   active_app == SCREEN_APP_ABOUT_CREDITS ||
                   active_app == SCREEN_APP_CHANGELOG_0814 ||
                   active_app == SCREEN_APP_CHANGELOG_0813 ||
                   active_app == SCREEN_APP_CHANGELOG_0812 ||
                   active_app == SCREEN_APP_CHANGELOG_0811 ||
                   active_app == SCREEN_APP_CHANGELOG_0810 ||
                   active_app == SCREEN_APP_CHANGELOG_089 ||
                   active_app == SCREEN_APP_CHANGELOG_088 ||
                   active_app == SCREEN_APP_CHANGELOG_087 ||
                   active_app == SCREEN_APP_CHANGELOG_086 ||
                   active_app == SCREEN_APP_CHANGELOG_085 ||
                   active_app == SCREEN_APP_CHANGELOG_084 ||
                   active_app == SCREEN_APP_CHANGELOG_083 ||
                   active_app == SCREEN_APP_CHANGELOG_082 ||
                   active_app == SCREEN_APP_CHANGELOG_081 ||
                   active_app == SCREEN_APP_CHANGELOG_080 ||
                   active_app == SCREEN_APP_CHANGELOG_075 ||
                   active_app == SCREEN_APP_CHANGELOG_074 ||
                   active_app == SCREEN_APP_CHANGELOG_073 ||
                   active_app == SCREEN_APP_CHANGELOG_072 ||
                   active_app == SCREEN_APP_CHANGELOG_071 ||
                   active_app == SCREEN_APP_CHANGELOG_070 ||
                   active_app == SCREEN_APP_CHANGELOG_060 ||
                   active_app == SCREEN_APP_CHANGELOG_051 ||
                   active_app == SCREEN_APP_CHANGELOG_050 ||
                   active_app == SCREEN_APP_CHANGELOG_041 ||
                   active_app == SCREEN_APP_CHANGELOG_040 ||
                   active_app == SCREEN_APP_CHANGELOG_030 ||
                   active_app == SCREEN_APP_CHANGELOG_020 ||
                   active_app == SCREEN_APP_CHANGELOG_010) {
            draw_screen_about_app(active_app);
```

# Attack-path analysis
Final: ignore | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
The original low classification is directionally conservative, but for security triage this should be ignored as a non-security functional regression. Static evidence confirms the dispatch omission, and the provided validation evidence confirms silent non-rendering with no sanitizer crash or memory-corruption behavior. The reachable path is local on-device UI navigation, not an externally exposed service or command channel. It crosses no trust boundary and reaches no sensitive sink, so probability × impact for security is effectively none.
## Likelihood
ignore - The functional bug is easy for a local operator to trigger through normal UI navigation, but exploitation likelihood is not meaningful because there is no security effect for an attacker to exploit.
## Impact
ignore - The only demonstrated impact is a blank/non-rendered changelog detail page. It does not expose data, execute commands, bypass controls, alter partitions, persist code, or affect confidentiality/integrity in the repository threat model.
## Assumptions
- The analyzed repository checkout is read-only and corresponds to commit fbf8b66c21394da1cb07eb7f7bbb6faa05f86b34.
- The v84 native-init HUD/menu code may be part of the on-device runtime, but this specific path only renders informational changelog UI.
- No cloud, production infrastructure, or external service exposure is inferred beyond repository artifacts.
- device is running the v84 native init runtime
- a local/trusted operator navigates to About/Changelog
- operator selects the 0.8.15 v84 changelog item
## Path
local menu selection -> SCREEN_APP_CHANGELOG_0815 -> omitted draw/HUD cases -> blank changelog UI
## Path evidence
- `stage3/linux_init/v84/40_menu_apps.inc.c:214-216` - The 0.8.15 v84 changelog item is present and selectable in the menu.
- `stage3/linux_init/v84/40_menu_apps.inc.c:351-361` - The selected SCREEN_MENU_CHANGELOG_0815 action maps to SCREEN_APP_CHANGELOG_0815.
- `stage3/linux_init/v84/40_menu_apps.inc.c:424-463` - draw_screen_about_app() handles changelog detail screens from SCREEN_APP_CHANGELOG_0814 downward and falls through to default return 0 for unhandled ids, omitting 0815.
- `stage3/linux_init/v84/40_menu_apps.inc.c:617-649` - The auto-HUD active_app routing predicate also starts at SCREEN_APP_CHANGELOG_0814 and omits SCREEN_APP_CHANGELOG_0815.
- `stage3/linux_init/v84/40_menu_apps.inc.c:4598-4602` - A real 0815 renderer exists in draw_screen_changelog_detail(), showing the omission is unintended but still only affects UI rendering.
## Narrative
The report is accurate as a functional regression: the v84 changelog menu contains a selectable 0.8.15 item and maps it to SCREEN_APP_CHANGELOG_0815, while draw_screen_about_app() and the auto-HUD routing predicate only handle changelog detail ids starting at 0814. A renderer for 0815 exists, confirming an omitted dispatch case. This does not create a realistic security vulnerability: there is no attacker-controlled network input, no auth boundary, no command/file/partition sink, no secret access, and no cross-boundary impact. The effect is limited to a local informational UI screen failing to render.
## Controls
- No public ingress or load balancer for this path
- No TCP/serial command parser involvement
- No authentication or authorization decision affected
- No executable sink reached
- No filesystem, partition, credential, or network mutation reached
## Blindspots
- Static review did not execute the full device UI on real hardware in this attack-path phase.
- Repository-only analysis cannot prove how often v84 is flashed or used operationally.
- The broader native-init runtime has high-risk root command surfaces, but they are not implicated by this specific changelog rendering defect.
