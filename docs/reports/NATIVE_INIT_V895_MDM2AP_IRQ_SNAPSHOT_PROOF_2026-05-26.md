# V895 MDM2AP IRQ Snapshot Proof Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper build | `tmp/wifi/v895-execns-helper-v143-build/manifest.json` | `v895-helper-v143-build-pass` |
| helper deploy | `tmp/wifi/v895-execns-helper-v143-deploy-safe/manifest.json` | `execns-helper-v143-deploy-pass` |
| live proof | `tmp/wifi/v895-mdm2ap-irq-snapshot-live/manifest.json` | `v895-mdm-status-irq-not-fired-reboot-cleaned` |

V895 proves that the guarded `ESOC_IMG_XFER_DONE` response does not make
SDX50M drive the MDM2AP status IRQ high in the current native path.

## Implementation

- Helper marker: `a90_android_execns_probe v143`.
- Helper sha256:
  `994959b2f70339c25f37d836803c12e9fda10f577cdd3b7452a883efa42f6bc4`.
- Added read-only parsing for `/proc/interrupts` line:
  `msmgpio-dc 142 Edge mdm status`.
- Added snapshots under:
  - `esoc_req_registered_subsys_hold_preflight.snapshot.*`
  - `esoc_conditional_response_preflight.irq_snapshot.*`

## Deploy

- First serial attempt with chunk `3000` was blocked by the line-safety check
  before any chunks were written.
- Safe serial retry with chunk `1850` deployed helper `v143` and verified
  remote sha/mode parity.
- Deploy did not execute live eSoC ioctls, subsystem open, daemon start, or
  Wi-Fi bring-up.

## Live Findings

- `REG_REQ_ENG`: executed and succeeded.
- `ESOC_REQ_IMG`: observed.
- `ESOC_IMG_XFER_DONE`: sent successfully.
- `ESOC_GET_STATUS`: polled `86` times.
- `ESOC_GET_STATUS` last value: `0`.
- `ESOC_BOOT_DONE`: not attempted and not sent.
- IRQ snapshot phases: `89`.
- Parsed GPIO `142` phases: `89`.
- `mdm status` IRQ count before image-done: `0`.
- `mdm status` IRQ count after image-done: `0`.
- Max observed IRQ count during the polling window: `0`.
- IRQ delta: `0`.

## Interpretation

The blocker is below the kernel ready-state setter. The MDM2AP status IRQ did
not fire at all, so this is not a case where the IRQ fired but the kernel failed
to set `mdm->ready`. Current evidence says the SDX50M side never drove the
MDM2AP status line high after native sent `ESOC_IMG_XFER_DONE`.

The most likely next question is whether Android `mdm_helper` performs an
image-transfer or link-establishment contract before sending image-done. A
blind retry, longer polling window, generic command engine, GPIO write, or
blind `BOOT_DONE` would not answer that question.

## Cleanup

- Helper child was not proven stopped, so cleanup reboot ran.
- Post-reboot health recovered.
- Current manual recheck after V895:
  - `bootstatus`: `BOOT OK`, `selftest fail=0`
  - `selftest`: `pass=11 warn=1 fail=0`

## Guardrails

- No `REG_CMD_ENG`.
- No direct userspace `CMD_EXE`.
- No explicit userspace `PWR_ON`.
- No blind `ESOC_BOOT_DONE`.
- No actor start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external
  ping, module load/unload, boot image write, partition write, firmware
  mutation, GPIO/sysfs/debugfs write, or Wi-Fi link-up.

## Next

V896 should be a host-only Android `mdm_helper` / image-transfer contract
classifier. It should determine what Android does between `ESOC_REQ_IMG` and
the eventual MDM2AP status-high transition before any new live mutating eSoC
state-machine attempt.
