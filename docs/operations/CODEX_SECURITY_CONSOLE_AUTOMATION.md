# Codex Security Console Disposition Automation

Date: 2026-06-10

This workflow closes or labels stale Codex Security console findings from a local triage plan. It is intentionally split into three pieces:

1. Generate a private disposition plan from the exported CSV and local triage JSON.
2. Capture one manual close request in the logged-in browser session.
3. Reuse that request shape with guarded dry-run, canary, and small-batch execution.

The public Codex Security docs currently describe plugin workflows and web-console finding review, not a documented bulk-close API. Treat this as a web-console helper for the owner's own logged-in session, not as a stable API client.

References:

- Codex Security overview: <https://developers.openai.com/codex/security>
- Codex Security cloud setup and findings review: <https://developers.openai.com/codex/security/setup>
- Codex Security plugin local workflow: <https://developers.openai.com/codex/security/plugin>

## Safety Rules

- Run this only in a browser session for an account and repository you own or administer.
- Do not paste cookies, access tokens, CSRF tokens, or private capture JSON into the repository.
- Keep exported capture and generated plans under `workspace/private/**`.
- Start with `dryRun()`, then one-finding canary, then batches of at most 10.
- Stop on the first unexpected HTTP status, changed response shape, or UI mismatch.
- Do not use this to close findings that remain `manual_review` in the generated plan.

## Known-Good Reuse Path

This was validated on 2026-06-10 against Codex Security findings:

- `fixed`: 81 planned findings completed with `ok=81`, `failed=0`, and already-fixed entries safely skipped.
- `wont_fix`: 499 planned findings used the same live-auth + `applyRemaining()` flow with a conservative `delayMs`.
- The API endpoint observed by the web UI is `https://chatgpt.com/backend-api/aardvark/scan-findings/<id>`.
- The request body observed for `fixed` is `{"version": <current>, "status": "fixed", "resolution_reason": "A90_TEMPLATE_CONTEXT"}`.
- The request body observed for `wont_fix` uses the same shape with the UI-selected non-fix status.

The reusable path after any browser refresh is:

1. Paste `workspace/public/src/scripts/security/collect_codex_security_close_request.js`.
2. Run `a90CodexSecurityCapture.clear(); a90CodexSecurityCapture.start({ mode: "all-mutations" });`.
3. Submit one template action in the UI with `A90_TEMPLATE_CONTEXT` in `추가 컨텍스트`.
4. Run `a90CodexSecurityCapture.stop(); window.A90_CODEX_SECURITY_CAPTURE = a90CodexSecurityCapture.export();`.
5. Paste `workspace/public/src/scripts/security/apply_codex_security_dispositions.js`.
6. Paste only the matching plan-only snippet:
   - `workspace/private/outputs/security/codex/2026-06-10/console-snippets/fixed_load_plan_subset_only.js`
   - `workspace/private/outputs/security/codex/2026-06-10/console-snippets/wont_fix_load_plan_subset_only.js`
7. Run `a90CodexSecurityApply.dryRun({ disposition: "<fixed|wont_fix>", limit: 5 });`.
8. Confirm `live_auth_headers: true`, `version_refresh: true`, `method: "PATCH"`, and the backend `scan-findings` URL.
9. Run `applyRemaining()` with a conservative delay.

Recommended long-run command:

```js
await a90CodexSecurityApply.applyRemaining({
  apply: true,
  confirm: a90CodexSecurityApply.REQUIRED_CONFIRMATION,
  disposition: "wont_fix",
  offset: 0,
  delayMs: 4500,
  allowLargeRun: true,
});
```

Use `delayMs: 2500` for smaller `fixed` runs and `delayMs: 4500` for large `wont_fix` runs. `offset: 0` is safe after a refresh because each target is fetched first and already-applied findings are recorded as `skipped_already_applied`.

## Generate The Private Plan

Default input paths match the 2026-06-10 Codex export and reclassification:

```bash
python3 workspace/public/src/scripts/security/generate_codex_security_disposition_plan.py
```

Outputs are private and ignored by Git:

- `workspace/private/outputs/security/codex/2026-06-10/codex_security_disposition_plan.json`
- `workspace/private/outputs/security/codex/2026-06-10/codex_security_apply_plan_eligible.json`
- `workspace/private/outputs/security/codex/2026-06-10/codex_security_disposition_plan.csv`
- `workspace/private/outputs/security/codex/2026-06-10/codex_security_disposition_plan_summary.json`

Default policy:

- `P0` and `P1` active/current findings become `fixed` and apply-eligible.
- `Deferred` or non-current/archive findings become `wont_fix` and apply-eligible.
- `P2` context-dependent findings stay `manual_review` and are not apply-eligible.

Use `--include-p2` only after manual review if you explicitly want P2 items in the apply plan as accepted-risk entries.

## Capture One Manual Request

Open the Codex Security findings page in the logged-in browser. Open DevTools Console, paste:

```js
/* paste workspace/public/src/scripts/security/collect_codex_security_close_request.js */
a90CodexSecurityCapture.start({ mode: "same-origin-mutations" });
```

Manually close one low-risk finding using the same console disposition path you plan to reuse.

Korean UI mapping observed in the Codex Security modal:

- `수정하지 않았음`: use for generated `wont_fix` entries.
- `이미 수정함`: use for generated `fixed` entries.
- `거짓 양성`: reserve for a separately reviewed false-positive plan; the default generator does not auto-map findings to this.

If you want the batch helper to fill the `추가 컨텍스트` field per finding, type this exact marker into the UI before submitting the manual template action:

```text
A90_TEMPLATE_CONTEXT
```

The apply helper replaces that marker with each plan item's `console_context`. If the captured request body is empty, the UI did not send the context field and the helper cannot invent that field safely.

