# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestTimeCreditRule(TestHrAttendanceTimeCreditCommon):
    """Tests for the rule evaluation engine: domain conditions, server action
    conditions and minutes computation, and inactive rule filtering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule = cls._make_rule("Match All - Fixed 30min", minutes_fixed=30)
        cls.condition_action = cls._make_server_action(
            "Condition: always true", "action = True"
        )
        cls.condition_action_false = cls._make_server_action(
            "Condition: always false", "action = False"
        )
        cls.minutes_action = cls._make_server_action("Minutes: fixed 45", "action = 45")
        cls.rule_sa = cls._make_rule(
            "Server Action Rule",
            condition_type="server_action",
            condition_action_id=cls.condition_action.id,
            minutes_type="server_action",
            minutes_action_id=cls.minutes_action.id,
            sequence=20,
        )

    # -- Domain condition tests --

    def test_domain_match_all_fixed_minutes(self):
        """A rule with empty domain should match any attendance."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule._evaluate(att)
        self.assertEqual(result, 30)

    def test_domain_no_match(self):
        """A rule with a restrictive domain should not match."""
        self.rule.domain = "[('employee_id.name', '=', 'Nobody')]"
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule._evaluate(att)
        self.assertFalse(result)

    def test_skip_time_credit_flag(self):
        """Attendance with skip_time_credit=True should always return False."""
        now = fields.Datetime.now()
        att = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            skip_time_credit=True,
        )
        result = self.rule._evaluate(att)
        self.assertFalse(result)

    @mute_logger(
        "odoo.addons.hr_attendance_time_credit.models.hr_attendance_time_credit_rule"
    )
    def test_invalid_domain_returns_false(self):
        """A malformed domain should not raise but return False."""
        self.rule.domain = "INVALID"
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule._evaluate(att)
        self.assertFalse(result)

    # -- Server action condition tests --

    def test_server_action_condition_true_and_minutes(self):
        """Server action condition returns True, minutes action returns 45."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule_sa._evaluate(att)
        self.assertEqual(result, 45)

    def test_server_action_condition_false(self):
        """Server action condition returns False; rule should not match."""
        self.rule_sa.condition_action_id = self.condition_action_false
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule_sa._evaluate(att)
        self.assertFalse(result)

    def test_server_action_condition_missing(self):
        """Rule with server_action type but no action set returns False."""
        self.rule_sa.condition_action_id = False
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule_sa._evaluate(att)
        self.assertFalse(result)

    def test_server_action_minutes_missing(self):
        """Condition passes but minutes action missing returns 0."""
        self.rule_sa.minutes_action_id = False
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule_sa._evaluate(att)
        self.assertEqual(result, 0)

    def test_server_action_with_fixed_minutes(self):
        """Server action condition + fixed minutes."""
        self.rule_sa.minutes_type = "fixed"
        self.rule_sa.minutes_fixed = 60
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule_sa._evaluate(att)
        self.assertEqual(result, 60)

    # -- Minutes cap tests --

    def test_cap_zero_means_no_cap(self):
        """minutes_cap=0 should not limit anything."""
        self.rule.minutes_fixed = 120
        self.rule.minutes_cap = 0
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule._evaluate(att)
        self.assertEqual(result, 120)

    def test_rate_then_cap(self):
        """Cap is applied after rate: 30 * 2.0 = 60, capped at 45 → 45."""
        self.rule.rate = 2.0
        self.rule.minutes_cap = 45
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule._evaluate(att)
        self.assertEqual(result, 45)

    # -- Inactive rule tests --

    def test_inactive_rule_not_evaluated(self):
        """An inactive rule should not produce credit lines on attendance create."""
        # Deactivate class-level rules so only the inactive rule created below
        # exists; their writes are rolled back after this test.
        self.rule.active = False
        self.rule_sa.active = False
        self._make_rule("Inactive rule", minutes_fixed=99, active=False)
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        # Inactive rules are excluded from the rule search
        self.assertEqual(len(att.time_credit_ids), 0)
