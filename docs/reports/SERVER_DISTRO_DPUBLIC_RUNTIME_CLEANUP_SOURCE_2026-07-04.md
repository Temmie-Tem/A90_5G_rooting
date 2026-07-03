# Server-Distro D-public Runtime Cleanup Source Gate

- Date: 2026-07-04 KST
- Unit: D-public Debian firstboot stale tunnel runtime cleanup.
- Scope: source/static validation only.
- Device action: none. No flash, no rollback, no reboot, no public tunnel start/stop.

## Verdict

D-public firstboot now cleans stale `cloudflared` runtime state before reporting tunnel status.

The live D-public appliance previously proved the Debian handoff, loopback smoke server, HUD, and optional quick
Tunnel path. The remaining rough edge was status hygiene: stale `/run/a90-dpublic/cloudflared-*` pid/log/url files
from earlier runs could make a later manual-mode boot look like a tunnel was still meaningful even when no tunnel
was intentionally started.

This unit keeps public exposure opt-in. In manual mode, firstboot kills any residual `cloudflared tunnel` process,
removes stale cloudflared pid/log/url files, records `cloudflared_runtime_cleanup=manual`, and then records
`tunnel_started=manual`.

## Change

`workspace/public/src/scripts/server-distro/a90_dpublic_firstboot.sh` now adds:

- `kill_pidfile_if_matching`: removes stale pidfiles and only kills the pid if its command line still matches the
  expected process.
- `cleanup_cloudflared_runtime`: stops residual `cloudflared tunnel` processes, removes `cloudflared-*.pid`,
  `cloudflared-*.log`, `cloudflared-*.url`, cloudflared URL sidecars, and `public-url.txt`, then appends a cleanup
  marker when `/run/a90-d3-marker` exists.

The cleanup runs in both branches:

- quick Tunnel enabled: cleanup happens before the new `cloudflared tunnel --no-autoupdate` process starts, so old
  logs and pidfiles do not contaminate the new session.
- manual mode: cleanup happens before `tunnel_started=manual`, so stale tunnel artifacts cannot be mistaken for a
  live public tunnel.

## Validation

Static/source validation:

```text
sh -n workspace/public/src/scripts/server-distro/a90_dpublic_firstboot.sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile tests/test_dpublic_smoke_helpers.py
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_dpublic_smoke_helpers \
  tests.test_prepare_dpublic_preflight
git diff --check
```

## Safety Boundary

- No native-init boot image was built or flashed in this unit.
- No device command, Wi-Fi action, block-device write, PMIC/GPIO/regulator/GDSC write, or display panel init path was
  used.
- The change does not auto-start public exposure; the quick Tunnel branch still requires the explicit
  `/etc/a90-dpublic/cloudflared-quick-enable` opt-in file.
- Public URLs, private run logs, and live tunnel identifiers remain outside git.

## Next Gate

On the next D-public appliance boot, validate:

- manual mode leaves no `cloudflared` process running;
- `/run/a90-d3-marker` contains `cloudflared_runtime_cleanup=manual` before `tunnel_started=manual`;
- stale `/run/a90-dpublic/cloudflared-*` pid/log/url files are absent;
- enable mode still starts a fresh tunnel only when `/etc/a90-dpublic/cloudflared-quick-enable` exists.
