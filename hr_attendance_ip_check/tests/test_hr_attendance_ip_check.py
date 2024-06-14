# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import time

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestHrAttendanceIPcheck(TransactionCase):
    """Tests for attendance date ranges validity"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Test Emp"})

    def test_valid_cidr(self):
        with self.assertRaises(ValidationError):
            self.attendance_cidr = self.env["attendance.cidr"].create(
                {"employee_ids": [self.employee.id], "cidr": "invalid"}
            )

    def test_ip_check(self):
        self.attendance_cidr = self.env["attendance.cidr"].create(
            {"employee_ids": [self.employee.id], "cidr": "127.0.0.1"}
        )
        Attendance = self.env["hr.attendance"].with_context(test_enable=True)
        self.attendance = Attendance.create(
            {
                "employee_id": self.employee.id,
                "check_in": time.strftime("%Y-%m-10 10:00"),
            }
        )
        emp_attendance = self.env["hr.attendance"].search(
            [("employee_id", "=", self.employee.id)]
        )
        self.assertTrue(self.attendance in emp_attendance)
