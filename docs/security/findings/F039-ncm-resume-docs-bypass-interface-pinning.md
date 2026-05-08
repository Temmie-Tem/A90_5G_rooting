# F039. NCM resume docs bypass interface pinning

## Metadata

| field | value |
|---|---|
| finding_id | `ec50fb4622608191b75c079435edffac` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/ec50fb4622608191b75c079435edffac |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-05-08T18:17:47.898547Z` |
| committed_at | `2026-05-09 02:00:18 +0900` |
| commit_hash | `19daf49ccc738a762edd59568ab3e5d23a6124eb` |
| relevant_paths | `docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md` <br> `scripts/revalidation/ncm_host_setup.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-08T18-39-05.112Z.csv` |

## CSV Description

This commit does not modify runtime code, but it introduces an unsafe operational workflow in a newly added report. `ncm_host_setup.py` has a protective default that refuses to configure a host NIC unless the operator supplies `--interface <ifname>` or explicitly opts into automatic selection. The newly committed resume instructions recommend `setup --allow-auto-interface` without pinning the USB/NCM interface. In the associated script, `ncm.host_addr` is parsed from device helper output, used to find a host interface by MAC address, and then passed to `sudo ip addr replace` and `sudo ip link set`. A malicious or compromised device helper, or spoofed bridge response, could report a MAC for an unintended host interface and cause privileged host network reconfiguration. The report also commits host interface/IP evidence, which can help target such spoofing in the same lab environment. The safer instruction should require `--interface <known-usb-ncm-ifname>` and avoid committing real host network identifiers.

## Local Initial Assessment

- Valid operational finding: the runtime script has a safer default, but the new report recommends bypassing it.
- Related to F017/F018 and the new mixed-soak/NCM gate: host NIC selection must be explicit before running privileged `sudo ip` commands.
- Lower implementation risk than F041/F040 because the fix is mostly documentation and operator workflow.

## Local Remediation

- Planned Batch D fix.
- Change resume instructions to require `--interface <known-usb-ncm-ifname>`.
- Keep `--allow-auto-interface` only as an explicit diagnostic fallback with a warning.
- Avoid preserving real host interface identifiers in future committed reports unless intentionally redacted.

## Codex Cloud Detail

NCM resume docs bypass interface pinning
Link: https://chatgpt.com/codex/cloud/security/findings/ec50fb4622608191b75c079435edffac?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 19daf49
Author: shs02140@gmail.com
Created: 2026. 5. 9. 오전 3:17:47
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced an operational security regression in documentation: the risky auto-interface primitive already exists in `ncm_host_setup.py`, but this commit newly recommends invoking it in the v166 resume path and commits host network metadata. No code-level vulnerability was added, but the added instructions undermine the existing interface-pinning guard.
This commit does not modify runtime code, but it introduces an unsafe operational workflow in a newly added report. `ncm_host_setup.py` has a protective default that refuses to configure a host NIC unless the operator supplies `--interface <ifname>` or explicitly opts into automatic selection. The newly committed resume instructions recommend `setup --allow-auto-interface` without pinning the USB/NCM interface. In the associated script, `ncm.host_addr` is parsed from device helper output, used to find a host interface by MAC address, and then passed to `sudo ip addr replace` and `sudo ip link set`. A malicious or compromised device helper, or spoofed bridge response, could report a MAC for an unintended host interface and cause privileged host network reconfiguration. The report also commits host interface/IP evidence, which can help target such spoofing in the same lab environment. The safer instruction should require `--interface <known-usb-ncm-ifname>` and avoid committing real host network identifiers.

# Validation
## Rubric
- [x] Confirm the commit newly adds V166 documentation containing host interface/IP metadata.
- [x] Confirm the new V166 resume steps recommend `setup --allow-auto-interface` without an explicit pinned `--interface`.
- [x] Confirm `ncm.host_addr` is parsed from device/bridge-controlled helper output.
- [x] Confirm `--allow-auto-interface` allows MAC-based host interface selection and feeds that result into privileged host `ip` commands.
- [x] Demonstrate the path non-destructively with the real CLI plus a fake bridge/fake ip wrappers and capture debugger evidence.
- [x] Attempt/consider crash and Valgrind first: no crash primitive for this Python/doc regression; Valgrind unavailable; used Python pdb for trace validation.
## Report
Validated the finding as an operational/documentation regression, not a newly introduced code-level bug. Commit 19daf49 adds docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md as a new file. That report commits host network evidence at lines 13-17 (`enx0000000005e1 UP 192.168.0.8/24 ...`) and recommends the resume command at lines 54-61: `python3 scripts/revalidation/ncm_host_setup.py setup --allow-auto-interface`, without requiring `--interface <known-usb-ncm-ifname>`. The existing script path matches the suspected risk: scripts/revalidation/ncm_host_setup.py:159-174 parses `ncm.host_addr` from device helper output; lines 223-243 refuse by default but, with `--allow-auto-interface`, resolve the host interface purely from that reported MAC; lines 302-310 pass the selected interface to host `ip addr replace ... dev <interface>` and `ip link set <interface> up` with sudo-capable execution. I built a non-destructive PoC using the real CLI and a fake local bridge. The fake bridge reported `ncm.host_addr` equal to the container's real `eth0` MAC. Without `--allow-auto-interface`, the script failed closed with `RuntimeError: refusing sudo host NIC configuration from device-reported MAC`. With the documented `--allow-auto-interface`, the real script selected `eth0` and attempted `ip addr replace 192.168.7.1/24 dev eth0` and `ip link set eth0 up`; fake `ip`/`ping` wrappers logged the commands instead of modifying networking. I also ran the same path under Python pdb non-interactively; at select_host_interface it printed `args.allow_auto_interface == True`, the forged host_addr, and resolved interface `'eth0'`. Crash/Valgrind are not meaningful for this Python/documentation regression; `valgrind` and `gdb` were unavailable in the container, and Python pdb was used for debugger validation. Caveat: a similar `--allow-auto-interface` recommendation already existed in an older V160 plan, so this commit is best characterized as adding a new unsafe V166 resume instruction plus host metadata exposure rather than inventing the underlying primitive.

# Evidence
docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md (L13 to 17)
  Note: The newly committed report exposes real host interface/IP evidence, including a MAC-like `enx...` interface name, which should remain private host evidence.
```
Host interfaces:

