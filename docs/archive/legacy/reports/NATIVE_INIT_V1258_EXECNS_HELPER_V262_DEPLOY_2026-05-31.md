# V1258 Execns Helper v262 Deploy

- report: `docs/reports/NATIVE_INIT_V1258_EXECNS_HELPER_V262_DEPLOY_2026-05-31.md`
- runner: `scripts/revalidation/wifi_execns_helper_v262_deploy_preflight_v1258.py`
- evidence: `tmp/wifi/v1258-execns-helper-v262-deploy/manifest.json`
- result: `execns-helper-v262-deploy-pass`
- pass: `true`

## Scope

V1258 is deploy-only for `a90_android_execns_probe v262`. It installs and verifies
`/cache/bin/a90_android_execns_probe`, then runs read-only postflight checks. It
does not execute the new gpiochip devnode-open mode, create a live device node,
request a GPIO line, write PMIC/GPIO/debugfs or regulator state, open
`/dev/subsys_esoc0`, start PM/CNSS/HAL actors, scan/connect, use credentials,
DHCP/routes, external ping, reboot, flash, boot image write, or partition write.

## Deploy Result

| Field | Value |
| --- | --- |
| helper marker | `a90_android_execns_probe v262` |
| local helper | `stage3/linux_init/helpers/a90_android_execns_probe_v262` |
| remote helper | `/cache/bin/a90_android_execns_probe` |
| SHA-256 | `17773e5bcdec090c061a962833d27a783439e1b718c96b47a504f625d79cc36d` |
| transfer method | serial fallback |
| serial chunks | `1010` |
| serial chunk size | `1800` |
| max cmdv1 line bytes | `3788` / safe limit `3968` |
| postflight selftest | `fail=0` |

The host NCM address was not present during this run, so `auto` transfer fell
back to serial. A too-large `3000` byte serial chunk was rejected by the wrapper's
line-limit preflight before writing any chunks; the committed V1258 wrapper uses
the verified `1800` byte default.

## Validation

| Check | Result |
| --- | --- |
| `python3 -m py_compile scripts/revalidation/wifi_execns_helper_v262_deploy_preflight_v1258.py` | pass |
| `git diff --check` | pass |
| local helper SHA/marker/mode | pass |
| remote helper SHA after deploy | pass |
| remote helper usage marker/mode | pass |
| service-manager process surface | clean |
| Wi-Fi link surface | clean |
| V373 post-deploy preflight | `service-manager-start-only-smoke-approval-required`, pass |

## Interpretation

V1258 closes the deploy gate for helper v262. The device now has the helper needed
for the next bounded live proof:
`wifi-companion-pmic-gpiochip-devnode-open-preflight` with
`--allow-pmic-gpiochip-devnode-open-preflight`.

## Next

V1259 should run only the bounded temporary gpiochip devnode-open proof. The
allowed live action is creating a temporary private char node for gpiochip
`254:2`, opening it read-only, running `GPIO_GET_CHIPINFO_IOCTL`, closing it, and
unlinking it. It must still print/verify `gpio_line_request_executed=0`,
`pmic_write_executed=0`, `esoc_ioctl_executed=0`, `pm_actor_executed=0`,
`cnss_daemon_start_executed=0`, `wifi_hal_start_executed=0`,
`scan_connect_linkup=0`, `credentials=0`, `dhcp_routing=0`, and
`external_ping=0`.

## Safety

- deploy-only; no execution of the new gpiochip devnode-open mode
- no live `mknod`, GPIO line request, PMIC/GPIO/debugfs/regulator write
- no eSoC ioctl, PM actor, CNSS actor, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, reboot, flash, boot image write, or partition write
