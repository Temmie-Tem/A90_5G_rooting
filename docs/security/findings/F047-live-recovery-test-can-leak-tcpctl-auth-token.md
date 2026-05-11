# F047. Live recovery test can leak tcpctl auth token

## Metadata

| field | value |
|---|---|
| finding_id | `3e2d2646d61c819189e730e29dfc70b2` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/3e2d2646d61c819189e730e29dfc70b2 |
| severity | `high` |
| status | `confirmed-pending-patch` |
| detected_at | `2026-05-11T19:23:10.587898Z` |
| committed_at | `2026-05-11 21:46:35 +0900` |
| commit_hash | `d0e7956a28174a7dd8d80f1578f5888ce328b94f` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90_broker_recovery_tests.py` <br> `scripts/revalidation/a90_broker.py` <br> `stage3/linux_init/a90_tcpctl.c` <br> `scripts/revalidation/README.md` |
| source_csv | `docs/security/codex-security-findings-2026-05-11T19-48-19.047Z.csv` |

## CSV Description

The added recovery test starts an ncm-tcpctl broker pointed at TCP port 29999 and then issues a `run /cache/bin/toybox uptime` request to simulate a listener-down failure. In the existing broker backend, every `run` request requires auth: before sending the TCP payload, it obtains the real tcpctl token over ACM and prepends `auth <token>` to the payload. The new test does not first prove that port 29999 is closed, does not pass a dummy token, and does not expose/use a `--no-auth` option for this negative test. Therefore, if an attacker or an accidental service is reachable at `--device-ip:29999` when an operator runs the README-advertised `--include-live` test, that service receives the valid tcpctl token. That token can then authenticate to the real tcpctl service, which gates root `run`/`shutdown` operations.

## Local Initial Assessment

- Confirmed against current code: `a90_broker_recovery_tests.py` still starts `ncm-tcpctl` on hard-coded port `29999` and sends a `run` command without a dummy token/no-auth isolation. This belongs with broker/tcpctl auth hardening.

## Local Remediation

- Patch recovery live negative test to avoid retrieving/sending the real tcpctl token to an arbitrary listener; require a closed-port precheck or use explicit dummy/no-auth test mode that cannot leak production token.

## Codex Cloud Detail

Live recovery test can leak tcpctl auth token
Link: https://chatgpt.com/codex/cloud/security/findings/3e2d2646d61c819189e730e29dfc70b2?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: d0e7956
Author: shs02140@gmail.com
Created: 2026. 5. 12. 오전 4:23:10
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
A security bug was introduced by the new live recovery test. The underlying ncm-tcpctl backend already sends auth tokens for `run`, but this commit newly uses it against a hard-coded negative-test port without a dummy token or closed-port verification, creating a token disclosure path.
The added recovery test starts an ncm-tcpctl broker pointed at TCP port 29999 and then issues a `run /cache/bin/toybox uptime` request to simulate a listener-down failure. In the existing broker backend, every `run` request requires auth: before sending the TCP payload, it obtains the real tcpctl token over ACM and prepends `auth <token>` to the payload. The new test does not first prove that port 29999 is closed, does not pass a dummy token, and does not expose/use a `--no-auth` option for this negative test. Therefore, if an attacker or an accidental service is reachable at `--device-ip:29999` when an operator runs the README-advertised `--include-live` test, that service receives the valid tcpctl token. That token can then authenticate to the real tcpctl service, which gates root `run`/`shutdown` operations.

# Validation
## Rubric
- [x] Confirm the commit added/advertised live broker recovery testing: `git show --stat` shows `scripts/revalidation/a90_broker_recovery_tests.py` added and README updated.
- [x] Confirm the live listener-down test uses the ncm-tcpctl backend against hard-coded port 29999 and issues a `run /cache/bin/toybox uptime` request: `a90_broker_recovery_tests.py:279-288`.
- [x] Confirm the recovery runner has no exposed/passed dummy-token or no-auth option for this test: parser lines `59-72`, start command lines `86-108`; broker supports `--token/--no-auth` at `a90_broker.py:1017-1019` but the test omits them.
- [x] Confirm the backend authenticates `run` by retrieving an ACM token and prepending `auth <token>` before sending to the configured TCP endpoint: `a90_broker.py:263-305`.
- [x] Confirm the token is security-sensitive and dynamically disclosed to a listener on 29999 via the actual `--include-live` test path: `a90_tcpctl.c:283-305` and `405-407`; PoC captured `auth 0123456789ABCDEF0123456789ABCDEF` on `127.0.0.1:29999`.
## Report
Validated the finding at commit d0e7956a28174a7dd8d80f1578f5888ce328b94f. Crash/valgrind were not applicable/useful for this Python token-disclosure issue; `which valgrind` and `which gdb` produced no paths in the container, so I used a targeted live PoC plus non-interactive Python pdb tracing.

Static evidence: `scripts/revalidation/a90_broker_recovery_tests.py:59-72` exposes `--include-live` but no `--token`/`--no-auth`; `start_broker()` at `scripts/revalidation/a90_broker_recovery_tests.py:86-108` invokes `a90_broker.py serve` without passing broker `--token` or `--no-auth`; `run_ncm_down_test()` at `scripts/revalidation/a90_broker_recovery_tests.py:279-288` hard-codes `unused_port = 29999`, starts backend `ncm-tcpctl`, then calls `run /cache/bin/toybox uptime`. The backend at `scripts/revalidation/a90_broker.py:263-269` prepends `auth {self.get_token(...)}` before `sock.sendall(payload.encode())` for auth-requiring commands, and `get_token()` at `scripts/revalidation/a90_broker.py:287-305` obtains/parses `tcpctl_token=...` through ACM if no explicit token is configured. The broker CLI does support `--token` and `--no-auth` at `scripts/revalidation/a90_broker.py:1017-1019`, but the recovery test does not expose or pass them. The token is security-sensitive because `stage3/linux_init/a90_tcpctl.c:283-305` accepts it via `auth <token>`, and `stage3/linux_init/a90_tcpctl.c:405-407` rejects `run` unless authorized. The README advertises `python3 ./scripts/revalidation/a90_broker_recovery_tests.py --include-live` at `scripts/revalidation/README.md:228-232`.

Dynamic reproduction using the actual live recovery test path: I created `poc_live_recovery_token_leak.py`, which starts a fake ACM/cmdv1 bridge returning `tcpctl_token=0123456789ABCDEF0123456789ABCDEF` and an attacker-controlled listener on `127.0.0.1:29999`, then runs the real `a90_broker_recovery_tests.py --include-live --device-ip 127.0.0.1`. Output saved in `poc_output.txt` shows: `RETURN_CODE: 1`, `FAIL tests=5 failed=1 include_live=True`, and the attacker listener captured exactly:
`auth 0123456789ABCDEF0123456789ABCDEF\nrun /cache/bin/toybox uptime\n`
The recovery summary shows only the negative listener-down test failed because a listener was present: `ncm listener down transport-error` had `status=error`, and `ncm-down-response.json` contains `text: ERR malicious listener captured request`. This is the expected exploit condition: the supposed closed-port negative test instead sent an authenticated tcpctl payload to the process listening on the hard-coded port.

Debugger evidence: I also ran non-interactive pdb against `debug_tcpctl_request.py` with a breakpoint at `a90_broker.py:267`, immediately after the payload is constructed and before the TCP connection/send. `pdb_trace.txt` shows `DUMMY_ACM_ARGV=netservice token show`, then `p payload` returned `'auth DEADBEEFDEADBEEFDEADBEEFDEADBEEF\nrun /cache/bin/toybox uptime\n'`, and the listener captured `auth DEADBEEF...|run /cache/bin/toybox uptime|`. This traces the exact token-acquisition and send path in the backend.

# Evidence
scripts/revalidation/a90_broker_recovery_tests.py (L279 to 288)
  Note: The listener-down test hard-codes port 29999 and sends a `run` request through the ncm-tcpctl backend; if anything is listening there, the broker will send an authenticated tcpctl payload rather than merely observing a refused connection.
```
def run_ncm_down_test(args: argparse.Namespace, store: EvidenceStore) -> TestCaseResult:
    started = time.monotonic()
    runtime_dir = store.mkdir("ncm-down-runtime")
    socket_path = runtime_dir / DEFAULT_SOCKET_NAME
    unused_port = 29999
    process = start_broker(args, runtime_dir, backend="ncm-tcpctl", tcp_port=unused_port)
    artifacts: list[str] = []
    try:
        wait_for_socket(socket_path, process, args.ready_timeout)
        response = call(socket_path, ["run", "/cache/bin/toybox", "uptime"], args.timeout)
