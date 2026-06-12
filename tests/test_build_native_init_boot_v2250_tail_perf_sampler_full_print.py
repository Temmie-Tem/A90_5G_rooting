"""Regression tests for build_native_init_boot_v2250_tail_perf_sampler_full_print."""

import json
import tempfile
import types
import unittest
from pathlib import Path

from _loader import load_revalidation

v2250 = load_revalidation("build_native_init_boot_v2250_tail_perf_sampler_full_print")


def nested_namespace(*names, leaf):
    current = leaf
    for name in reversed(names):
        current = types.SimpleNamespace(**{name: current})
    return current


def fake_base_args():
    return [
        "--cycle", "OLD",
        "--decision", "old-decision",
        "--cycle-label", "old-label",
        "--init-version", "0.0.0",
        "--init-build", "old-build",
        "--out-dir", "old-out",
        "--init-binary", "old-init",
        "--helper-binary", "old-helper",
        "--ramdisk-cpio", "old-ramdisk",
        "--boot-image", "old-boot",
        "--wifi-test-klog-prefix", "OLD",
        "--wifi-test-disable", "old-disable",
        "--wifi-test-log", "old-log",
        "--wifi-test-summary", "old-summary",
        "--wifi-test-helper-result", "old-helper-result",
        "--wifi-test-pid", "old-pid",
        "--wifi-test-watcher-pid", "old-watcher",
        "--wifi-test-property-root", "old-prop",
        "--wifi-test-helper-mode", "old-mode",
        "--wifi-test-watch-sec", "1",
        "--wifi-test-supervisor-timeout-sec", "2",
    ]


def fake_v2237_with_base(fake_base):
    def set_arg(args, key, value):
        index = args.index(key)
        args[index + 1] = value

    helper_builder = types.SimpleNamespace(HELPER_FLAGS=("builder-initial",))
    prev2131 = types.SimpleNamespace(HELPER_FLAGS=("prev2131-initial",))
    prev2133 = types.SimpleNamespace(prev2131=prev2131, HELPER_FLAGS=("prev2133-initial",))
    prev2135 = types.SimpleNamespace(prev2133=prev2133, HELPER_FLAGS=("prev2135-initial",))
    prev2137 = types.SimpleNamespace(
        prev2135=prev2135,
        HELPER_FLAGS=(
            "-DOTHER=1",
            "-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1",
            v2250.TAIL_SAMPLER_FLAGS[0],
            v2250.TAIL_SAMPLER_FLAGS[1],
        ),
    )
    v726 = types.SimpleNamespace(set_arg=set_arg)
    v2230 = nested_namespace("v2189", "v2188", "v2187", "v2182", "v2178", "v2176", "v2174", "v2169", "v726", leaf=v726)

    def with_bridge_flag(flags):
        bridge = "-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1"
        return (*tuple(flag for flag in flags if flag != bridge), bridge)

    fake = types.SimpleNamespace(
        OUT_DIR=None,
        REPORT_PATH=None,
        BOOT_IMAGE=None,
        INIT_BINARY=None,
        RAMDISK_CPIO=None,
        REMOTE_PROPERTY_ROOT=None,
        EXTRA_INIT_FLAGS=("-DEXTRA=1",),
        HELPER_MODE="fake-helper-mode",
        HELPER_RUNTIME_MODE="fake-runtime-mode",
        v2230=v2230,
        with_bridge_flag=with_bridge_flag,
        base_module=lambda: fake_base,
        helper_chain=lambda: prev2137,
        helper_builder_module=lambda: helper_builder,
    )
    fake.configure_base = lambda: setattr(fake, "configured", True)
    return fake, prev2137, helper_builder


class PatchV2237:
    def __init__(self, fake):
        self.fake = fake
        self.old = None

    def __enter__(self):
        self.old = v2250.v2237
        v2250.v2237 = self.fake
        return self.fake

    def __exit__(self, exc_type, exc, tb):
        v2250.v2237 = self.old


