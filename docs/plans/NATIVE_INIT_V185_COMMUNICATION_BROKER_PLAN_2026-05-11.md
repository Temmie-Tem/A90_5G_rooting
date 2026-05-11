# A90 v185 Communication Broker Protocol Plan

Date: `2026-05-11`
Baseline device build: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v185` host protocol/broker design, not a native-init boot image
Device flash: none
Parent roadmap: post-`v184` serverization readiness follow-up

## Summary

v185 moves the next work item from Wi-Fi bring-up to communication control
hardening. The current USB ACM serial bridge is stable as a rescue/control path,
but it is still a single byte stream with one TCP client and one foreground
device shell loop. It is not a safe multi-client control plane.

The v185 objective is to define an `A90B1` broker protocol and host-side broker
boundary before adding wider network access. The broker becomes the single owner
of serial/NCM transports, serializes unsafe commands, routes responses by
request id, and gives future harnesses one consistent API.

## Current Control Paths

- USB ACM rescue path:
  - device shell over `/dev/ttyGS0`
  - host `serial_tcp_bridge.py` on `127.0.0.1:54321`
  - current bridge uses one accepted client and one serial stream
- Framed shell protocol:
  - `cmdv1` / `cmdv1x`
  - `A90P1 BEGIN` / `A90P1 END`
  - host wrapper: `scripts/revalidation/a90ctl.py`
- NCM/TCP operational path:
  - USB NCM device IP `192.168.7.2`
  - host IP `192.168.7.1`
  - token-authenticated `a90_tcpctl` on port `2325`
- Remote shell path:
  - token-authenticated `a90_rshell`
  - explicit operator shell, not the default automation RPC path

## Problem Statement

The physical ACM channel is bidirectional, but the project protocol currently
uses it as a sequential 1:1 request/response stream. That is appropriate for
rescue and deterministic bring-up, but it creates avoidable risk when multiple
host tools, observers, security scans, long-soak collectors, and operator
commands all want to talk to the device.

The missing pieces are:

- request identity at the host API layer
- client identity and ownership
- response routing for concurrent host clients
- command class policy before dispatch
- explicit exclusive locks for dangerous/rebind commands
- cancellation/deadline semantics
- transport fallback policy between ACM and NCM/TCP
- unified audit evidence for every host-side control request

## Design Principles

- ACM serial remains the rescue channel.
- The bridge must not become a public multi-client root shell.
- A broker owns each physical transport; user tools do not write serial/NCM
  directly during broker-managed runs.
- Read-only observation commands may be queued and retried safely.
- Operator-action commands are serialized.
- Exclusive/destructive/rebind commands require an exclusive lock or foreground
  raw-control path.
- Wi-Fi or non-USB exposure must not start until broker policy, auth, bind, and
  audit behavior are testable.

## Proposed Broker Protocol

The initial protocol is host-local `A90B1`. It wraps existing device protocols
instead of replacing `A90P1` on-device in v185.

Request example:

```json
{"proto":"A90B1","id":"req-001","op":"cmd","argv":["status"],"timeout_ms":10000,"class":"observe"}
```

Response example:

```json
{"proto":"A90B1","id":"req-001","ok":true,"rc":0,"status":"ok","duration_ms":42,"backend":"acm-cmdv1","text":"..."}
```

Event example:

```json
{"proto":"A90B1","type":"event","source":"broker","level":"warn","message":"serial reconnect"}
```

The first implementation should expose this through a private local endpoint:

- preferred: Unix domain socket under a private runtime directory
- acceptable fallback: `127.0.0.1` TCP with explicit bind and owner-only runtime
  directory

## Command Classes

### Observe

Examples:

- `version`
- `status`
- `bootstatus`
- `selftest verbose`
- `pid1guard`
- `storage`
- `mountsd status`
- `netservice status`
- `exposure`
- `policycheck`

Behavior:

- safe to retry on bridge reconnect
- may be queued behind an exclusive command
- should never mutate device state

### Operator Action

Examples:

- `screenmenu`
- `hide`
- `autohud 2`
- `longsoak start`
- `longsoak stop`

Behavior:

- serialized
- normally no automatic retry unless the command is explicitly marked idempotent
- produces audit records

### Exclusive

Examples:

- `run ...`
- `cpustress ...`
- storage I/O workload commands
- NCM setup/stop
- `usbacmreset`
- helper deployment

Behavior:

- requires exclusive transport lock
- blocks or rejects concurrent mutating commands
- observation commands may be allowed only when the device path is known safe

### Rebind / Destructive

Examples:

- `recovery`
- `reboot`
- `poweroff`
- USB gadget rebind commands
- future Wi-Fi enable/disable commands

Behavior:

- not multiplexed
- no automatic retry
- explicit foreground/raw-control execution with operator-visible state

## Transport Backends

### `acm-cmdv1`

Primary rescue/control backend. Uses `serial_tcp_bridge.py` and
`run_cmdv1_command()` with `A90P1` parsing. It remains the safest default for
boot recovery and first contact.

### `ncm-tcpctl`

Operational backend after NCM is up and token authentication is available. It is
preferred for long-running serverization validation, but must remain USB-local
unless a later network exposure gate explicitly changes that policy.

### `rshell`

Interactive token-authenticated shell backend. It is intentionally not the
default automation RPC channel.

### `local-observer`

Host-only evidence reader for bundle/status files. It does not send device
commands and can be used by the broker for status pages and audit summaries.

## v185 Deliverables

This v185 cycle is a design and implementation-readiness milestone.

- this plan document
- task queue update selecting broker work before Wi-Fi refresh
- a stable `A90B1` request/response schema
- command-class policy table draft
- implementation split for v186-v190
- no native init version bump
- no boot image rebuild

## v186-v190 Implementation Split

### v186: Host Broker Skeleton

- add `scripts/revalidation/a90_broker.py`
- private runtime directory and endpoint
- single worker queue
- fake backend tests
- `acm-cmdv1` backend wrapper around `run_cmdv1_command()`
- request id, deadline, command class, and audit JSONL

### v187: Harness Integration

- add broker backend to shared host device client
- move observer/supervisor read-only calls through broker
- verify concurrent read-only clients do not contend for raw serial

### v188: NCM/TCP Backend

- add authenticated `ncm-tcpctl` backend selection
- prefer NCM for supported commands when NCM is ready
- retain ACM fallback for rescue and boot-time checks

### v189: Locking, Cancellation, and Failure Classification

- exclusive command lock
- cancellation token
- timeout classification
- serial reconnect classification
- structured `busy`, `transport-down`, `auth-failed`, `device-error`, and
  `operator-required` statuses

### v190: Broker Mixed-Soak Gate

- run observer, workload clients, and operator-style commands through broker
- prove no raw bridge contention during mixed-soak
- produce broker audit bundle
- use this as the next prerequisite before Wi-Fi/server-style exposure work

## Test Plan

### Documentation Checks

```bash
git diff --check
rg -n "v185|A90B1|broker|Communication Broker" \
  docs/plans/NATIVE_INIT_V185_COMMUNICATION_BROKER_PLAN_2026-05-11.md \
  docs/plans/NATIVE_INIT_NEXT_WORK_2026-04-25.md \
  docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md
