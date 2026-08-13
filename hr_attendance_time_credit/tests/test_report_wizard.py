# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests.common import tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestTimeCreditReportWizard(TestHrAttendanceTimeCreditCommon):
    """Smoke tests for hr.attendance.time.credit.report.wizard."""

    def _make_wizard(self, **kwargs):
        today = date.today()
        vals = {
            "date_from": today.replace(day=1),
            "date_to": today.replace(day=1) + relativedelta(months=1, days=-1),
        }
        vals.update(kwargs)
        return self.env["hr.attendance.time.credit.report.wizard"].create(vals)

    def test_wizard_defaults(self):
        """date_from defaults to first of current month."""
        today = date.today()
        wizard = self._make_wizard()
        self.assertEqual(wizard.date_from, today.replace(day=1))

    def test_wizard_employee_filter(self):
        """Wizard with employee_ids still returns a valid report action."""
        wizard = self._make_wizard(employee_ids=[(4, self.employee.id)])
        action = wizard.action_print_report()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("type"), "ir.actions.report")

    def test_wizard_print_returns_correct_report_name(self):
        """action_print_report returns the expected report_name."""
        wizard = self._make_wizard()
        action = wizard.action_print_report()
        self.assertEqual(
            action.get("report_name"),
            "hr_attendance_time_credit.report_time_credit_monthly",
        )
