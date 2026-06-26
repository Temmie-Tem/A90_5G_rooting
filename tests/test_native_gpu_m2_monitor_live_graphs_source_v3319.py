from __future__ import annotations

import unittest
from pathlib import Path

from _loader import load_script


ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / "workspace/public/src/native-init/v319/80_shell_dispatch.inc.c"
MONITOR = ROOT / "workspace/public/src/native-init/a90_monitor.c"
MONITOR_H = ROOT / "workspace/public/src/native-init/a90_monitor.h"

runner = load_script(
    "workspace/public/src/scripts/revalidation/build_native_init_boot_v3319_gpu_m2_monitor_live_graphs.py"
)


class NativeGpuM2MonitorLiveGraphsSourceV3319Tests(unittest.TestCase):
    def test_v3319_identity_and_required_markers(self) -> None:
        self.assertEqual(runner.CYCLE, "V3319")
        self.assertEqual(runner.INIT_VERSION, "0.11.90")
        self.assertEqual(runner.INIT_BUILD, "v3319-gpu-m2-monitor-live-graphs")
        self.assertEqual(
            runner.BOOT_IMAGE.name,
            "boot_linux_v3319_gpu_m2_monitor_live_graphs.img",
        )

        required = b"\n".join(runner.REQUIRED_STRINGS)
        self.assertIn(b"0.11.90", required)
        self.assertIn(b"v3319-gpu-m2-monitor-live-graphs", required)
        self.assertIn(b"m2-monitor-live-graph-probe", required)
        self.assertIn(b"gpu.m2.graph.scope=", required)
        self.assertIn(b"gpu.m2.graph.power_write_attempted=0", required)
        self.assertIn(b"gpu.m2.graph.kgsl_submit_attempted=1", required)
        self.assertIn(b"gpu.m2.graph.kms_present_attempted=1", required)
        self.assertIn(b"gpu.m2.graph.graph_pixels_set=%u", required)
        self.assertIn(b"gpu.m2.graph.present_rc=%d", required)
        self.assertIn(b"gpu.m2.graph.result=%s", required)
        self.assertIn(b"monitor-live-graph-pass", required)

    def test_monitor_source_contains_graph_series_contract(self) -> None:
        source = MONITOR.read_text(encoding="utf-8")
        header = MONITOR_H.read_text(encoding="utf-8")

        self.assertIn("#define A90_MONITOR_M0_DEFAULT_SAMPLES 3U", header)
        self.assertIn("#define A90_MONITOR_M0_MAX_SAMPLES 16U", header)
        self.assertIn("#define A90_MONITOR_GRAPH_MAX_POINTS 32U", header)
        self.assertIn("struct a90_monitor_graph_series", header)
        self.assertIn("a90_monitor_graph_sample", header)
        self.assertIn("a90_monitor_graph_render_mono1", header)
        self.assertIn("struct a90_monitor_history", source)
        self.assertIn("monitor_discover_topology", source)
        self.assertIn("monitor_parse_cpu_list_mask", source)
        self.assertIn("monitor_graph_draw_lane", source)
        self.assertIn("monitor_graph_draw_line", source)
        self.assertIn("monitor_graph_set_pixel", source)
        self.assertIn("a90_monitor_graph_sample", source)
        self.assertIn("a90_monitor_graph_render_mono1", source)
        self.assertIn("cpufreq/related_cpus", source)
        self.assertIn("cpufreq/cpuinfo_max_freq", source)
        self.assertIn("Silver", source)
        self.assertIn("Gold", source)
        self.assertIn("Prime", source)
        self.assertIn("/proc/stat", source)
        self.assertIn("/proc/meminfo", source)
        self.assertIn("/proc/loadavg", source)
        self.assertIn("/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage", source)
        self.assertIn("/sys/class/kgsl/kgsl-3d0/devfreq/cur_freq", source)
        self.assertIn("/sys/class/power_supply/battery/capacity", source)
        self.assertIn("a90_sensormap_collect_summary", source)
        self.assertNotIn("O_WRONLY", source)
        self.assertNotIn("O_RDWR", source)

    def test_dispatch_routes_m2_monitor_live_graph(self) -> None:
        source = DISPATCH.read_text(encoding="utf-8")

        self.assertIn('strcmp(subcommand, "m2-monitor-live-graph-probe") == 0', source)
        self.assertIn('strcmp(subcommand, "monitor-live-graph-probe") == 0', source)
        self.assertIn('strcmp(argv[index], "--frames") == 0', source)
        self.assertIn('strcmp(argv[index], "--interval-ms") == 0', source)
        self.assertIn('strcmp(argv[index], "--timeout-ms") == 0', source)
        self.assertIn('strcmp(argv[index], "--hold-ms") == 0', source)
        self.assertIn("GPU_M2_GRAPH_DEFAULT_FRAMES", source)
        self.assertIn("GPU_M2_GRAPH_MAX_FRAMES", source)
        self.assertIn("GPU_M2_GRAPH_MAX_INTERVAL_MS", source)
        self.assertIn("gpu_m2_monitor_live_graph_probe", source)
        self.assertIn("gpu_m2_monitor_live_graph_child", source)
        self.assertIn("a90_monitor_graph_render_mono1", source)
        self.assertIn("gpu_d3_render_frame_to_kms", source)
        self.assertIn("m2-monitor-live-graph-probe [--frames N] [--interval-ms N] [--timeout-ms N] [--hold-ms N] [--materialize-devnode]", source)

    def test_builder_manifest_records_m2_live_validation(self) -> None:
        manifest = runner._minimal_gpu_m2_manifest()
        report = runner.render_report(
            {
                "decision": runner.DECISION,
                "boot_image": str(runner.BOOT_IMAGE),
                "boot_sha256": "0" * 64,
                "init_version": runner.INIT_VERSION,
                "init_build": runner.INIT_BUILD,
            },
            (),
            (),
        )

        self.assertEqual(manifest["scope"], "gpu-m2-live-monitor-graphs-textured-2d")
        self.assertEqual(
            manifest["command"],
            "gpu m2-monitor-live-graph-probe --frames 12 --interval-ms 200 --timeout-ms 60000 --hold-ms 5000 --materialize-devnode",
        )
        self.assertEqual(manifest["expected_result"], "monitor-live-graph-pass")
        self.assertFalse(manifest["power_write_attempted"])
        self.assertTrue(manifest["kgsl_submit_attempted"])
        self.assertTrue(manifest["kms_present_attempted"])
        self.assertIn("require-presented-frames-12", manifest["next_live_validation"])
        self.assertIn("require-graph-pixels-positive", manifest["next_live_validation"])
        self.assertIn("require-semantic-match-count-64", manifest["next_live_validation"])
        self.assertIn("mono1 graph-frame renderer", report)
        self.assertIn("real KGSL submit path", report)
        self.assertIn("No backlight", report)


if __name__ == "__main__":
    unittest.main()
