# F019. Auto re-enumeration check allows serial bridge device hijack

## Metadata

| field | value |
|---|---|
| finding_id | `02396069e06c819181647d72e8963baa` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/02396069e06c819181647d72e8963baa |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-04-28T09:19:16.229727Z` |
| committed_at | `2026-04-25 04:32:03 +0900` |
| commit_hash | `8dce12a0e3645d5f44e6188433e0cb23ee397527` |
| relevant_paths | `scripts/revalidation/serial_tcp_bridge.py` |
| has_patch | `false` |

## CSV Description

This commit adds periodic serial identity checks in `serial_tcp_bridge.py`. Instead of validating the already-open device path, the new code re-runs auto-discovery (`glob` + first sorted match) every 0.5s and compares that result's stat identity to the active connection. If another matching device appears (or ordering changes), the bridge treats it as re-enumeration, disconnects, then reconnects to whichever device now sorts first. In practice, a malicious USB serial gadget spoofing the Samsung by-id pattern can cause device confusion/hijacking of the trusted root-shell channel (commands and responses redirected to attacker-controlled endpoint). This is newly introduced by the identity-check feature.

## Codex Cloud Detail

Auto re-enumeration check allows serial bridge device hijack
Link: https://chatgpt.com/codex/cloud/security/findings/02396069e06c819181647d72e8963baa?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 8dce12a
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 6:19:16
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced security bug: periodic identity verification re-resolves an auto-selected device and can switch trust to a different matching serial node, enabling channel hijack/impersonation under realistic lab physical/shared-host attacker models.
This commit adds periodic serial identity checks in `serial_tcp_bridge.py`. Instead of validating the already-open device path, the new code re-runs auto-discovery (`glob` + first sorted match) every 0.5s and compares that result's stat identity to the active connection. If another matching device appears (or ordering changes), the bridge treats it as re-enumeration, disconnects, then reconnects to whichever device now sorts first. In practice, a malicious USB serial gadget spoofing the Samsung by-id pattern can cause device confusion/hijacking of the trusted root-shell channel (commands and responses redirected to attacker-controlled endpoint). This is newly introduced by the identity-check feature.

# Validation
## Rubric
- [x] Confirm auto-discovery is mutable (`sorted(glob(...))[0]`) and not pinned to original path.
- [x] Confirm identity baseline is captured at open (`self.serial_stat`) from opened fd.
- [x] Confirm periodic check re-resolves device via glob and compares that identity to active fd identity.
- [x] Confirm mismatch path closes serial and tick reconnects using auto-discovery (possible device switch).
- [x] Demonstrate practical impact with PoC: traffic before switch reaches victim endpoint, after switch reaches attacker endpoint.
## Report
I validated the finding on commit 8dce12a0e3645d5f44e6188433e0cb23ee397527 with a targeted Python PoC against `scripts/revalidation/serial_tcp_bridge.py`.

Key code evidence:
- `resolve_device()` returns first sorted glob match (`serial_tcp_bridge.py:66-73`).
- Initial open binds `self.serial_stat` from the opened fd (`:92-116`).
- Periodic identity check re-runs `resolve_device()` and stats that newly resolved path instead of checking the already-open path (`:139-170`).
- On mismatch it calls `close_serial()`; next loop reconnects via auto-discovery (`:269-274`).

Reproduction steps and outputs:
1) Direct execution PoC (`PYTHONPATH=/workspace/A90_5G_rooting python3 .../poc_serial_switch.py`) creates two PTYs and by-id-like symlinks.
2) PoC output showed:
   - `INITIAL_SELECTED=..._Z_victim`
   - `AFTER_CHECK_SERIAL_FD_NONE=True`
   - `RECONNECTED_SELECTED=..._A_attacker`
   - `BEFORE_ON_VICTIM=b'BEFORE'`
   - `AFTER_ON_ATTACKER=b'AFTER'`
3) Bridge stderr logs during same run showed:
   - `serial connected: ..._Z_victim`
   - `serial device was re-enumerated: ..._A_attacker`
   - `serial disconnected`
   - `serial connected: ..._A_attacker`

This demonstrates trust switching to a different matching node when glob ordering changes, and actual command-channel redirection after reconnect.

Required method attempts:
- Crash attempt: executed PoC as a direct run (`crash_attempt.exit=0`); no process crash (logic/security issue, not memory corruption).
- Valgrind attempt: unavailable in container (`bash: command not found: valgrind`).
- Debugger attempt: non-interactive pdb breakpoint at `serial_tcp_bridge.py:155` showed `device` resolved to attacker path while `self.serial_stat` still referenced prior device identity, confirming mismatch trigger path.

# Evidence
scripts/revalidation/serial_tcp_bridge.py (L139 to 170)
  Note: New check re-runs `resolve_device()` and closes the active serial connection if the newly resolved node identity differs, enabling forced disconnect/switch to another matching device.
```
    def check_serial_identity(self) -> None:
        if self.serial_fd is None:
            return

        now = time.monotonic()
        if now < self.next_serial_identity_check:
            return

        self.next_serial_identity_check = now + 0.5
        device = self.resolve_device()
        if device is None:
            self.log("serial device path disappeared")
            self.close_serial()
            return

        try:
            current_stat = os.stat(device)
        except OSError as exc:
            if exc.errno in {errno.ENOENT, errno.ENODEV, errno.EACCES}:
                self.log(f"serial device path is no longer valid: {exc.strerror}")
                self.close_serial()
                return
            raise

        current_identity = (
            current_stat.st_dev,
            current_stat.st_ino,
            current_stat.st_rdev,
        )
        if current_identity != self.serial_stat:
            self.log(f"serial device was re-enumerated: {device}")
            self.close_serial()
