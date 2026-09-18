# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from datetime import date, datetime

from odoo import fields
from odoo.tests.common import tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestTimeCreditReportModel(TestHrAttendanceTimeCreditCommon):
    """Tests for hr.attendance.time.credit.report SQL view."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule = cls._make_rule("Test Rule - 30min travel", minutes_fixed=30)

    def setUp(self):
        """Create a fresh employee for each test."""
        super().setUp()
        self.test_employee = self.env["hr.employee"].create(
            {"name": "Test Employee Report", "company_id": self.company.id}
        )

    def _get_report_rows(self, employee, month_date):
        """Return report rows for employee in the month containing month_date."""
        month_start = month_date.replace(day=1)
        return self.env["hr.attendance.time.credit.report"].search(
            [
                ("employee_id", "=", employee.id),
                ("month", "=", month_start),
            ]
        )

    def _create_test_attendance(self, check_in_dt, check_out_dt=None, **kwargs):
        """Create attendance for the test employee."""
        vals = {
            "employee_id": self.test_employee.id,
            "check_in": check_in_dt,
        }
        if check_out_dt:
            vals["check_out"] = check_out_dt
        vals.update(kwargs)
        return self.env["hr.attendance"].create(vals)

    def test_month_aggregation_basic(self):
        """Two closed attendances in same month produce one row with correct sums."""
        self._create_test_attendance(
            datetime(2026, 1, 15, 7, 0, 0),
            datetime(2026, 1, 15, 8, 0, 0),
        )
        self._create_test_attendance(
            datetime(2026, 1, 15, 9, 0, 0),
            datetime(2026, 1, 15, 16, 0, 0),
        )

        rows = self._get_report_rows(self.test_employee, date(2026, 1, 15))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.total_credited_minutes, 60)  # 30 min x 2 attendances
        self.assertEqual(rows.attendance_count, 2)

    def test_month_boundary_two_months(self):
        """Attendances in different months produce separate rows."""
        jan = datetime(2025, 1, 15, 8, 0)
        feb = datetime(2025, 2, 15, 8, 0)
        self._create_test_attendance(jan, datetime(2025, 1, 15, 16, 0))
        self._create_test_attendance(feb, datetime(2025, 2, 15, 16, 0))

        jan_rows = self._get_report_rows(self.test_employee, date(2025, 1, 1))
        feb_rows = self._get_report_rows(self.test_employee, date(2025, 2, 1))
        self.assertEqual(len(jan_rows), 1)
        self.assertEqual(len(feb_rows), 1)
        self.assertEqual(jan_rows.month, date(2025, 1, 1))
        self.assertEqual(feb_rows.month, date(2025, 2, 1))

    def test_no_credits_month(self):
        """Attendance with no matching rule produces a row with zero credits."""
        self.rule.active = False
        now = fields.Datetime.now()
        self._create_test_attendance(fields.Datetime.subtract(now, hours=8), now)
        rows = self._get_report_rows(self.test_employee, now.date())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.total_credited_minutes, 0)
        self.assertEqual(rows.attendance_count, 1)
        self.rule.active = True

    def test_open_attendance_excluded(self):
        """Attendance without check_out must not produce a report row."""
        now = fields.Datetime.now()
        # Create open attendance (no check_out)
        self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": fields.Datetime.subtract(now, hours=1),
            }
        )
        # Search the report for rows with attendance_count from open records only
        # by disabling the rule so we can isolate this test cleanly
        self.rule.active = False
        rows = self._get_report_rows(self.test_employee, now.date())
        # All rows in the report must come from closed attendances only;
        # if only an open record exists (no previous closed ones), rows must be empty
        self.assertEqual(len(rows), 0)
        self.rule.active = True

    def test_multi_company_isolation(self):
        """Report for another company's employee is scoped by company_id."""
        other_company = self.env["res.company"].create({"name": "Isolation Test Co"})
        other_employee = self.env["hr.employee"].create(
            {"name": "Isolated Employee", "company_id": other_company.id}
        )
        now = fields.Datetime.now()
        self.env["hr.attendance"].create(
            {
                "employee_id": other_employee.id,
                "check_in": fields.Datetime.subtract(now, hours=8),
                "check_out": now,
            }
        )
        # Report rows for other_employee should have other_company as company_id
        rows = self.env["hr.attendance.time.credit.report"].search(
            [("employee_id", "=", other_employee.id)]
        )
        for row in rows:
            self.assertEqual(row.company_id, other_company)

    def test_own_reader_sees_only_self(self):
        """A user with own_reader access sees only their own report rows."""
        other_user = self.env["res.users"].create(
            {
                "name": "Own Reader Test User",
                "login": "own_reader_report_test@test.com",
                "groups_id": [
                    (4, self.env.ref("hr_attendance.group_hr_attendance_own_reader").id)
                ],
            }
        )
        other_employee = self.env["hr.employee"].create(
            {
                "name": "Own Reader Employee",
                "company_id": self.company.id,
                "user_id": other_user.id,
            }
        )
        now = fields.Datetime.now()
        self._create_test_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.env["hr.attendance"].create(
            {
                "employee_id": other_employee.id,
                "check_in": fields.Datetime.subtract(now, hours=8),
                "check_out": now,
            }
        )
        rows = (
            self.env["hr.attendance.time.credit.report"]
            .with_user(other_user)
            .search([])
        )
        # Security rule filters rows by (employee_id.user_id == user.id)
        # so other_user should only see rows for other_employee
        self.assertEqual(len(rows), 1)
        # Verify the returned row is for other_employee (not test_employee)
        # by comparing employee_id without accessing restricted fields
        row_matches_other = rows.filtered(lambda r: r.employee_id == other_employee)
        self.assertEqual(len(row_matches_other), 1)