```text
enx0000000005e1  UP  192.168.0.8/24 fe80::f944:4e7a:2cb2:efcd/64
```
```

docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md (L54 to 61)
  Note: The new resume instructions recommend `setup --allow-auto-interface` rather than requiring an explicitly pinned USB/NCM interface before sudo network mutation.
```
## Operator Resume Steps

```bash
python3 scripts/revalidation/ncm_host_setup.py setup --allow-auto-interface

# If sudo is required, run manually:
sudo ip addr replace 192.168.7.1/24 dev <enx...>
sudo ip link set <enx...> up
```

scripts/revalidation/ncm_host_setup.py (L159 to 174)
  Note: The script parses `ncm.host_addr` from device helper output; this is the untrusted value used later for automatic host interface selection.
```
def parse_status(output: str) -> UsbnetStatus:
    ifname_match = IFNAME_RE.search(output)
    dev_match = DEV_ADDR_RE.search(output)
    host_match = HOST_ADDR_RE.search(output)
    return UsbnetStatus(
        ifname=ifname_match.group(1) if ifname_match else None,
        dev_addr=dev_match.group(1).lower() if dev_match else None,
        host_addr=host_match.group(1).lower() if host_match else None,
        raw=output,
    )


def get_usbnet_status(args: argparse.Namespace) -> UsbnetStatus:
    output = device_command(args, f"run {args.device_helper} status")
    print(output, end="" if output.endswith("\n") else "\n")
    return parse_status(output)
```

scripts/revalidation/ncm_host_setup.py (L223 to 243)
  Note: Without `--interface`, `--allow-auto-interface` explicitly permits selecting the host interface from the device-reported MAC address.
```
def select_host_interface(args: argparse.Namespace, status: UsbnetStatus) -> str:
    if args.interface:
        validate_host_interface_name(args.interface)
        actual_mac = sysfs_mac_for(args.interface)
        if status.host_addr and actual_mac and actual_mac != status.host_addr:
            raise RuntimeError(
                f"host interface {args.interface} MAC {actual_mac} does not match "
                f"device-reported NCM host_addr {status.host_addr}"
            )
        return args.interface

    if not args.allow_auto_interface:
        raise RuntimeError(
            "refusing sudo host NIC configuration from device-reported MAC; "
            "pass --interface <ifname> or opt in with --allow-auto-interface"
        )

    if not status.host_addr:
        raise RuntimeError("device NCM host_addr was not reported")
    log(f"waiting for host interface with MAC {status.host_addr}")
    return wait_for_interface_by_mac(status.host_addr, args.interface_timeout)
```

scripts/revalidation/ncm_host_setup.py (L302 to 310)
  Note: The automatically selected interface is then used as the target of privileged `ip addr` and `ip link` commands.
