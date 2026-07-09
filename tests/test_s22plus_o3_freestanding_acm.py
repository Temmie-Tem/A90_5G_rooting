import json
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NATIVE_DIR = ROOT / "workspace/public/src/native-init"
SOURCE = NATIVE_DIR / "s22plus_init_o3f_freestanding_acm.c"
PROTOCOL = NATIVE_DIR / "s22plus_o3_freestanding_protocol.h"
HOST_TEST = ROOT / "tests/s22plus_o3_freestanding_protocol_test.c"
PLAN_DIR = ROOT / "workspace/private/outputs/s22plus_native_init/o3_minimal_acm_plan_v0_2"
BUILDER = ROOT / "workspace/public/src/scripts/revalidation/build_s22plus_o3f_freestanding_acm.py"
OUTPUT_DIR = ROOT / "workspace/private/outputs/s22plus_native_init/o3f_freestanding_acm_v0_1"
MANIFEST = OUTPUT_DIR / "manifest.json"

EXPECTED_HASHES = {
    "base_boot": "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e",
    "kernel": "bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff",
    "plan_tsv": "a34ebbad3b5d770f133e37a450cc3007e4a84ab831788484680e88aad6b3d534",
    "plan_header": "45727cff30952096d9604682a3ba3d284807a75e6622ed4c8ae57bc153d5b863",
}


