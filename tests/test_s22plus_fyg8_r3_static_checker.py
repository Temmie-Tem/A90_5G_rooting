import hashlib
import importlib.util
import io
import struct
import sys
import tarfile
import unittest
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workspace/public/src/scripts/revalidation/s22plus_fyg8_r3_static_checker.py"


def load_module():
    spec = importlib.util.spec_from_file_location("s22plus_fyg8_r3_static_checker_tested", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusFyg8R3StaticCheckerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.geometry = cls.module.BootGeometry(
            total_size=16_384,
            header_end=4_096,
            kernel_start=4_096,
            kernel_end=4_224,
            kernel_pad_end=8_192,
            ramdisk_end=8_292,
            ramdisk_pad_end=12_288,
            signature_end=12_352,
            signer_end=12_880,
            vbmeta_start=13_312,
            vbmeta_end=13_376,
            footer_start=16_320,
        )

    def make_stock(self):
        g = self.geometry
        image = bytearray(g.total_size)
        image[:8] = self.module.ANDROID_MAGIC
        struct.pack_into(
            "<4I",
            image,
            8,
            g.kernel_end - g.kernel_start,
            g.ramdisk_end - g.ramdisk_start,
            0,
            1584,
        )
        struct.pack_into("<I", image, 40, 4)
        struct.pack_into("<I", image, 1580, g.signature_end - g.signature_start)
        kernel = bytearray(g.kernel_end - g.kernel_start)
        struct.pack_into("<IIQQQQQQII", kernel, 0, 1, 2, 0, 256, 10, 0, 7, 0, 0x644D5241, 64)
        kernel[64:] = b"K" * (len(kernel) - 64)
        image[g.kernel_start : g.kernel_end] = kernel
        image[g.ramdisk_start : g.ramdisk_end] = b"R" * (g.ramdisk_end - g.ramdisk_start)
        signer_prefix = self.module.SEANDROID_MAGIC + b"SignerVer02"
        signer = signer_prefix + b"S" * (g.signer_end - g.signer_start - len(signer_prefix))
        image[g.signer_start : g.signer_end] = signer
        image[g.vbmeta_start : g.vbmeta_end] = b"AVB0" + b"V" * (g.vbmeta_end - g.vbmeta_start - 4)
        footer = struct.pack(
            self.module.AVB_FOOTER_FORMAT,
            b"AVBf",
            1,
            0,
            g.signer_end,
            g.vbmeta_start,
            g.vbmeta_end - g.vbmeta_start,
            bytes(28),
        )
        image[g.footer_start :] = footer
        return bytes(image)

    def make_r2_kernel(self, stock):
        g = self.geometry
        kernel = bytearray(stock[g.kernel_start : g.kernel_end])
        kernel[80] ^= 0x5A
        return bytes(kernel)

    @staticmethod
    def make_lz4_frame(payload=b"payload"):
        return (
            b"\x04\x22\x4d\x18"
            + bytes([0x60, 0x40, 0])
            + struct.pack("<I", 0x80000000 | len(payload))
            + payload
            + bytes(4)
        )

    @staticmethod
    def make_tar(payload, *, duplicate=False, typeflag=None, metadata=True):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w", format=tarfile.USTAR_FORMAT) as archive:
            count = 2 if duplicate else 1
            for _ in range(count):
                info = tarfile.TarInfo("boot.img.lz4")
                info.size = len(payload)
                info.mode = 0o644
                info.uid = 0 if metadata else 1000
                info.gid = 0 if metadata else 1000
                info.mtime = 0 if metadata else 1
                if typeflag is not None:
                    info.type = typeflag
                    info.size = 0
                    archive.addfile(info)
                else:
                    archive.addfile(info, io.BytesIO(payload))
        return output.getvalue()

    def test_stock_geometry_and_signer_are_explicit(self):
        stock = self.make_stock()
        signer = stock[self.geometry.signer_start : self.geometry.signer_end]
        result = self.module.validate_stock_boot(
            stock,
            self.geometry,
            hashlib.sha256(signer).hexdigest(),
        )
        self.assertEqual(len(result["regions"]), 11)
        self.assertEqual(result["footer"]["original_image_size"], self.geometry.signer_end)

    def test_stock_rejects_unknown_signer(self):
        stock = bytearray(self.make_stock())
        stock[self.geometry.signer_start] ^= 1
        with self.assertRaisesRegex(self.module.CheckError, "signer record marker"):
            self.module.validate_stock_boot(bytes(stock), self.geometry, "0" * 64)

    def test_r3c0_accepts_only_exact_normalization(self):
        stock = self.make_stock()
        control = self.module.expected_control_bytes(stock, self.geometry)
        result = self.module.validate_control_boot(stock, control, self.geometry)
        self.assertTrue(result["exact_expected_bytes"])
        self.assertTrue(result["exact_stock_vbmeta"])
        self.assertEqual(
            result["footer"]["original_image_size"],
            self.geometry.signer_start + len(self.module.SEANDROID_MAGIC),
        )

    def test_r3c0_rejects_noncontract_delta(self):
        stock = self.make_stock()
        control = bytearray(self.module.expected_control_bytes(stock, self.geometry))
        control[self.geometry.ramdisk_start] ^= 1
        with self.assertRaisesRegex(self.module.CheckError, "outside exact normalized contract"):
            self.module.validate_control_boot(stock, bytes(control), self.geometry)

    def test_r3c1_accepts_kernel_only_delta(self):
        stock = self.make_stock()
        control = self.module.expected_control_bytes(stock, self.geometry)
        r2 = self.make_r2_kernel(stock)
        candidate = bytearray(control)
        candidate[self.geometry.kernel_start : self.geometry.kernel_end] = r2
        result = self.module.validate_candidate_boot(control, bytes(candidate), r2, self.geometry)
        self.assertTrue(result["exact_expected_bytes"])
        self.assertTrue(result["exact_r3c0_vbmeta"])

    def test_r3c1_rejects_nonkernel_delta(self):
        stock = self.make_stock()
        control = self.module.expected_control_bytes(stock, self.geometry)
        r2 = self.make_r2_kernel(stock)
        candidate = bytearray(control)
        candidate[self.geometry.kernel_start : self.geometry.kernel_end] = r2
        candidate[self.geometry.ramdisk_start] ^= 1
        with self.assertRaisesRegex(self.module.CheckError, "outside exact kernel-only contract"):
            self.module.validate_candidate_boot(control, bytes(candidate), r2, self.geometry)

    def test_tar_requires_one_regular_deterministic_member(self):
        frame = self.make_lz4_frame()
        member, parsed = self.module.parse_single_boot_tar(self.make_tar(frame), True)
        self.assertEqual(member["name"], "boot.img.lz4")
        self.assertEqual(parsed, frame)
        with self.assertRaisesRegex(self.module.CheckError, "exactly one"):
            self.module.parse_single_boot_tar(self.make_tar(frame, duplicate=True), True)
        with self.assertRaisesRegex(self.module.CheckError, "non-regular"):
            self.module.parse_single_boot_tar(self.make_tar(frame, typeflag=tarfile.SYMTYPE), True)
        with self.assertRaisesRegex(self.module.CheckError, "metadata uid"):
            self.module.parse_single_boot_tar(self.make_tar(frame, metadata=False), True)

    def test_tar_checksum_corruption_is_rejected(self):
        raw = bytearray(self.make_tar(self.make_lz4_frame()))
        raw[10] ^= 1
        with self.assertRaisesRegex(self.module.CheckError, "checksum"):
            self.module.parse_single_boot_tar(bytes(raw), True)

    def test_tar_non_ustar_header_is_rejected(self):
        raw = bytearray(self.make_tar(self.make_lz4_frame()))
        raw[257:263] = b"legacy"
        raw[148:156] = b"        "
        checksum = sum(raw[:512])
        raw[148:156] = f"{checksum:06o}\0 ".encode("ascii")
        with self.assertRaisesRegex(self.module.CheckError, "POSIX ustar"):
            self.module.parse_single_boot_tar(bytes(raw), True)

    def test_lz4_requires_one_complete_frame(self):
        frame = self.make_lz4_frame(b"abc")
        result = self.module.parse_lz4_frame(frame)
        self.assertEqual(result["block_count"], 1)
        with self.assertRaisesRegex(self.module.CheckError, "trailing or concatenated"):
            self.module.parse_lz4_frame(frame + frame)
        with self.assertRaisesRegex(self.module.CheckError, "truncated"):
            self.module.parse_lz4_frame(frame[:-2])

    def test_ap_md5_trailer_shape_is_exact(self):
        raw = self.make_tar(self.make_lz4_frame())
        trailer = f"{hashlib.md5(raw).hexdigest()}  AP.tar\n".encode("ascii")
        match = self.module.AP_TRAILER_RE.fullmatch(trailer)
        self.assertIsNotNone(match)
        self.assertIsNone(self.module.AP_TRAILER_RE.fullmatch(trailer.replace(b"  ", b" ", 1)))

    def test_sha_pin_must_be_exact_lowercase(self):
        self.assertEqual(self.module.validate_pin("a" * 64, "test"), "a" * 64)
        for value in (None, "a" * 63, "A" * 64, "g" * 64):
            with self.assertRaises(self.module.CheckError):
                self.module.validate_pin(value, "test")

    def test_stage_shape_rejects_ignored_artifacts(self):
        names = (
            "r3c0_boot",
            "r3c0_ap",
            "r3c0_boot_sha256",
            "r3c0_ap_sha256",
            "r3c1_boot",
            "r3c1_ap",
            "r3c1_boot_sha256",
            "r3c1_ap_sha256",
        )
        values = {name: None for name in names}
        values["r3c0_boot"] = Path("ignored.img")
        with self.assertRaisesRegex(self.module.CheckError, "forbids unused"):
            self.module.validate_stage_shape(Namespace(stage="inputs", **values))

    def test_stage_requirements_fail_before_input_audit(self):
        values = {
            "r3c0_boot": None,
            "r3c0_ap": None,
            "r3c0_boot_sha256": None,
            "r3c0_ap_sha256": None,
        }
        with self.assertRaisesRegex(self.module.CheckError, "missing required"):
            self.module.require_stage_args(Namespace(stage="r3c0", **values), tuple(values))


if __name__ == "__main__":
    unittest.main()
