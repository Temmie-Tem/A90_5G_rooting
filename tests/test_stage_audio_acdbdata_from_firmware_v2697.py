import struct
import tempfile
import unittest
from pathlib import Path

from workspace.public.src.scripts.revalidation import stage_audio_acdbdata_from_firmware_v2697 as v2697


class TestStageAudioAcdbdataFromFirmwareV2697(unittest.TestCase):
    def test_convert_android_sparse_handles_raw_fill_and_dontcare(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: self.remove_tree(root))
        src = root / "in.sparse"
        dst = root / "out.raw"
        block_size = 4
        chunks = [
            self.chunk(v2697.CHUNK_RAW, 1, b"ABCD"),
            self.chunk(v2697.CHUNK_FILL, 2, struct.pack("<I", 0x11223344)),
            self.chunk(v2697.CHUNK_DONT_CARE, 1, b""),
        ]
        header = struct.pack(
            "<IHHHHIIII",
            v2697.SPARSE_MAGIC,
            1,
            0,
            28,
            12,
            block_size,
            4,
            len(chunks),
            0,
        )
        src.write_bytes(header + b"".join(chunks))

        meta = v2697.convert_android_sparse(src, dst)

        self.assertEqual(meta["block_size"], block_size)
        self.assertEqual(meta["total_blocks"], 4)
        self.assertEqual(meta["chunk_counts"], {"raw": 1, "fill": 1, "dont_care": 1, "crc32": 0})
        self.assertEqual(dst.read_bytes(), b"ABCD" + struct.pack("<I", 0x11223344) * 2 + b"\x00" * 4)

    def test_list_staged_files_reports_size_and_sha(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: self.remove_tree(root))
        staged = root / "acdbdata"
        staged.mkdir()
        (staged / "sample.acdb").write_bytes(b"abc")

        files = v2697.list_staged_files(staged)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["size"], 3)
        self.assertTrue(files[0]["sha256"])

    def chunk(self, chunk_type: int, blocks: int, payload: bytes) -> bytes:
        return struct.pack("<HHII", chunk_type, 0, blocks, 12 + len(payload)) + payload

    def remove_tree(self, path: Path):
        import shutil

        shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
