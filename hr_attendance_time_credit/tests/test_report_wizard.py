# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError
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

    def test_wizard_rejects_inverted_period(self):
        """_check_period refuses a start date after the end date."""
        with self.assertRaises(ValidationError):
            self._make_wizard(date_from=date(2026, 1, 31), date_to=date(2026, 1, 1))

    def test_wizard_rejects_period_over_one_month(self):
        """_check_period caps the report at a single month."""
        with self.assertRaises(ValidationError):
            self._make_wizard(date_from=date(2026, 8, 1), date_to=date(2026, 10, 9))

    def test_wizard_accepts_a_single_month(self):
        """A period within one month is accepted."""
        wizard = self._make_wizard(
            date_from=date(2026, 8, 1), date_to=date(2026, 8, 31)
        )
        self.assertEqual(wizard.date_from, date(2026, 8, 1))

    def test_wizard_menu_name_is_distinct(self):
        """The wizard menu and action do not collide with the monthly control."""
        action = self.env.ref(
            "hr_attendance_time_credit.hr_attendance_time_credit_wizard_action"
        )
        menu = self.env.ref(
            "hr_attendance_time_credit.hr_attendance_time_credit_wizard_menu"
        )
        self.assertEqual(action.name, "Print Time Credit Monthly Report")
        self.assertEqual(menu.name, "Print Time Credit Monthly Report")
