# S22+ M34 S10C0 Direct-Finit Loader Audit Live Gate Source

Date: 2026-07-09 20:42 KST / 2026-07-09 11:42 UTC

## Verdict

S10C0 live-gate source is ready and host-validated. No flash, reboot, ADB
write, Odin transfer, or device action was performed.

`AGENTS.md` was not modified. There is still no active S10C0 live
authorization.

## Helper

New helper:

```text
workspace/public/src/scripts/revalidation/s22plus_m34_s10c0_direct_finit_loader_audit_live_gate.py
```

New tests:

```text
tests/test_s22plus_m34_s10c0_direct_finit_loader_audit_live_gate.py
```

The helper pins the S10C0 artifact from:

```text
workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_13/
```

S10C0 candidate hashes:

```text
AP.tar.md5  9221cfa3ea3ce0776860a5041981e23a84d0be9b833203401dab771897266c6f
boot.img    8d77e1434cd47fe47f4723c948e4ff6db759cbe4bf75dd21e9e0c265d928c6df
/init       cd80d5923c94f8a423821bc6dee4547f22763e177fbcc637d1bcb101c4b8c39b
modules     c07425f4c738b53822e9f6783a142a2b5eafd72a15bd34c06fb3b49357c8fe26
template    e7c8e62487701d6af31b5e7bc060a12091a5f55737aec67c4b45be484f67666b
kernel      bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
base boot   2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

## Runtime Predicate

S10C0 checks the direct loader result for `cmd-db.ko`, not `/proc/modules`.

Expected native-init record:

```text
phase=s10c_module_loader_audit_probe
predicate=cmd_db_finit_accepted
present=<0|1>
modules_open_rc=<rc>
modules_read_rc=<rc>
attempted=<count>
expected=89
ok=<count>
eexist=<count>
fail=<count>
first_fail_index=<index>
first_fail_rc=<rc>
first_fail_name=<module|none>
cmd_db_seen=<0|1>
cmd_db_rc=<rc>
true_action=reboot_download
false_action=park
```

HIT means `cmd-db.ko` was attempted and its `finit_module` rc was `0` or
`-EEXIST`; the candidate then requests Download mode. MISS means `cmd-db.ko`
was not attempted or direct `finit_module` failed; the candidate parks and
requires manual Download rollback.

## Rollback Artifacts

Primary rollback remains the known Magisk boot AP:

```text
workspace/private/outputs/s22plus_magisk_root_boot_only/AP.tar.md5
d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
```

The previous canonical stock boot fallback file had been removed during
private-output cleanup, so a S10C0-specific stock boot-only fallback AP was
regenerated from the retained FYG8 stock raw boot image. The raw boot image
matches the known stock boot SHA256:

```text
stock raw boot 4150b962314e6136acba61b20f471d6ee1c418b83cf8c3ee4d9cf7c91a3640ae
```

Regenerated fallback AP:

```text
workspace/private/outputs/s22plus_native_init/odin4_stock_rollback_fyg8_raw_repacked_20260709/AP.tar.md5
2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94
```

This regenerated AP is S10C0-specific and is pinned by the S10C0 helper. It
does not replace the older global `1ee92a86...` contract used by historical
helpers.

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/s22plus_m34_s10c0_direct_finit_loader_audit_live_gate.py
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests/test_s22plus_m34_s10c0_direct_finit_loader_audit_live_gate.py
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m34_s10c0_direct_finit_loader_audit_live_gate.py --offline-check --run-dir workspace/private/runs/s22plus_m34_s10c0_direct_finit_loader_audit_offline_check_20260709T114208Z
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests/test_s22plus_m34_s10c0_direct_finit_loader_audit_live_gate.py tests/test_s22plus_m34_s10b0_module_load_prefix_live_gate.py tests/test_s22plus_m34_runtime_gadget_split_build.py
```

Result:

```text
py_compile: ok
unittest: Ran 6 tests, OK
offline-check: ok
combined unittest: Ran 17 tests, OK, skipped=2
```

AGENTS candidate path was also exercised without writing `AGENTS.md`:

```text
--write-agents-candidate /tmp/.../AGENTS.s10c0.candidate.md
--verify-agents-candidate /tmp/.../AGENTS.s10c0.candidate.md
```

Both commands passed and performed no device action.

## Next

If proceeding live, insert the exact generated active S10C0 exception into
`AGENTS.md`, run default dry-run against the current rooted Android baseline,
then require explicit operator approval with the S10C0 live ack token. Do not
flash S10C0 from the source-ready state alone.
