# F018. Untrusted device MAC drives sudo host network reconfiguration

## Metadata

| field | value |
|---|---|
| finding_id | `c1522842459881919ce5e5e7b4ba7d43` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/c1522842459881919ce5e5e7b4ba7d43 |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-04-28T09:18:07.473788Z` |
| committed_at | `2026-04-26 00:01:24 +0900` |
| commit_hash | `db83601d65bfaf9ad21bffa98c623452f344e363` |
| relevant_paths | `scripts/revalidation/ncm_host_setup.py` |
| has_patch | `false` |

## CSV Description

In `ncm_host_setup.py`, `ncm.host_addr` is parsed from device/bridge output and used as the sole selector for the host NIC. The script then executes `sudo ip addr replace ... dev <iface>` and `sudo ip link set <iface> up`. A malicious or compromised device helper (or spoofed bridge response) can return a MAC belonging to a different host interface (e.g., production Ethernet/Wi-Fi), causing privileged reconfiguration of the wrong interface. This can disrupt connectivity and potentially redirect traffic in lab environments where operators run the helper with sudo.

## Codex Cloud Detail

Untrusted device MAC drives sudo host network reconfiguration
Link: https://chatgpt.com/codex/cloud/security/findings/c1522842459881919ce5e5e7b4ba7d43?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: db83601
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 6:18:07
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced bug: new helper performs privileged host network changes based on untrusted device-originated metadata (`ncm.host_addr`) without binding checks (driver/type/newly enumerated interface), enabling attacker-influenced host misconfiguration.
In `ncm_host_setup.py`, `ncm.host_addr` is parsed from device/bridge output and used as the sole selector for the host NIC. The script then executes `sudo ip addr replace ... dev <iface>` and `sudo ip link set <iface> up`. A malicious or compromised device helper (or spoofed bridge response) can return a MAC belonging to a different host interface (e.g., production Ethernet/Wi-Fi), causing privileged reconfiguration of the wrong interface. This can disrupt connectivity and potentially redirect traffic in lab environments where operators run the helper with sudo.

# Validation
## Rubric
- [x] Confirm `ncm.host_addr` comes from untrusted device-helper status output path (regex/parse + `get_usbnet_status`).
- [x] Confirm host interface resolution depends only on MAC match from that field (`wait_for_interface_by_mac`/`find_interface_by_mac`) with no binding checks.
- [x] Confirm selected interface is passed into privileged host configuration commands (`ip addr replace`, `ip link set`, sudo-capable path).
- [x] Demonstrate end-to-end controllability with a minimal non-destructive PoC that forges `host_addr` to a real non-USB host NIC MAC and observes intended host commands target that NIC.
- [x] Attempt alternate validation methods first (direct crash run, valgrind, debugger) and record constraints/results.
## Report
I validated the finding on commit db83601 with a bounded dynamic PoC plus focused source review. Source chain: untrusted `ncm.host_addr` is parsed from helper output (`HOST_ADDR_RE` and `parse_status`: scripts/revalidation/ncm_host_setup.py:23,107-115), helper output is taken directly from `run <device_helper> status` (`get_usbnet_status`: :119-122), interface selection is only MAC-based (`find_interface_by_mac`/`wait_for_interface_by_mac`: :139-161), and privileged host commands are then executed on that interface (`command_setup` -> `run_host_command` with `use_sudo=True`: :215-224,170-178; sudo decision in :164-167). There is no check that the chosen host NIC is the expected newly-enumerated USB/NCM interface, driver, or type. Dynamic PoC: `/workspace/validation_artifacts/ncm_host_addr_iface_confusion/poc_ncm_host_addr_confusion.py` monkeypatches device/host execution to avoid destructive changes, injects forged status with `ncm.host_addr` set to the container host NIC MAC (eth0), and runs real `command_setup()`. Output (`poc_run.log`) shows: `[ncm] host interface: eth0`, then `WOULD_RUN: sudo -n ip addr replace 192.168.7.1/24 dev eth0` and `WOULD_RUN: sudo -n ip link set eth0 up`. This demonstrates attacker-influenced metadata can steer privileged host network reconfiguration to an unintended interface. Required method attempts were made first: direct run (bridge timeout, no crash primitive) in `crash_attempt.log`, valgrind unavailable (`valgrind_attempt.log`: command not found), and non-interactive debugger run via lldb in `debugger_attempt.log`.

# Evidence
scripts/revalidation/ncm_host_setup.py (L119 to 122)
  Note: Fetches status from device helper (`run ... status`) and feeds it into parser without trust validation.
```
def get_usbnet_status(args: argparse.Namespace) -> UsbnetStatus:
    output = device_command(args, f"run {args.device_helper} status")
    print(output, end="" if output.endswith("\n") else "\n")
    return parse_status(output)
```

scripts/revalidation/ncm_host_setup.py (L154 to 161)
  Note: Selects host interface solely by matching MAC address from untrusted status.
```
def wait_for_interface_by_mac(mac: str, timeout_sec: float) -> str:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        interface = find_interface_by_mac(mac)
        if interface is not None:
            return interface
        time.sleep(0.5)
    raise RuntimeError(f"host interface with MAC {mac} was not found")