```

scripts/revalidation/a90_broker_recovery_tests.py (L59 to 72)
  Note: The new test runner exposes live NCM testing but provides no --token or --no-auth option that would let the negative listener-down test avoid using the real tcpctl token.
```
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run A90B1 broker recovery/failure tests.")
    parser.add_argument("--run-dir", type=Path,
                        default=Path("tmp") / f"a90-v192-broker-recovery-{timestamp()}")
    parser.add_argument("--bridge-host", default=DEFAULT_BRIDGE_HOST)
    parser.add_argument("--bridge-port", type=int, default=DEFAULT_BRIDGE_PORT)
    parser.add_argument("--device-ip", default=DEFAULT_DEVICE_IP)
    parser.add_argument("--tcp-port", type=int, default=DEFAULT_TCP_PORT)
    parser.add_argument("--tcp-timeout", type=float, default=DEFAULT_TCP_TIMEOUT)
    parser.add_argument("--expect-version", default=DEFAULT_EXPECT_VERSION)
    parser.add_argument("--include-live", action="store_true",
                        help="also run live ACM/NCM-path recovery checks")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--ready-timeout", type=float, default=5.0)
```

scripts/revalidation/a90_broker.py (L263 to 269)
  Note: For commands requiring auth, the broker prepends `auth <token>` and sends the resulting payload to the configured TCP endpoint.
```
    def tcpctl_request(self, command: str, timeout_sec: float) -> str:
        payload = command.rstrip("\n") + "\n"
        if not self.no_auth and self.command_requires_auth(command):
            payload = f"auth {self.get_token(timeout_sec)}\n{payload}"
        with socket.create_connection((self.device_ip, self.tcp_port), timeout=min(timeout_sec, self.tcp_timeout)) as sock:
            sock.settimeout(0.5)
            sock.sendall(payload.encode())
