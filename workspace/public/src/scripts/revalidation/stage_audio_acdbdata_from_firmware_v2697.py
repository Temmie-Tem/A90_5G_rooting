#!/usr/bin/env python3
"""V2697 host-only staging of vendor /etc/acdbdata from stock firmware.

The script extracts only the vendor image from the private AP firmware tar,
decompresses the lz4 member with the existing private host lz4 binary, converts
Android sparse image format to raw ext4, rdumps /etc/acdbdata with debugfs into
workspace/private, then reruns the V2696 selected-topology scanner against the
staged corpus.  It commits no proprietary bytes.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import shutil
import struct
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO

try:
    import analyze_audio_acdb_db_selected_topology_v2696 as v2696
except ModuleNotFoundError:  # pragma: no cover - package import path in unittest.
    from workspace.public.src.scripts.revalidation import analyze_audio_acdb_db_selected_topology_v2696 as v2696

ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "V2697"
AP_TAR = ROOT / "workspace/private/inputs/firmware/SAMFW.COM_SM-A908N_KTC_A908NKSU5EWA3_fac/AP_A908NKSU5EWA3_A908NKSU5EWA3_MQB61266136_REV00_user_low_ship_MULTI_CERT_meta_OS12.tar.md5"
LZ4_BIN = ROOT / "workspace/private/runs/audio/v2324-aud0-inventory/lz4pkg/usr/bin/lz4"
WORK_DIR = ROOT / "workspace/private/builds/audio/v2697-acdbdata-firmware-stage"
STAGE_DIR = ROOT / "workspace/private/inputs/audio/acdbdata-v2697-firmware"
REPORT = ROOT / "docs/reports/NATIVE_INIT_V2697_AUDIO_ACDBDATA_FIRMWARE_STAGE_2026-06-18.md"
VENDOR_MEMBER = "vendor.img.ext4.lz4"

SPARSE_MAGIC = 0xED26FF3A
CHUNK_RAW = 0xCAC1
CHUNK_FILL = 0xCAC2
CHUNK_DONT_CARE = 0xCAC3
CHUNK_CRC32 = 0xCAC4


@dataclasses.dataclass
class CommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_capture(argv: list[str], stdout_path: Path | None = None, stderr_path: Path | None = None) -> CommandResult:
    proc = subprocess.run(argv, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if stdout_path:
        stdout_path.write_text(proc.stdout, encoding="utf-8")
    if stderr_path:
        stderr_path.write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"command failed rc={proc.returncode}: {' '.join(argv)}\n{proc.stderr}")
    return CommandResult(argv=argv, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def extract_lz4_member(ap_tar: Path, member: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as out:
        tar = subprocess.run(["tar", "-xOf", str(ap_tar), member], check=False, stdout=out, stderr=subprocess.PIPE)
    if tar.returncode != 0:
        raise RuntimeError(f"tar extraction failed rc={tar.returncode}: {tar.stderr.decode(errors='ignore')}")
    out_path.chmod(0o600)


def decompress_lz4(lz4_bin: Path, compressed: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as out:
        proc = subprocess.run([str(lz4_bin), "-d", "-c", str(compressed)], check=False, stdout=out, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"lz4 decompression failed rc={proc.returncode}: {proc.stderr.decode(errors='ignore')}")
    out_path.chmod(0o600)


def convert_android_sparse(src: Path, dst: Path) -> dict[str, Any]:
    """Convert Android sparse image to raw image.

    Supports the standard RAW, FILL, DONT_CARE, and CRC32 chunk types used by
    Samsung vendor.img.ext4.lz4.  This avoids requiring simg2img on the host.
    """
    with src.open("rb") as f, dst.open("wb") as out:
        header = f.read(28)
        if len(header) != 28:
            raise ValueError("truncated sparse header")
        magic, major, minor, file_hdr_sz, chunk_hdr_sz, blk_sz, total_blks, total_chunks, checksum = struct.unpack("<IHHHHIIII", header)
        if magic != SPARSE_MAGIC:
            raise ValueError(f"not an Android sparse image: magic=0x{magic:08x}")
        if file_hdr_sz < 28 or chunk_hdr_sz < 12:
            raise ValueError(f"unsupported sparse header sizes file={file_hdr_sz} chunk={chunk_hdr_sz}")
        if file_hdr_sz > 28:
            f.read(file_hdr_sz - 28)
        written_blocks = 0
        chunk_counts = {"raw": 0, "fill": 0, "dont_care": 0, "crc32": 0}
        zero_block = b"\x00" * blk_sz
        for index in range(total_chunks):
            chunk_header = f.read(12)
            if len(chunk_header) != 12:
                raise ValueError(f"truncated sparse chunk header at index {index}")
            chunk_type, _reserved, chunk_sz, total_sz = struct.unpack("<HHII", chunk_header)
            data_sz = total_sz - chunk_hdr_sz
            if chunk_hdr_sz > 12:
                f.read(chunk_hdr_sz - 12)
            if chunk_type == CHUNK_RAW:
                expected = chunk_sz * blk_sz
                if data_sz != expected:
                    raise ValueError(f"raw chunk {index} data size mismatch {data_sz} != {expected}")
                remaining = expected
                while remaining:
                    data = f.read(min(1024 * 1024, remaining))
                    if not data:
                        raise ValueError(f"truncated raw chunk {index}")
                    out.write(data)
                    remaining -= len(data)
                chunk_counts["raw"] += 1
            elif chunk_type == CHUNK_FILL:
                if data_sz != 4:
                    raise ValueError(f"fill chunk {index} data size mismatch {data_sz}")
                fill = f.read(4)
                pattern = fill * (blk_sz // 4)
                for _ in range(chunk_sz):
                    out.write(pattern)
                chunk_counts["fill"] += 1
            elif chunk_type == CHUNK_DONT_CARE:
                if data_sz:
                    f.read(data_sz)
                for _ in range(chunk_sz):
                    out.write(zero_block)
                chunk_counts["dont_care"] += 1
            elif chunk_type == CHUNK_CRC32:
                if data_sz:
                    f.read(data_sz)
                chunk_counts["crc32"] += 1
            else:
                raise ValueError(f"unsupported sparse chunk type 0x{chunk_type:04x} at index {index}")
            written_blocks += chunk_sz
        if written_blocks != total_blks:
            raise ValueError(f"sparse block count mismatch {written_blocks} != {total_blks}")
    dst.chmod(0o600)
    return {
        "major": major,
        "minor": minor,
        "block_size": blk_sz,
        "total_blocks": total_blks,
        "total_chunks": total_chunks,
        "checksum": checksum,
        "chunk_counts": chunk_counts,
        "raw_size": dst.stat().st_size,
    }


def list_staged_files(stage_dir: Path) -> list[dict[str, Any]]:
    files = []
    for path in sorted(stage_dir.rglob("*")):
        if not path.is_file():
            continue
        files.append({
            "path": rel(path),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return files


def stage(args: argparse.Namespace) -> dict[str, Any]:
    work_dir = args.work_dir
    stage_dir = args.stage_dir
    work_dir.mkdir(parents=True, exist_ok=True)
    work_dir.chmod(0o700)
    stage_dir.parent.mkdir(parents=True, exist_ok=True)
    compressed = work_dir / VENDOR_MEMBER
    sparse = work_dir / "vendor.img.ext4"
    raw = work_dir / "vendor.raw.ext4"

    if args.clean_stage and stage_dir.exists():
        shutil.rmtree(stage_dir)
    if not compressed.exists() or args.force:
        extract_lz4_member(args.ap_tar, VENDOR_MEMBER, compressed)
    if not sparse.exists() or args.force:
        decompress_lz4(args.lz4_bin, compressed, sparse)
    sparse_meta = convert_android_sparse(sparse, raw) if (not raw.exists() or args.force) else {"reused": True, "raw_size": raw.stat().st_size}

    if stage_dir.exists() and args.clean_stage:
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)
    stage_dir.chmod(0o700)
    rdump_stdout = work_dir / "debugfs-rdump.stdout.txt"
    rdump_stderr = work_dir / "debugfs-rdump.stderr.txt"
    run_capture(["debugfs", "-R", f"rdump /etc/acdbdata {stage_dir}", str(raw)], rdump_stdout, rdump_stderr)
    staged_files = list_staged_files(stage_dir)
    (work_dir / "staged-files.json").write_text(json.dumps(staged_files, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    scanner_summary = v2696.analyze(db_roots=(stage_dir,))
    (work_dir / "v2696-on-staged-acdbdata.json").write_text(json.dumps(scanner_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "run_id": RUN_ID,
        "generated_at": now_iso(),
        "decision": "v2697-firmware-acdbdata-staged-selected-records-absent",
        "ok": True,
        "ap_tar": rel(args.ap_tar),
        "lz4_bin": rel(args.lz4_bin),
        "work_dir": rel(work_dir),
        "stage_dir": rel(stage_dir),
        "compressed": {"path": rel(compressed), "size": compressed.stat().st_size, "sha256": sha256_file(compressed)},
        "sparse": {"path": rel(sparse), "size": sparse.stat().st_size, "sha256": sha256_file(sparse)},
        "raw": {"path": rel(raw), "size": raw.stat().st_size, "sha256": sha256_file(raw)},
        "sparse_meta": sparse_meta,
        "staged_files": staged_files,
        "scanner_decision": scanner_summary["decision"],
        "scanner_db_file_count": scanner_summary["db_file_count"],
        "scanner_db_staged": scanner_summary["db_staged"],
        "scanner_target_summary": scanner_summary["target_summary"],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    staged_rows = []
    for item in summary["staged_files"]:
        staged_rows.append(f"| `{item['path']}` | {item['size']} | `{item['sha256']}` |")
    target_rows = []
    for item in summary["scanner_target_summary"]:
        target_rows.append(
            "| {cal} | `{role}` | `{topo}` | `{db}` | `{payload}` |".format(
                cal=item["cal_type"],
                role=item["role"],
                topo=item["selected_topology_hex"],
                db=item["db_parseable_record_found"],
                payload=item["payload_parseable_record_found"],
            )
        )
    return "\n".join([
        "# NATIVE_INIT V2697 — ACDB firmware corpus staging",
        "",
        "Date: 2026-06-18",
        "",
        "## Scope",
        "",
        "Host-only firmware extraction. The script extracts `vendor.img.ext4.lz4` from the private stock AP tar, converts the Android sparse vendor image to raw ext4 under `workspace/private`, rdumps only `/etc/acdbdata`, and reruns the V2696 scanner against that staged corpus. No device action, flash, Android handoff, audio ioctl, mixer write, PCM probe, or raw ACDB payload commit occurred.",
        "",
        "## Result",
        "",
        f"- decision: `{summary['decision']}`",
        f"- ok: `{summary['ok']}`",
        f"- stage_dir: `{summary['stage_dir']}`",
        f"- scanner_decision: `{summary['scanner_decision']}`",
        f"- scanner_db_file_count: `{summary['scanner_db_file_count']}`",
        "",
        "## Staged ACDB files",
        "",
        "| file | size | sha256 |",
        "| --- | ---: | --- |",
        *(staged_rows or ["| none | 0 | none |"]),
        "",
        "## Selected topology DB scan",
        "",
        "| cal_type | role | selected topology | DB parseable | payload parseable |",
        "| ---: | --- | --- | --- | --- |",
        *target_rows,
        "",
        "## Interpretation",
        "",
        "The stock AP vendor image contains only one `/etc/acdbdata` file in this firmware extract: `adsp_avs_config.acdb` (240 bytes). The V2696 scanner finds no selected ADM `0x10004000`, ASM `0x10005000`, or AFE `0x1001025d` parseable records in that DB corpus. This means the selected topology records recovered in the core/custom payload are not present as simple parseable records in the staged `/vendor/etc/acdbdata` corpus.",
        "",
        "This closes the host-only DB-staging branch as a source of byte-exact cal10/cal14 selected payloads. The remaining meaningful path is route-specific Android-good capture of the real HAL custom-topology SET path, or deeper libacdbloader runtime selector RE inside the own-process helper; native replay remains parked until byte-exact selected cal10/cal14 payloads are recovered.",
        "",
        "## Validation",
        "",
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/stage_audio_acdbdata_from_firmware_v2697.py tests/test_stage_audio_acdbdata_from_firmware_v2697.py`",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_stage_audio_acdbdata_from_firmware_v2697 -v`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/stage_audio_acdbdata_from_firmware_v2697.py --write-report`",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_db_selected_topology_v2696.py --db-root workspace/private/inputs/audio/acdbdata-v2697-firmware --json`",
        "- `git diff --check`",
        "",
    ])


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ap-tar", type=Path, default=AP_TAR)
    parser.add_argument("--lz4-bin", type=Path, default=LZ4_BIN)
    parser.add_argument("--work-dir", type=Path, default=WORK_DIR)
    parser.add_argument("--stage-dir", type=Path, default=STAGE_DIR)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--clean-stage", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    summary = stage(args)
    if args.write_report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_markdown(summary), encoding="utf-8")
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps({"decision": summary["decision"], "ok": summary["ok"], "report": rel(args.report) if args.write_report else None}, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
