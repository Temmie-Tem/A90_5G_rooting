# F034. Unvalidated device path triggers unbounded host cat

## Metadata

| field | value |
|---|---|
| finding_id | `d08d0c6799308191a35805df1461a6ec` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/d08d0c6799308191a35805df1461a6ec |
| severity | `medium` |
| status | `mitigated-v153` |
| detected_at | `2026-05-07T19:33:00.126769Z` |
| committed_at | `2026-05-08 04:04:51 +0900` |
| commit_hash | `be9feb12401ade15e501cc93169c58a3626a488d` |
| relevant_paths | `scripts/revalidation/native_long_soak.py` <br> `scripts/revalidation/a90ctl.py` <br> `stage3/linux_init/v148/60_shell_basic_commands.inc.c` |
| source_csv | `docs/security/codex-security-findings-2026-05-07T20-00-44.982Z.csv` |

## CSV Description

`native_long_soak.py` parses `longsoak path` output, trusts either `longsoak: path=<value>` or any line beginning with `/`, then sends that value back to the root native shell as `cat <device_path>`. The device path is not validated as an expected longsoak JSONL path, regular file, trusted directory child, or bounded-size file. A malicious/fake bridge or compromised device can return paths such as `/dev/zero`, `/proc/kmsg`, or a large file, causing host memory/disk pressure or a stuck native shell `cat`.

## Local Initial Assessment

- Valid class: host tooling trusts device-provided path and uses unbounded `cat`.
- Likely fix: avoid raw device path `cat`; add strict longsoak export path validation and/or a device-side bounded `longsoak export` command.
- Related group: host tooling trust boundary and longsoak evidence export.

## Local Remediation

- Mitigated in v153 Longsoak Security Hardening.
- Replace host-side `cat <device_path>` with a bounded device-side `longsoak export [max_lines] [max_bytes]` command.
- Keep `longsoak path` as metadata only; do not use it as a host-selected read target.

## Codex Cloud Detail

Unvalidated device path triggers unbounded host cat
Link: https://chatgpt.com/codex/cloud/security/findings/d08d0c6799308191a35805df1461a6ec?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: be9feb1
Author: shs02140@gmail.com
Created: 2026. 5. 8. 오전 4:33:00
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced: v148 added automatic device JSONL export in `native_long_soak.py`, but the export uses an unvalidated device-controlled path with an unbounded `cat` operation.
The new long-soak export code parses the `longsoak path` response and accepts either `longsoak: path=<anything>` or any line beginning with `/`. It then sends that value back to the root native shell as `cat <device_path>` without verifying that the path is the expected long-soak JSONL file, under the expected runtime log directory, a regular file, or bounded in size. The existing device-side `cat` streams until EOF with no output limit, and the host-side `a90ctl` buffers received bytes in memory until it sees an END marker/prompt or times out; if parsing fails, it includes the full captured text in an exception string that `native_long_soak.py` records. A malicious/fake serial bridge or compromised device can answer `longsoak path` with `/dev/zero`, `/proc/kmsg`, or a very large file. This can exhaust host memory/disk during validation and can leave the PID1 shell stuck in an endless `cat` until interrupted/rebooted.

# Validation
## Rubric
- [x] Verify the longsoak path parser accepts arbitrary device-controlled absolute paths rather than only the expected JSONL path. - [x] Verify native_long_soak.py automatically passes the parsed path into a cat command. - [x] Verify the a90ctl receive path has no response-size cap and accumulates bytes until marker/close/timeout. - [x] Verify missing END marker/error handling can include the full captured stream in host-side records. - [x] Verify device-side cat itself reads arbitrary opened paths until EOF without file-type or size bounds.
## Report
Validated the finding against commit be9feb12401ade15e501cc93169c58a3626a488d. Code inspection showed scripts/revalidation/native_long_soak.py:134-142 accepts attacker-controlled values such as longsoak: path=/dev/zero and bare absolute paths such as /proc/kmsg; scripts/revalidation/native_long_soak.py:221-243 then automatically runs record_command(..., [cat, device_path]). scripts/revalidation/a90ctl.py:120-144 appends all received chunks to an unbounded bytearray, and scripts/revalidation/a90ctl.py:177-183 embeds the full captured text in RuntimeError if no END marker is present. Device-side support in stage3/linux_init/v148/60_shell_basic_commands.inc.c:356-383 opens the supplied path and reads until EOF without regular-file or size checks. A targeted unit check returned '/dev/zero' for 'longsoak: path=/dev/zero' and '/proc/kmsg' for a bare absolute path. Dynamic PoC: I ran a fake serial bridge that returned longsoak: path=/dev/zero, then streamed 1 MiB of Z bytes without A90P1 END for cat. native_long_soak.py exited rc=1, and the fake bridge log shows CMD 7: cmdv1 cat /dev/zero plus CAT_PATH /dev/zero, proving the host fed the untrusted device path back to cat. The host output sizes were host.jsonl=1050662 bytes and out.txt=1049400 bytes; the last host JSONL record had command='cat /dev/zero', ok=false, error_len=1048630, and error_prefix='A90P1 END marker not found\nA90P1 BEGIN seq=7 cmd=cat\r\nZZZZ...', proving the received stream was buffered and amplified into the recorded exception text. Crash attempt: I reran with a 45 MB virtual-memory ulimit and an 80 MB stream; the process did not produce a useful crash stack, instead native_long_soak.py returned rc=1 with an empty caught error and the fake bridge saw ConnectionResetError, so I did not classify validation as crash. Valgrind attempt: valgrind was unavailable in the container (rc=127, 'bash: command not found: valgrind'). Debugger attempt: python -m pdb with a breakpoint in native_long_soak.py printed device_path == '/dev/zero' at the export path and the paired fake bridge log again recorded cmdv1 cat /dev/zero. This validates the suspected availability vulnerability with a bounded fake-device reproduction.

