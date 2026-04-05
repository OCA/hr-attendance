# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import TestHrAttendanceAllowanceCommon


@tagged("post_install", "-at_install")
class TestAllowanceRule(TestHrAttendanceAllowanceCommon):
    """Tests for the rule evaluation engine: domain conditions, server action
    conditions and minutes computation, and inactive rule filtering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule = cls.env["hr.attendance.allowance.rule"].create(
            {
                "name": "Match All - Fixed 30min",
                "allowance_type_id": cls.allowance_type.id,
                "company_id": cls.company.id,
                "condition_type": "domain",
                "domain": "[]",
                "minutes_type": "fixed",
                "minutes_fixed": 30,
                "sequence": 10,
            }
        )
        cls.condition_action = cls.env["ir.actions.server"].create(
            {
                "name": "Condition: always true",
                "model_id": cls.hr_attendance_model_id,
                "state": "code",
                "code": "action = True",
            }
        )
        cls.condition_action_false = cls.env["ir.actions.server"].create(
            {
                "name": "Condition: always false",
                "model_id": cls.hr_attendance_model_id,
                "state": "code",
                "code": "action = False",
            }
        )
        cls.minutes_action = cls.env["ir.actions.server"].create(
            {
                "name": "Minutes: fixed 45",
                "model_id": cls.hr_attendance_model_id,
                "state": "code",
                "code": "action = 45",
            }
        )
        cls.rule_sa = cls.env["hr.attendance.allowance.rule"].create(
            {
                "name": "Server Action Rule",
                "allowance_type_id": cls.allowance_type.id,
                "company_id": cls.company.id,
                "condition_type": "server_action",
                "condition_action_id": cls.condition_action.id,
                "minutes_type": "server_action",
                "minutes_action_id": cls.minutes_action.id,
                "sequence": 20,
            }
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

    def test_skip_allowance_flag(self):
        """Attendance with skip_allowance=True should always return False."""
        now = fields.Datetime.now()
        att = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            skip_allowance=True,
        )
        result = self.rule._evaluate(att)
        self.assertFalse(result)

    @mute_logger(
        "odoo.addons.hr_attendance_allowance.models.hr_attendance_allowance_rule"
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

    # -- Rate multiplier tests --

    def test_rate_below_one(self):
        """Rate < 1 should grant a fraction of the computed minutes."""
        self.rule.rate = 0.5
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule._evaluate(att)
        self.assertEqual(result, 15)

    def test_rate_above_one(self):
        """Rate > 1 should multiply minutes above the base value."""
        self.rule.rate = 1.5
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule._evaluate(att)
        self.assertEqual(result, 45)

    # -- Minutes cap tests --

    def test_cap_limits_minutes(self):
        """minutes_cap should clamp the computed value."""
        self.rule.minutes_cap = 20
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        result = self.rule._evaluate(att)
        self.assertEqual(result, 20)

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
        """An inactive rule should not produce allowance lines on attendance create."""
        # Deactivate class-level rules so only the inactive rule created below
        # exists; their writes are rolled back after this test.
        self.rule.active = False
        self.rule_sa.active = False
        self.env["hr.attendance.allowance.rule"].create(
            {
                "name": "Inactive rule",
                "allowance_type_id": self.allowance_type.id,
                "company_id": self.company.id,
                "condition_type": "domain",
                "domain": "[]",
                "minutes_type": "fixed",
                "minutes_fixed": 99,
                "sequence": 10,
                "active": False,
            }
        )
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        # Inactive rules are excluded from the rule search
        self.assertEqual(len(att.allowance_ids), 0)