```

scripts/revalidation/ncm_host_setup.py (L170 to 178)
  Note: Executes host commands (including sudo-prefixed ones) directly once interface is chosen.
```
def run_host_command(args: argparse.Namespace,
                     command: list[str],
                     *,
                     use_sudo: bool = False) -> None:
    full_command = (sudo_prefix(args) if use_sudo else []) + command
    print("+ " + shlex.join(full_command), flush=True)
    result = subprocess.run(full_command, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"host command failed rc={result.returncode}: {shlex.join(full_command)}")
```

scripts/revalidation/ncm_host_setup.py (L204 to 224)
  Note: Uses parsed `host_addr` to choose interface and runs privileged host `ip` commands via sudo.
```
    if not status.host_addr:
        raise RuntimeError("device NCM host_addr was not reported")

    netmask = prefix_to_netmask(args.prefix)
    log(f"setting device {status.ifname} to {args.device_ip}/{args.prefix}")
    output = device_command(
        args,
        f"run {args.toybox} ifconfig {status.ifname} {args.device_ip} netmask {netmask} up",
    )
    print(output, end="" if output.endswith("\n") else "\n")

    log(f"waiting for host interface with MAC {status.host_addr}")
    interface = wait_for_interface_by_mac(status.host_addr, args.interface_timeout)
    log(f"host interface: {interface}")

    run_host_command(
        args,
        ["ip", "addr", "replace", f"{args.host_ip}/{args.prefix}", "dev", interface],
        use_sudo=True,
    )
    run_host_command(args, ["ip", "link", "set", interface, "up"], use_sudo=True)
```

scripts/revalidation/ncm_host_setup.py (L23 to 25)
  Note: Parses `ncm.host_addr` directly from device output, establishing the untrusted input source.
```
HOST_ADDR_RE = re.compile(r"^ncm\.host_addr:\s*([0-9a-fA-F:]{17})\s*$", re.MULTILINE)
DEV_ADDR_RE = re.compile(r"^ncm\.dev_addr:\s*([0-9a-fA-F:]{17})\s*$", re.MULTILINE)
IFNAME_RE = re.compile(r"^ncm\.ifname:\s*(\S+)\s*$", re.MULTILINE)
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: low | Policy adjusted: low
## Rationale
Probability is moderate (requires attacker control of device-side status path or bridge spoofing plus operator-run setup). Impact is meaningful but mainly host network integrity/availability, not direct arbitrary host code execution or broad data compromise. This aligns with medium in this repo’s own threat context and does not meet high/critical thresholds.
## Likelihood
medium - Exploitation needs attacker influence over helper/bridge output and operator execution with sudo-capable path; feasible in compromised-device/shared-lab scenarios but not broadly internet-exposed by default.
## Impact
medium - Can reconfigure unintended host NIC with elevated privileges, causing host network disruption and integrity changes (routing/addressing changes) during normal lab operations.
## Assumptions
- Operator runs `scripts/revalidation/ncm_host_setup.py setup` in normal lab workflow.
- Host command path has sudo/root capability (interactive sudo, cached sudo, or root shell).
- Attacker can influence `a90_usbnet status` output via compromised/malicious device-side helper or spoofed bridge response.
- Run of `ncm_host_setup.py setup`
- Attacker-controlled or spoofed `ncm.host_addr` in status output
- Chosen MAC must match an existing non-loopback host NIC
## Path
status output (ncm.host_addr) -> MAC match in /sys/class/net -> sudo ip addr/link on chosen iface
## Path evidence
- `scripts/revalidation/ncm_host_setup.py:23-25` - Parses `ncm.host_addr` from status text.
- `scripts/revalidation/ncm_host_setup.py:119-122` - Status is taken directly from device helper command output and fed to parser.
- `scripts/revalidation/ncm_host_setup.py:139-161` - Interface resolution is MAC-only lookup under `/sys/class/net`, with no USB/NCM binding check.
- `scripts/revalidation/ncm_host_setup.py:219-224` - Selected interface is used in `ip addr replace` and `ip link set` with `use_sudo=True`.
- `scripts/revalidation/README.md:45-48` - Operational docs state host interface auto-detection from `ncm.host_addr` and host IP setup.
- `/workspace/validation_artifacts/attack_path/user-uCP64b5dIkMxZJ7N2kDGpa8n_github-1095371052_db83601d65bfaf9ad21bffa98c623452f344e363/extracted/ncm_host_addr_iface_confusion/poc_run.log:3-14` - PoC shows forged host_addr resolves to `eth0` and would run sudo `ip` commands on that interface.
## Narrative
The finding is valid. `ncm_host_setup.py` parses `ncm.host_addr` from device helper output, uses that value as the only selector for a host interface, then runs privileged host networking commands on the selected interface. No verification ties the chosen interface to the intended USB-NCM link. Repository docs show this is normal operational workflow, and validation artifacts include an executable PoC demonstrating steering to `eth0` and issuing the sudo `ip` commands against it. This is a real cross-boundary integrity/availability risk on host networking, but constrained by operator execution and attacker ability to influence helper/bridge output.
## Controls
- Bridge default host is localhost (`127.0.0.1`).
- Single-client bridge design reduces opportunistic concurrent interference.
- Subprocess invocation uses argv lists (not shell injection).
## Blindspots
- Static-only review cannot prove real-world bridge exposure configuration in each deployment.
- No live hardware test here to measure attacker ability to learn target host NIC MAC in all setups.
- Sudo policy/environment differences (NOPASSWD, cached creds, root shells) may change practical exploit friction.
