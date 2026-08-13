# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""The SQL report view and the wizard/PDF path in two scenarios."""

from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import new_test_user, tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestReportingScenario(TestHrAttendanceTimeCreditCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule = cls._make_rule("Report rule", minutes_fixed=30)
        cls.report_model = cls.env["hr.attendance.time.credit.report"]

    def _rows(self, employee, month):
        return self.report_model.search(
            [("employee_id", "=", employee.id), ("month", "=", month.replace(day=1))]
        )

    def test_report_view_scenario(self):
        employee = self.env["hr.employee"].create(
            {"name": "Report Employee", "company_id": self.company.id}
        )
        self._att_on(employee, date(2026, 1, 15), hours=1, check_in_hour=7)
        self._att_on(employee, date(2026, 1, 15), hours=7, check_in_hour=9)
        rows = self._rows(employee, date(2026, 1, 15))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.total_credited_minutes, 60)
        self.assertAlmostEqual(rows.credited_hours, 1.0)
        self.assertEqual(rows.attendance_count, 2)

        # Several credit lines on one attendance must not fan out worked hours.
        fan = self.env["hr.employee"].create(
            {"name": "Fan-out Employee", "company_id": self.company.id}
        )
        attendance = self._att_on(fan, date(2026, 3, 10), hours=8)
        self.env["hr.attendance.time.credit"].create(
            {
                "attendance_id": attendance.id,
                "type_id": self.credit_type.id,
                "minutes": 15,
                "origin": "manual",
            }
        )
        self.env.flush_all()
        fan_rows = self._rows(fan, date(2026, 3, 10))
        self.assertEqual(len(fan_rows), 1)
        self.assertAlmostEqual(fan_rows.worked_hours, attendance.worked_hours)
        self.assertEqual(fan_rows.total_credited_minutes, 45)
        self.assertAlmostEqual(fan_rows.credited_hours, 0.75)
        self.assertAlmostEqual(fan_rows.total_hours, attendance.worked_hours + 0.75)
        self.assertEqual(fan_rows.attendance_count, 1)

        # Rows belonging to another company carry that company's id.
        other_company = self.env["res.company"].create({"name": "Report Other Co"})
        other_employee = self.env["hr.employee"].create(
            {"name": "Other Company Employee", "company_id": other_company.id}
        )
        self._att_on(other_employee, date(2026, 3, 11), hours=8)
        other_rows = self._rows(other_employee, date(2026, 3, 11))
        self.assertTrue(other_rows)
        self.assertEqual(other_rows.mapped("company_id"), other_company)

        # A reader restricted to their own employee sees only that row.
        reader = self.env["res.users"].create(
            {
                "name": "Report Reader",
                "login": "report_reader_scenario@test.com",
                "groups_id": [
                    (4, self.env.ref("hr_attendance.group_hr_attendance_own_reader").id)
                ],
            }
        )
        reader_employee = self.env["hr.employee"].create(
            {
                "name": "Reader Employee",
                "company_id": self.company.id,
                "user_id": reader.id,
            }
        )
        self._att_on(reader_employee, date(2026, 3, 12), hours=8)
        visible = self.report_model.with_user(reader).search([])
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible.employee_id, reader_employee)


@tagged("post_install", "-at_install")
class TestReportWizardScenario(TestHrAttendanceTimeCreditCommon):
    def _wizard(self, **kwargs):
        today = date.today()
        vals = {
            "date_from": today.replace(day=1),
            "date_to": today.replace(day=1) + relativedelta(months=1, days=-1),
        }
        vals.update(kwargs)
        return self.env["hr.attendance.time.credit.report.wizard"].create(vals)

    def test_report_wizard_and_pdf_scenario(self):
        # Period validation accepts one month but rejects inversions and
        # ranges that cross a month boundary.
        wizard = self._wizard(date_from=date(2026, 8, 1), date_to=date(2026, 8, 31))
        self.assertEqual(wizard.date_from, date(2026, 8, 1))
        with self.assertRaises(ValidationError):
            self._wizard(date_from=date(2026, 1, 31), date_to=date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            self._wizard(date_from=date(2026, 8, 1), date_to=date(2026, 10, 9))

        filtered = self._wizard(employee_ids=[(4, self.employee.id)])
        action = filtered.action_print_report()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("type"), "ir.actions.report")
        self.assertEqual(
            action.get("report_name"),
            "hr_attendance_time_credit.report_time_credit_monthly",
        )

        # The rendered PDF data is scoped to the user's allowed companies.
        other_company = self.env["res.company"].create({"name": "PDF Other Co"})
        other_employee = self.env["hr.employee"].create(
            {"name": "PDF Outsider", "company_id": other_company.id}
        )
        self._create_attendance(
            datetime(2026, 6, 15, 8, 0), datetime(2026, 6, 15, 16, 0)
        )
        self.env["hr.attendance"].create(
            {
                "employee_id": other_employee.id,
                "check_in": datetime(2026, 6, 15, 8, 0),
                "check_out": datetime(2026, 6, 15, 16, 0),
            }
        )
        user = new_test_user(
            self.env,
            "pdf_company_user",
            groups="base.group_user,hr_attendance.group_hr_attendance_manager",
            company_id=self.company.id,
            company_ids=[(6, 0, [self.company.id])],
        )
        pdf_wizard = (
            self.env["hr.attendance.time.credit.report.wizard"]
            .with_user(user)
            .create({"date_from": date(2026, 6, 1), "date_to": date(2026, 6, 30)})
        )
        report = self.env.ref(
            "hr_attendance_time_credit.action_report_time_credit_monthly"
        )
        html = (
            self.env["ir.actions.report"]
            .with_user(user)
            ._render_qweb_html(report.id, pdf_wizard.ids)[0]
        ).decode()
        self.assertIn("Test Employee", html)
        self.assertNotIn("PDF Outsider", html)