If the captured request body contains a `version` field, the apply helper performs a same-origin `GET` for each target finding before the mutating request and replaces `version` with the current value. This avoids replaying the template finding's stale optimistic-lock version onto other findings.

Then run:

```js
a90CodexSecurityCapture.stop();
const capture = a90CodexSecurityCapture.export();
```

Do not paste `start()` and `stop()` in the same console execution. `start()` must run first, the UI submit must happen while capture is active, and only then should `stop()` and `export()` run.

Save the exported JSON under `workspace/private/raw-logs/security/codex/2026-06-10/console-capture/`. Inspect it before use:

- `entries.length` should be at least 1.
- `entries[0].method` should be `POST`, `PATCH`, `PUT`, or `DELETE`.
- `entries[0].url` should contain `/codex/` and `/security`.
- `request_headers` must not contain real cookies or tokens.
- `request_body` should describe the close/disposition action.

By default `export()` keeps only likely finding mutations, such as `backend-api/aardvark/scan-findings/<id>`, and omits same-origin telemetry. Use `export({ securityOnly: false })` only for debugging.

If the captured request requires an explicit CSRF header that was redacted, stop. The helper deliberately does not preserve secrets.

Some Codex Security API calls require an `Authorization` header that is added by the web app. The exported JSON redacts that header by design. For actual apply runs, the safest path is to capture and apply in the same page session:

1. Paste the latest collector script.
2. Run `a90CodexSecurityCapture.start({ mode: "all-mutations" })`.
3. Submit one template action in the UI.
4. Run `a90CodexSecurityCapture.stop()`.
5. Set `window.A90_CODEX_SECURITY_CAPTURE = a90CodexSecurityCapture.export();` without saving raw headers.
6. Paste only the matching plan-subset snippet, such as `fixed_load_plan_subset_only.js`.

The collector keeps live raw request headers only in memory as `a90CodexSecurityCapture.liveEntries`. They are not printed or exported. The apply helper uses them for same-origin `GET`/`PATCH` requests and still drops raw cookies.

If `entries` is empty after a real manual close action:

1. Ignore unrelated console noise such as localStorage quota or missing translation warnings.
2. Re-paste the latest collector script. It restores the previous hook automatically.
3. Run `a90CodexSecurityCapture.start({ mode: "all-mutations" })`.
4. Close one finding manually again.
5. Export and inspect the capture. If it is still empty, the page likely used a transport outside `fetch`, `XMLHttpRequest`, or `sendBeacon`; use the browser Network tab and copy the mutating request as HAR into `workspace/private/**`.

## Dry-Run And Canary

Paste the apply helper into the same DevTools Console:

```js
/* paste workspace/public/src/scripts/security/apply_codex_security_dispositions.js */
```

Load the private capture and plan into the page. The exact paste method is manual by design so secrets never enter the repo:

```js
window.A90_CODEX_SECURITY_CAPTURE = /* exported capture JSON */;
window.A90_CODEX_SECURITY_PLAN = /* contents of codex_security_apply_plan_eligible.json */;
```

For live-auth apply, prefer:

```js
window.A90_CODEX_SECURITY_CAPTURE = a90CodexSecurityCapture.export();
/* paste workspace/private/outputs/security/codex/2026-06-10/console-snippets/fixed_load_plan_subset_only.js */
```

Dry-run the first few planned requests:

```js
a90CodexSecurityApply.dryRun({ disposition: "wont_fix", limit: 5 });
```

Run one canary only after the dry-run URL, method, and disposition look correct:

```js
a90CodexSecurityApply.canary({
  apply: true,
  confirm: a90CodexSecurityApply.REQUIRED_CONFIRMATION,
  disposition: "wont_fix",
  limit: 1,
});
```

Refresh the UI and confirm the single finding changed as expected.

## Batch Apply

Use small batches only:

```js
a90CodexSecurityApply.applyBatch({
  apply: true,
  confirm: a90CodexSecurityApply.REQUIRED_CONFIRMATION,
  disposition: "wont_fix",
  offset: 1,
  limit: 10,
  delayMs: 1500,
});
```

For a longer visible run after canary succeeds, use `applyRemaining()`. It logs each processed finding, waits between requests, refreshes each finding's current `version`, and skips findings already in the target disposition:

```js
await a90CodexSecurityApply.applyRemaining({
  apply: true,
  confirm: a90CodexSecurityApply.REQUIRED_CONFIRMATION,
  disposition: "fixed",
  offset: 0,
  delayMs: 2500,
});
```

Progress can be checked at any time:

```js
a90CodexSecurityApply.progress("fixed");
```

Use `offset: 0` for recovery after a refresh when the page state was lost; already-fixed findings are detected by the preflight `GET` and recorded as `skipped_already_applied`.

Recommended order:

1. Close `wont_fix` archived/non-current findings in batches.
2. Capture a separate `이미 수정함` manual action for `fixed` findings, ideally with `A90_TEMPLATE_CONTEXT` in the additional context box.
3. Leave `manual_review` findings untouched unless a separate review changes their disposition.

The helper stores per-request responses in:

```js
a90CodexSecurityApply.results
```

Copy the final results JSON into `workspace/private/raw-logs/security/codex/2026-06-10/console-apply/` for auditability.

## Failure Handling

- HTTP 401/403: session expired, missing CSRF, or permissions changed. Stop and use the UI manually.
- HTTP 404: finding ID no longer exists or URL shape changed. Regenerate the CSV export and plan.
- HTTP 409/422: finding already changed or payload schema mismatch. Re-capture a fresh manual request.
- Any unexpected body or status: stop the batch and inspect before retrying.

This workflow never bypasses authentication. It only reuses the browser's current logged-in session through same-origin requests.
