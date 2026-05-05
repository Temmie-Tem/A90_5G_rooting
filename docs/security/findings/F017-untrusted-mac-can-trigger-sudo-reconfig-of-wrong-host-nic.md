# F017. Untrusted MAC can trigger sudo reconfig of wrong host NIC

## Metadata

| field | value |
|---|---|
| finding_id | `76510c5c6fe88191934b0a8170f4c25a` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/76510c5c6fe88191934b0a8170f4c25a |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-04-28T06:45:57.155591Z` |
| committed_at | `2026-04-26 02:02:10 +0900` |
| commit_hash | `8d58ee16a7b1de4d4d2d4659ee1cb772bf4ab0a4` |
| relevant_paths | `scripts/revalidation/netservice_reconnect_soak.py` |
| has_patch | `false` |

## CSV Description

In `netservice_reconnect_soak.py`, host interface selection is driven by `ncm.host_addr` parsed from device command output (`run /cache/bin/a90_usbnet status`). That value is then used to find a local interface by MAC and run privileged host commands (`ip addr replace`, `ip link set`) via sudo, without an interface allowlist or USB/NCM origin verification. A malicious or compromised device can report a MAC matching another host NIC (e.g., management LAN), causing unintended privileged reconfiguration and potential connectivity loss or traffic-path manipulation.

## Codex Cloud Detail

Untrusted MAC can trigger sudo reconfig of wrong host NIC
Link: https://chatgpt.com/codex/cloud/security/findings/76510c5c6fe88191934b0a8170f4c25a?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 8d58ee1
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 3:45:57
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Security bug introduced: newly added script creates a confused-deputy path where untrusted device metadata controls privileged host networking actions.
In `netservice_reconnect_soak.py`, host interface selection is driven by `ncm.host_addr` parsed from device command output (`run /cache/bin/a90_usbnet status`). That value is then used to find a local interface by MAC and run privileged host commands (`ip addr replace`, `ip link set`) via sudo, without an interface allowlist or USB/NCM origin verification. A malicious or compromised device can report a MAC matching another host NIC (e.g., management LAN), causing unintended privileged reconfiguration and potential connectivity loss or traffic-path manipulation.

# Validation
## Rubric
- [x] Confirm the vulnerable code was introduced in the target commit (new netservice_reconnect_soak.py).
- [x] Verify trust boundary: device status output directly populates `status.host_addr` (untrusted input).
- [x] Verify interface selection is based solely on MAC match without interface allowlist/origin verification.
- [x] Verify selected interface is passed into privileged host network reconfiguration commands.
- [x] Demonstrate with PoC that spoofing `ncm.host_addr` to host NIC MAC (eth0) yields sudo `ip addr replace` / `ip link set` on that NIC.

Method-attempt checklist:
- [x] Crash attempt performed (not applicable to this logic bug; no vuln crash).
- [x] Valgrind attempt performed (tool unavailable in container).
- [x] Debugger attempt performed (lldb non-interactive; no native fault to trace).
## Report
I validated the finding as real for commit 8d58ee16a7b1de4d4d2d4659ee1cb772bf4ab0a4 (the script is newly introduced in this commit).

Key code path:
1) Untrusted device output is parsed for ncm.host_addr (`parse_usbnet_status`), sourced from `run ... status` (`get_usbnet_status`) at scripts/revalidation/netservice_reconnect_soak.py:115-123,127-130.
2) That host_addr is used directly to locate a host NIC by MAC (`wait_for_interface_by_mac` -> `find_interface_by_mac`) with no allowlist/origin validation at :141-152,155-162,356-358.
3) The selected interface is then reconfigured with privileged commands (`ip addr replace`, `ip link set`) via `sudo_command` in `configure_host_interface` at :189-193 and :195-214.

Targeted PoC execution (non-destructive harness) shows control of privileged host command target from spoofed device metadata:
- Command run: `python3 /workspace/validation_artifacts/netservice_confused_deputy_poc/poc_confused_deputy.py`
- Evidence from output/log:
  - `[reconnect] host interface: eth0 (32:82:d0:9b:c9:ae)`
  - `+ sudo -n ip addr replace 192.168.7.1/24 dev eth0`
  - `+ sudo -n ip link set eth0 up`
  - Captured subprocess commands include `['sudo', '-n', 'ip', 'addr', 'replace', '192.168.7.1/24', 'dev', 'eth0']`.
This demonstrates the confused-deputy condition: attacker-controlled `ncm.host_addr` can steer privileged host network reconfiguration to an unintended NIC.

Required method attempts:
- Crash attempt: executed `configure_host_interface` directly; got `FileNotFoundError: 'ip'` in this container (no `ip` binary), not a vulnerability crash.
- Valgrind attempt: `valgrind` unavailable (`command not found`).
- Debugger attempt: non-interactive `lldb` run performed; process exits normally (interpreted Python logic; no native crash trace).
Given this is a Python logic flaw (not memory corruption), code-understanding + PoC harness is the appropriate validation.

# Evidence
scripts/revalidation/netservice_reconnect_soak.py (L127 to 130)
  Note: Device command output is consumed and parsed without trust/authenticity verification.
```
def get_usbnet_status(args: argparse.Namespace) -> UsbnetStatus:
    output = device_command(args, f"run {args.device_helper} status", timeout=20.0)
    print(output, end="" if output.endswith("\n") else "\n")
    return parse_usbnet_status(output)
