# Native Init V2178 Wi-Fi Profile Autoconnect Plan

Date: `2026-06-09`

## Goal

Turn the verified manual Wi-Fi command surface into an explicitly gated
persistent-profile and boot-autoconnect feature without leaking credentials or
making boot networking implicit by default.

Current anchor:

- Baseline boot/init: `A90 Linux init 0.9.251 (v2174-wifi-urandom-connect)`.
- Validated test route: V2176 connect → DHCP → bounded ping, N=3 clean.
- Validated stability route: V2177 connect → DHCP → 180s hold → cleanup →
  reconnect → DHCP → bounded ping → cleanup, rollback/selftest clean.
- Existing commands:
  - `wifi config status`
  - `wifi config prepare [profile]`
  - `wifi status`
  - `wifi scan [delay_ms]`
  - `wifi connect [profile]`
  - `wifi dhcp [profile]`
  - `wifi cleanup`

## Non-Goals

- Do not put SSID/PSK or generated `wpa_supplicant.conf` into public git,
  reports, bridge logs, or uploaded artifacts.
- Do not enable boot autoconnect unless an explicit config says
  `autoconnect=1`.
- Do not run external ping at boot.
- Do not implement Wi-Fi scan/connect through Android Wi-Fi HAL, framework
  services, credentials store, or NetworkManager.
- Do not make `wifi connect` install DHCP/routes; keep association and DHCP as
  separate primitives.

## Design Decision

Use the existing `a90_wificfg.c` config parser and `a90_wifi.c` connect/DHCP
implementation. Add only the missing control plane:

1. profile inventory/status commands;
2. explicit autoconnect status/enable/disable/once commands;
3. a boot-time background autoconnect worker that is disabled by default;
4. a host-side profile staging helper for secret-safe file creation.

Do not add raw-secret arguments to native `wifi profile add`. Passing PSK over
serial command arguments is too easy to leak through host shell history,
cmdv1 transcripts, or bridge logs. The first implementation should stage
profile files from the host using a redacted helper, then let native-init
validate and consume those files.

## Config Layout

Use the existing paths already implemented in `a90_wificfg.c`:

| Purpose | Path |
| --- | --- |
| Persistent config root | `/mnt/sdext/a90/config/wifi/` |
| Persistent secret root | `/mnt/sdext/a90/secrets/wifi/` |
| Cache fallback config root | `/cache/a90-wifi/config/` |
| Runtime root | `/cache/a90-wifi/` |
| Generated supplicant config | `/cache/a90-wifi/wpa_supplicant.conf` |
| Supplicant ctrl dir | `/cache/a90-wifi/sockets/` |
| Runtime HUD/status summary | `/cache/native-init-wifi-runtime.summary` |
| Optional runtime input summary | `/cache/native-init-wifi-runtime-input.summary` |

Persistent files:

```text
/mnt/sdext/a90/config/wifi/autoconnect.conf
/mnt/sdext/a90/config/wifi/profiles/<profile>.conf
/mnt/sdext/a90/secrets/wifi/<profile>.ssid
/mnt/sdext/a90/secrets/wifi/<profile>.psk
```

Mode rules:

- directories: `0700`;
- config files: `0600`;
- secret files: `0600`;
- symlink secret files: reject;
- inline `ssid=`, `psk=`, or `password=` in profile metadata: reject.

## Config Format

`autoconnect.conf`:

```ini
version=1
autoconnect=0
default_profile=home5g
connect_timeout_sec=35
dhcp=1
external_ping=0
scan_before_connect=1
retry_count=1
```

`profiles/home5g.conf`:

```ini
version=1
enabled=1
ssid_file=/mnt/sdext/a90/secrets/wifi/home5g.ssid
psk_file=/mnt/sdext/a90/secrets/wifi/home5g.psk
band=5g
priority=100
key_mgmt=WPA-PSK
```

Initial support target:

- `key_mgmt=WPA-PSK` only;
- one selected default profile for boot autoconnect;
- multiple profiles may be listed/statused, but automatic priority roaming is
  out of scope for V2178.

## Native Command Surface

Add:

```text
wifi profile list
wifi profile status [profile]
wifi autoconnect status
wifi autoconnect enable [profile]
wifi autoconnect disable
wifi autoconnect once [profile]
```

Command behavior:

- `wifi profile list`
  - prints profile names, source, enabled, band, priority, key management, and
    secret presence booleans only;
  - does not read or print SSID/PSK values.
- `wifi profile status [profile]`
  - validates a specific profile or the default profile;
  - reuses the same checks as `wifi config status` and
    `wifi config prepare`.
- `wifi autoconnect status`
  - prints global autoconnect state, default profile, DHCP flag, retry count,
    and current runtime summary decision.
- `wifi autoconnect enable [profile]`
  - validates the selected profile first;
  - writes or updates persistent `autoconnect.conf` with `autoconnect=1`;
  - fails closed if the persistent config root is not writable;
  - does not generate supplicant config or connect.
- `wifi autoconnect disable`
  - writes `autoconnect=0`;
  - does not clean up an existing live connection unless the operator also runs
    `wifi cleanup`.
- `wifi autoconnect once [profile]`
  - runs the same sequence the boot worker would run, but explicitly from the
    operator command path;
  - may print redacted command telemetry like the existing `wifi connect` and
    `wifi dhcp` commands.

## Boot Worker

Hook point:

- after console attach, auto-HUD start, and netservice/rshell start;
- before `shell_loop()`;
- spawn a child and return immediately so the serial shell stays responsive.

