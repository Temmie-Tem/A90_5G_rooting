"""Regression tests for a90_kernel_v2242_user_elf_offset_context."""

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _loader import load_revalidation

v2242 = load_revalidation("a90_kernel_v2242_user_elf_offset_context")
v2241 = load_revalidation("a90_kernel_v2241_user_uprobe_offset_base_map")


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def probe_line(group: str, event: str, address: int):
    return {
        "group": group,
        "event": event,
        "surface": "uprobe",
        "ts": 1.0,
        "line": f"task [000] .... 1.000000: {group}:{event}: (0x{address:x})",
    }


def spec(group: str, name: str, offset: int):
    return v2241.UprobeSpec(group, name, name, offset, hex(offset), 10)


def full_key_event_helper_source():
    cnss_rows = "\n".join(
        f'    {{"{event}", "{event}", 0x{0x1000 + index * 0x100:x}ULL}},'
        for index, (group, event) in enumerate(sorted(v2242.KEY_EVENTS))
        if group == "a90cnss"
    )
    pm_rows = "\n".join(
        f'    {{"{event}", "{event}", 0x{0x3000 + index * 0x100:x}ULL}},'
        for index, (group, event) in enumerate(sorted(v2242.KEY_EVENTS))
        if group == "a90pmsrv"
    )
    libqmi_rows = "\n".join(
        f'    {{"{event}", "{event}", 0x{0x5000 + index * 0x100:x}ULL}},'
        for index, (group, event) in enumerate(sorted(v2242.KEY_EVENTS))
        if group == "a90libqmi"
    )
    return f"""
static const struct cnss_wlfw_uprobe_event cnss_wlfw_uprobe_events[] = {{
{cnss_rows}
}};
static const struct pm_service_uprobe_event pm_service_uprobe_events[] = {{
{pm_rows}
}};
static const struct libqmi_cci_uprobe_event libqmi_cci_uprobe_events[] = {{
{libqmi_rows}
}};
"""


class LoadSegmentHelpers(unittest.TestCase):
    def test_load_segment_properties_contains_and_file_offset(self):
        segment = v2242.LoadSegment(
            index=2,
            offset=0x400,
            virt_addr=0x1000,
            file_size=0x200,
            mem_size=0x300,
            flags="R E",
            align=0x1000,
        )

        self.assertEqual(segment.end_vaddr, 0x1300)
        self.assertEqual(segment.end_file_vaddr, 0x1200)
        self.assertTrue(segment.executable)
        self.assertTrue(segment.contains_vaddr(0x12FF))
        self.assertFalse(segment.contains_vaddr(0x1300))
        self.assertEqual(segment.file_offset_for_vaddr(0x1100), 0x500)
        self.assertIsNone(segment.file_offset_for_vaddr(0x1200))
        self.assertIsNone(segment.file_offset_for_vaddr(0x0FFF))
        self.assertEqual(segment.public_dict()["virt_addr"], "0x1000")

    def test_find_segment_returns_first_containing_segment(self):
        segments = [
            v2242.LoadSegment(0, 0x0, 0x0, 0x100, 0x100, "R", 0x1000),
            v2242.LoadSegment(1, 0x100, 0x1000, 0x100, 0x100, "R E", 0x1000),
        ]

        self.assertEqual(v2242.find_segment(segments, 0x1080).index, 1)
        self.assertIsNone(v2242.find_segment(segments, 0x2000))

    def test_parse_load_segments_reports_missing_file_without_running_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            segments, metadata = v2242.parse_load_segments(Path(tmp) / "missing")

        self.assertEqual(segments, [])
        self.assertFalse(metadata["exists"])

    def test_object_for_spec_routes_peripheral_events_to_libperipheral_object(self):
        self.assertEqual(v2242.object_for_spec(spec("a90cnss", "periph_register", 0x1000)), "a90periph")
        self.assertEqual(v2242.object_for_spec(spec("a90cnss", "wlfw_start", 0x1000)), "a90cnss")


