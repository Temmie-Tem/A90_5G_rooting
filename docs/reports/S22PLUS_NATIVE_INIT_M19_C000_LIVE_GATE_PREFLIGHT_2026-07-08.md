# S22+ M19 C000 Live Gate Preflight (2026-07-08)

## Verdict

PASS, preflight only.

Codex added a guarded M19 C000 live gate and a SHA-pinned `AGENTS.md` exception
for exactly one M19 prefix: `C000`. No live flash was executed.

## Scope

M19 C000 is the floor checkpoint from the dependency-closed M19 matrix:

- direct PID1 native `/init`;
- freestanding raw-syscall runtime;
- mount runtime virtual filesystems;
- read the boot-ramdisk `s22plus_m19_closed_usb.modules` text file;
- skip all module loads (`prefix_count=0`, `modules_prefix_skipped`);
- emit `S22_NATIVE_INIT_M19_CLOSED_CHECKPOINT`;
- request Samsung download mode.

Positive proof for a future live run is only a host-observed Odin/download
endpoint after the original candidate-flash Odin endpoint disconnects.

## New Helper

`workspace/public/src/scripts/revalidation/s22plus_m19_c000_checkpoint_live_gate.py`

Modes:

- default dry-run: verify candidate, rollback APs, `AGENTS.md` exception,
  current Android identity, and current boot SHA; no flash;
- `--offline-check`: verify host artifacts only; no device action;
- `--live --ack S22PLUS-M19-C000-CHECKPOINT-LIVE-GATE`: attended candidate
  boot-only flash plus immediate rollback after self-download proof;
- `--rollback-from-download --ack S22PLUS-M19-C000-ROLLBACK-FROM-DOWNLOAD`:
  rollback-only path after operator manual download-mode entry.

## Pinned Candidate

- Candidate AP.tar.md5 SHA256:
  `d712840f1aa7d4ef9d07a7be404b29e5f5dd8065701db7f3d39d76c71296b9d4`
- Candidate boot.img SHA256:
  `0ae71d30257dafdc453db252bd77b11b554202f27c458e3b538d13c61df98ebb`
- Base Magisk boot SHA256:
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`
- Kernel SHA256:
  `bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff`
- M19 C000 init SHA256:
  `7d4f7c8fb30af6aa1e21fe1fe6b24a6597c7385424f5d90e3bf6309a68441135`
- M19 module-list SHA256:
  `c92bb69fd5605cba0ff0aafa44a1ee9f3ac0a66f7e3f1390a19363760e04c94f`
- M19 source SHA256:
  `4c83607d102006b045c32edb0dbb58b1ff14822febc01e8a9da281561522e9af`
- AP tar member: `['boot.img.lz4']`

Rollback APs:

- Magisk boot-only rollback:
  `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`
- Stock boot-only fallback:
  `1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e`

## Safety

The exception authorizes only C000 from the M19 matrix. It does not authorize
C129/C135/C137/C140/C144/C145/C147/C150.

The C000 candidate has:

- boot-only AP package;
- no recovery/vendor_boot/vbmeta/dtbo/non-boot payload;
- no ACM;
- no configfs;
- no USB role force;
- no module binary injection into the boot ramdisk;
- no module load at runtime for this prefix;
- no persistent partition mount;
- no block-device write;
- no Android/Magisk handoff;
- no watchdog touch.

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m19_c000_checkpoint_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m19_c000_checkpoint_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m19_c000_checkpoint_live_gate.py

git diff --check
```

Results:

- `py_compile`: pass.
- `--offline-check`: pass.
- default dry-run: pass.
- `git diff --check`: pass.

Dry-run private log:

`workspace/private/runs/s22plus_m19_c000_checkpoint_live_gate_20260707T171602Z/s22plus_m19_c000_checkpoint_live_gate.txt`

Dry-run evidence:

- `agents_exception_missing=[]`
- candidate AP SHA matched;
- candidate manifest hashes matched;
- rollback AP hashes matched;
- Android preflight matched `SM-S906N` / `g0q` / `S906NKSS7FYG8`;
- `sys.boot_completed=1`;
- Magisk root present;
- current boot SHA matched the pinned Magisk boot baseline;
- host `odin4 -l` snapshot was empty.

## Next

The live command is now prepared but not executed:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m19_c000_checkpoint_live_gate.py \
  --live --ack S22PLUS-M19-C000-CHECKPOINT-LIVE-GATE
```

If C000 self-downloads, rollback must run immediately inside the helper. If it
does not self-download, stop and use only the helper's rollback-from-download
mode after operator manual download-mode entry.
