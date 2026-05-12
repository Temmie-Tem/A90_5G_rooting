# Raw New Findings

Source CSV: `docs/security/codex-security-findings-2026-05-12T08-30-30.417Z.csv`

---

## New Non-Duplicate Candidates

### F054 candidate. Observe-only broker can leak tcpctl auth token

- severity: `high`
- status: `new`
- commit: `fc300f7cce5ec46abcd0aef5bc840de02f498e40`
- finding URL: <https://chatgpt.com/codex/cloud/security/findings/7e29d366e9c88191858b21e4613abe7f>
- relevant paths: `scripts/revalidation/a90_broker.py`, `stage3/linux_init/init_v73.c`

CSV description:

> This commit adds a broker authorization boundary where default policy permits only `observe` commands. However, `cat` remains classified as an observe command without path restrictions. The native init implementation of `cat` opens and returns any requested file path as root. Since the tcpctl token path is known (`/cache/native-init-tcpctl.token`), an observer-only broker client can request `cat /cache/native-init-tcpctl.token`, obtain the tcpctl authentication token, and then connect to the device tcpctl service directly to authenticate and run absolute-path commands as root. Even without the tcpctl escalation step, the policy allows arbitrary root file reads through a mode documented as observe-only.

### F055 candidate. Wi-Fi gate failure does not fail capability summary

- severity: `medium`
- status: `new`
- commit: `4c984a72716d269354789324e5bdca141fa61cdf`
- finding URL: <https://chatgpt.com/codex/cloud/security/findings/f634a0fd39088191a848638f85af0421>
- relevant paths: `scripts/revalidation/a90_kernel_tools.py`, `scripts/revalidation/kernel_capability_summary.py`

CSV description:

> The v202 summary is intended to merge v197-v200 evidence with a live `wififeas gate` result before guiding the next Wi-Fi/network/debug decision. However, `wifi_gate()` initializes the decision to `unknown` and only parses text; it does not propagate whether the command actually succeeded. The shared `run_capture()` helper catches connection/protocol failures and returns an empty failed capture, so a missing bridge, unavailable device, unsupported command, or malformed response becomes `wifi_decision == "unknown"`. `build_summary()` then calculates `pass_ok` only from the four JSON evidence files and their version flags, excluding the Wi-Fi gate result entirely. As a result, stale passing JSON evidence plus a failed live Wi-Fi gate still produces `PASS`, writes a manifest with `"pass": true`, and exits 0. Automation or operators relying on the script exit status can therefore treat the safety preflight as successful despite the live Wi-Fi gate being absent or unverifiable.

### F056 candidate. Lifecycle token capture crashes before starting tcpctl

- severity: `informational`
- status: `new`
- commit: `5f0462aa9568f20907b0dc2efd814fe783a2a448`
- finding URL: <https://chatgpt.com/codex/cloud/security/findings/c8ec2316bbf88191aa389761867c9e36>
- relevant paths: `scripts/revalidation/a90_broker_ncm_lifecycle_check.py`, `scripts/revalidation/tcpctl_host.py`

CSV description:

> In non-dry-run mode without an explicit --token, a90_broker_ncm_lifecycle_check.py now calls get_tcpctl_token(args). That helper is imported from tcpctl_host.py and expects tcpctl_host-style common arguments such as device_protocol and busy_retries. The lifecycle parser only added token_command, token_path, and bridge_timeout, so the default execution path raises AttributeError before any listener lifecycle validation can run. This is a host-side validation/availability regression rather than a direct exploitable security issue.
