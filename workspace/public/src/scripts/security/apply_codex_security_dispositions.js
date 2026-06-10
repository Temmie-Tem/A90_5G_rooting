(function () {
  "use strict";

  const GLOBAL_NAME = "a90CodexSecurityApply";
  const REQUIRED_CONFIRMATION = "I understand this uses an undocumented web UI request";
  const MAX_BATCH = 10;
  const DEFAULT_DELAY_MS = 1200;
  const DEFAULT_REMAINING_DELAY_MS = 2500;
  const MAX_REMAINING_WITHOUT_LARGE_CONFIRM = 100;
  const SENSITIVE_HEADER = /^(authorization|cookie|set-cookie|x-csrf|csrf|x-openai|sec-|proxy-authorization)/i;
  const SECRET_VALUE = /^\[REDACTED\]$/;
  const FINDING_ID_PATTERN = /\/(?:scan-findings|findings)\/([A-Za-z0-9_-]+)/;
  const CONTEXT_MARKER = "A90_TEMPLATE_CONTEXT";
  const TEMPLATE_STATUS_TO_DISPOSITION = {
    fixed: "fixed",
    resolved: "fixed",
    wontfix: "wont_fix",
    "wont_fix": "wont_fix",
    "won't_fix": "wont_fix",
    dismissed: "wont_fix",
  };
  const results = [];

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function numberOption(value, fallback) {
    return value === undefined ? fallback : Number(value);
  }

  function logProgress(message, payload) {
    console.log(`[A90 Codex Security] ${message}`, payload || "");
  }

  function requirePlan() {
    const plan = window.A90_CODEX_SECURITY_PLAN;
    if (!Array.isArray(plan)) {
      throw new Error("Set window.A90_CODEX_SECURITY_PLAN to the generated eligible plan array first.");
    }
    return plan.filter((item) => item && item.apply_eligible === true);
  }

  function requireCaptureEntry(options) {
    const capture = window.A90_CODEX_SECURITY_CAPTURE;
    if (!capture) {
      throw new Error("Set window.A90_CODEX_SECURITY_CAPTURE to the exported capture JSON first.");
    }
    if (capture.method && capture.url) {
      return capture;
    }
    const entries = Array.isArray(capture.entries) ? capture.entries : [];
    const index = Number.isInteger(options.templateIndex) ? options.templateIndex : 0;
    const entry = entries[index];
    if (!entry || !entry.method || !entry.url) {
      throw new Error("Capture JSON has no usable mutating request entry at templateIndex.");
    }
    return entry;
  }

  function normalizeDisposition(value) {
    const key = String(value || "").trim().toLowerCase();
    return TEMPLATE_STATUS_TO_DISPOSITION[key] || key;
  }

  function normalizedTargetDisposition(item) {
    return normalizeDisposition(item && item.disposition);
  }

  function statusAlreadyMatches(item, currentStatus) {
    return Boolean(currentStatus && normalizedTargetDisposition(item) === normalizeDisposition(currentStatus));
  }

  function templateDisposition(template) {
    const body = template && template.response && template.response.body;
    const candidates = [];
    if (body && body.kind === "json" && body.json && typeof body.json === "object") {
      candidates.push(body.json.status, body.json.disposition, body.json.resolution);
    }
    if (body && typeof body.text === "string") {
      const statusMatch = body.text.match(/"status"\s*:\s*"([^"]+)"/);
      const dispositionMatch = body.text.match(/"disposition"\s*:\s*"([^"]+)"/);
      const resolutionMatch = body.text.match(/"resolution"\s*:\s*"([^"]+)"/);
      candidates.push(statusMatch && statusMatch[1], dispositionMatch && dispositionMatch[1], resolutionMatch && resolutionMatch[1]);
    }
    for (const candidate of candidates) {
      const normalized = normalizeDisposition(candidate);
      if (normalized) {
        return normalized;
      }
    }
    return "";
  }

  function findingIdFromUrl(url) {
    const match = String(url || "").match(FINDING_ID_PATTERN);
    return match ? match[1] : "";
  }

  function replaceAllText(text, replacements) {
    let output = String(text);
    for (const [from, to] of replacements) {
      if (from) {
        output = output.split(from).join(to);
      }
    }
    return output;
  }

  function itemContext(item) {
    if (item.console_context) {
      return String(item.console_context);
    }
    return `${item.disposition_reason || ""} Evidence: ${item.evidence_refs || ""}`.trim();
  }

  function cloneJson(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function replaceInJson(value, replacements) {
    if (Array.isArray(value)) {
      return value.map((item) => replaceInJson(item, replacements));
    }
    if (value && typeof value === "object") {
      const output = {};
      for (const [key, innerValue] of Object.entries(value)) {
        output[key] = adjustJsonField(key, replaceInJson(innerValue, replacements));
      }
      return output;
    }
    if (typeof value === "string") {
      return replaceAllText(value, replacements);
    }
    return value;
  }

  function bodyNeedsVersionRefresh(body) {
    return Boolean(body && typeof body === "object" && Object.prototype.hasOwnProperty.call(body, "version"));
  }

  async function fetchCurrentFinding(url, headers) {
    const response = await fetch(url, { method: "GET", headers, credentials: "include" });
    const text = await response.text().catch(() => "");
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        throw new Error(`Version refresh failed for ${url}: HTTP ${response.status}. Re-capture the template and run apply in the same page session so live Authorization headers are available.`);
      }
      throw new Error(`Version refresh failed for ${url}: HTTP ${response.status}`);
    }
    try {
      return JSON.parse(text);
    } catch (error) {
      throw new Error(`Version refresh returned non-JSON for ${url}`);
    }
  }

  async function refreshRequestStateIfNeeded(request, item, options) {
    const opts = options || {};
    const shouldRefresh = request.versionNeedsRefresh || opts.refreshBeforeEach === true || opts.skipAlreadyApplied !== false;
    if (!shouldRefresh) {
      return request;
    }
    const current = await fetchCurrentFinding(request.url, request.versionHeaders);
    request.currentStatus = normalizeDisposition(current.status);
    if (request.versionNeedsRefresh && !Object.prototype.hasOwnProperty.call(current, "version")) {
      throw new Error(`Version refresh response has no version for ${request.url}`);
    }
    if (request.versionNeedsRefresh) {
      const parsedBody = JSON.parse(request.init.body);
      parsedBody.version = current.version;
      request.init.body = JSON.stringify(parsedBody);
      request.version = current.version;
    }
    return request;
  }

  function adjustJsonField(key, value) {
    const item = adjustJsonField.currentItem;
    if (!item) {
      return value;
    }
    const lowerKey = String(key).toLowerCase();
    if (/^(comment|note|message|context|additional_context|details|explanation|resolution_comment|resolution_context|resolution_note)$/.test(lowerKey)) {
      return itemContext(item);
    }
    if (/^(reason|resolution_reason|dismissal_reason)$/.test(lowerKey)) {
      return item.disposition_reason;
    }
    if (/^(resolution|disposition)$/.test(lowerKey)) {
      return item.disposition;
    }
    return value;
  }

  function liveTemplateFor(template) {
    const captureTool = window.a90CodexSecurityCapture;
    const liveEntries = captureTool && Array.isArray(captureTool.liveEntries) ? captureTool.liveEntries : [];
    if (!liveEntries.length) {
      return null;
    }
    if (template.live_template_id) {
      const byId = liveEntries.find((entry) => entry.live_template_id === template.live_template_id);
      if (byId) {
        return byId;
      }
    }
    return liveEntries.find((entry) => entry.sequence === template.sequence && entry.url === template.url) || null;
  }

  function safeHeaders(templateHeaders, replacements, options) {
    const opts = options || {};
    const headers = {};
    for (const [key, value] of Object.entries(templateHeaders || {})) {
      if (!opts.allowSensitive && SENSITIVE_HEADER.test(key)) {
        continue;
      }
      if (SECRET_VALUE.test(String(value))) {
        continue;
      }
      const lowerKey = String(key).toLowerCase();
      if (lowerKey === "content-length" || lowerKey === "host" || lowerKey === "origin" || lowerKey === "referer" || lowerKey === "cookie") {
        continue;
      }
      headers[key] = replaceAllText(String(value), replacements || []);
    }
    return headers;
  }

  function buildRequest(template, item) {
    const capturedId = findingIdFromUrl(template.url);
    if (!capturedId) {
      throw new Error("Captured request URL does not contain /findings/<id>.");
    }
    const replacements = [
      [capturedId, item.finding_id],
      [CONTEXT_MARKER, itemContext(item)],
    ];
    const url = replaceAllText(template.url, replacements);
    const method = String(template.method || "PATCH").toUpperCase();
    const liveTemplate = liveTemplateFor(template);
    const liveHeaders = liveTemplate && liveTemplate.request_headers_raw ? liveTemplate.request_headers_raw : null;
    const headers = liveHeaders
      ? safeHeaders(liveHeaders, replacements, { allowSensitive: true })
      : safeHeaders(template.request_headers, replacements, { allowSensitive: false });
    const requestBody = template.request_body || {};
    let body = undefined;
    let versionNeedsRefresh = false;

    if (requestBody.kind === "json" && requestBody.json !== undefined) {
      adjustJsonField.currentItem = item;
      const patched = replaceInJson(cloneJson(requestBody.json), replacements);
      adjustJsonField.currentItem = null;
      body = JSON.stringify(patched);
      headers["content-type"] = headers["content-type"] || "application/json";
      versionNeedsRefresh = bodyNeedsVersionRefresh(patched);
    } else if (typeof requestBody.text === "string" && requestBody.text.length > 0) {
      body = replaceAllText(requestBody.text, replacements);
    }

    return {
      url,
      init: { method, headers, body, credentials: "include" },
      versionHeaders: Object.assign({}, headers),
      versionNeedsRefresh,
      liveAuthHeaders: Boolean(liveHeaders),
    };
  }

  function selectItems(options) {
    const plan = requirePlan();
    const offset = Math.max(0, Number(options.offset || 0));
    const requestedLimit = Number(options.limit || 1);
    const limit = Math.min(Math.max(1, requestedLimit), MAX_BATCH);
    const disposition = options.disposition ? String(options.disposition) : "";
    const filtered = disposition ? plan.filter((item) => item.disposition === disposition) : plan;
    return filtered.slice(offset, offset + limit);
  }

  function selectRemainingItems(options) {
    const opts = options || {};
    const plan = requirePlan();
    const offset = Math.max(0, Number(opts.offset || 0));
    const disposition = opts.disposition ? String(opts.disposition) : "";
    const doneIds = new Set(results.filter((result) => result && result.ok).map((result) => result.finding_id));
    const filtered = disposition ? plan.filter((item) => item.disposition === disposition) : plan;
    const remaining = filtered.filter((item, index) => index >= offset && !doneIds.has(item.finding_id));
    const requestedLimit = opts.limit === undefined ? remaining.length : Number(opts.limit);
    const limit = Math.max(0, requestedLimit);
    return remaining.slice(0, limit);
  }

  function summarizeRequest(template, item) {
    const request = buildRequest(template, item);
    return {
      row: item.row,
      finding_id: item.finding_id,
      title: item.title,
      disposition: item.disposition,
      bucket: item.disposition_bucket,
      method: request.init.method,
      url: request.url,
      has_body: request.init.body !== undefined,
      version_refresh: request.versionNeedsRefresh,
      live_auth_headers: request.liveAuthHeaders,
    };
  }

  function resultSummary(result) {
    return {
      row: result.row,
      ok: result.ok,
      status: result.status,
      skipped: Boolean(result.skipped),
      version: result.version,
      live_auth_headers: result.live_auth_headers,
    };
  }

  async function sendOne(template, item, options) {
    const opts = options || {};
    const request = await refreshRequestStateIfNeeded(buildRequest(template, item), item, opts);
    const startedAt = new Date().toISOString();
    if (opts.skipAlreadyApplied !== false && statusAlreadyMatches(item, request.currentStatus)) {
      const result = {
        row: item.row,
        finding_id: item.finding_id,
        disposition: item.disposition,
        started_at: startedAt,
        finished_at: new Date().toISOString(),
        ok: true,
        status: "skipped_already_applied",
        statusText: request.currentStatus,
        skipped: true,
        version: request.version,
        live_auth_headers: request.liveAuthHeaders,
        response_excerpt: "",
      };
      results.push(result);
      return result;
    }
    const response = await fetch(request.url, request.init);
    const text = await response.text().catch(() => "");
    const result = {
      row: item.row,
      finding_id: item.finding_id,
      disposition: item.disposition,
      started_at: startedAt,
      finished_at: new Date().toISOString(),
      ok: response.ok,
      status: response.status,
      statusText: response.statusText,
      version: request.version,
      live_auth_headers: request.liveAuthHeaders,
      skipped: false,
      response_excerpt: text.slice(0, 2048),
    };
    results.push(result);
    if (!response.ok) {
      throw new Error(`Close request failed for ${item.finding_id}: HTTP ${response.status}`);
    }
    return result;
  }

  async function applyBatch(options) {
    const opts = options || {};
    if (opts.apply !== true || opts.confirm !== REQUIRED_CONFIRMATION) {
      throw new Error(`Refusing to send requests. Pass {apply: true, confirm: "${REQUIRED_CONFIRMATION}"}.`);
    }
    if (!opts.disposition && opts.allowMixedDispositions !== true) {
      throw new Error("Refusing mixed-disposition apply. Pass disposition: 'wont_fix' or capture/use a matching template for the target disposition.");
    }
    const template = requireCaptureEntry(opts);
    const capturedDisposition = templateDisposition(template);
    const requestedDisposition = normalizeDisposition(opts.disposition);
    if (capturedDisposition && requestedDisposition && capturedDisposition !== requestedDisposition && opts.allowTemplateStatusMismatch !== true) {
      throw new Error(`Captured template appears to apply '${capturedDisposition}', but requested '${requestedDisposition}'. Capture a matching manual action or pass allowTemplateStatusMismatch only after manual review.`);
    }
    const items = selectItems(opts);
    const delayMs = Math.max(0, numberOption(opts.delayMs, DEFAULT_DELAY_MS));
    const output = [];
    for (const [index, item] of items.entries()) {
      const result = await sendOne(template, item, opts);
      output.push(result);
      if (opts.logProgress === true) {
        logProgress(`${index + 1}/${items.length}`, resultSummary(result));
      }
      if (delayMs > 0) {
        await sleep(delayMs);
      }
    }
    return output;
  }

  async function applyRemaining(options) {
    const opts = Object.assign({ delayMs: DEFAULT_REMAINING_DELAY_MS, logProgress: true, skipAlreadyApplied: true }, options || {});
    if (opts.apply !== true || opts.confirm !== REQUIRED_CONFIRMATION) {
      throw new Error(`Refusing to send requests. Pass {apply: true, confirm: "${REQUIRED_CONFIRMATION}"}.`);
    }
    if (!opts.disposition && opts.allowMixedDispositions !== true) {
      throw new Error("Refusing mixed-disposition applyRemaining. Pass disposition: 'fixed' or 'wont_fix'.");
    }
    const template = requireCaptureEntry(opts);
    const capturedDisposition = templateDisposition(template);
    const requestedDisposition = normalizeDisposition(opts.disposition);
    if (capturedDisposition && requestedDisposition && capturedDisposition !== requestedDisposition && opts.allowTemplateStatusMismatch !== true) {
      throw new Error(`Captured template appears to apply '${capturedDisposition}', but requested '${requestedDisposition}'.`);
    }
    const items = selectRemainingItems(opts);
    if (items.length > MAX_REMAINING_WITHOUT_LARGE_CONFIRM && opts.allowLargeRun !== true) {
      throw new Error(`Refusing large run of ${items.length} items. Pass allowLargeRun: true after reviewing dryRun/summary.`);
    }
    const delayMs = Math.max(0, numberOption(opts.delayMs, DEFAULT_REMAINING_DELAY_MS));
    const output = [];
    logProgress("applyRemaining:start", {
      disposition: opts.disposition,
      offset: Math.max(0, Number(opts.offset || 0)),
      total: items.length,
      delayMs,
    });
    for (const [index, item] of items.entries()) {
      const result = await sendOne(template, item, opts);
      output.push(result);
      logProgress(`${index + 1}/${items.length}`, resultSummary(result));
      if (delayMs > 0 && index + 1 < items.length) {
        await sleep(delayMs);
      }
    }
    logProgress("applyRemaining:done", {
      total: output.length,
      ok: output.filter((result) => result.ok).length,
      skipped: output.filter((result) => result.skipped).length,
      failed: output.filter((result) => !result.ok).length,
    });
    return output;
  }

  function progress(disposition) {
    const plan = requirePlan();
    const filtered = disposition ? plan.filter((item) => item.disposition === disposition) : plan;
    const doneIds = new Set(results.filter((result) => result && result.ok).map((result) => result.finding_id));
    const missing = filtered
      .map((item, index) => (doneIds.has(item.finding_id) ? null : { i: index, row: item.row, title: item.title }))
      .filter(Boolean);
    return {
      disposition: disposition || "all",
      doneResults: results.length,
      doneUnique: doneIds.size,
      totalPlan: filtered.length,
      remaining: missing.length,
      nextOffset: missing.length ? missing[0].i : null,
      last10: results.slice(-10).map(resultSummary),
      next: missing.slice(0, 10),
    };
  }

  window[GLOBAL_NAME] = {
    REQUIRED_CONFIRMATION,
    results,
    dryRun(options) {
      const opts = options || {};
      const template = requireCaptureEntry(opts);
      return selectItems(opts).map((item) => summarizeRequest(template, item));
    },
    canary(options) {
      return applyBatch(Object.assign({}, options || {}, { limit: 1 }));
    },
    applyBatch,
    applyRemaining,
    progress,
  };

  console.log("A90 Codex Security apply helper installed. Set A90_CODEX_SECURITY_CAPTURE and A90_CODEX_SECURITY_PLAN, then run a90CodexSecurityApply.dryRun().");
})();