```

scripts/revalidation/a90_broker.py (L287 to 305)
  Note: If no explicit token is supplied, the broker retrieves the real tcpctl token from the device over ACM, so the new test can disclose the live credential.
```
    def get_token(self, timeout_sec: float) -> str:
        if self.token:
            return self.token
        token_request = BrokerRequest(
            request_id="ncm-token",
            client_id="broker",
            op="cmd",
            argv=list(DEFAULT_TOKEN_COMMAND),
            timeout_ms=int(timeout_sec * 1000),
            command_class="observe",
        )
        result = self.acm.execute(token_request)
        if result.rc != 0 or result.status != "ok":
            raise RuntimeError(f"token command failed rc={result.rc} status={result.status}\n{result.text}")
        match = re.search(r"tcpctl_token=([0-9A-Fa-f]{32})", result.text)
        if not match:
            raise RuntimeError(f"tcpctl token was not found in output:\n{result.text}")
        self.token = match.group(1)
        return self.token
```

scripts/revalidation/README.md (L228 to 232)
  Note: The README advertises running the new live recovery test without warning that the listener-down check may send the real token to the configured device IP and hard-coded port.
```
A90B1 broker recovery tests 예:

```bash
python3 ./scripts/revalidation/a90_broker_recovery_tests.py
python3 ./scripts/revalidation/a90_broker_recovery_tests.py --include-live
```

stage3/linux_init/a90_tcpctl.c (L283 to 305)
  Note: The leaked token is the credential accepted by tcpctl's auth command.
```
static int command_auth(int client_fd,
                        const struct tcpctl_server_config *config,
                        struct tcpctl_client_state *state,
                        char **argv,
                        int argc)
{
    char expected[128];

    if (!auth_required(config)) {
        state->authenticated = true;
        return send_text(client_fd, "OK auth-not-required\n");
    }
    if (argc != 2) {
        return send_text(client_fd, "ERR usage: auth <token>\n");
    }
    if (read_token_file(config->token_path, expected, sizeof(expected)) < 0) {
        return sendf(client_fd, "ERR auth-token-unavailable: %s\n", strerror(errno));
    }
    if (strcmp(argv[1], expected) != 0) {
        return send_text(client_fd, "ERR auth-failed\n");
    }
    state->authenticated = true;
    return send_text(client_fd, "OK authenticated\n");
```

stage3/linux_init/a90_tcpctl.c (L405 to 407)
  Note: tcpctl requires this authentication before executing `run`, making the leaked token security-sensitive.
```
    if (!client_authorized(config, state)) {
        return send_text(client_fd, "ERR auth-required\n");
    }
```

