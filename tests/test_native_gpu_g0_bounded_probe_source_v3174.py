from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"
BASIC = ROOT / "workspace/public/src/native-init/v319/60_shell_basic_commands.inc.c"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3174_gpu_g0_bounded_probe.py"
)


class NativeGpuG0BoundedProbeSourceV3174Tests(unittest.TestCase):
    def test_v3174_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3174")
        self.assertEqual(runner.INIT_VERSION, "0.11.17")
        self.assertEqual(runner.INIT_BUILD, "v3174-gpu-g0-bounded-probe")

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.17", required)
        self.assertIn(b"v3174-gpu-g0-bounded-probe", required)
        self.assertIn(b"gpu [g0-status|g0-open-probe", required)
        self.assertIn(b"gpu.g0.scope=kgsl-open-hang-diagnosis", required)
        self.assertIn(b"gpu.g0.safety=read-only-status-plus-bounded-open-probe", required)
        self.assertIn(b"gpu.g0.bright_line.no_power_writes=1", required)
        self.assertIn(b"gpu.g0.open.parent_enters_open=0", required)
        self.assertIn(b"gpu.g0.open.ioctl_attempted=0", required)
        self.assertIn(b"gpu.g0.open.mmap_attempted=0", required)
        self.assertIn(b"gpu.g0.open.power_write_attempted=0", required)
        self.assertIn(b"gpu.g0.open.result=%s", required)

    def test_dispatch_exposes_gpu_g0_commands(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        self.assertIn('static int handle_gpu(char **argv, int argc)', source)
        self.assertIn('{ "gpu", handle_gpu, "gpu [g0-status|g0-open-probe', source)
        self.assertIn('strcmp(subcommand, "g0-status")', source)
        self.assertIn('strcmp(subcommand, "g0-open-probe")', source)
        self.assertIn('"--materialize-devnode"', source)
        self.assertIn('"--timeout-ms"', source)
        self.assertIn('"--rdwr"', source)

    def test_probe_is_parent_bounded_and_child_only_open(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        start = source.index("struct gpu_g0_open_probe_result")
        end = source.index("static int handle_audio", start)
        gpu_section = source[start:end]

        self.assertIn("pid = fork();", gpu_section)
        self.assertIn("return gpu_g0_open_probe_child(GPU_G0_DEVNODE, flags, pipefd[1]);", gpu_section)
        self.assertIn("fd = open(path, flags | O_CLOEXEC);", gpu_section)
        self.assertIn("poll(&pfd, 1, poll_ms)", gpu_section)
        self.assertIn("kill(pid, SIGKILL)", gpu_section)
        self.assertIn("waitpid(pid, &child_status, WNOHANG)", gpu_section)
        self.assertIn("return timed_out ? -ETIMEDOUT : 0;", gpu_section)
        self.assertIn('"gpu.g0.open.parent_enters_open=0', gpu_section)
        self.assertIn('"gpu.g0.open.ioctl_attempted=0', gpu_section)
        self.assertIn('"gpu.g0.open.mmap_attempted=0', gpu_section)
        self.assertIn('"gpu.g0.open.power_write_attempted=0', gpu_section)
        self.assertNotIn("ioctl(", gpu_section)
        self.assertNotIn("mmap(", gpu_section)
        self.assertNotIn("/sys/kernel/debug/regulator", gpu_section)
        self.assertNotIn("/sys/kernel/debug/gpio", gpu_section)
        self.assertNotIn("libGLES", gpu_section)
        self.assertNotIn("EGL", gpu_section)

    def test_status_is_read_only_and_devnode_materialize_is_explicit(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")
        start = source.index("static int gpu_g0_status(void)")
        end = source.index("static int gpu_g0_open_probe_child", start)
        status_section = source[start:end]

        self.assertIn('GPU_G0_SYSFS_DEV "/sys/class/kgsl/kgsl-3d0/dev"', source)
        self.assertIn('GPU_G0_SYSFS_UEVENT "/sys/class/kgsl/kgsl-3d0/uevent"', source)
        self.assertIn('"/sys/module/firmware_class/parameters/path"', status_section)
        self.assertIn('"/vendor/firmware/a630_sqe.fw"', status_section)
        self.assertIn('"/vendor/firmware/a640_gmu.bin"', status_section)
        self.assertIn('"/firmware_mnt/image/a640_zap.mdt"', status_section)
        self.assertIn("gpu_g0_materialize_devnode", source)
        self.assertIn("ensure_char_node(GPU_G0_DEVNODE", source)

    def test_help_lists_gpu_command(self) -> None:
        source = BASIC.read_text(encoding="utf-8")
        self.assertIn("gpu [g0-status|g0-open-probe", source)

    def test_manifest_metadata_records_g0_policy(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertIn('"source_baseline": "v3173-badapple-nyan-pcm-duration"', source)
        self.assertIn('"gpu g0-status"', source)
        self.assertIn('"gpu g0-open-probe --timeout-ms 2000 --materialize-devnode"', source)
        self.assertIn('"open_probe_parent_enters_open": False', source)
        self.assertIn('"open_probe_timeout_guard_ms_default": 2000', source)
        self.assertIn('"kgsl-ioctl"', source)
        self.assertIn('"GDSC-write"', source)
        self.assertIn('"proprietary-adreno-blob"', source)
        self.assertIn('"pending-gpu-g0-bounded-live-validation"', source)


if __name__ == "__main__":
    unittest.main()