```

### v186 Static Tests

When implementation starts:

```bash
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/serial_tcp_bridge.py \
  scripts/revalidation/tcpctl_host.py \
  scripts/revalidation/a90_broker.py
```

Required unit coverage:

- request id is preserved from request to response
- FIFO order is preserved for one backend worker
- unsafe command is rejected or locked while another exclusive command is active
- read-only commands retry only under the existing safe retry policy
- broker emits audit events for accept, dispatch, result, timeout, and reconnect

### v186-v190 Device Smoke

The first real-device smoke should not rebuild the device image:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py selftest verbose
```

Then repeat the same commands through the broker endpoint and verify identical
device-visible results.

## Acceptance Criteria

- Existing `a90ctl.py` direct path remains usable for rescue.
- Broker can serve at least two host clients issuing read-only commands without
  interleaving serial bytes.
- Broker refuses or serializes mutating commands according to command class.
- Broker records audit JSONL with request id, client id, backend, command class,
  rc/status, duration, and error classification.
- No public listener is introduced.
- No Wi-Fi bring-up, rfkill write, module load/unload, partition write, or
  watchdog open is performed.

## Non-Goals

- no native init version bump
- no boot image generation
- no replacement of on-device `A90P1`
- no ADB revival
- no Wi-Fi bring-up
- no public network exposure
- no full remote shell replacement

## Assumptions

- v184 24h serverization readiness passed, but that does not make current serial
  tooling multi-client safe.
- Fresh security scan and patch-effect confirmation may continue in parallel.
- Security findings take priority if they expose a high-risk listener, auth, path,
  or artifact handling issue.
- The broker is an enabling layer for later Wi-Fi/server work, not a serverization
  approval by itself.