# Evidence
scripts/revalidation/a90ctl.py (L120 to 144)
  Note: Host command transport accumulates all received bytes in an unbounded bytearray until protocol completion or timeout.
```
def read_until(sock: socket.socket,
               markers: tuple[bytes, ...],
               timeout_sec: float,
               *,
               require_prompt_after_end: bool = False) -> bytes:
    deadline = time.monotonic() + timeout_sec
    data = bytearray()
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(8192)
        except socket.timeout:
            continue
        if not chunk:
            break
        data.extend(chunk)
        if any(marker in data for marker in markers):
            if require_prompt_after_end and not has_prompt_after_last_end(data):
                continue
            time.sleep(0.15)
            try:
                data.extend(sock.recv(8192))
            except socket.timeout:
                pass
            break
    return bytes(data)
```

scripts/revalidation/a90ctl.py (L177 to 183)
  Note: If no END marker is found, the full captured response is embedded into an exception string, which can amplify memory/disk use when recorded by the caller.
```
def parse_protocol_output(text: str) -> ProtocolResult:
    begin_matches = list(BEGIN_RE.finditer(text))
    end_matches = list(END_RE.finditer(text))
    begin_match = begin_matches[-1] if begin_matches else None
    end_match = end_matches[-1] if end_matches else None
    if end_match is None:
        raise RuntimeError(f"A90P1 END marker not found\n{text}")
```

scripts/revalidation/native_long_soak.py (L134 to 142)
  Note: The parser trusts any `longsoak: path=` value, and even any line starting with `/`, without validating it is the expected long-soak JSONL path.
```
def extract_longsoak_path(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("longsoak: path="):
            path = line.split("=", 1)[1].strip()
            if path and path != "-":
                return path
        if line.startswith("/"):
            return line.strip()
    return None
```

scripts/revalidation/native_long_soak.py (L221 to 243)
  Note: The trusted path is automatically fed back into a root-shell `cat` command and the resulting text is processed/written on the host.
```
    sample, path_text = record_command(args, jsonl_path, seq, ["longsoak", "path"])
    append_summary(lines, sample)
    failures += 0 if sample.ok else 1
    ok_count += 1 if sample.ok else 0
    max_duration = max(max_duration, sample.duration_sec)
    seq += 1
    device_path = extract_longsoak_path(path_text)
    exported_device_lines: list[str] = []
    if device_path is not None:
        sample, _ = record_command(args, jsonl_path, seq, ["hide"])
        append_summary(lines, sample)
        failures += 0 if sample.ok else 1
        ok_count += 1 if sample.ok else 0
        max_duration = max(max_duration, sample.duration_sec)
        seq += 1
        sample, cat_text = record_command(args, jsonl_path, seq, ["cat", device_path])
        append_summary(lines, sample)
        failures += 0 if sample.ok else 1
        ok_count += 1 if sample.ok else 0
        max_duration = max(max_duration, sample.duration_sec)
        seq += 1
        exported_device_lines = extract_device_jsonl(cat_text)
        device_jsonl_path.write_text("\n".join(exported_device_lines) + ("\n" if exported_device_lines else ""), encoding="utf-8")
```

stage3/linux_init/v148/60_shell_basic_commands.inc.c (L356 to 383)
  Note: The device-side `cat` implementation opens arbitrary paths and streams until EOF with no regular-file check or output cap.
