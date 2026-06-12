"""Regression tests for native_kernel_static_tracepoint_object_chain_audit_v2238."""

import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

v2238 = load_revalidation("native_kernel_static_tracepoint_object_chain_audit_v2238")


class TracepointParsingHelpers(unittest.TestCase):
    def test_clean_cmdv1_text_removes_transport_noise(self):
        text = (
            "A90P1 BEGIN rc=0\n"
            "linker: Warning: failed to find generated linker configuration\n"
            "cfg80211:rdev_scan\n"
            "[done]\n"
            "dfc:dfc_qmi_tc\n"
        )

        self.assertEqual(v2238.clean_cmdv1_text(text), "cfg80211:rdev_scan\ndfc:dfc_qmi_tc\n")

    def test_split_top_level_args_preserves_nested_commas_and_strings(self):
        args = v2238.split_top_level_args(
            "event, TP_PROTO(struct wiphy *wiphy, const char *name), \"a,b\", FOO(1, 2)"
        )

        self.assertEqual(args, [
            "event",
            "TP_PROTO(struct wiphy *wiphy, const char *name)",
            '"a,b"',
            "FOO(1, 2)",
        ])

    def test_extract_macro_call_handles_nested_parentheses(self):
        block = "TRACE_EVENT(foo, TP_PROTO(struct wiphy *wiphy, FOO(1, 2)), TP_ARGS(wiphy))"

        self.assertEqual(
            v2238.extract_macro_call(block, "TP_PROTO"),
            "struct wiphy *wiphy, FOO(1, 2)",
        )
        self.assertEqual(v2238.extract_macro_call(block, "MISSING"), "")

    def test_pointer_params_categorizes_struct_and_byte_pointers(self):
        params = v2238.pointer_params("struct wiphy *wiphy, const u8 *addr, int status")

        self.assertEqual(params, [
            {"type": "struct wiphy", "name": "wiphy", "category": "struct_pointer"},
            {"type": "const u8", "name": "addr", "category": "byte_or_string_pointer"},
        ])

    def test_source_fields_and_live_format_detect_pointer_retention(self):
        source = """
            __field( u32, ifindex )
            __field( struct net_device *, dev )
            __array( u8, bssid, 6 )
        """
        fields = v2238.source_fields(source)
        live = v2238.parse_live_format(
            "field:unsigned int ifindex; offset:8; size:4; signed:0;\n"
            "field:struct net_device * dev; offset:16; size:8; signed:0;\n"
            "field:unsigned char bssid[6]; offset:24; size:6; signed:0;\n"
        )

        self.assertIn({"kind": "field", "type": "struct net_device *", "name": "dev"}, fields)
        self.assertIn({"kind": "array", "type": "u8", "name": "bssid"}, fields)
        self.assertEqual(live["field_names"], ["ifindex", "dev", "bssid"])
        self.assertEqual(live["raw_pointer_fields"][0]["name"], "dev")


class SourceSummaryAndClassification(unittest.TestCase):
    def test_extract_trace_blocks_merges_define_event_template_fields(self):
        trace_source = """
TRACE_EVENT(cfg80211_scan_done,
    TP_PROTO(struct wiphy *wiphy, bool aborted),
    TP_ARGS(wiphy, aborted),
    TP_STRUCT__entry(
        WIPHY_ENTRY
        __field(bool, aborted)
    ),
    TP_fast_assign(),
    TP_printk("")
);

DECLARE_EVENT_CLASS(rdev_template,
    TP_PROTO(struct wiphy *wiphy, struct net_device *netdev),
    TP_ARGS(wiphy, netdev),
    TP_STRUCT__entry(
        WIPHY_ENTRY
        NETDEV_ENTRY
    ),
    TP_fast_assign(),
    TP_printk("")
);

DEFINE_EVENT(rdev_template, rdev_scan,
    TP_PROTO(struct wiphy *wiphy, struct net_device *netdev),
    TP_ARGS(wiphy, netdev)
);
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.h"
            path.write_text(trace_source, encoding="utf-8")

            summary = v2238.event_source_summary("cfg80211", path)

        self.assertIn("cfg80211_scan_done", summary["events"])
        self.assertIn("rdev_scan", summary["events"])
        scan = summary["events"]["cfg80211_scan_done"]
        rdev = summary["events"]["rdev_scan"]
        self.assertEqual(scan["scalarized_macros"], ["WIPHY_ENTRY"])
        self.assertEqual(rdev["template"], "rdev_template")
        self.assertEqual(rdev["scalarized_macros"], ["NETDEV_ENTRY", "WIPHY_ENTRY"])
        self.assertEqual(rdev["proto_pointer_params"][0]["type"], "struct wiphy")

    def test_classify_event_distinguishes_pointer_anchor_and_scalarized_records(self):
        scalarized = {
            "proto_pointer_params": [
                {"type": "struct wiphy", "name": "wiphy", "category": "struct_pointer"},
            ],
            "source_raw_pointer_fields": [],
            "scalarized_macros": ["WIPHY_ENTRY"],
        }
        retained = {
            "proto_pointer_params": [],
            "source_raw_pointer_fields": [{"kind": "field", "type": "struct wiphy *", "name": "wiphy"}],
            "scalarized_macros": [],
        }

        scalar_result = v2238.classify_event(scalarized, {"raw_pointer_fields": []})
        retained_result = v2238.classify_event(retained, None)

        self.assertEqual(scalar_result["feasibility"], "caller-pointer-record-scalarized")
        self.assertEqual(scalar_result["score"], 1)
        self.assertEqual(retained_result["feasibility"], "record-pointer-chain-possible")
        self.assertEqual(retained_result["score"], 3)

    def test_residual_state_marks_live_selftest_failure_as_cleanup_required(self):
        dry = v2238.residual_state({"steps": []})
        ok = v2238.residual_state({"steps": [{"name": "status"}], "selftest_fail0": True})
        bad = v2238.residual_state({"steps": [{"name": "status"}], "selftest_fail0": False})

        self.assertFalse(dry["device_touched"])
        self.assertTrue(dry["selftest_ok"])
        self.assertTrue(ok["device_touched"])
        self.assertFalse(ok["cleanup_required"])
        self.assertTrue(bad["cleanup_required"])
        self.assertEqual(bad["residual_risk"], "post-selftest-incomplete")
        self.assertFalse(bad["partition_write"])
        self.assertFalse(bad["bpf_attach"])


if __name__ == "__main__":
    unittest.main()