```

scripts/revalidation/netservice_reconnect_soak.py (L141 to 152)
  Note: Host interface is selected solely by matching the untrusted MAC value.
```
def find_interface_by_mac(mac: str) -> str | None:
    try:
        names = sorted(os.listdir("/sys/class/net"))
    except OSError:
        return None

    for name in names:
        if name == "lo":
            continue
        if sysfs_mac_for(name) == mac.lower():
            return name
    return None
```

scripts/revalidation/netservice_reconnect_soak.py (L189 to 193)
  Note: Privileged command prefix is constructed (`sudo ...`) for host network changes.
```
def sudo_command(args: argparse.Namespace, command: list[str]) -> list[str]:
    if os.geteuid() == 0 or args.no_sudo:
        return command
    return shlex.split(args.sudo) + command
```

scripts/revalidation/netservice_reconnect_soak.py (L195 to 214)
  Note: Selected interface is reconfigured with `ip addr replace`/`ip link set` under sudo, enabling misconfiguration of unintended NICs.
```
def configure_host_interface(args: argparse.Namespace, interface: str) -> None:
    cidr = f"{args.host_ip}/{args.prefix}"
    if interface_has_addr(interface, cidr):
        log(f"host {interface} already has {cidr}")
        return

    commands = [
        ["ip", "addr", "replace", cidr, "dev", interface],
        ["ip", "link", "set", interface, "up"],
    ]

    if args.no_configure_host:
        print_required_host_commands(interface, cidr)
        raise RuntimeError(f"host interface {interface} does not have {cidr}")

    for command in commands:
        full_command = sudo_command(args, command)
        print("+ " + shlex.join(full_command), flush=True)
        result = subprocess.run(full_command, check=False)
        if result.returncode != 0:
