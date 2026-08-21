from datetime import date, datetime

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTimesheetAttendanceHours(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.tz = "UTC"
        cls.company = cls.env.ref("base.main_company")
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Test Worker", "company_id": cls.company.id}
        )
        cls.project = cls.env["project.project"].create(
            {"name": "Test Project", "company_id": cls.company.id}
        )
        cls.today = date.today()
        cls.base = datetime.combine(cls.today, datetime.min.time())

    def _make_attendance(self, hour_in, hour_out):
        return self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": self.base.replace(hour=hour_in),
                "check_out": self.base.replace(hour=hour_out),
            }
        )

    def _make_timesheet(self, hours, name="Task"):
        return self.env["account.analytic.line"].create(
            {
                "name": name,
                "employee_id": self.employee.id,
                "project_id": self.project.id,
                "date": self.today,
                "unit_amount": hours,
            }
        )

    def test_attendance_hours_basic(self):
        self._make_attendance(9, 17)
        line = self._make_timesheet(6.0)
        self.env.flush_all()
        line.invalidate_recordset()
        self.assertAlmostEqual(line.attendance_hours, 8.0, places=1)

    def test_no_attendance_zero(self):
        line = self._make_timesheet(4.0)
        self.assertEqual(line.attendance_hours, 0.0)

    def test_multiple_attendances_summed(self):
        self._make_attendance(8, 12)
        self._make_attendance(13, 17)
        line = self._make_timesheet(8.0)
        self.env.flush_all()
        line.invalidate_recordset()
        self.assertAlmostEqual(line.attendance_hours, 8.0, places=1)

    def test_open_attendance_excluded(self):
        self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": self.base.replace(hour=9),
            }
        )
        line = self._make_timesheet(4.0)
        self.assertEqual(line.attendance_hours, 0.0)

    def test_different_employees_independent(self):
        other = self.env["hr.employee"].create(
            {"name": "Other", "company_id": self.company.id}
        )
        self.env["hr.attendance"].create(
            {
                "employee_id": other.id,
                "check_in": self.base.replace(hour=9),
                "check_out": self.base.replace(hour=17),
            }
        )
        line = self._make_timesheet(8.0)
        self.assertEqual(line.attendance_hours, 0.0)

    def test_daily_timesheet_hours_single(self):
        self._make_attendance(9, 17)
        line = self._make_timesheet(6.0)
        self.env.flush_all()
        line.invalidate_recordset()
        self.assertAlmostEqual(line.daily_timesheet_hours, 6.0, places=1)

    def test_daily_timesheet_hours_multiple_tasks(self):
        self._make_attendance(9, 18)
        line1 = self._make_timesheet(3.0, "Task 1")
        line2 = self._make_timesheet(6.0, "Task 2")
        self.env.flush_all()
        (line1 | line2).invalidate_recordset()
        self.assertAlmostEqual(line1.daily_timesheet_hours, 9.0, places=1)
        self.assertAlmostEqual(line2.daily_timesheet_hours, 9.0, places=1)
        self.assertAlmostEqual(line1.attendance_hours, 9.0, places=1)

    def test_color_green(self):
        self._make_attendance(8, 18)
        line = self._make_timesheet(9.0)
        self.env.flush_all()
        line.invalidate_recordset()
        self.assertGreater(line.attendance_hours, line.daily_timesheet_hours + 0.5)

    def test_color_yellow(self):
        self._make_attendance(9, 18)
        line = self._make_timesheet(9.0)
        self.env.flush_all()
        line.invalidate_recordset()
        self.assertGreaterEqual(line.attendance_hours, line.daily_timesheet_hours)
        self.assertLess(line.attendance_hours, line.daily_timesheet_hours + 0.5)

    def test_color_red(self):
        self._make_attendance(9, 16)
        line = self._make_timesheet(9.0)
        self.env.flush_all()
        line.invalidate_recordset()
        self.assertLess(line.attendance_hours, line.daily_timesheet_hours)
