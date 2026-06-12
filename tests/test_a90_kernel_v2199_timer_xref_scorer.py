"""Regression tests for a90_kernel_v2199_timer_xref_scorer.

Pins the host-only timer xref scorer's pure normalization and scoring helpers.
No device access, source-tree scan, or V2198 artifact is required.
"""

import unittest

from _loader import load_revalidation

scorer = load_revalidation("a90_kernel_v2199_timer_xref_scorer")


def make_xref(
    *,
    name="timer_cb",
    api="setup_timer",
    timer_expr="foo->timer",
    expires="jiffies + 1",
    definitions=True,
    rkp_addr_taken=False,
):
    xref = scorer.CallbackXref(name=name)
    xref.timer_uses.append(scorer.TimerUse(
        api=api,
        timer_expr=timer_expr,
        timer_leaf=scorer.timer_leaf(timer_expr),
        callback=name,
        path="drivers/example.c",
        line=10,
        context=f"{api}(..., {name}, ...)",
    ))
    if expires is not None:
        xref.arm_refs.append(scorer.ArmRef(
            api="mod_timer",
            timer_expr=timer_expr,
            timer_leaf=scorer.timer_leaf(timer_expr),
            expires=expires,
            interval_class=scorer.interval_class(expires),
            path="drivers/example.c",
            line=20,
            context=f"mod_timer(..., {expires})",
        ))
    if definitions:
        xref.definitions.append(scorer.SourceRef(
            path="drivers/example.c",
            line=1,
            text=f"static void {name}(...)",
        ))
    xref.rkp_addr_taken = rkp_addr_taken
    return xref


class FormattingAndExpressionHelpers(unittest.TestCase):
    def test_format_signed_hex(self):
        self.assertEqual(scorer.format_signed_hex(0), "0x0")
        self.assertEqual(scorer.format_signed_hex(0x123), "0x123")
        self.assertEqual(scorer.format_signed_hex(-0x123), "-0x123")

    def test_clean_expr_strips_outer_ampersand_and_collapses_space(self):
        self.assertEqual(scorer.clean_expr("  &foo->bar\n\t"), "foo->bar")
        self.assertEqual(scorer.clean_expr("timer . field"), "timer . field")

    def test_timer_leaf_uses_last_identifier(self):
        cases = {
            "&foo->bar": "bar",
            "timer.field": "field",
            "((struct foo *)p)->timer": "timer",
            "": "",
        }
        for expr, expected in cases.items():
            with self.subTest(expr=expr):
                self.assertEqual(scorer.timer_leaf(expr), expected)


class IntervalClassification(unittest.TestCase):
    def test_interval_class_known_patterns(self):
        cases = {
            "": "none",
            "jiffies + 1": "jiffies_plus_1",
            "jiffies + HZ / 10": "short_poll",
            "now + 24 * 60 * 60 * HZ": "daily",
            "300 * HZ": "five_minutes",
            "t_expires": "journal_transaction_expiry",
            "gc_at - now": "gc_seconds",
            "2 * HZ": "hz_relative",
            "jiffies + delay": "jiffies_relative",
            "deadline": "variable",
        }
        for expires, expected in cases.items():
            with self.subTest(expires=expires):
                self.assertEqual(scorer.interval_class(expires), expected)

    def test_interval_score_orders_hot_and_cold_timers(self):
        self.assertGreater(
            scorer.interval_score("jiffies_plus_1"),
            scorer.interval_score("short_poll"),
        )
        self.assertGreater(
            scorer.interval_score("jiffies_relative"),
            scorer.interval_score("variable"),
        )
        self.assertLess(scorer.interval_score("daily"), 0)
        self.assertLess(scorer.interval_score("five_minutes"), 0)


class XrefScoring(unittest.TestCase):
    def test_score_xref_none_is_neutral_with_note(self):
        result = scorer.score_xref(None)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["best_interval_class"], "none")
        self.assertEqual(result["notes"], ["no source timer xref"])
        self.assertEqual(result["uses"], [])
        self.assertEqual(result["arms"], [])

    def test_score_xref_runtime_setup_struct_timer_hot_interval(self):
        xref = make_xref(rkp_addr_taken=True)
        result = scorer.score_xref(xref)

        self.assertEqual(result["score"], 280)
        self.assertEqual(result["best_interval_class"], "jiffies_plus_1")
        self.assertEqual(result["api_kinds"], ["setup_timer"])
        self.assertEqual(result["timer_leaves"], ["timer"])
        self.assertEqual(result["arm_count"], 1)
        self.assertEqual(result["definition_count"], 1)
        self.assertTrue(result["rkp_addr_taken"])
        self.assertIn("explicit runtime timer setup", result["notes"])
        self.assertIn("struct-field timer object", result["notes"])

    def test_score_xref_applies_known_timer_object_adjustments(self):
        low = make_xref(
            api="define_timer",
            timer_expr="key_gc_timer",
            expires="now + 300 * HZ",
            definitions=False,
        )
        low_result = scorer.score_xref(low)
        self.assertEqual(low_result["score"], 0)
        self.assertIn("low-cadence known timer object", low_result["notes"])

        nocb = make_xref(
            api="function_assignment",
            timer_expr="rdp->nocb_timer",
            expires="jiffies + HZ",
            definitions=False,
        )
        nocb_result = scorer.score_xref(nocb)
        self.assertEqual(nocb_result["score"], 135)
        self.assertIn("RCU no-CB per-cpu timer object", nocb_result["notes"])


class CandidateScoring(unittest.TestCase):
    def test_score_candidate_weights_rows_and_penalizes_non_callback_magic(self):
        xref = make_xref(rkp_addr_taken=True)
        candidate = {
            "slide": 0x1000,
            "slide_hex": "0x1000",
            "known_callback_weight": 7,
            "magic_weight": 11,
            "timer_rows": [
                {
                    "index": 0,
                    "runtime": "0xffffff8000001000",
                    "count": 3,
                    "symbol": "timer_cb",
                    "symbol_offset": 0,
                    "magic_deltas": [0],
                },
                {
                    "index": 1,
                    "runtime": "0xffffff8000002004",
                    "count": 2,
                    "symbol": "not_a_timer",
                    "symbol_offset": 4,
                    "magic_deltas": [4],
                },
                {
                    "index": 2,
                    "runtime": "ignored",
                    "count": 99,
                    "symbol": "ignored",
                    "symbol_offset": 0,
                    "magic_deltas": [],
                },
            ],
        }

        result = scorer.score_candidate(candidate, {"timer_cb": xref})

        self.assertEqual(result["slide"], 0x1000)
        self.assertEqual(result["slide_hex"], "0x1000")
        self.assertEqual(result["dominant_xref_score"], 280)
        self.assertEqual(result["weighted_xref_score"], 840)
        self.assertEqual(result["non_callback_magic_penalty"], 50)
        self.assertEqual(result["final_score"], 790)
        self.assertEqual(len(result["rows"]), 2)
        self.assertEqual(result["rows"][1]["offset_penalty"], 20)
        self.assertEqual(result["rows"][1]["row_score"], 0)


if __name__ == "__main__":
    unittest.main()