class S22PlusO3FreestandingAcmTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("cc"), "host C compiler unavailable")
    def test_protocol_core_host_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "protocol-test"
            built = subprocess.run(
                [
                    "cc",
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(NATIVE_DIR),
                    str(HOST_TEST),
                    "-o",
                    str(binary),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            result = subprocess.run([str(binary)], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "s22plus_o3_freestanding_protocol_test=PASS")

    @unittest.skipUnless(shutil.which("aarch64-linux-gnu-gcc"), "arm64 compiler unavailable")
    @unittest.skipUnless(PLAN_DIR.is_dir(), "pinned O3 plan unavailable")
    def test_arm64_init_is_small_freestanding_and_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "init"
            command = [
                "aarch64-linux-gnu-gcc",
                "-std=gnu11",
                "-nostdlib",
                "-static",
                "-ffreestanding",
                "-fno-builtin",
                "-fno-stack-protector",
                "-fno-asynchronous-unwind-tables",
                "-fno-unwind-tables",
                "-Os",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-Wl,--build-id=none",
                "-Wl,-e,_start",
                "-Wl,-z,noexecstack",
                "-I",
                str(NATIVE_DIR),
                "-I",
                str(PLAN_DIR),
                str(SOURCE),
                "-o",
                str(binary),
            ]
            built = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            file_info = subprocess.run(["file", str(binary)], text=True, capture_output=True, check=False)
            readelf = subprocess.run(
                ["aarch64-linux-gnu-readelf", "-h", "-l", str(binary)],
                text=True,
                capture_output=True,
                check=False,
            )
            undefined = subprocess.run(
                ["aarch64-linux-gnu-nm", "-u", str(binary)],
                text=True,
                capture_output=True,
                check=False,
            )
            strings = subprocess.run(
                ["strings", "-a", str(binary)], text=True, capture_output=True, check=False
            )
            size = binary.stat().st_size
        self.assertIn("ARM aarch64", file_info.stdout)
        self.assertIn("statically linked", file_info.stdout)
        self.assertNotIn("INTERP", readelf.stdout)
        self.assertEqual(undefined.stdout.strip(), "")
        self.assertLess(size, 131072)
        for token in [
            "S22_NATIVE_INIT_O3F_FREESTANDING_ACM",
            "runtime=freestanding",
            "raw_syscalls=1",
            "S22O3FACM01",
            "O3 STATUS",
            "acm.usb0",
            "a600000.dwc3",
        ]:
            self.assertIn(token, strings.stdout)
        for token in ["ld-linux", "libc.so", "/system/bin/init", "ss_acm", "max77705"]:
            self.assertNotIn(token, strings.stdout)

    def test_source_preserves_o3_contract_without_reboot_or_exec(self):
        text = SOURCE.read_text(encoding="ascii")
        for required in [
            "s22plus_o2_execute_module_plan",
            "s22plus_o2_scan_proc_modules",
            "S22PLUS_O2_BIND_GATE_COUNT",
            "phase=entry-pre-mount",
            '"/config/usb_gadget/g1/functions/acm.usb0"',
            '"/sys/devices/platform/soc/a600000.ssusb/mode", "peripheral"',
            '"/config/usb_gadget/g1/UDC", "a600000.dwc3"',
            "o3f_control_loop(&state)",
        ]:
            self.assertIn(required, text)
        for forbidden in [
            "NR_REBOOT",
            "NR_EXECVE",
            "execve(",
            "system(",
            "functionfs",
            "ffs.adb",
            "ss_acm",
            "max77705",
            "/sys/module/eud/parameters/enable",
            "sysrq",
            "/system/bin/init",
        ]:
            self.assertNotIn(forbidden.lower(), text.lower())
        self.assertNotIn("none", text.split("/config/usb_gadget/g1/UDC", 1)[1][:80])
        self.assertIn("if (amount == 0)", text)
        eof_branch = text.split("if (amount == 0)", 1)[1].split("continue;", 1)[0]
        self.assertIn("o3f_close((int)fd)", eof_branch)
        self.assertIn("fd = -1", eof_branch)

    def test_protocol_header_is_bounded_and_structured(self):
        text = PROTOCOL.read_text(encoding="ascii")
        self.assertIn("S22PLUS_O3F_MAX_PAYLOAD 1024U", text)
        self.assertIn("S22PLUS_O3F_FRAME_CRC", text)
        self.assertIn("frame_length != S22PLUS_O3F_HEADER_SIZE", text)
        self.assertNotIn("malloc", text)

    def test_builder_is_host_only_and_pins_the_fyg8_inputs(self):
        text = BUILDER.read_text(encoding="ascii")
        for required in [
            "o2.verify_fyg8_pins(metadata)",
            "o2.verify_o3_minimal_acm_plan_identity(metadata, plan)",
            "EXPECTED_BASE_BOOT_SHA256",
            'members != ["boot.img.lz4"]',
            '"live_flash_authorized": False',
            '"requires_new_sha_pinned_agents_exception_before_flash": True',
            '"kernel_changed": False',
            '"module_binary_injection": False',
        ]:
            self.assertIn(required, text)
        for forbidden in ["subprocess.run([\"adb\"", "odin4 flash", "heimdall flash"]:
            self.assertNotIn(forbidden, text)

    @unittest.skipUnless(MANIFEST.is_file(), "O3F build manifest unavailable")
    def test_real_manifest_matches_host_only_artifact_contract(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "s22plus_o3f_freestanding_acm_build_v1")
        self.assertEqual(data["target"], "SM-S906N/g0q/S906NKSS7FYG8")
        self.assertEqual(data["tar_members"], ["boot.img.lz4"])
        self.assertEqual(data["plan"]["module_count"], 59)
        self.assertEqual(data["ramdisk"]["replaced_entry"], "init")
        self.assertEqual(data["ramdisk"]["added_entries"], [])
        self.assertEqual(data["ramdisk"]["module_files_injected"], 0)
        for name, expected in EXPECTED_HASHES.items():
            self.assertEqual(data["hashes"][name], expected)
        self.assertEqual(
            data["hashes"]["source"],
            hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            data["hashes"]["protocol_header"],
            hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        )
        safety = data["safety"]
        self.assertTrue(safety["boot_only"])
        self.assertTrue(safety["host_only_build"])
        self.assertTrue(safety["requires_new_sha_pinned_agents_exception_before_flash"])
        for key in [
            "live_flash_authorized",
            "auto_reboot",
            "reboot_syscall",
            "block_device_writes",
            "kernel_changed",
            "module_binary_injection",
            "daemon_exec",
        ]:
            self.assertFalse(safety[key], key)


if __name__ == "__main__":
    unittest.main()