class BuildWrapperConfiguration(unittest.TestCase):
    def test_sha256_hashes_file_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.bin"
            path.write_bytes(b"abc")

            digest = v2250.sha256(path)

        self.assertEqual(digest, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_with_tail_flags_deduplicates_bridge_and_all_full_print_tail_flags(self):
        fake_base = types.SimpleNamespace(DEFAULT_ARGS=fake_base_args(), base=types.SimpleNamespace(EXTRA_INIT_FLAGS=[]))
        fake, _, _ = fake_v2237_with_base(fake_base)
        duplicate_flags = (
            "-DOTHER=1",
            v2250.TAIL_SAMPLER_FLAGS[0],
            "-DSECOND=1",
            *v2250.TAIL_SAMPLER_FLAGS,
        )

        with PatchV2237(fake):
            flags = v2250.with_tail_flags(duplicate_flags)

        self.assertEqual(flags[-len(v2250.TAIL_SAMPLER_FLAGS):], v2250.TAIL_SAMPLER_FLAGS)
        for flag in v2250.TAIL_SAMPLER_FLAGS:
            self.assertEqual(flags.count(flag), 1)
        self.assertIn("-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1", flags)

    def test_configure_base_rewrites_v2237_axes_and_propagates_full_print_flags(self):
        fake_base = types.SimpleNamespace(DEFAULT_ARGS=fake_base_args(), base=types.SimpleNamespace(EXTRA_INIT_FLAGS=[]))
        fake, prev2137, helper_builder = fake_v2237_with_base(fake_base)

        with PatchV2237(fake):
            helper_flags = v2250.configure_base()

        args = dict(zip(fake_base.DEFAULT_ARGS[0::2], fake_base.DEFAULT_ARGS[1::2]))
        self.assertTrue(fake.configured)
        self.assertEqual(fake.OUT_DIR, v2250.OUT_DIR)
        self.assertEqual(fake.REPORT_PATH, v2250.REPORT_PATH)
        self.assertEqual(args["--cycle"], "V2250")
        self.assertEqual(args["--decision"], "v2250-tail-perf-sampler-full-print-source-build-pass")
        self.assertEqual(args["--init-version"], "0.9.270")
        self.assertEqual(args["--init-build"], "v2250-tail-perf-sampler-full-print")
        self.assertEqual(args["--wifi-test-klog-prefix"], "A90v2250")
        self.assertEqual(args["--wifi-test-watch-sec"], "190")
        self.assertEqual(args["--wifi-test-supervisor-timeout-sec"], "245")
        self.assertIn("a90_android_execns_probe_v429_tail_perf_sampler_full_print", args["--helper-binary"])
        self.assertEqual(helper_flags[-len(v2250.TAIL_SAMPLER_FLAGS):], v2250.TAIL_SAMPLER_FLAGS)
        self.assertEqual(prev2137.HELPER_FLAGS, helper_flags)
        self.assertEqual(prev2137.prev2135.HELPER_FLAGS, helper_flags)
        self.assertEqual(prev2137.prev2135.prev2133.prev2131.HELPER_FLAGS, helper_flags)
        self.assertEqual(helper_builder.HELPER_FLAGS, helper_flags)
        self.assertEqual(fake_base.base.EXTRA_INIT_FLAGS, v2250.EXTRA_INIT_FLAGS)

    def test_patch_ramdisk_helpers_adds_tail_sampler_binary(self):
        original = lambda args: {"bin/existing": Path("existing")}
        base_wrapper = types.SimpleNamespace(base=types.SimpleNamespace(ramdisk_helpers=original))

        v2250.patch_ramdisk_helpers(base_wrapper)
        helpers = base_wrapper.base.ramdisk_helpers(types.SimpleNamespace())

        self.assertEqual(helpers["bin/existing"], Path("existing"))
        self.assertEqual(helpers[v2250.BPF_HELPER_RAMDISK_PATH], v2250.BPF_HELPER_BINARY)

    def test_render_report_includes_full_print_contract_and_safety_scope(self):
        manifest = {
            "decision": "v2250-tail-perf-sampler-full-print-source-build-pass",
            "boot_image": "workspace/private/inputs/boot_images/boot_linux_v2250.img",
            "boot_sha256": "boot-sha",
            "init_version": "0.9.270",
            "init_build": "v2250-tail-perf-sampler-full-print",
            "helper_marker": "a90_android_execns_probe v429",
            "helper_sha256": "helper-sha",
            "wifi_test": {
                "helper_runtime_mode": "wifi-companion",
                "helper_timeout_sec": 245,
            },
        }

        report = v2250.render_report(manifest, ("-DOTHER=1", *v2250.TAIL_SAMPLER_FLAGS))

        self.assertIn("# Native Init V2250 Tail Perf Sampler Full Print Source Build", report)
        self.assertIn("Decision: `v2250-tail-perf-sampler-full-print-source-build-pass`", report)
        self.assertIn("A90 Linux init 0.9.270 (v2250-tail-perf-sampler-full-print)", report)
        self.assertIn("printed only 512/668 occupied entries", report)
        self.assertIn("print up to 1024 samples", report)
        self.assertIn("A90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_PRINT_LIMIT=1024", report)
        self.assertIn("/cache/native-init-v2250-tail-perf-regs-codeword.log", report)
        self.assertIn("does not scan/connect Wi-Fi beyond the existing bounded validation route", report)


class MainMetadataUpdate(unittest.TestCase):
    def test_main_rewrites_manifest_and_promotion_metadata_without_running_real_build(self):
        tmp_parent = v2250.REPO_ROOT / "tmp"
        tmp_parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_parent) as tmp:
            root = Path(tmp)
            out_dir = root / "out"
            out_dir.mkdir()
            boot_image = root / "boot_linux_v2250_tail_perf_sampler_full_print.img"
            report_path = root / "report.md"
            manifest_path = out_dir / "manifest.json"
            manifest_path.write_text(json.dumps({
                "decision": "v2250-tail-perf-sampler-full-print-source-build-pass",
                "boot_sha256": "boot-sha",
                "init_version": "0.9.270",
                "init_build": "v2250-tail-perf-sampler-full-print",
                "helper_sha256": "helper-sha",
            }), encoding="utf-8")
            old_values = {
                "OUT_DIR": v2250.OUT_DIR,
                "BOOT_IMAGE": v2250.BOOT_IMAGE,
                "REPORT_PATH": v2250.REPORT_PATH,
            }
            old_functions = {
                "configure_base": v2250.configure_base,
                "build_bpf_helper": v2250.build_bpf_helper,
                "helper_builder_module": v2250.helper_builder_module,
                "base_module": v2250.base_module,
            }
            helper_builder = types.SimpleNamespace(patch_helper_builder=lambda base: setattr(base, "helper_patched", True))
            fake_base = types.SimpleNamespace(
                base=types.SimpleNamespace(ramdisk_helpers=lambda args: {}),
                main=lambda: 0,
            )
            v2250.OUT_DIR = out_dir
            v2250.BOOT_IMAGE = boot_image
            v2250.REPORT_PATH = report_path
            v2250.configure_base = lambda: ("-DTEST=1", *v2250.TAIL_SAMPLER_FLAGS)
            v2250.build_bpf_helper = lambda: None
            v2250.helper_builder_module = lambda: helper_builder
            v2250.base_module = lambda: fake_base
            try:
                rc = v2250.main()
            finally:
                for name, value in old_values.items():
                    setattr(v2250, name, value)
                for name, value in old_functions.items():
                    setattr(v2250, name, value)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            promotion = json.loads((out_dir / "promotion-candidate.json").read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(fake_base.helper_patched)
        self.assertEqual(manifest["candidate_tag"], "v2250-tail-perf-sampler-full-print")
        self.assertEqual(manifest["parent_baseline"], "v2237-supplicant-terminate-poll")
        self.assertFalse(manifest["promoted_baseline"])
        self.assertEqual(manifest["tail_sampler"]["output_path"], "/cache/native-init-v2250-tail-perf-regs-codeword.log")
        self.assertEqual(manifest["tail_sampler"]["duration_ms"], 45000)
        self.assertEqual(manifest["tail_sampler"]["period_ns"], 1000000)
        self.assertEqual(manifest["tail_sampler"]["print_limit"], 1024)
        self.assertEqual(promotion["candidate_tag"], "v2250-tail-perf-sampler-full-print")
        self.assertEqual(promotion["tail_sampler_sha256"], v2250.EXPECTED_BPF_HELPER_SHA256)


if __name__ == "__main__":
    unittest.main()