```

scripts/revalidation/netservice_reconnect_soak.py (L24 to 26)
  Note: Parsers extract `ncm.host_addr` from device output, which becomes trusted control data.
```
HOST_ADDR_RE = re.compile(r"^ncm\.host_addr:\s*([0-9a-fA-F:]{17})\s*$", re.MULTILINE)
DEV_ADDR_RE = re.compile(r"^ncm\.dev_addr:\s*([0-9a-fA-F:]{17})\s*$", re.MULTILINE)
IFNAME_RE = re.compile(r"^ncm\.ifname:\s*(\S+)\s*$", re.MULTILINE)
```

scripts/revalidation/netservice_reconnect_soak.py (L340 to 358)
  Note: `status.host_addr` from device is directly used to resolve interface and trigger privileged host configuration.
```
def verify_ncm_and_tcp(args: argparse.Namespace) -> None:
    status = get_usbnet_status(args)
    if not status.ifname:
        log("device NCM ifname was not reported; using v60 netservice default ncm0")
        status.ifname = "ncm0"
    if not status.host_addr:
        raise RuntimeError("device NCM host_addr was not reported")

    netmask = prefix_to_netmask(args.prefix)
    output = device_command(
        args,
        f"run {args.toybox} ifconfig {status.ifname} {args.device_ip} netmask {netmask} up",
        timeout=10.0,
    )
    print(output, end="" if output.endswith("\n") else "\n")

    interface = wait_for_interface_by_mac(status.host_addr, args.interface_timeout)
    log(f"host interface: {interface} ({status.host_addr})")
    configure_host_interface(args, interface)
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: low | Policy adjusted: low
## Rationale
Kept at medium. Evidence strongly supports a real cross-boundary logic flaw with executable PoC behavior and privileged host command sink. However, exploitation requires non-trivial preconditions (device/helper compromise or malicious attached device, plus operator script execution and effective sudo path). Impact is significant for host networking (tampering/DoS) but does not by itself demonstrate full host code execution or broad remote compromise.
## Likelihood
medium - Exploitation needs attacker influence over device status output plus operator execution of the script in lab workflow; this is not internet-exposed but is plausible in the stated host↔device threat boundary.
## Impact
medium - Primary impact is host network integrity/availability: unintended NIC readdress/up operations can disrupt management connectivity or alter traffic routing on the operator host.
## Assumptions
- Operator runs scripts/revalidation/netservice_reconnect_soak.py as documented in normal lab workflow.
- Connected device output for `run /cache/bin/a90_usbnet status` can be attacker-influenced when device/helper is compromised or malicious.
- Host either runs script as root, has sudo rights, or may follow printed host reconfiguration commands.
- Attacker can control device-reported usbnet status fields (notably ncm.host_addr)
- Operator executes netservice_reconnect_soak.py once/soak flow
- Host has a NIC whose MAC matches attacker-chosen value
## Path
Device-controlled ncm.host_addr
  -> parse_usbnet_status()
  -> find_interface_by_mac()
  -> sudo ip addr/link on matched host NIC
  -> host network integrity/availability impact
## Path evidence
- `scripts/revalidation/netservice_reconnect_soak.py:127-130` - Reads device helper status output and directly parses it.
- `scripts/revalidation/netservice_reconnect_soak.py:141-152` - Selects host interface purely by MAC match across /sys/class/net.
- `scripts/revalidation/netservice_reconnect_soak.py:195-214` - Executes privileged host network commands (via sudo) on chosen interface.
- `scripts/revalidation/netservice_reconnect_soak.py:356-358` - Connects untrusted `status.host_addr` directly to interface selection and reconfiguration sink.
- `scripts/revalidation/README.md:170-177` - Shows script is part of standard operations and may run with sudo.
## Narrative
The vulnerability is real: untrusted data from device command output (`ncm.host_addr`) is parsed and used as control input to choose a host NIC by MAC, then privileged host commands are executed on that interface. There is no interface allowlist or origin verification that the matched NIC is the intended USB NCM interface. This creates a confused-deputy path where a malicious/compromised device can steer host sudo network reconfiguration toward another NIC. Existing validation evidence includes executable PoC logs showing `eth0` selected and sudo `ip` commands targeted to it.
## Controls
- Bridge defaults to localhost (reduces remote exposure)
- MAC parser regex validates format only (not trust/origin)
- Optional `--no-configure-host` / `--manual-host-config` modes exist but are not default hardening
## Blindspots
- Static review cannot confirm real-world sudoers policy or whether operators typically run this flow as root/NOPASSWD.
- No hardware-in-the-loop validation in this step; relied on provided validation artifact for runtime demonstration.
- Potential downstream blast radius depends on host network role (single lab host vs shared critical environment).
