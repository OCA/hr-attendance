# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Tests for rule scope hierarchy (company → calendar → employee)."""

from datetime import datetime

from odoo.tests.common import tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestRuleScope(TestHrAttendanceTimeCreditCommon):
    """Tests for calendar_id / employee_id scope on credit rules."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar_a = cls._make_calendar(5, name="Calendar A")
        cls.calendar_b = cls._make_calendar(
            5, hour_from=9, hour_to=18, name="Calendar B"
        )
        cls.employee.resource_calendar_id = cls.calendar_a
        cls.employee_b = cls.env["hr.employee"].create(
            {"name": "Employee B", "company_id": cls.company.id}
        )
        cls.employee_b.resource_calendar_id = cls.calendar_b

    def _make_rule(self, credit_type, fixed_minutes, calendar=None, employee=None):
        vals = {"minutes_fixed": fixed_minutes}
        if calendar:
            vals["calendar_id"] = calendar.id
        if employee:
            vals["employee_id"] = employee.id
        return super()._make_rule(f"Rule {credit_type.code}", credit_type, **vals)

    def _att(self, employee=None):
        emp = employee or self.employee
        return self.env["hr.attendance"].create(
            {
                "employee_id": emp.id,
                "check_in": datetime(2026, 1, 7, 8, 0, 0),
                "check_out": datetime(2026, 1, 7, 16, 0, 0),
            }
        )

    def test_company_rule_fires_when_no_narrower(self):
        """Company-level rule applies when no calendar/employee rule exists."""
        self._make_rule(self.credit_type, 10)
        att = self._att()
        credit_lines = att.time_credit_ids.filtered(
            lambda c: c.type_id == self.credit_type and c.origin == "automatic"
        )
        self.assertEqual(len(credit_lines), 1)
        self.assertEqual(credit_lines.minutes, 10)

    def test_calendar_rule_overrides_company_for_same_type(self):
        """Calendar-scoped rule fires; company rule skipped for same type."""
        self._make_rule(self.credit_type, 10)
        self._make_rule(self.credit_type, 20, calendar=self.calendar_a)
        att = self._att()
        credit_lines = att.time_credit_ids.filtered(
            lambda c: c.type_id == self.credit_type and c.origin == "automatic"
        )
        self.assertEqual(len(credit_lines), 1)
        self.assertEqual(credit_lines.minutes, 20)

    def test_employee_rule_overrides_calendar_and_company_for_same_type(self):
        """Employee-scoped rule fires; calendar/company rules skipped."""
        self._make_rule(self.credit_type, 10)
        self._make_rule(self.credit_type, 20, calendar=self.calendar_a)
        self._make_rule(self.credit_type, 30, employee=self.employee)
        att = self._att()
        credit_lines = att.time_credit_ids.filtered(
            lambda c: c.type_id == self.credit_type and c.origin == "automatic"
        )
        self.assertEqual(len(credit_lines), 1)
        self.assertEqual(credit_lines.minutes, 30)

    def test_employee_rule_type_a_does_not_suppress_company_type_b(self):
        """Employee rule for type A does not suppress company rule for type B."""
        self._make_rule(self.credit_type, 30, employee=self.employee)
        self._make_rule(self.credit_type_2, 15)
        att = self._att()
        credits_a = att.time_credit_ids.filtered(
            lambda c: c.type_id == self.credit_type and c.origin == "automatic"
        )
        credits_b = att.time_credit_ids.filtered(
            lambda c: c.type_id == self.credit_type_2 and c.origin == "automatic"
        )
        self.assertEqual(len(credits_a), 1)
        self.assertEqual(credits_a.minutes, 30)
        self.assertEqual(len(credits_b), 1)
        self.assertEqual(credits_b.minutes, 15)

    def test_calendar_rule_does_not_apply_to_other_calendar(self):
        """Calendar-scoped rule does not apply to different calendar."""
        self._make_rule(self.credit_type, 20, calendar=self.calendar_a)
        att = self._att(employee=self.employee_b)
        credit_lines = att.time_credit_ids.filtered(
            lambda c: c.type_id == self.credit_type and c.origin == "automatic"
        )
        self.assertEqual(len(credit_lines), 0)
