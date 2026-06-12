"""Regression tests for a90_kernel_v2241_user_uprobe_offset_base_map."""

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2241 = load_revalidation("a90_kernel_v2241_user_uprobe_offset_base_map")


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def probe_line(group: str, event: str, address: int, ts: float = 1.0):
    return {
        "group": group,
        "event": event,
        "surface": "uprobe",
        "source_path": f"/tmp/{group}.txt",
        "ts": ts,
        "line": f"task-1 [000] .... {ts:.6f}: {group}:{event}: (0x{address:x})",
    }


def helper_source_text():
    return """
static const struct cnss_wlfw_uprobe_event cnss_wlfw_uprobe_events[] = {
    CNSS_WLFW_UPROBE_EVENT("wlfw_start", "start", 0x1000ULL),
};
static const struct cnss_wlfw_uprobe_event cnss_peripheral_uprobe_events[] = {
    {"peripheral_vote", "vote", 0x1800ULL},
};
static const struct pm_service_uprobe_event pm_service_uprobe_events[] = {
    {"pm_vote", "pm", 0x2000ULL},
};
static const struct libqmi_cci_uprobe_event libqmi_cci_uprobe_events[] = {
    CNSS_WLFW_UPROBE_EVENT_FETCH("libqmi_loop", "loop", 0x3000ULL),
};
"""


class StaticAndRuntimeParsing(unittest.TestCase):
    def test_parse_uprobe_specs_reads_macro_fetch_and_brace_rows_by_array_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "helper.c"
            write_text(source, helper_source_text())

            specs = v2241.parse_uprobe_specs(source)

        self.assertEqual(specs[("a90cnss", "wlfw_start")].offset_hex, "0x1000")
        self.assertEqual(specs[("a90cnss", "peripheral_vote")].key, "vote")
        self.assertEqual(specs[("a90pmsrv", "pm_vote")].group, "a90pmsrv")
        self.assertEqual(specs[("a90libqmi", "libqmi_loop")].offset, 0x3000)

    def test_extract_runtime_probes_deduplicates_group_event_and_keeps_source_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v9201-live/parser/summary.json"
            write_json(
                path,
                {
                    "timeline": [
                        probe_line("a90cnss", "wlfw_start", 0x7F10001000, ts=2.0),
                        probe_line("a90cnss", "wlfw_start", 0x7F10009999, ts=3.0),
                        probe_line("a90pmsrv", "_surface_nonlog", 0x7F20002000, ts=4.0),
                        {"group": "a90libqmi", "event": "libqmi_loop", "line": "no address", "ts": 5.0},
                        probe_line("other", "wlfw_start", 0x7F30003000, ts=6.0),
                    ]
                },
            )

            probes = v2241.extract_runtime_probes(path)

        self.assertEqual(len(probes), 1)
        self.assertEqual(probes[0].run_id, "v9201")
        self.assertEqual(probes[0].address_hex, "0x7f10001000")
        self.assertEqual(probes[0].source_path, "/tmp/a90cnss.txt")

    def test_extract_runtime_probes_rejects_missing_timeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v9202-live/parser/summary.json"
            write_json(path, {"timeline": []})

            with self.assertRaisesRegex(ValueError, "missing timeline"):
                v2241.extract_runtime_probes(path)


