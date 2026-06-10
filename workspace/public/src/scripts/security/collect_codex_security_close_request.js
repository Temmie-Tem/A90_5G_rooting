(function () {
  "use strict";

  const GLOBAL_NAME = "a90CodexSecurityCapture";
  const MAX_BODY_CHARS = 32768;
  const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
  const SENSITIVE_HEADER = /^(authorization|cookie|set-cookie|x-csrf|csrf|x-openai|sec-|proxy-authorization)/i;
  const SENSITIVE_BODY_KEY = /(authorization|cookie|csrf|token|secret|password|credential|session)/i;

  if (window[GLOBAL_NAME] && typeof window[GLOBAL_NAME].restore === "function") {
    window[GLOBAL_NAME].restore();
  }

  const originalFetch = window.fetch;
  const originalXhrOpen = XMLHttpRequest.prototype.open;
  const originalXhrSend = XMLHttpRequest.prototype.send;
  const originalXhrSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;
  const originalSendBeacon = navigator.sendBeacon;
  let active = false;
  let sequence = 0;
  let mode = "same-origin-mutations";
  const entries = [];
  const liveEntries = [];

  function nowIso() {
    return new Date().toISOString();
  }

  function safeUrl(value) {
    try {
      if (typeof value === "string") {
        return new URL(value, window.location.href).toString();
      }
      if (value && typeof value.url === "string") {
        return new URL(value.url, window.location.href).toString();
      }
    } catch (error) {
      return String(value || "");
    }
    return String(value || "");
  }

  function shouldCapture(method, url) {
    const upperMethod = String(method || "GET").toUpperCase();
    if (!MUTATING_METHODS.has(upperMethod)) {
      return false;
    }
    if (mode === "all-mutations") {
      return true;
    }
    if (mode === "same-origin-mutations") {
      try {
        return new URL(url, window.location.href).origin === window.location.origin;
      } catch (error) {
        return false;
      }
    }
    const lowerUrl = String(url || "").toLowerCase();
    return lowerUrl.includes("/codex/") && lowerUrl.includes("/security");
  }

  function isLikelyFindingMutation(entry) {
    const url = String((entry && entry.url) || "").toLowerCase();
    return url.includes("/backend-api/aardvark/scan-findings/") || url.includes("/codex/cloud/security/findings/");
  }

  function headersToObject(headers) {
    const output = {};
    if (!headers) {
      return output;
    }
    try {
      new Headers(headers).forEach((value, key) => {
        output[key] = value;
      });
    } catch (error) {
      if (Array.isArray(headers)) {
        for (const pair of headers) {
          if (Array.isArray(pair) && pair.length >= 2) {
            output[String(pair[0])] = String(pair[1]);
          }
        }
      } else if (typeof headers === "object") {
        for (const [key, value] of Object.entries(headers)) {
          output[key] = String(value);
        }
      }
    }
    return output;
  }

  function redactHeaders(headers) {
    const output = {};
    for (const [key, value] of Object.entries(headersToObject(headers))) {
      output[key] = SENSITIVE_HEADER.test(key) ? "[REDACTED]" : value;
    }
    return output;
  }

  function storeLiveEntry(entry, rawHeaders) {
    const liveEntry = {
      live_template_id: entry.live_template_id,
      sequence: entry.sequence,
      method: entry.method,
      url: entry.url,
      request_headers_raw: Object.assign({}, rawHeaders || {}),
    };
    liveEntries.push(liveEntry);
    return liveEntry;
  }

  function redactBody(value) {
    if (Array.isArray(value)) {
      return value.map((item) => redactBody(item));
    }
    if (value && typeof value === "object") {
      const output = {};
      for (const [key, innerValue] of Object.entries(value)) {
        output[key] = SENSITIVE_BODY_KEY.test(key) ? "[REDACTED]" : redactBody(innerValue);
      }
      return output;
    }
    return value;
  }

  function summarizeBody(body) {
    if (body === undefined || body === null) {
      return { kind: "empty", text: "" };
    }
    if (typeof body === "string") {
      return parseBodyText(body);
    }
    if (body instanceof URLSearchParams) {
      return parseBodyText(body.toString());
    }
    if (body instanceof FormData) {
      const fields = {};
      body.forEach((value, key) => {
        fields[key] = value instanceof File ? `[File ${value.name} ${value.size} bytes]` : String(value);
      });
      return { kind: "form-data", json: redactBody(fields) };
    }
    return { kind: Object.prototype.toString.call(body), text: "[non-text request body omitted]" };
  }

  function parseBodyText(text) {
    const truncated = text.length > MAX_BODY_CHARS;
    const bodyText = truncated ? text.slice(0, MAX_BODY_CHARS) : text;
    try {
      return { kind: "json", json: redactBody(JSON.parse(bodyText)), truncated };
    } catch (error) {
      return { kind: "text", text: redactText(bodyText), truncated };
    }
  }

  function redactText(text) {
    return String(text).replace(/(authorization|cookie|csrf|token|secret|password|credential|session)(["'\s:=]+)([^"',\s}]+)/gi, "$1$2[REDACTED]");
  }

  async function responseSummary(response) {
    const summary = {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok,
      url: response.url,
      headers: redactHeaders(response.headers),
    };
    try {
      const text = await response.clone().text();
      summary.body = parseBodyText(text);
    } catch (error) {
      summary.body = { kind: "unavailable", error: String(error && error.message ? error.message : error) };
    }
    return summary;
  }

  function requestHeaders(input, init) {
    const headers = {};
    if (input && input.headers) {
      Object.assign(headers, headersToObject(input.headers));
    }
    if (init && init.headers) {
      Object.assign(headers, headersToObject(init.headers));
    }
    return headers;
  }

  async function summarizeFetchBody(input, init) {
    if (init && init.body !== undefined) {
      return summarizeBody(init.body);
    }
    if (typeof Request !== "undefined" && input instanceof Request) {
      try {
        const text = await input.clone().text();
        return parseBodyText(text);
      } catch (error) {
        return { kind: "unavailable", error: String(error && error.message ? error.message : error) };
      }
    }
    return summarizeBody(undefined);
  }

  window.fetch = async function a90CapturedFetch(input, init) {
    const fetchInit = init || {};
    const method = String(fetchInit.method || (input && input.method) || "GET").toUpperCase();
    const url = safeUrl(input);
    const capture = active && shouldCapture(method, url);
    const rawHeaders = capture ? requestHeaders(input, fetchInit) : {};
    const entry = capture
      ? {
          sequence: ++sequence,
          live_template_id: `a90-live-${sequence}`,
          started_at: nowIso(),
          transport: "fetch",
          method,
          url,
          request_headers: redactHeaders(rawHeaders),
          request_body: await summarizeFetchBody(input, fetchInit),
        }
      : null;
    if (entry) {
      storeLiveEntry(entry, rawHeaders);
    }

    try {
      const response = await originalFetch.apply(this, arguments);
      if (entry) {
        entry.finished_at = nowIso();
        entry.response = await responseSummary(response);
        entries.push(entry);
      }
      return response;
    } catch (error) {
      if (entry) {
        entry.finished_at = nowIso();
        entry.error = String(error && error.message ? error.message : error);
        entries.push(entry);
      }
      throw error;
    }
  };

  XMLHttpRequest.prototype.open = function a90CapturedXhrOpen(method, url) {
    this.__a90Capture = {
      method: String(method || "GET").toUpperCase(),
      url: safeUrl(url),
      request_headers: {},
    };
    return originalXhrOpen.apply(this, arguments);
  };

  XMLHttpRequest.prototype.setRequestHeader = function a90CapturedXhrHeader(key, value) {
    if (this.__a90Capture) {
      this.__a90Capture.request_headers[String(key)] = String(value);
    }
    return originalXhrSetRequestHeader.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function a90CapturedXhrSend(body) {
    const meta = this.__a90Capture;
    const capture = meta && active && shouldCapture(meta.method, meta.url);
    const rawHeaders = capture ? Object.assign({}, meta.request_headers) : {};
    const entry = capture
      ? {
          sequence: ++sequence,
          live_template_id: `a90-live-${sequence}`,
          started_at: nowIso(),
          transport: "xhr",
          method: meta.method,
          url: meta.url,
          request_headers: redactHeaders(rawHeaders),
          request_body: summarizeBody(body),
        }
      : null;
    if (entry) {
      storeLiveEntry(entry, rawHeaders);
    }

    if (entry) {
      this.addEventListener("loadend", () => {
        entry.finished_at = nowIso();
        entry.response = {
          status: this.status,
          statusText: this.statusText,
          ok: this.status >= 200 && this.status < 300,
          url: this.responseURL,
          body: parseBodyText(String(this.responseText || "")),
        };
        entries.push(entry);
      });
      this.addEventListener("error", () => {
        entry.finished_at = nowIso();
        entry.error = "XMLHttpRequest error";
        entries.push(entry);
      });
    }
    return originalXhrSend.apply(this, arguments);
  };

  if (typeof originalSendBeacon === "function") {
    navigator.sendBeacon = function a90CapturedSendBeacon(url, data) {
      const normalizedUrl = safeUrl(url);
      const capture = active && shouldCapture("POST", normalizedUrl);
      if (capture) {
        const entry = {
          sequence: ++sequence,
          live_template_id: `a90-live-${sequence}`,
          started_at: nowIso(),
          finished_at: nowIso(),
          transport: "sendBeacon",
          method: "POST",
          url: normalizedUrl,
          request_headers: {},
          request_body: summarizeBody(data),
          response: { status: 0, statusText: "sendBeacon queued", ok: true, url: normalizedUrl },
        };
        entries.push(entry);
        storeLiveEntry(entry, {});
      }
      return originalSendBeacon.apply(this, arguments);
    };
  }

  window[GLOBAL_NAME] = {
    start(options) {
      const opts = options || {};
      mode = opts.mode || "same-origin-mutations";
      active = true;
      return { active, mode, entries: entries.length };
    },
    stop() {
      active = false;
      return { active, mode, entries: entries.length };
    },
    clear() {
      entries.length = 0;
      liveEntries.length = 0;
      sequence = 0;
      return { active, entries: entries.length };
    },
    entries,
    liveEntries,
    securityEntries() {
      return entries.filter(isLikelyFindingMutation);
    },
    export(options) {
      const opts = options || {};
      const exportedEntries = opts.securityOnly === false ? entries : entries.filter(isLikelyFindingMutation);
      const payload = {
        exported_at: nowIso(),
        origin: window.location.origin,
        page_url: window.location.href,
        entries: exportedEntries,
        total_entries_seen: entries.length,
        security_only: opts.securityOnly !== false,
        note: "Sensitive headers and common body secret fields are redacted. Store this JSON under workspace/private only.",
      };
      const text = JSON.stringify(payload, null, 2);
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(() => {});
      }
      console.log(text);
      return payload;
    },
    restore() {
      active = false;
      window.fetch = originalFetch;
      XMLHttpRequest.prototype.open = originalXhrOpen;
      XMLHttpRequest.prototype.send = originalXhrSend;
      XMLHttpRequest.prototype.setRequestHeader = originalXhrSetRequestHeader;
      if (typeof originalSendBeacon === "function") {
        navigator.sendBeacon = originalSendBeacon;
      }
      return { restored: true, entries: entries.length };
    },
  };

  console.log("A90 Codex Security capture installed. Run a90CodexSecurityCapture.start({mode: 'same-origin-mutations'}), close one finding manually, then stop() and export().");
})();
