# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""One scenario walking the scope hierarchy and its isolation between employees."""

from datetime import date

from odoo.tests.common import tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestRuleScopeScenario(TestHrAttendanceTimeCreditCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar_a = cls._make_calendar(5, name="Calendar A")
        cls.calendar_b = cls._make_calendar(
            5, hour_from=9, hour_to=18, name="Calendar B"
        )
        cls.employee.resource_calendar_id = cls.calendar_a
        cls.employee_b = cls.env["hr.employee"].create(
            {"name": "Employee B", "company_id": cls.company.id, "tz": "UTC"}
        )
        cls.employee_b.resource_calendar_id = cls.calendar_b

    def _minutes(self, attendance):
        return sorted(
            attendance.time_credit_ids.filtered(
                lambda c: c.type_id == self.credit_type and c.origin == "automatic"
            ).mapped("minutes")
        )

    def test_scope_precedence_scenario(self):
        # A company-less rule is global: it applies to every company.
        global_rule = self._make_rule(
            "Global", minutes_fixed=40, company_id=False, sequence=5
        )
        self.assertEqual(
            self._minutes(self._att_on(self.employee, date(2026, 1, 5))), [40]
        )

        # A company rule and the global rule are both in scope at company level.
        self._make_rule("Company", minutes_fixed=10, sequence=10)
        self.assertEqual(
            self._minutes(self._att_on(self.employee, date(2026, 1, 6))), [10, 40]
        )

        # A calendar rule wins over company and global for the same credit type.
        self._make_rule(
            "Calendar A", minutes_fixed=20, calendar_id=self.calendar_a.id, sequence=15
        )
        self.assertEqual(
            self._minutes(self._att_on(self.employee, date(2026, 1, 7))), [20]
        )

        # An employee rule wins over every broader scope.
        self._make_rule(
            "Employee A", minutes_fixed=30, employee_id=self.employee.id, sequence=20
        )
        self.assertEqual(
            self._minutes(self._att_on(self.employee, date(2026, 1, 8))), [30]
        )

        # The narrower rules do not leak to a colleague on another calendar:
        # only the company and global tiers remain for them.
        self.assertEqual(
            self._minutes(self._att_on(self.employee_b, date(2026, 1, 9))), [10, 40]
        )
        self.assertFalse(global_rule.employee_id)
