# v129 Plan: Changelog Paging

Date: 2026-05-07
Target: `A90 Linux init 0.9.29 (v129)`
Marker: `0.9.29 v129 CHANGELOG PAGING`

## Summary

v129 fixes the growing changelog UX problem. The work is split into three
phases and keeps the existing physical-button menu model.

## Phase 1: Menu Viewport

- Add selected-row viewport rendering to long menu pages.
- Keep VOL+/VOL-/POWER navigation unchanged.
- Show a visible range marker such as `1-12/64` when a page is longer than the
  available screen rows.
- Apply this generally so `ABOUT / CHANGELOG` benefits without a one-off hack.

## Phase 2: Changelog Data Sharing

- Add `a90_changelog.c/h` as the shared changelog data source.
- Build the changelog menu page from the shared table.
- Draw ABOUT changelog list/detail from the same shared table.
- Keep old per-version detail functions available for retained compatibility,
  but route the current UI through the shared table.

## Phase 3: ABOUT Page Navigation

- Add page-aware ABOUT drawing for long text lists.
- Show page count in the title when content spans multiple pages.
- Use VOL+/VOL- to change pages inside ABOUT/changelog app screens and POWER to
  return to the menu.

## Validation

- ARM64 static build includes `a90_changelog.c`.
- `strings` confirms `A90 Linux init 0.9.29 (v129)`, `A90v129`, and
  `0.9.29 v129 CHANGELOG PAGING`.
- Host harness confirms changelog table/menu mapping and `BACK` item.
- Real-device flash confirms `cmdv1 version/status`.
- Runtime checks confirm `screenmenu`, `hide`, post-hide `run`, and menu-visible
  busy gate remain functional.

## Acceptance

- Long changelog menu no longer draws every row off-screen.
- Changelog list/menu/detail share a single data source for future version
  additions.
- ABOUT/changelog app screens have a defined page-navigation behavior.