Proposed patch:
diff --git a/scripts/revalidation/a90_broker_recovery_tests.py b/scripts/revalidation/a90_broker_recovery_tests.py
index 17b554ae9ca34b7476356d4dc9eb638a60014509..6cb680f52e12a707d58fc66a321d54444539018b 100644
--- a/scripts/revalidation/a90_broker_recovery_tests.py
+++ b/scripts/revalidation/a90_broker_recovery_tests.py
@@ -59,106 +59,120 @@ def timestamp() -> str:
 def build_parser() -> argparse.ArgumentParser:
     parser = argparse.ArgumentParser(description="Run A90B1 broker recovery/failure tests.")
     parser.add_argument("--run-dir", type=Path,
                         default=Path("tmp") / f"a90-v192-broker-recovery-{timestamp()}")
     parser.add_argument("--bridge-host", default=DEFAULT_BRIDGE_HOST)
     parser.add_argument("--bridge-port", type=int, default=DEFAULT_BRIDGE_PORT)
     parser.add_argument("--device-ip", default=DEFAULT_DEVICE_IP)
     parser.add_argument("--tcp-port", type=int, default=DEFAULT_TCP_PORT)
     parser.add_argument("--tcp-timeout", type=float, default=DEFAULT_TCP_TIMEOUT)
     parser.add_argument("--expect-version", default=DEFAULT_EXPECT_VERSION)
     parser.add_argument("--include-live", action="store_true",
                         help="also run live ACM/NCM-path recovery checks")
     parser.add_argument("--timeout", type=float, default=5.0)
     parser.add_argument("--ready-timeout", type=float, default=5.0)
     return parser
 
 
 def broker_script() -> Path:
     return SCRIPT_DIR / "a90_broker.py"
 
 
 def start_broker(args: argparse.Namespace,
                  runtime_dir: Path,
                  *,
                  backend: str,
-                 tcp_port: int | None = None) -> subprocess.Popen[str]:
+                 tcp_port: int | None = None,
+                 token: str | None = None,
+                 no_auth: bool = False) -> subprocess.Popen[str]:
     ensure_private_dir(runtime_dir)
     command = [
         sys.executable,
         str(broker_script()),
         "serve",
         "--backend",
         backend,
         "--runtime-dir",
         str(runtime_dir),
         "--socket-name",
         DEFAULT_SOCKET_NAME,
         "--audit-name",
         DEFAULT_AUDIT_NAME,
         "--bridge-host",
         args.bridge_host,
         "--bridge-port",
         str(args.bridge_port),
         "--device-ip",
         args.device_ip,
         "--tcp-port",
         str(args.tcp_port if tcp_port is None else tcp_port),
         "--tcp-timeout",
         str(args.tcp_timeout),
     ]
+    if token:
+        command.extend(["--token", token])
+    if no_auth:
+        command.append("--no-auth")
     return subprocess.Popen(
         command,
         cwd=REPO_ROOT,
         stdout=subprocess.PIPE,
         stderr=subprocess.PIPE,
         text=True,
         start_new_session=True,
     )
 
 
 def stop_broker(process: subprocess.Popen[str] | None) -> tuple[str, str]:
     if process is None:
         return "", ""
     if process.poll() is None:
         try:
             os.killpg(process.pid, signal.SIGTERM)
         except ProcessLookupError:
             pass
         try:
             return process.communicate(timeout=2.0)
         except subprocess.TimeoutExpired:
             try:
                 os.killpg(process.pid, signal.SIGKILL)
             except ProcessLookupError:
                 pass
     try:
         return process.communicate(timeout=2.0)
     except subprocess.TimeoutExpired:
         return "", "broker output collection timed out\n"
 
 