```
    interface = select_host_interface(args, status)
    log(f"host interface: {interface}")

    run_host_command(
        args,
        ["ip", "addr", "replace", f"{args.host_ip}/{args.prefix}", "dev", interface],
        use_sudo=True,
    )
    run_host_command(args, ["ip", "link", "set", interface, "up"], use_sudo=True)
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Kept as medium. The issue is real and in-scope because the repository's host-side NCM setup workflow explicitly uses device-reported values to drive sudo host networking, and the new documentation bypasses the script's safer interface-pinning default. The impact is meaningful host network integrity/availability degradation, and validation evidence demonstrated the real CLI selecting an unintended interface and attempting privileged `ip` commands when `--allow-auto-interface` is used. It is not high or critical because it is not public, not unauthenticated internet-reachable, requires operator interaction and sudo, and does not directly yield host code execution or secret compromise.
## Likelihood
low - Exploitation requires a lab-specific chain: operator follows the unsafe documentation, a malicious/compromised device or bridge controls the reported MAC, the target host interface MAC is known or guessable, and sudo/root execution is granted.
## Impact
medium - Successful exploitation can make the host tool perform privileged IP/link changes on an unintended local interface, disrupting or polluting host networking. It does not directly provide code execution or broad data compromise.
## Assumptions
- The operator uses the newly added V166 resume instructions as written.
- The device helper output or localhost serial bridge output can be maliciously controlled or spoofed by a compromised/malicious device in the lab workflow.
- The operator grants sudo, runs as root, or manually executes the printed sudo commands.
- The attacker knows or can guess a MAC address for an unintended host interface.
- operator follows documentation and runs ncm_host_setup.py setup --allow-auto-interface
- malicious or compromised device/helper/bridge supplies attacker-chosen ncm.host_addr
- host has an unintended interface whose MAC matches the supplied value
- sudo/root permission is available for host ip commands
## Path
V166 docs -> operator runs --allow-auto-interface -> device/bridge reports ncm.host_addr -> MAC lookup selects host NIC -> sudo ip addr/link -> unintended NIC reconfiguration
## Path evidence
- `docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md:13-17` - The newly added report includes real host network interface/IP evidence that could help target interface spoofing in the same lab environment.
- `docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md:54-61` - The operator resume steps recommend `setup --allow-auto-interface` and manual sudo network commands rather than requiring a pinned USB/NCM interface.
- `scripts/revalidation/ncm_host_setup.py:159-174` - The script parses `ncm.host_addr` from device helper output, making device/bridge-provided status text the source for later host interface selection.
- `scripts/revalidation/ncm_host_setup.py:223-243` - The script fails closed by default, but `--allow-auto-interface` permits selecting a host interface by the device-reported MAC address.
- `scripts/revalidation/ncm_host_setup.py:246-260` - Host commands are run through a sudo prefix unless disabled or already root, giving the selected interface privileged mutation capability.
- `scripts/revalidation/ncm_host_setup.py:302-310` - The automatically selected interface is used as the target of `ip addr replace` and `ip link set` host commands.
- `scripts/revalidation/ncm_host_setup.py:390-392` - The CLI help confirms that `--allow-auto-interface` allows selecting the sudo target interface from the device-reported NCM MAC.
## Narrative
The finding is valid as an operational/documentation regression. The new report commits host interface/IP evidence and tells operators to run `ncm_host_setup.py setup --allow-auto-interface`. In the script, `ncm.host_addr` is parsed from device helper output, and the protective default refuses MAC-based host selection unless `--interface` is provided or `--allow-auto-interface` is set. With the documented flag, that device-reported MAC is used to find a host interface and the resulting ifname is passed into sudo-capable `ip addr replace` and `ip link set` commands. This is not public remote RCE, and it requires a malicious/compromised device or bridge plus operator sudo interaction, but it is in-scope for this lab host tooling and can cause privileged host network misconfiguration.
## Controls
- Default fail-closed behavior unless `--interface` or `--allow-auto-interface` is supplied
- Explicit `--interface` path validates the host interface exists and compares actual MAC when device reports one
- Default bridge host is localhost
- Host interface names are regex-validated before explicit use
- Operator-controlled sudo is required for actual host network mutation
## Blindspots
- Static-only repository review did not interact with real USB hardware or cloud/runtime infrastructure.
- Actual exploitability depends on the operator's host OS interface inventory, sudo policy, and whether the malicious device/bridge can supply convincing status output.
- The review cannot measure how often operators will follow this specific documentation path.
- A similar unsafe recommendation existed in older documentation, so this commit primarily reintroduces/extends the risky workflow for V166 rather than creating the underlying primitive.
