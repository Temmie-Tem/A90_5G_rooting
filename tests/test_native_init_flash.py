"""Host-only regression tests for native_init_flash safety helpers."""

from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path

from _loader import load_revalidation


flash = load_revalidation("native_init_flash")


class NativeInitFlashSafetyHelpers(unittest.TestCase):
    def test_parse_adb_devices_filters_header_blank_lines_and_keeps_states(self) -> None:
        output = """
List of devices attached

R58M123456 device product:r3q model:SM_A908N
offline-serial offline
recovery-serial recovery
"""

        self.assertEqual(
            flash.parse_adb_devices(output),
            [
                ("R58M123456", "device"),
                ("offline-serial", "offline"),
                ("recovery-serial", "recovery"),
            ],
        )

    def test_normalize_sha256_accepts_none_and_lowercases_valid_hex(self) -> None:
        self.assertIsNone(flash.normalize_sha256(None, label="hash"))
        self.assertEqual(flash.normalize_sha256("A" * 64, label="hash"), "a" * 64)

        for value in ("a" * 63, "g" * 64):
            with self.assertRaisesRegex(RuntimeError, "64-character hex SHA256"):
                flash.normalize_sha256(value, label="hash")

    def test_quote_remote_path_rejects_non_absolute_and_nul_paths(self) -> None:
        self.assertEqual(flash.quote_remote_path("/tmp/native init.img", label="remote"), "'/tmp/native init.img'")

        for path in ("relative.img", "/tmp/bad\x00name"):
            with self.assertRaisesRegex(RuntimeError, "absolute remote path"):
                flash.quote_remote_path(path, label="remote")

    def test_file_contains_finds_markers_across_chunk_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "image.bin"
            needle = b"v2237-marker"
            path.write_bytes(b"A" * (1024 * 1024 - 4) + needle + b"ZZZ")

            self.assertTrue(flash.file_contains(path, needle))
            self.assertFalse(flash.file_contains(path, b"missing-marker"))

    def test_inspect_local_image_accepts_pinned_aligned_image_with_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "boot.img"
            marker = b"A90 Linux init 0.9.268"
            image.write_bytes(marker + b"\0" * (flash.BOOT_READBACK_BLOCK_SIZE - len(marker)))
            image.chmod(0o600)
            expected_hash = flash.local_sha256(image)

            path, digest, size = flash.inspect_local_image(
                types.SimpleNamespace(
                    boot_image=str(image),
                    expect_version=marker.decode(),
                    expect_sha256=expected_hash,
                )
            )

        self.assertEqual(path, image)
        self.assertEqual(digest, expected_hash)
        self.assertEqual(size, flash.BOOT_READBACK_BLOCK_SIZE)

    def test_inspect_local_image_rejects_unsafe_or_unpinned_images(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing = root / "missing.img"
            with self.assertRaises(FileNotFoundError):
                flash.inspect_local_image(
                    types.SimpleNamespace(boot_image=str(missing), expect_version=None, expect_sha256=None)
                )

            image = root / "boot.img"
            image.write_bytes(b"x" * flash.BOOT_READBACK_BLOCK_SIZE)
            image.chmod(0o664)
            with self.assertRaisesRegex(RuntimeError, "group/world writable"):
                flash.inspect_local_image(
                    types.SimpleNamespace(boot_image=str(image), expect_version=None, expect_sha256=None)
                )

            image.chmod(0o600)
            image.write_bytes(b"unaligned")
            with self.assertRaisesRegex(RuntimeError, "4096-byte aligned"):
                flash.inspect_local_image(
                    types.SimpleNamespace(boot_image=str(image), expect_version=None, expect_sha256=None)
                )

            image.write_bytes(b"x" * flash.BOOT_READBACK_BLOCK_SIZE)
            with self.assertRaisesRegex(RuntimeError, "expected version marker not found"):
                flash.inspect_local_image(
                    types.SimpleNamespace(boot_image=str(image), expect_version="missing", expect_sha256=None)
                )

            with self.assertRaisesRegex(RuntimeError, "local image sha256 mismatch"):
                flash.inspect_local_image(
                    types.SimpleNamespace(boot_image=str(image), expect_version=None, expect_sha256="0" * 64)
                )

    def test_sealed_local_image_copy_rejects_source_mutation_and_yields_private_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image = Path(temp_dir) / "boot.img"
            image.write_bytes(b"a" * flash.BOOT_READBACK_BLOCK_SIZE)
            digest = flash.local_sha256(image)
            with flash.sealed_local_image_copy(image, digest, flash.BOOT_READBACK_BLOCK_SIZE) as sealed:
                self.assertNotEqual(sealed, image)
                self.assertEqual(sealed.stat().st_mode & 0o777, 0o600)
                self.assertEqual(flash.local_sha256(sealed), digest)

            image.write_bytes(b"b" * flash.BOOT_READBACK_BLOCK_SIZE)
            with self.assertRaisesRegex(RuntimeError, "sealed image sha256 mismatch"):
                with flash.sealed_local_image_copy(image, digest, flash.BOOT_READBACK_BLOCK_SIZE):
                    pass

            image.write_bytes(b"c")
            with self.assertRaisesRegex(RuntimeError, "boot image size changed before push"):
                with flash.sealed_local_image_copy(image, digest, flash.BOOT_READBACK_BLOCK_SIZE):
                    pass

    def test_verify_cmdv1_result_rejects_nonzero_rc_or_status(self) -> None:
        flash.verify_cmdv1_result(types.SimpleNamespace(rc=0, status="ok", text="fine"), "version")

        for result in (
            types.SimpleNamespace(rc=1, status="ok", text="bad rc"),
            types.SimpleNamespace(rc=0, status="err", text="bad status"),
        ):
            with self.assertRaisesRegex(RuntimeError, "cmdv1 version failed"):
                flash.verify_cmdv1_result(result, "version")


if __name__ == "__main__":
    unittest.main()
