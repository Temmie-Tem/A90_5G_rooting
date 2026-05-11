# F052. NCM broker treats auth OK as command success

## Metadata

| field | value |
|---|---|
| finding_id | `94ed5ca8246481919bcb415840c3e58f` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/94ed5ca8246481919bcb415840c3e58f |
| severity | `medium` |
| status | `mitigated-host-batch-h1` |
| detected_at | `2026-05-11T19:22:42.006948Z` |
| committed_at | `2026-05-11 21:41:54 +0900` |
| commit_hash | `a801e4598e6e0cb139feca259d71b8f34e0b768d` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90_broker.py` <br> `stage3/linux_init/a90_tcpctl.c` |
| source_csv | `docs/security/codex-security-findings-2026-05-11T19-48-19.047Z.csv` |

## CSV Description

The newly added NcmTcpctlBackend sends an auth line before run commands by default, then determines success by checking whether the entire tcpctl response contains "\nOK" anywhere or ends with "OK". a90_tcpctl responds to a valid auth command with "OK authenticated\n" and then continues to execute the requested run command. Therefore, if authentication succeeds, a later failing run response such as "[exit 1]\nERR exit=1\n" is still classified by the broker as rc=0/status=ok because the earlier auth acknowledgement satisfies the substring test. This corrupts broker results and audit records for the new NCM backend: failed root commands can be reported as successful, non_ok_results can stay zero, and automation may proceed based on a false PASS. The check should parse the final tcpctl command trailer instead, e.g. require the last non-empty protocol line to be exactly OK for the run command and treat final ERR lines as failures.

## Local Initial Assessment

- Confirmed against current code: `NcmTcpctlBackend.tcpctl_status()` still accepts any `\nOK` in the combined response. An `OK authenticated` line can mask a later `ERR exit=N` trailer.

## Local Remediation

- Implemented in Batch H1; see `docs/security/SECURITY_FINDINGS_F047_F053_H1_REPORT_2026-05-12.md`. The NCM tcpctl backend now parses the final non-empty tcpctl trailer and treats final `ERR ...` as failure.

## Codex Cloud Detail

NCM broker treats auth OK as command success
Link: https://chatgpt.com/codex/cloud/security/findings/94ed5ca8246481919bcb415840c3e58f?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: a801e45
Author: shs02140@gmail.com
Created: 2026. 5. 12. 오전 4:22:42
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
A security-relevant integrity bug was introduced in the new NcmTcpctlBackend. The bug is not in the basic TCP connection code; it is in the response-success parser added by this commit. Because the backend prepends an auth command and then searches the whole combined response for any OK marker, the auth success marker masks later command failure.
The newly added NcmTcpctlBackend sends an auth line before run commands by default, then determines success by checking whether the entire tcpctl response contains "\nOK" anywhere or ends with "OK". a90_tcpctl responds to a valid auth command with "OK authenticated\n" and then continues to execute the requested run command. Therefore, if authentication succeeds, a later failing run response such as "[exit 1]\nERR exit=1\n" is still classified by the broker as rc=0/status=ok because the earlier auth acknowledgement satisfies the substring test. This corrupts broker results and audit records for the new NCM backend: failed root commands can be reported as successful, non_ok_results can stay zero, and automation may proceed based on a false PASS. The check should parse the final tcpctl command trailer instead, e.g. require the last non-empty protocol line to be exactly OK for the run command and treat final ERR lines as failures.

# Validation
## Rubric
- [x] Confirm NcmTcpctlBackend maps an absolute-path run request to a tcpctl run command rather than ACM fallback.
- [x] Confirm default NCM behavior prepends auth before run when no_auth is false.
- [x] Confirm actual a90_tcpctl emits an auth success line containing OK and continues to process the following run command on the same connection.
- [x] Confirm a failing child command produces a final ERR trailer, specifically ERR exit=1 for /bin/false.
- [x] Confirm the backend parser evaluates the combined response globally and returns rc=0/status=ok, which the broker would report/audit as ok.
## Report
Validated the finding against the checked-out commit a801e4598e6e0cb139feca259d71b8f34e0b768d. I built the actual tcpctl server from stage3/linux_init/a90_tcpctl.c with debug symbols and ran a PoC that starts it with auth required, then calls scripts/revalidation/a90_broker.py::NcmTcpctlBackend.execute() for argv=["run", "/bin/false"]. The real tcpctl response was: a90_tcpctl v1 ready / OK authenticated / [pid ...] / [exit 1] / ERR exit=1. Despite the final protocol line being ERR exit=1, the backend returned rc=0 and status=ok. This matches the suspected parser bug at scripts/revalidation/a90_broker.py:248-255, where line 253 checks the whole response for any "\nOK" or trailing OK. The auth prefix is added at scripts/revalidation/a90_broker.py:263-266 for run commands when no_auth is false. The C endpoint emits OK authenticated at stage3/linux_init/a90_tcpctl.c:304-305, continues processing subsequent commands on the same connection at stage3/linux_init/a90_tcpctl.c:576-586, and reports failed child exits as ERR exit=N at stage3/linux_init/a90_tcpctl.c:360-369. A non-interactive pdb-based trace stopped at a90_broker.py:253 and captured: contains_newline_OK=true, endswith_OK=false, final_line="ERR exit=1"; execution then returned rc=0/status=ok. BrokerServer would convert that BackendResult into ok=true at scripts/revalidation/a90_broker.py:572-581 and audit it as ok at scripts/revalidation/a90_broker.py:603-615. Direct crash reproduction was attempted but no crash is expected because this is an integrity/parser bug. Valgrind was unavailable in the container; an ASan build of a90_tcpctl reproduced the same false-success behavior without sanitizer findings. gdb was unavailable, so I used a non-interactive Python pdb trace for the parser condition.

# Evidence
scripts/revalidation/a90_broker.py (L248 to 255)
  Note: The newly introduced NCM backend classifies the whole tcpctl response as successful if it contains any newline-prefixed OK, not if the run command's final status is OK.
```
    def execute(self, request: BrokerRequest) -> BackendResult:
        command = self.tcpctl_command(request.argv)
        if command is None:
            return self.acm.execute(request)
        text = self.tcpctl_request(command, request.timeout_ms / 1000.0)
        if "\nOK" not in text and not text.rstrip().endswith("OK"):
            return BackendResult(1, "error", text, self.name)
        return BackendResult(0, "ok", text, self.name)