```
static int cmd_cat(const char *path) {
    char buf[512];
    int fd = open(path, O_RDONLY);

    if (fd < 0) {
        a90_console_printf("cat: %s: %s\r\n", path, strerror(errno));
        return negative_errno_or(ENOENT);
    }

    while (1) {
        ssize_t rd = read(fd, buf, sizeof(buf));
        if (rd < 0) {
            if (errno == EINTR) {
                continue;
            }
            a90_console_printf("cat: %s: %s\r\n", path, strerror(errno));
            close(fd);
            return negative_errno_or(EIO);
        }
        if (rd == 0) {
            break;
        }
        a90_console_write(buf, (size_t)rd);
    }

    close(fd);
    a90_console_printf("\r\n");
    return 0;
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: low | Policy adjusted: low
## Rationale
Kept at medium. Static evidence and the provided PoC support the core claim: arbitrary device-reported paths are trusted and fed into root-shell `cat`, while host-side receive/error handling is unbounded. The attack crosses the device/bridge-to-host trust boundary relevant to this repository, and can cause host/device availability degradation. It does not justify high or critical because the affected component is lab/operator tooling behind a localhost serial bridge, requires user action and attacker control of the device/bridge output, and the demonstrated impact is DoS/log amplification rather than RCE, authentication bypass, sensitive secret exfiltration, or persistent compromise.
## Likelihood
medium - The exploit is straightforward once the attacker controls the bridge/device response, and the affected script is part of the documented validation workflow. However, the default exposure is localhost and exploitation requires operator interaction plus a malicious/fake/compromised attached device or serial bridge, so this is not broadly internet-reachable.
## Impact
medium - Impact is meaningful availability loss: host memory pressure and log/disk amplification, plus a stuck root/PID1 shell if cat reads a non-terminating source. The evidence does not show host code execution, host secret theft, privilege escalation, or broad remote compromise.
## Assumptions
- The operator runs scripts/revalidation/native_long_soak.py as part of the documented v148 long-soak validation workflow.
- An attacker can influence the serial bridge/device response, either by presenting a fake/malicious bridge endpoint on localhost:54321, physically substituting a device, or compromising the attached device/control channel.
- No cloud APIs, deployment manifests, or external runtime state were consulted; conclusions are based only on repository artifacts and provided validation evidence.
- operator interaction to run the host validation script
- attacker control over device or serial-bridge output
- host script can connect to the attacker-influenced bridge/device
## Path
operator native_long_soak.py -> malicious bridge/device -> trusted path parser -> cmdv1 cat /dev/zero -> root cmd_cat stream -> unbounded host buffer/log -> DoS
## Path evidence
- `scripts/revalidation/native_long_soak.py:134-142` - Path parser trusts `longsoak: path=` values and any line beginning with `/`, with no directory, filename, file-type, or size validation.
- `scripts/revalidation/native_long_soak.py:221-243` - The parsed device-controlled path is automatically passed into `record_command(..., ["cat", device_path])` and the resulting text is processed and written on the host.
- `scripts/revalidation/a90ctl.py:120-144` - Host receive loop appends all socket chunks to a bytearray without a maximum response-size guard.
- `scripts/revalidation/a90ctl.py:177-183` - Missing protocol END marker raises an exception containing the full captured response text, amplifying memory/disk impact when recorded by the caller.
- `stage3/linux_init/v148/60_shell_basic_commands.inc.c:356-383` - Device-side `cmd_cat` opens the supplied path and reads until EOF, with no regular-file check and no byte cap.
- `stage3/linux_init/a90_longsoak.c:52-64` - The legitimate long-soak path is expected to be generated under the runtime log directory with a `longsoak-<session>.jsonl` filename, giving a concrete validation policy the host could enforce.
- `stage3/linux_init/a90_longsoak.c:297-299` - The real device command prints only the current long-soak path or `-`; a malicious/fake endpoint can spoof this output across the trusted serial boundary.
## Narrative
The finding is real and reachable in the repository's stated lab threat model. native_long_soak.py obtains `longsoak path`, accepts arbitrary absolute or `longsoak: path=` values, and then automatically issues `cat` on the parsed path. a90ctl buffers all received data until a protocol marker, close, or timeout and includes full captured text in missing-END exceptions. The v148 device `cmd_cat` opens the supplied path and streams until EOF without checking file type or size. The supplied validation PoC demonstrated a fake bridge returning `/dev/zero`, after which the host sent `cmdv1 cat /dev/zero` and wrote roughly 1 MiB of attacker-controlled output/error text. This is a credible availability vulnerability, but not high/critical because exploitation requires operator interaction and attacker control of a local/fake/compromised device or bridge, and the demonstrated impact is DoS/log amplification rather than code execution, credential compromise, or broad remote compromise.
## Controls
- serial bridge defaults to 127.0.0.1:54321
- per-command timeout defaults to 20 seconds
- cmdv1 argument encoding avoids shell metacharacter expansion but does not validate the path target
- no authentication is present on the serial root shell/bridge workflow in the lab trust model
- no host response byte cap
- no device cat byte cap or file-type restriction
## Blindspots
- Static review did not execute the repository beyond reading files; runtime behavior relies on provided validation evidence.
- No cloud/IaC/manifests were present or consulted, so external deployment exposure cannot be established from repository artifacts.
- Actual memory exhaustion severity depends on host timeout, bridge throughput, host memory limits, and where output files are written.
- A real uncompromised device normally emits a generated long-soak JSONL path; exploitation requires spoofed or compromised device/bridge output.