Worker flow:

1. Read `autoconnect.conf`.
2. Exit with summary `wifi-autoconnect-disabled` if missing or
   `autoconnect=0`.
3. Reject `external_ping=1`.
4. Validate default profile and secret file modes.
5. Wait for `wlan0` using the same bounded readiness as `wifi connect`.
6. Optionally run a bounded scan if `scan_before_connect=1`.
7. Generate `/cache/a90-wifi/wpa_supplicant.conf`.
8. Start/reuse standalone `wpa_supplicant`.
9. Wait for carrier.
10. If `dhcp=1`, run bounded `wifi dhcp`.
11. Write safe runtime summary and autoconnect result file.
12. Leave the connection up on success.

Worker output:

- write detailed redacted output to `/cache/a90-wifi/autoconnect.log`;
- write machine-readable result to `/cache/a90-wifi/autoconnect.result`;
- update `/cache/native-init-wifi-runtime.summary`;
- do not print to serial while running in boot-background mode.

Implementation note:

- Existing `a90_wifi_connect_profile()` and `a90_wifi_dhcp_profile()` print to
  `a90_console_printf()`. For boot-background mode, either add quiet backend
  variants or silence the inherited console fd in the forked child and emit a
  separate result file. The preferred V2178 path is minimal: add a child-only
  console-silence helper and high-level autoconnect result summary, avoiding a
  broad connect/DHCP refactor.

## Host Staging Helper

Add a public helper script:

```text
workspace/public/src/scripts/revalidation/a90_wifi_profile_stage.py
```

Inputs:

- `A90_WIFI_ENV_FILE`;
- profile name;
- optional band/priority/default/autoconnect flags.

Outputs on device:

- profile metadata file;
- SSID secret file;
- PSK secret file;
- optional `autoconnect.conf` with `autoconnect=0` by default.

Rules:

- never print raw SSID/PSK;
- upload only via selected bridge/transport path;
- chmod/chown files on device;
- run `wifi config status` and `wifi config prepare <profile>` after staging;
- secret scan any produced public artifact against raw and hex-encoded secrets.

## Build And Run Numbering

Recommended next unit:

- build/run ID: `V2178`;
- native init version: `0.9.253`;
- build tag: `v2178-wifi-profile-autoconnect`;
- builder:
  `workspace/public/src/scripts/revalidation/build_native_init_boot_v2178_wifi_profile_autoconnect.py`;
- test image:
  `workspace/private/inputs/boot_images/boot_linux_v2178_wifi_profile_autoconnect.img`;
- rollback image:
  `workspace/private/inputs/boot_images/boot_linux_v2174_wifi_urandom_connect.img`.

## Validation Matrix

### Host/static

- `py_compile` changed Python scripts.
- Native C build passes.
- PBKDF2 vector remains passing.
- `git diff --check` passes.
- Secret scan finds no SSID/PSK in tracked public files.

### Live gate 1: autoconnect disabled

- Flash V2178 over V2174.
- No profile staged or `autoconnect=0`.
- Verify:
  - no automatic supplicant start;
  - no automatic scan/connect/DHCP/default route;
  - shell/bridge remains responsive;
  - `selftest fail=0`;
  - rollback to V2174 passes.

### Live gate 2: profile staging

- Stage one 2.4 GHz profile and one 5 GHz profile from
  `workspace/private/secrets/a90-wifi-test.env`.
- Verify:
  - `wifi profile list`;
  - `wifi profile status <profile>`;
  - `wifi config prepare <profile>`;
  - generated config mode/owner only;
  - `secret_values_logged=0`.

### Live gate 3: explicit once

- Run `wifi autoconnect once <profile>`.
- Verify:
  - carrier up;
  - DHCP pass if config says `dhcp=1`;
  - bounded external ping only from the harness, not boot worker;
  - `wifi cleanup` clears residue.

### Live gate 4: boot autoconnect

- Enable autoconnect for one profile.
- Reboot/flash V2178.
- Verify:
  - background worker starts and exits or holds connection without blocking
    serial shell;
  - carrier and DHCP are established;
  - no external ping at boot;
  - HUD/status summary updates;
  - cleanup/disable works;
  - rollback to V2174 and `selftest fail=0`.

### Live gate 5: band coverage

- Repeat explicit once or boot autoconnect for both configured target bands:
  - 2.4 GHz profile;
  - 5 GHz profile.

## Promotion Criteria

Do not promote V2178 or newer until:

- `autoconnect=0` boot is behaviorally equivalent to V2174 except for new
  inert commands;
- explicit autoconnect once succeeds;
- boot autoconnect succeeds without blocking bridge/shell;
- both target bands have at least one successful connect/DHCP/ping validation;
- cleanup/disable leaves no stale supplicant, DHCP pidfile, DNS, or route
  residue;
- rollback to V2174 reports `selftest fail=0`;
- public reports remain redacted.

## Risks

- SD card availability: persistent profile storage depends on `/mnt/sdext`.
  Fail closed if it is absent or read-only.
- Boot output contamination: boot worker must not print detailed connect/DHCP
  telemetry to serial while the operator shell is active.
- Stale runtime state: runtime summaries must distinguish stale prior success
  from current boot autoconnect result.
- Secret handling: native commands must not accept raw PSK as argv; use the
  host staging helper or pre-created private files.
- Long first-connect latency: V2177 saw an initial connect window over two
  minutes. Autoconnect must remain backgrounded and bounded so it does not make
  boot feel hung.

