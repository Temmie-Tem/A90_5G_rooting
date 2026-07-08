# S22+ Native-Init M28 Dependency-Complete Live Gate Source (2026-07-08)

## Verdict

SOURCE READY / NO LIVE AUTH: the guarded M28 live-gate helper is implemented
and validates the dependency-complete `S24`/`F43` artifacts, rollback APs, and
DTBO context. The current `AGENTS.md` has no fresh M28 exception, so default
execution fails closed before Android/device access. No flash, reboot,
rollback, partition write, sysfs write, or device action was performed.

## Helper

```text
workspace/public/src/scripts/revalidation/s22plus_m28_dep_complete_live_gate.py
```

Helper SHA256:

```text
83521d521c55ceda8c860a940f8eb334e66638561b785231c5a5b007ad791d3b
```

M28 build manifest:

```text
workspace/private/outputs/s22plus_native_init/m28_dep_complete_download_v0_1/manifest.json
4986940e214dcb32916f5e06806f0cb2342479e82347abec0244edb2a09a250e
```

## Policy Encoded

Authorized source-level candidate sequence:

```text
S24
S24,F43
```

The helper rejects `F43` alone and any non-M28 label such as `P08`. Live order
is `S24` first. If `S24` fails, does not cleanly self-enter Download mode, or
requires operator manual Download, the helper stops and does not run `F43`.

The helper distinguishes the expected proof shape:

- candidate boot AP flashed from an existing Odin endpoint,
- original Odin endpoint must disconnect,
- only a later Odin endpoint may count as clean candidate self-download,
- manual Download is contamination and must not be interpreted as proof.

## Pinned Artifacts

Inherited M25 DTBO context:

```text
M25 high-speed DTBO AP: 35afd774444066fd8e2ffe831da11dd73ee47dce3bdd5b1e37675f82344e56b6
patched raw DTBO:       8962cbbded722c85dbdebfbdc2eba5476b9a64e2a2933888b81f947159eddc17
stock DTBO rollback AP: 6f397421bee84f4ea0c80a8519be0f6f6af84119794970e8a1faaa05f261caaa
stock raw DTBO:         97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c
```

M28 candidates:

| Label | Modules | Modules SHA256 | AP.tar.md5 SHA256 | boot.img SHA256 | /init SHA256 |
| --- | ---: | --- | --- | --- | --- |
| `S24` | 26 | `8c605e2c69aad74f80191bdbc1843b002539d22d49bcffa86bb85bbcb343e5e4` | `c684f6a21bcc9aa50b066b447f4356958fe6d7bfed93edf0ac1b7dcaae8ce75f` | `a1459931001bfd6e17593dd329fc682f00ab61f4841b6543791f5349dd012cd0` | `5c04a2023b2b56ef98746da6f7168121b62d7859cee81c756b80d1a382c1964e` |
| `F43` | 43 | `430050d648d85dd6c3fea459a6cd627a58fd234afe1b485820ccc1f2eb65f87b` | `003ea5760d9e33402750afd7a52b6b95727e4b4cff3f4d3cf66c559eabbb38d1` | `6453b8f2dd685757148056ba8767c2820b0547123f4e5e5e423c4adb0c70496c` | `68de58cd3f05fd77af00984027948ad5ab953ae128dc4133d336e0a521cd588f` |

## Validation

Commands run:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_s22plus_m28_dep_complete_live_gate
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m28_dep_complete_live_gate.py --offline-check
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/s22plus_m28_dep_complete_live_gate.py
```

Results:

- Unit tests: `Ran 9 tests`, `OK`.
- `--offline-check`: verified M28 candidates and rollback APs with no device action.
- Default run: expected fail-closed on missing M28 `AGENTS.md` exception markers
  before Android/device access.

## Next

The next step, if live execution is desired, is a fresh SHA-pinned
`AGENTS.md` exception for this exact helper and artifact matrix. That exception
must authorize only the M28 boot+DTBO live gate, run `S24` first, stop on any
manual Download contamination, and require Magisk boot rollback plus stock DTBO
rollback cleanup.