```

scripts/revalidation/a90_broker.py (L263 to 267)
  Note: By default the backend prepends an auth command before run, so the combined response will include an auth acknowledgement before the actual command result.
```
    def tcpctl_request(self, command: str, timeout_sec: float) -> str:
        payload = command.rstrip("\n") + "\n"
        if not self.no_auth and self.command_requires_auth(command):
            payload = f"auth {self.get_token(timeout_sec)}\n{payload}"
        with socket.create_connection((self.device_ip, self.tcp_port), timeout=min(timeout_sec, self.tcp_timeout)) as sock:
```

stage3/linux_init/a90_tcpctl.c (L304 to 305)
  Note: a90_tcpctl emits 'OK authenticated' after successful auth, which satisfies the broker's broad substring success test before the run result is known.
```
    state->authenticated = true;
    return send_text(client_fd, "OK authenticated\n");
```

stage3/linux_init/a90_tcpctl.c (L360 to 369)
  Note: Failed child commands are reported with an ERR trailer, but the new broker backend can ignore this because an earlier auth OK already matched.
```
static int report_child_status(int client_fd, int status)
{
    if (WIFEXITED(status)) {
        int code = WEXITSTATUS(status);

        sendf(client_fd, "[exit %d]\n", code);
        if (code == 0) {
            return send_text(client_fd, "OK\n");
        }
        return sendf(client_fd, "ERR exit=%d\n", code);
```

stage3/linux_init/a90_tcpctl.c (L576 to 586)
  Note: After auth succeeds, a90_tcpctl continues to process the following run command on the same connection, so auth OK and run result appear in one combined response.
```
        if (strcmp(argv[0], "auth") == 0) {
            if (command_auth(client_fd, config, &state, argv, argc) < 0) {
                return -1;
            }
            if (!state.authenticated && auth_required(config)) {
                return 0;
            }
            continue;
        }
        if (strcmp(argv[0], "run") == 0) {
            return command_run(client_fd, config, &state, argv, argc);
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: low | Policy adjusted: low
## Rationale
Severity remains medium. Static evidence and prior executable PoC show the parser bug is real: the broker prepends auth, a90_tcpctl returns 'OK authenticated', a later failed run returns final 'ERR exit=N', and the broker still returns rc=0/status=ok because it searches the combined response for any OK marker. The affected component is in scope because it is active host-side revalidation/control tooling for the documented USB NCM tcpctl path. However, the impact is workflow/audit integrity rather than direct privilege escalation or new remote command execution, and reachability is constrained to a host-local/private broker and lab-local NCM device-control setup. Those factors support medium, not high or critical.
## Likelihood
medium - The bug is easy to trigger during normal authenticated ncm-tcpctl use with any non-zero run command, and validation reproduced it. Exploitation as an attacker is constrained by the host-local/private broker socket, lab USB NCM reachability, and need to influence broker requests or the tcpctl endpoint, so it is not internet/publicly likely.
## Impact
medium - Impact is integrity loss in a privileged device-control workflow: a failed root command can be reported and audited as successful, causing false PASS results and potentially unsafe downstream actions. It does not itself grant new root execution, expose broad secrets, or bypass authentication; the rooted command channel is already intended and authenticated in this path.
## Assumptions
- The ncm-tcpctl broker backend is used in the documented host-local A90B1 broker workflow.
- The tcpctl listener is reachable over the lab USB NCM path, normally 192.168.7.2:2325.
- Authentication succeeds, either because the operator supplied --token or the broker retrieved the token from the device through the ACM fallback path.
- A broker caller or automation issues a run command whose child process exits non-zero, or a malicious/spoofed endpoint returns an auth OK followed by a final command ERR.
- a90_broker.py served with --backend ncm-tcpctl
- tcpctl auth succeeds for a run or shutdown-class command
- the subsequent run command fails or returns a final ERR trailer
- downstream automation, CLI exit status, or audit report relies on broker ok/rc/status
## Path
broker client
  -> a90_broker NcmTcpctlBackend
      -> auth <token> + run /path over USB NCM tcpctl
          -> OK authenticated
          -> [exit 1] / ERR exit=1
      -> parser sees earlier \nOK
  -> rc=0,status=ok,audit ok=true
## Path evidence
- `scripts/revalidation/a90_broker.py:248-255` - NcmTcpctlBackend executes tcpctl requests and incorrectly checks the whole response for any '\nOK' or trailing OK before returning rc=0/status=ok.
- `scripts/revalidation/a90_broker.py:263-266` - For auth-required commands, the backend prepends an auth line before the run command, creating a combined auth+run response.
- `scripts/revalidation/a90_broker.py:282-285` - run and shutdown commands are considered auth-required, so the vulnerable auth-prefix behavior applies to the relevant run path by default.
- `stage3/linux_init/a90_tcpctl.c:300-305` - a90_tcpctl returns 'OK authenticated' after successful token authentication, which satisfies the broker's broad OK search.
- `stage3/linux_init/a90_tcpctl.c:360-370` - Failed child commands are represented by a final 'ERR exit=N' trailer after an '[exit N]' line.
- `stage3/linux_init/a90_tcpctl.c:576-586` - After auth succeeds, the server continues reading commands on the same connection and then dispatches run, so auth and run results appear in one response stream.
- `scripts/revalidation/a90_broker.py:572-581` - BrokerServer maps BackendResult rc=0/status=ok into response ok=true.
- `scripts/revalidation/a90_broker.py:603-615` - The broker audit record stores the corrupted ok/rc/status values.
- `scripts/revalidation/a90_broker.py:770-813` - Audit reporting computes non_ok_results from ok=false records, so falsely ok results can keep non_ok_results at zero.
- `scripts/revalidation/a90_broker.py:645-650` - The broker listens on a Unix domain socket and chmods it 0600, limiting exposure to local/same-user host contexts.
- `scripts/revalidation/a90_broker.py:1007-1020` - The ncm-tcpctl backend is a documented serve mode with NCM/tcpctl options, confirming operational reachability.
- `docs/reports/NATIVE_INIT_V191_NCM_TCPCTL_BROKER_BACKEND_2026-05-11.md:10-15` - Project documentation describes ncm-tcpctl as an A90B1 broker backend for token-authenticated NCM run requests.
## Narrative
The finding is real and in scope. NcmTcpctlBackend turns absolute-path broker run requests into tcpctl run commands, prepends auth by default, and then treats the entire combined response as successful if it contains any newline-prefixed OK or ends with OK. a90_tcpctl emits 'OK authenticated' for a valid auth command and then continues processing the subsequent run command on the same connection. Failed children emit '[exit N]' followed by 'ERR exit=N'. Therefore a normal authenticated failing run can be classified by the broker as rc=0/status=ok, and BrokerServer then records ok=true. This does not create new code execution beyond the intended rooted command channel, but it is a security-relevant control/audit integrity issue in the documented lab automation path.
## Controls
- Broker runtime directory is created private and broker Unix socket is chmod 0600.
- tcpctl run commands require absolute paths.
- Authenticated tcpctl mode is supported and used by default by the broker unless --no-auth is supplied.
- The tcpctl token is redacted/validated by pattern in broker CLI/audit helpers, but the protocol itself is plaintext on the lab NCM link.
- Netservice/NCM operation is opt-in in the broader project workflow.
- Existing controls do not prevent this issue because the vulnerable success parser accepts the auth OK as if it were the run command success.
## Blindspots
- Static repository review cannot determine how often operators deploy the ncm-tcpctl backend in real environments.
- No live cloud, CI, or device network exposure was inspected; assessment relies on repository defaults and documentation.
- Actual exploitability by a third party depends on local host access, broker socket permissions, USB NCM topology, or ability to spoof/control the tcpctl endpoint.
- Downstream automation consequences depend on external operator scripts and processes that consume broker audit PASS/ok results.

