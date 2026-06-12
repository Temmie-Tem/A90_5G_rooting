"""Regression tests for a90harness.evidence output/path helpers.

Uses temporary directories only. No device, live logs, firmware, boot images, or
private workspace artifacts are touched.
"""

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _loader import load_harness


evidence = load_harness("evidence")


class LabelAndPathHelpers(unittest.TestCase):
    def test_safe_artifact_label_sanitizes_and_truncates(self):
        self.assertEqual(evidence.safe_artifact_label("  ../bad label!*  "), "bad-label")
        self.assertEqual(evidence.safe_artifact_label("...---", default="fallback"), "fallback")
        self.assertEqual(evidence.safe_artifact_label("abcdef", max_len=4), "abcd")
        self.assertEqual(evidence.safe_artifact_label("----abcdef", max_len=4), "abcd")

    def test_artifact_path_builders_validate_kinds_and_suffixes(self):
        self.assertEqual(
            evidence.wifi_artifact_dir("runs", "bad label/one", timestamp=False),
            evidence.WIFI_TMP_ROOT / "runs" / "bad-label-one",
        )
        self.assertEqual(
            evidence.tmp_log_dir("kernel", "trace dump", timestamp=False),
            evidence.TMP_LOG_ROOT / "kernel" / "trace-dump",
        )
        self.assertEqual(
            evidence.docs_artifact_path("report/name", suffix="md"),
            evidence.DOC_ARTIFACT_ROOT / "report-name.md",
        )
        self.assertEqual(
            evidence.workspace_public_path("bad kind", "label one", suffix="txt"),
            evidence.WORKSPACE_PUBLIC_ROOT / "bad-kind" / "label-one.txt",
        )
        with self.assertRaises(ValueError):
            evidence.wifi_artifact_root("unknown")
        with self.assertRaises(ValueError):
            evidence.tmp_log_root("unknown")

    def test_workspace_private_roots_honor_env_overrides_and_validate_kinds(self):
        with tempfile.TemporaryDirectory() as tmp:
            override = Path(tmp) / "inputs"
            build_override = Path(tmp) / "builds"
            with patch.dict(
                os.environ,
                {
                    "A90_BOOT_IMAGE_ROOT": str(override),
                    "A90_BUILD_ROOT": str(build_override),
                },
                clear=False,
            ):
                self.assertEqual(
                    evidence.workspace_private_input_root("boot_images"),
                    override,
                )
                self.assertEqual(
                    evidence.workspace_private_input_path("boot_images", "boot.img", legacy_fallback=False),
                    override / "boot.img",
                )
                self.assertEqual(
                    evidence.workspace_private_build_root("helpers"),
                    build_override / "helpers",
                )
                self.assertEqual(
                    evidence.workspace_private_build_path("helpers", "tool"),
                    build_override / "helpers" / "tool",
                )
        with self.assertRaises(ValueError):
            evidence.workspace_private_input_root("bad")
        with self.assertRaises(ValueError):
            evidence.workspace_private_build_root("bad")


class PrivatePublicWriters(unittest.TestCase):
    def test_private_and_public_writers_set_expected_modes_and_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_path = root / "private" / "payload.json"
            public_path = root / "public" / "note.txt"

            evidence.write_private_json(private_path, {"b": 2, "a": 1})
            evidence.write_public_text(public_path, "hello")

            self.assertEqual(json.loads(private_path.read_text()), {"a": 1, "b": 2})
            self.assertEqual(public_path.read_text(), "hello")
            self.assertEqual(stat.S_IMODE(private_path.stat().st_mode), evidence.PRIVATE_FILE_MODE)
            self.assertEqual(stat.S_IMODE(private_path.parent.stat().st_mode), evidence.PRIVATE_DIR_MODE)
            self.assertEqual(stat.S_IMODE(public_path.stat().st_mode), evidence.PUBLIC_FILE_MODE)
            self.assertEqual(stat.S_IMODE(public_path.parent.stat().st_mode), evidence.PUBLIC_DIR_MODE)

    def test_append_private_jsonl_appends_sorted_json_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run" / "events.jsonl"

            evidence.append_private_jsonl(path, {"z": 1, "a": 2})
            evidence.append_private_jsonl(path, {"b": 3})

            self.assertEqual(
                path.read_text().splitlines(),
                ['{"a": 2, "z": 1}', '{"b": 3}'],
            )
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), evidence.PRIVATE_FILE_MODE)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_writers_reject_symlink_destinations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.txt"
            link = root / "link.txt"
            target.write_text("original")
            os.symlink(target, link)

            with self.assertRaises(RuntimeError):
                evidence.write_private_text(link, "replacement")
            with self.assertRaises(RuntimeError):
                evidence.write_public_text(link, "replacement")
            self.assertEqual(target.read_text(), "original")


class BoundedReaders(unittest.TestCase):
    def test_read_bounded_bytes_text_json_accept_regular_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.json"
            path.write_text('{"ok": true}\n')

            self.assertEqual(evidence.read_bounded_bytes(path, max_bytes=32), b'{"ok": true}\n')
            self.assertEqual(evidence.read_bounded_text(path, max_bytes=32), '{"ok": true}\n')
            self.assertEqual(evidence.read_bounded_json(path, max_bytes=32), {"ok": True})

    def test_read_bounded_bytes_rejects_invalid_limits_nonregular_and_oversize(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "payload.bin"
            path.write_bytes(b"abcdef")

            with self.assertRaises(ValueError):
                evidence.read_bounded_bytes(path, max_bytes=0)
            with self.assertRaises(RuntimeError):
                evidence.read_bounded_bytes(path, max_bytes=5)
            with self.assertRaises(RuntimeError):
                evidence.read_bounded_bytes(root, max_bytes=32)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_read_bounded_bytes_rejects_symlink_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.txt"
            link = root / "link.txt"
            target.write_text("secret")
            os.symlink(target, link)

            with self.assertRaises(RuntimeError):
                evidence.read_bounded_bytes(link, max_bytes=32)


class EvidenceStoreTests(unittest.TestCase):
    def test_evidence_store_sanitizes_log_paths_and_writes_private_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = evidence.EvidenceStore(Path(tmp) / "run")

            self.assertEqual(
                store.log_relative_path("host logs", "bad/name.txt"),
                str(Path("logs") / "host-logs" / "bad-name.txt"),
            )
            text_path = store.write_text("notes/out.txt", "text")
            log_path = store.write_log("host logs", "bad/name.txt", "log")
            json_path = store.write_json("summary.json", {"ok": True})
            jsonl_path = store.append_jsonl("events.jsonl", {"event": "one"})
            store.append_jsonl("events.jsonl", {"event": "two"})
            made_dir = store.mkdir("nested", "dir")

            self.assertEqual(text_path.read_text(), "text")
            self.assertEqual(log_path.read_text(), "log")
            self.assertEqual(json.loads(json_path.read_text()), {"ok": True})
            self.assertEqual(
                jsonl_path.read_text().splitlines(),
                ['{"event": "one"}', '{"event": "two"}'],
            )
            self.assertTrue(made_dir.is_dir())
            self.assertEqual(stat.S_IMODE(store.run_dir.stat().st_mode), evidence.PRIVATE_DIR_MODE)
            self.assertEqual(stat.S_IMODE(log_path.stat().st_mode), evidence.PRIVATE_FILE_MODE)


if __name__ == "__main__":
    unittest.main()