```

scripts/revalidation/serial_tcp_bridge.py (L269 to 274)
  Note: Periodic tick invokes identity check, and once disconnected immediately attempts reconnect using auto-resolved (potentially attacker-controlled) device.
```
    def tick(self) -> None:
        self.check_serial_identity()

        if self.serial_fd is None and time.monotonic() >= self.next_serial_retry:
            self.open_serial()
            if self.serial_fd is None:
```

scripts/revalidation/serial_tcp_bridge.py (L66 to 73)
  Note: Auto-discovery always returns the first sorted glob match, creating a mutable selection if additional matching devices appear.
```
    def resolve_device(self) -> str | None:
        if self.args.device != "auto":
            return self.args.device

        matches = sorted(glob.glob(self.args.device_glob))
        if not matches:
            return None
        return matches[0]
```

scripts/revalidation/serial_tcp_bridge.py (L92 to 116)
  Note: Bridge stores identity of the currently opened serial endpoint, but later logic does not bind checks to this path.
```
    def open_serial(self) -> None:
        device = self.resolve_device()
        if device is None:
            return

        try:
            fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            self.configure_serial(fd)
            serial_stat = os.fstat(fd)
        except OSError as exc:
            if exc.errno in {errno.ENOENT, errno.ENODEV, errno.EACCES, errno.EBUSY}:
                self.log(f"serial not ready at {device}: {exc.strerror}")
                return
            raise

        self.serial_fd = fd
        self.serial_device = device
        self.serial_stat = (
            serial_stat.st_dev,
            serial_stat.st_ino,
            serial_stat.st_rdev,
        )
        self.next_serial_identity_check = time.monotonic() + 0.5
        self.selector.register(fd, selectors.EVENT_READ, "serial")
        self.log(f"serial connected: {device}")
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Kept at medium: vulnerability is real, reachable, and validated with executable PoC; impact to channel integrity/confidentiality is substantial. However, exploitation needs physical/shared-host conditions (AV:P-like), operator workflow timing, and matching-device spoofing, which materially limits probability versus high/critical remote scenarios.
## Likelihood
low - Requires physical/shared-host access and ability to present a spoofed matching USB serial identity during operation; plausible in lab/shared setups but not broadly remote.
## Impact
high - Successful exploitation redirects/confuses a trusted root-shell control channel, allowing command interception and response spoofing during privileged device operations.
## Assumptions
- Operational workflow uses scripts/revalidation/serial_tcp_bridge.py with default --device auto.
- Attacker can attach a spoofed USB serial gadget (or otherwise create a higher-priority matching by-id node) on the host running the bridge.
- Operator/automation continues to trust bridge output as device root-shell output.
- Bridge running with auto-discovery glob matching /dev/serial/by-id/usb-SAMSUNG_SAMSUNG_Android_*
- Second matching device appears or sort order changes during periodic identity check
- Operator/client actively uses bridged shell channel
## Path
[Spoofed USB device]
   -> [resolve_device() picks sorted first match]
   -> [identity mismatch closes current fd]
   -> [auto-reconnect selects attacker node]
   -> [localhost client traffic hijacked/spoofed]
## Path evidence
- `scripts/revalidation/serial_tcp_bridge.py:66-73` - Auto-discovery uses sorted(glob)[0], making selected device mutable when new matches appear.
- `scripts/revalidation/serial_tcp_bridge.py:92-116` - Bridge records serial_stat from currently opened fd as baseline identity.
- `scripts/revalidation/serial_tcp_bridge.py:139-170` - Periodic identity check re-resolves device path and compares that path's stat to old fd identity; mismatch forces close.
- `scripts/revalidation/serial_tcp_bridge.py:269-274` - After close, loop immediately reopens via auto-discovery, enabling trust switch to attacker-controlled node.
- `scripts/revalidation/README.md:18-24` - Bridge is documented as normal operational path and explicitly includes re-enumeration behavior.
- `stage3/linux_init/init_v48.c:4875-4884` - Control channel carries high-privilege commands (run, reboot, recovery, poweroff), so channel integrity matters.
## Narrative
The finding is valid and introduced by commit 8dce12a0: the bridge stores identity of the opened serial fd, but periodic checks stat a newly auto-resolved glob winner instead of the active fd/path. A changed match ordering triggers disconnect and automatic reconnect to another matching device. Repository docs show this bridge is a normal control path for native-init operations, and native init exposes powerful root commands over this channel. Prior validation includes an executable PoC demonstrating actual switch from victim endpoint to attacker endpoint with command redirection.
## Controls
- Default listener bound to 127.0.0.1
- Single-client policy
- Reject client when serial absent (unless --allow-client-without-serial)
- Manual --device can bypass auto-discovery
## Blindspots
- Static analysis cannot confirm how often operators pin --device versus using auto mode in real deployments.
- No runtime udev policy audit was performed to quantify how easy by-id spoofing is across host environments.
- Assessment is limited to repository artifacts and provided validation logs; no cloud/network telemetry or fleet exposure data.
