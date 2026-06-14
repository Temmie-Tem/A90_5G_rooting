# Native Init V2250 Tail Perf Sampler Full Print Live

## Summary

- Cycle: `V2250`
- Type: rollbackable live test boot of the full-print post-FWREADY perf regs/codeword sampler.
- Decision: `v2250-tail-perf-sampler-full-print-live-pass-no-tail-target-hit`
- Result: PASS for capture contract; PATH-NEGATIVE for the V2246 firmware_class/qcacld-HDD target whitelist under generic CPU-clock sampling.
- Private run: `workspace/private/runs/kernel/v2250-tail-perf-sampler-full-print-live-20260612-124426`
- Test boot: `workspace/private/inputs/boot_images/boot_linux_v2250_tail_perf_sampler_full_print.img`
- Rollback boot: `workspace/private/inputs/boot_images/boot_linux_v2237_supplicant_terminate_poll.img`

## Live Result

- V2250 flash/readback SHA matched: `f74347f8cb23f9d182327683d385406dc11983d6417275883df891c64175a73a`.
- V2250 boot verified: `A90 Linux init 0.9.270 (v2250-tail-perf-sampler-full-print)`.
- V2250 selftest before validation: `fail=0`.
- Helper route result: `wlan0-ready`.
- Tail sampler start marker: `tail_perf_regs_codeword_sampler.started=1`.
- Tail sampler finish marker: `finish.after_fwclass_feeder.output_exists=1`.
- Tail sampler process: `wait_rc=0`, `exit_code=0`, `timed_out=0`.
- Rollback to V2237 verified: `A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)`, selftest `fail=0`.

## Full-Print Check

- Printed samples: `835`.
- Occupied samples: `835`.
- Sample capacity: `1024`.
- Perf stats count: `835`.
- Read errors: `10`.
- Unique `ctx_pc`: `433`.
- Unique `ctx_lr`: `296`.
- Unique comms: `36`.

V2250 removed the V2249 output-loss blocker: every occupied ring entry was emitted and parsed.

## Codeword Slide Check

- Best per-boot slide: `0x1dcef4`.
- Exact PC codeword match: `834/835`.
- LR-4 codeword match: `830/830`.
- LR codeword match: `830/830`.
- Strict exact label: `false`.
- Usable symbolization slide label: `true`.
- Acceptance reason: `lr_exact_single_pc_mismatch`.

The single PC mismatch was inspected host-only. It was in a uaccess/copy-style runtime text patch site where the live instruction was an unprivileged load form while the stock raw byte at the same static location was the paired-load template. The LR and LR-4 codewords were exact for all readable LR samples, and the runner-up slide had only `6` LR matches, so the slide is usable for symbolization while the stricter `exact` label remains false.

## Tail Scoring

- V2247 scorer decision after reanalysis: `v2247-tail-pc-lr-scorer-pass`.
- V2246 target whitelist count: `7`.
- V2247 target hits: `0/835` printed samples.
- Source hit counts: none.
- Symbol hit counts: none.

Targets checked: `_request_firmware`, `request_firmware`, `qdf_file_read`, `qdf_ini_parse`, `cfg_parse`, `hdd_context_create`, and `wlan_hdd_pld_probe`.

## Interpretation

V2250 proves the helper-started tail sampler can run across the post-FWREADY boot_wlan and firmware_class feeder window without output loss. The generic CPU-clock PC/LR sampler did not hit the V2246 firmware_class/qcacld-HDD whitelist in 835 complete samples from the same boot that reached `wlan0-ready`.

This should not be retried as another generic CPU-clock sampling duration tweak. The next T1 unit should switch to a target-specific observable for the post-FWREADY tail: a focused trace/uprobe/kprobe-equivalent read-only path around firmware_class or qcacld/HDD entry points, or a helper-owned user-space/kernel boundary marker that can prove whether those functions execute without depending on random CPU-clock sampling.

## Parser/Scorer Update

- `native_kernel_perf_regs_codeword_sample_ring_v2216.py` now preserves strict `accepted_exact_codeword_slide` but adds `accepted_near_exact_codeword_slide`, `accepted_symbolization_slide`, and `acceptance_reason`.
- `a90_kernel_v2247_tail_pc_lr_scorer.py` now gates scoring on `accepted_symbolization_slide` rather than requiring a strict exact label.
- This keeps exactness semantics intact while allowing a defensible single runtime-patch PC mismatch when LR/LR-4 are exact and the slide is unique.

## Next Unit

Do not rerun V2250 as another generic CPU-clock retry. Build the next bounded T1 unit around a target-specific post-FWREADY observable for the V2246 whitelist or adjacent firmware_class/qcacld-HDD boundary. The goal is to distinguish `function not executed` from `function executed but too narrow for generic CPU-clock sampling`.

## Safety

The live run stayed within the current safety scope: boot partition flash only through `native_init_flash.py`, rollback to V2237, read-only BPF perf-event observation, no `probe_write_user`, no tracefs control write, no eSoC/PCIe/GDSC/PMIC/GPIO path, no Wi-Fi credentials, no DHCP/routes, and no external ping.