+def is_tcp_port_open(host: str, port: int, timeout_sec: float = 0.2) -> bool:
+    try:
+        with socket.create_connection((host, port), timeout=timeout_sec):
+            return True
+    except OSError:
+        return False
+
+
 def wait_for_socket(socket_path: Path, process: subprocess.Popen[str], timeout_sec: float) -> None:
     deadline = time.monotonic() + timeout_sec
     while time.monotonic() < deadline:
         if process.poll() is not None:
             raise RuntimeError(f"broker exited before ready rc={process.returncode}")
         if socket_path.exists():
             try:
                 with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                     client.settimeout(0.2)
                     client.connect(str(socket_path))
                 return
             except OSError:
                 pass
         time.sleep(0.05)
     raise RuntimeError(f"socket not ready: {socket_path}")
 
 
 def request(argv: list[str], *, timeout_ms: int = 2000) -> dict[str, Any]:
     return {
         "proto": PROTO,
         "id": f"v192-{uuid.uuid4().hex[:12]}",
         "client_id": f"v192:{os.getpid()}",
         "op": "cmd",
         "argv": argv,
         "timeout_ms": timeout_ms,
@@ -259,52 +273,62 @@ def run_stale_path_test(args: argparse.Namespace, store: EvidenceStore) -> TestC
         "--backend",
         "fake",
         "--runtime-dir",
         str(runtime_dir),
     ]
     result = subprocess.run(
         command,
         cwd=REPO_ROOT,
         check=False,
         text=True,
         stdout=subprocess.PIPE,
         stderr=subprocess.STDOUT,
         timeout=5,
     )
     store.write_text("stale-path-output.txt", result.stdout)
     ok = result.returncode != 0 and "refusing to replace non-socket path" in result.stdout
     detail = f"rc={result.returncode}"
     return TestCaseResult("stale non-socket path refusal", ok, detail, time.monotonic() - started, ["stale-path-output.txt"])
 
 
 def run_ncm_down_test(args: argparse.Namespace, store: EvidenceStore) -> TestCaseResult:
     started = time.monotonic()
     runtime_dir = store.mkdir("ncm-down-runtime")
     socket_path = runtime_dir / DEFAULT_SOCKET_NAME
     unused_port = 29999
-    process = start_broker(args, runtime_dir, backend="ncm-tcpctl", tcp_port=unused_port)
     artifacts: list[str] = []
+    if is_tcp_port_open(args.device_ip, unused_port):
+        detail = f"refusing test: {args.device_ip}:{unused_port} is reachable; token disclosure risk"
+        return TestCaseResult("ncm listener down transport-error", False, detail, time.monotonic() - started, artifacts)
+
+    process = start_broker(
+        args,
+        runtime_dir,
+        backend="ncm-tcpctl",
+        tcp_port=unused_port,
+        token="0" * 32,
+    )
     try:
         wait_for_socket(socket_path, process, args.ready_timeout)
         response = call(socket_path, ["run", "/cache/bin/toybox", "uptime"], args.timeout)
         store.write_json("ncm-down-response.json", response)
         artifacts.append("ncm-down-response.json")
         audit = collect_audit(store, runtime_dir, "ncm-down")
         ok = (
             response.get("ok") is False and
             response.get("status") == "transport-error" and
             audit is not None and
             audit["status_counts"].get("transport-error") == 1
         )
         detail = f"status={response.get('status')} error={response.get('error')}"
         return TestCaseResult("ncm listener down transport-error", ok, detail, time.monotonic() - started, artifacts)
     finally:
         stdout, stderr = stop_broker(process)
         if stdout:
             store.write_text("ncm-down-stdout.txt", stdout)
         if stderr:
             store.write_text("ncm-down-stderr.txt", stderr)
 
 
 def run_acm_fallback_test(args: argparse.Namespace, store: EvidenceStore) -> TestCaseResult:
     started = time.monotonic()
     runtime_dir = store.mkdir("acm-fallback-runtime")

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
The original high severity is retained. The vulnerability is in an in-scope documented operations path, and the data exposed is a real tcpctl credential that gates root run/shutdown operations. The validation evidence included an executable reproduction of the actual live recovery path capturing an auth <token> payload at port 29999. The main mitigating factors are strong preconditions: --include-live is opt-in, the service is lab/NCM-local rather than public, and an attacker must control or observe the configured negative-test endpoint. Those factors make likelihood low, but the impact is full privileged tcpctl access, which is sufficient for high severity in this repository's device-control threat model.
## Likelihood
low - Exploitation is not internet-exposed and is not zero-click. It requires the operator to run the optional --include-live test and the attacker to control or observe a service at the configured device IP on port 29999, or otherwise be on-path in the lab NCM setup. These are plausible in shared or misconfigured lab workflows but not generally easy.
## Impact
high - The disclosed value is the tcpctl authentication token. Static code shows tcpctl accepts that token via auth <token> and rejects run unless authorized; in this project, tcpctl run is a privileged root device-control operation. A captured token can therefore enable root command execution or shutdown through the intended tcpctl interface.
## Assumptions
- An operator runs the README-advertised live recovery test with --include-live against a live device/control setup.
- An attacker can control, observe, or intercept a service reachable at the configured --device-ip on TCP port 29999, or the operator points --device-ip at an attacker-controlled endpoint.
- The broker can obtain the real tcpctl token through the ACM path using netservice token show.
- The leaked token remains valid long enough for the attacker to connect to the real tcpctl service on port 2325.
- operator interaction: run scripts/revalidation/a90_broker_recovery_tests.py --include-live
- live ACM/NCM setup available
- attacker-controlled or attacker-observable listener at configured device-ip:29999
- real tcpctl service reachable by attacker after token disclosure
## Path
operator --include-live
  -> run_ncm_down_test(port 29999)
  -> ncm-tcpctl broker without --no-auth/--token
  -> ACM netservice token show
  -> send 'auth <token>\nrun ...' to device-ip:29999
  -> attacker listener captures token
  -> attacker authenticates to tcpctl:2325 for root run/shutdown