class BiasMapping(unittest.TestCase):
    def test_build_bias_observations_classifies_matches_missing_and_alias_duplicates(self):
        specs = {
            ("a90cnss", "wlfw_start"): v2241.UprobeSpec("a90cnss", "wlfw_start", "start", 0x1000, "0x1000", 10),
        }
        probes = [
            v2241.RuntimeProbe("v1", "a90cnss", "wlfw_start", 0x7F10001000, "0x7f10001000", 1.0, None),
            v2241.RuntimeProbe("v1", "a90libqmi", "wlfw_start", 0x7F10001000, "0x7f10001000", 1.0, None),
            v2241.RuntimeProbe("v1", "a90pmsrv", "pm_vote", 0x7F10002000, "0x7f10002000", 2.0, None),
        ]

        observations, missing, aliases = v2241.build_bias_observations(probes, specs)

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].load_bias_hex, "0x7f10000000")
        self.assertTrue(observations[0].page_aligned)
        self.assertEqual(len(aliases), 1)
        self.assertIn("same run/event/address", aliases[0]["reason"])
        self.assertEqual(missing[0]["event"], "pm_vote")

    def test_summarize_biases_reports_dominant_bias_alignment_and_mismatches(self):
        observations = [
            v2241.BiasObservation("v1", "a90cnss", "a", "0x1100", "0x100", 0x1000, "0x1000", True),
            v2241.BiasObservation("v1", "a90cnss", "b", "0x2200", "0x200", 0x2000, "0x2000", True),
            v2241.BiasObservation("v1", "a90cnss", "c", "0x1301", "0x301", 0x1000, "0x1000", False),
        ]

        summary = v2241.summarize_biases(observations)

        row = summary["v1:a90cnss"]
        self.assertEqual(row["matched_events"], 3)
        self.assertEqual(row["unique_load_biases"], 2)
        self.assertEqual(row["dominant_load_bias"], "0x1000")
        self.assertEqual(row["dominant_count"], 2)
        self.assertFalse(row["all_page_aligned"])
        self.assertEqual(row["mismatches"][0]["event"], "b")

    def test_elf_metadata_for_missing_path_is_side_effect_free(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = v2241.elf_metadata(Path(tmp) / "missing.elf")

        self.assertFalse(result["exists"])
        self.assertTrue(result["path"].endswith("missing.elf"))


class SummaryBuilder(unittest.TestCase):
    def write_parser(self, root: Path, run: str, bias: int):
        path = root / f"{run}-live/parser/summary.json"
        write_json(
            path,
            {
                "timeline": [
                    probe_line("a90cnss", "wlfw_start", bias + 0x1000, ts=1.0),
                    probe_line("a90pmsrv", "pm_vote", bias + 0x2000, ts=2.0),
                    probe_line("a90libqmi", "libqmi_loop", bias + 0x3000, ts=3.0),
                ]
            },
        )
        return path

    def make_args(self, root: Path, parser_paths):
        helper_source = root / "helper.c"
        v2240_path = root / "v2240.json"
        write_text(helper_source, helper_source_text())
        write_json(v2240_path, {"decision": "v2240-codepath-identity-boundary-pass"})
        return argparse.Namespace(
            label="unit",
            helper_source=helper_source,
            parser_summaries=parser_paths,
            v2240=v2240_path,
            elf={
                "a90cnss": root / "missing-cnss",
                "a90pmsrv": root / "missing-pm",
                "a90libqmi": root / "missing-qmi",
            },
        )

    def test_build_summary_passes_when_each_run_group_has_one_aligned_bias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = [
                self.write_parser(root, "v9203", 0x7F10000000),
                self.write_parser(root, "v9204", 0x7F20000000),
            ]

            summary = v2241.build_summary(self.make_args(root, paths), root / "out")

        self.assertTrue(summary["pass"])
        self.assertEqual(summary["decision"], "v2241-user-uprobe-offset-base-map-pass")
        self.assertEqual(summary["static_spec_counts"], {
            "a90cnss": 2,
            "a90libqmi": 1,
            "a90pmsrv": 1,
        })
        self.assertEqual(summary["matched_observation_count"], 6)
        self.assertEqual(summary["missing_static_spec_count"], 0)
        self.assertEqual(summary["bias_summary"]["v9203:a90cnss"]["dominant_load_bias"], "0x7f10000000")
        self.assertEqual(
            summary["identity_contract"]["load_bias_formula"],
            "load_bias = runtime_probe_ip - static_uprobe_offset",
        )

    def test_build_summary_is_incomplete_when_a_group_has_no_matching_static_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "v9205-live/parser/summary.json"
            write_json(
                path,
                {
                    "timeline": [
                        probe_line("a90cnss", "wlfw_start", 0x7F10001000),
                        probe_line("a90pmsrv", "unmapped_pm_event", 0x7F10002000),
                        probe_line("a90libqmi", "libqmi_loop", 0x7F10003000),
                    ]
                },
            )

            summary = v2241.build_summary(self.make_args(root, [path]), root / "out")

        self.assertFalse(summary["pass"])
        self.assertEqual(summary["decision"], "v2241-user-uprobe-offset-base-map-incomplete")
        self.assertEqual(summary["missing_static_spec_count"], 1)
        self.assertEqual(summary["missing_static_specs"][0]["event"], "unmapped_pm_event")


if __name__ == "__main__":
    unittest.main()