class ContextMapping(unittest.TestCase):
    def test_observed_spec_keys_keeps_only_runtime_probes_with_static_specs(self):
        specs = {
            ("a90cnss", "wlfw_start"): spec("a90cnss", "wlfw_start", 0x1000),
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v9301-live/parser/summary.json"
            write_json(
                path,
                {"timeline": [
                    probe_line("a90cnss", "wlfw_start", 0x7F10001000),
                    probe_line("a90cnss", "wlfw_cap_qmi", 0x7F10002000),
                ]},
            )

            keys = v2242.observed_spec_keys([path], specs)

        self.assertEqual(keys, {("a90cnss", "wlfw_start")})

    def test_build_offset_contexts_classifies_exec_mapping_and_static_issues(self):
        specs = {
            ("a90cnss", "wlfw_start"): spec("a90cnss", "wlfw_start", 0x1100),
            ("a90cnss", "data_event"): spec("a90cnss", "data_event", 0x2100),
            ("a90pmsrv", "missing_file"): spec("a90pmsrv", "missing_file", 0x1100),
            ("a90libqmi", "no_mapping"): spec("a90libqmi", "no_mapping", 0x1100),
        }
        existing = Path(__file__)
        missing = existing.parent / "definitely-missing-elf"
        rows = v2242.build_offset_contexts(
            specs,
            {("a90cnss", "wlfw_start")},
            {"a90cnss": existing, "a90pmsrv": missing},
            {
                "a90cnss": [
                    v2242.LoadSegment(0, 0x100, 0x1000, 0x800, 0x800, "R E", 0x1000),
                    v2242.LoadSegment(1, 0x900, 0x2000, 0x800, 0x800, "RW", 0x1000),
                ],
                "a90pmsrv": [],
            },
        )
        by_event = {row.event: row for row in rows}

        self.assertIsNone(by_event["wlfw_start"].issue)
        self.assertTrue(by_event["wlfw_start"].observed)
        self.assertEqual(by_event["wlfw_start"].file_offset_hex, "0x200")
        self.assertEqual(by_event["data_event"].issue, "offset_not_executable")
        self.assertEqual(by_event["missing_file"].issue, "missing_elf_file")
        self.assertEqual(by_event["no_mapping"].issue, "missing_elf_mapping")

    def test_write_private_context_writes_bytes_only_for_clean_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            elf = root / "tiny.bin"
            elf.write_bytes(bytes(range(64)))
            row = v2242.OffsetContext(
                group="a90cnss",
                object="a90cnss",
                event="wlfw_start",
                offset=0x10,
                offset_hex="0x10",
                source_line=7,
                observed=True,
                key_event=True,
                elf_path=str(elf),
                elf_exists=True,
                segment_index=0,
                segment_flags="R E",
                executable_segment=True,
                file_offset=0x10,
                file_offset_hex="0x10",
                in_file=True,
                issue=None,
            )

            with patch.object(v2242, "disassembler_command", return_value=None):
                path, meta = v2242.write_private_context(
                    root,
                    [row],
                    {"a90cnss": elf},
                    before=4,
                    after=8,
                    include_all_observed=False,
                )
                payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(meta["entry_count"], 1)
        self.assertIsNone(meta["disassembler"])
        self.assertEqual(payload["entries"][0]["bytes_start_file_offset"], "0xc")
        self.assertEqual(payload["entries"][0]["bytes_hex"], bytes(range(12, 24)).hex())


class SummaryBuilder(unittest.TestCase):
    def make_args(self, root: Path, parser_paths, helper_source: Path):
        v2241_path = root / "v2241.json"
        write_json(v2241_path, {"decision": "v2241-user-uprobe-offset-base-map-pass"})
        for name in ("cnss", "pm", "qmi"):
            (root / name).write_bytes(b"\x00" * 16)
        return argparse.Namespace(
            label="unit",
            helper_source=helper_source,
            parser_summaries=parser_paths,
            v2241=v2241_path,
            elf={
                "a90cnss": root / "cnss",
                "a90pmsrv": root / "pm",
                "a90libqmi": root / "qmi",
            },
            window_before=4,
            window_after=8,
            include_all_observed_context=True,
        )

    def test_build_summary_passes_when_all_static_key_offsets_are_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper_source = root / "helper.c"
            parser = root / "v9302-live/parser/summary.json"
            write_text(helper_source, full_key_event_helper_source())
            write_json(parser, {"timeline": [probe_line("a90cnss", "wlfw_start", 0x7F10001000)]})

            segment = v2242.LoadSegment(0, 0, 0x0, 0x10000, 0x10000, "R E", 0x1000)
            with patch.object(v2242, "parse_load_segments", return_value=([segment], {"exists": True})):
                with patch.object(
                    v2242,
                    "write_private_context",
                    return_value=(root / "private_instruction_context.json", {"path": "private", "entry_count": 11}),
                ):
                    summary = v2242.build_summary(self.make_args(root, [parser], helper_source), root / "out")

        self.assertTrue(summary["pass"])
        self.assertEqual(summary["decision"], "v2242-user-elf-offset-context-pass")
        self.assertEqual(summary["key_event_count"], len(v2242.KEY_EVENTS))
        self.assertEqual(summary["key_issue_count"], 0)
        self.assertEqual(summary["identity_contract"]["file_offset_formula"], "file_offset = segment.p_offset + (helper_static_uprobe_offset - segment.p_vaddr)")

    def test_build_summary_is_incomplete_when_key_offsets_are_outside_load_segments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper_source = root / "helper.c"
            parser = root / "v9303-live/parser/summary.json"
            write_text(helper_source, full_key_event_helper_source())
            write_json(parser, {"timeline": [probe_line("a90cnss", "wlfw_start", 0x7F10001000)]})

            segment = v2242.LoadSegment(0, 0, 0x9000, 0x100, 0x100, "R E", 0x1000)
            with patch.object(v2242, "parse_load_segments", return_value=([segment], {"exists": True})):
                with patch.object(
                    v2242,
                    "write_private_context",
                    return_value=(root / "private_instruction_context.json", {"path": "private", "entry_count": 0}),
                ):
                    summary = v2242.build_summary(self.make_args(root, [parser], helper_source), root / "out")

        self.assertFalse(summary["pass"])
        self.assertEqual(summary["decision"], "v2242-user-elf-offset-context-incomplete")
        self.assertGreater(summary["key_issue_count"], 0)
        self.assertEqual(summary["issues"]["key"][0]["issue"], "offset_outside_load_segments")


if __name__ == "__main__":
    unittest.main()
