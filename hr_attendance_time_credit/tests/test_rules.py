# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""One scenario covering rule evaluation, from condition to final minutes."""

from datetime import datetime

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import TestHrAttendanceTimeCreditCommon

RULE_LOGGER = (
    "odoo.addons.hr_attendance_time_credit.models.hr_attendance_time_credit_rule"
)


@tagged("post_install", "-at_install")
class TestRuleEvaluationScenario(TestHrAttendanceTimeCreditCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Rule edits cascade over existing attendances; lift the lookback so the
        # scenario's fixed 2026 dates are always refreshed.
        cls.env["ir.config_parameter"].sudo().set_param(
            "hr_attendance_time_credit.cron_lookback_days", "0"
        )
        cls.cond_true = cls._make_server_action("Cond true", "action = True")
        cls.cond_false = cls._make_server_action("Cond false", "action = False")
        cls.minutes_45 = cls._make_server_action("Minutes 45", "action = 45")
        cls.minutes_bad = cls._make_server_action("Minutes text", "action = 'oops'")
        cls.rule_fixed = cls._make_rule("Fixed 30", minutes_fixed=30, sequence=10)
        cls.rule_sa = cls._make_rule(
            "Server action",
            cls.credit_type_2,
            condition_type="server_action",
            condition_action_id=cls.cond_true.id,
            minutes_type="server_action",
            minutes_action_id=cls.minutes_45.id,
            sequence=20,
        )
        cls.rule_factor = cls._make_rule(
            "Factor 1.5",
            cls._new_type("Factor"),
            minutes_type="worked_time_factor",
            factor_value=1.5,
            sequence=30,
        )
        cls.rule_accum = cls._make_rule(
            "Accum factor",
            cls._new_type("Accum"),
            minutes_type="worked_time_factor",
            factor_value=1.5,
            factor_base="accumulated_hours",
            sequence=40,
        )
        # The engine is skipped at creation so rule writes are free to cascade
        # without changing what this record is used to inspect.
        cls.eval_att = cls._create_attendance(
            datetime(2026, 1, 7, 8, 0),
            datetime(2026, 1, 7, 16, 0),
            context={"skip_time_credit_recompute": True},
        )

    @mute_logger(RULE_LOGGER)
    def test_rule_evaluation_scenario(self):
        # Condition types and the three minutes types.
        self.assertEqual(self.rule_fixed._evaluate(self.eval_att), 30)
        self.assertEqual(self.rule_sa._evaluate(self.eval_att), 45)
        # 8h * 60 * (1.5 - 1.0) = 240
        self.assertEqual(self.rule_factor._evaluate(self.eval_att), 240)
        # An explicitly supplied accumulated base is used verbatim.
        # int(8.5 * 60 * 0.5) = 255
        self.assertEqual(
            self.rule_accum._evaluate(self.eval_att, accumulated_hours=8.5), 255
        )

        # A false condition, a missing condition action, a missing minutes
        # action and a non-numeric minutes return all skip the rule safely.
        self.rule_sa.condition_action_id = self.cond_false
        self.assertFalse(self.rule_sa._evaluate(self.eval_att))
        self.rule_sa.condition_action_id = False
        self.assertFalse(self.rule_sa._evaluate(self.eval_att))
        self.rule_sa.condition_action_id = self.cond_true
        self.rule_sa.minutes_action_id = False
        self.assertEqual(self.rule_sa._evaluate(self.eval_att), 0)
        self.rule_sa.minutes_action_id = self.minutes_bad
        self.assertFalse(self.rule_sa._evaluate(self.eval_att))
        self.rule_sa.minutes_action_id = self.minutes_45

        # Rate is applied before the cap: int(30 * 2.0) = 60 -> capped to 45.
        self.rule_fixed.rate = 2.0
        self.rule_fixed.minutes_cap = 45
        self.assertEqual(self.rule_fixed._evaluate(self.eval_att), 45)
        self.rule_fixed.rate = 1.0
        self.rule_fixed.minutes_cap = 0

        # A malformed domain is logged and the rule is skipped.
        self.rule_fixed.domain = "INVALID"
        self.assertFalse(self.rule_fixed._evaluate(self.eval_att))
        self.rule_fixed.domain = "[]"

        # skip_time_credit short-circuits even a matching rule.
        skipped = self._create_attendance(
            datetime(2026, 1, 8, 8, 0),
            datetime(2026, 1, 8, 16, 0),
            skip_time_credit=True,
        )
        self.assertFalse(self.rule_fixed._evaluate(skipped))
        self.assertFalse(skipped.time_credit_ids)

        # Full pipeline: rules fire in sequence order, one line per type, and
        # the accumulated-hours rule sees the minutes granted before it.
        att = self._create_attendance(
            datetime(2026, 1, 9, 8, 0), datetime(2026, 1, 9, 16, 0)
        )
        self.assertEqual(len(att.time_credit_ids), 4)
        minutes_by_rule = {line.rule_id: line.minutes for line in att.time_credit_ids}
        self.assertEqual(minutes_by_rule[self.rule_fixed], 30)
        self.assertEqual(minutes_by_rule[self.rule_sa], 45)
        self.assertEqual(minutes_by_rule[self.rule_factor], 240)
        # The factor rules inherit a segmented type, so the accumulated rule
        # uses that day's segment base: 8h worked + 240 min credited = 12h.
        self.assertEqual(minutes_by_rule[self.rule_accum], int(12.0 * 60 * 0.5))

        # Inactive rules are excluded from the search, so a fresh attendance
        # receives nothing and the cascade clears the earlier lines.
        for rule in (self.rule_fixed, self.rule_sa, self.rule_factor, self.rule_accum):
            rule.active = False
        att.invalidate_recordset(["time_credit_ids"])
        self.assertFalse(att.time_credit_ids)
        fresh = self._create_attendance(
            datetime(2026, 1, 10, 8, 0), datetime(2026, 1, 10, 16, 0)
        )
        self.assertFalse(fresh.time_credit_ids)