## Path evidence
- `scripts/revalidation/a90_broker_recovery_tests.py:59-72` - The test runner advertises --include-live but provides no --token or --no-auth option for live negative tests.
- `scripts/revalidation/a90_broker_recovery_tests.py:80-108` - start_broker invokes a90_broker.py serve and passes bridge/device/tcp settings, but does not pass broker --token or --no-auth despite the broker supporting them.
- `scripts/revalidation/a90_broker_recovery_tests.py:279-288` - The listener-down test hard-codes unused_port = 29999 and sends a run command through the ncm-tcpctl backend.
- `scripts/revalidation/a90_broker.py:263-269` - tcpctl_request prefixes auth <token> for auth-required commands and sends the resulting payload to the configured TCP endpoint.
- `scripts/revalidation/a90_broker.py:287-305` - If no explicit token is configured, get_token obtains the real tcpctl token from the device over ACM and caches it.
- `scripts/revalidation/a90_broker.py:1012-1019` - The underlying broker CLI supports --token and --no-auth, showing safer controls exist but are not exposed by the recovery test.
- `stage3/linux_init/a90_tcpctl.c:283-305` - tcpctl's auth command accepts the token from the configured token file and marks the client authenticated.
- `stage3/linux_init/a90_tcpctl.c:405-407` - tcpctl refuses run when the client is not authorized, proving the leaked value is a meaningful privilege-bearing credential.
- `stage3/linux_init/a90_netservice.c:304-314` - netservice starts a90_tcpctl with the configured token path, making token authentication part of the deployed service.
- `stage3/linux_init/a90_config.h:31-38` - The real NCM service uses device IP 192.168.7.2, TCP port 2325, and /cache/native-init-tcpctl.token.
- `scripts/revalidation/README.md:228-232` - The README advertises running the live recovery test with --include-live.
## Narrative
The finding is real and reachable in the documented live recovery workflow. The recovery test exposes --include-live but does not expose or pass --token/--no-auth. When --include-live is used, run_ncm_down_test starts ncm-tcpctl against hard-coded port 29999 and sends run /cache/bin/toybox uptime. The broker backend treats run as auth-required, obtains the real token over ACM, prefixes auth <token>, and sends the payload to the configured TCP endpoint. If an attacker controls or observes device-ip:29999, the token is disclosed. That token is security-sensitive because tcpctl compares auth <token> against the token file and refuses run unless the client is authorized. Severity remains high in this repository's lab-control threat model because successful exploitation converts a local/NCM-positioned attacker into an authenticated root tcpctl client, but likelihood is low because it requires operator interaction and control or observation of the negative-test endpoint.
## Controls
- tcpctl requires auth for run/shutdown when started with a token path
- netservice token file is written 0600 with O_NOFOLLOW
- default bridge host is 127.0.0.1
- NCM tcpctl is an internal USB/lab network service rather than public internet exposure
- --include-live is opt-in
- broker supports --token and --no-auth, but the recovery test fails to expose or use those controls
## Blindspots
- Static analysis cannot prove how often operators run --include-live or whether their actual NCM topology permits an attacker to observe device-ip:29999.
- The provided validation PoC demonstrates token disclosure through the live recovery code path using a fake ACM bridge and listener; it does not show a full post-disclosure command execution against real hardware.
- Token lifetime and rotation behavior after the live test were inferred from repository code, not observed on a physical device in this analysis.
- No cloud, Kubernetes, or load-balancer artifacts are present for this finding; exposure is limited to repository code and documented lab operations.

