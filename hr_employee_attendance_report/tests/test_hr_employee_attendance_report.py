# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime

from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase


class TestHrAttendanceReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_report_hr_attendance_value(self):
        self.report = self.env["report.hr_employee_attendance_report.hr_employee"]
        self.company = self.env["res.company"].create(
            {
                "name": "TestCom Inc.",
                "overtime_start_date": datetime(2021, 1, 1),
                "hr_attendance_overtime": True,
                "overtime_company_threshold": 10,
                "overtime_employee_threshold": 10,
            }
        )
        self.user = new_test_user(
            self.env,
            login="fru",
            groups="base.group_user,hr_attendance.group_hr_attendance_manager",
            company_id=self.company.id,
        ).with_company(self.company)
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Demo Emp",
                "user_id": self.user.id,
                "company_id": self.company.id,
            }
        )

        self.leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Time Off",
                "time_type": "leave",
                "requires_allocation": "yes",
                "allocation_validation_type": "no",
            }
        )
        self.leave = self.env["hr.leave"].create(
            {
                "name": "Leave test",
                "holiday_status_id": self.leave_type.id,
                "request_date_from": datetime(2021, 1, 2, 8, 0, 0),
                "request_date_to": datetime(2021, 1, 5, 17, 0, 0),
                "employee_id": self.employee.id,
            }
        )
        self.allocation = self.env["hr.leave.allocation"].create(
            {
                "name": "Some Holiday",
                "holiday_type": "employee",
                "employee_ids": [(4, self.employee.id)],
                "employee_id": self.employee.id,
                "holiday_status_id": self.leave_type.id,
                "allocation_type": "regular",
                "date_from": datetime(2021, 1, 2, 8),
                "date_to": datetime(2021, 1, 3, 17),
            }
        )
        self.resource_leave = self.env["resource.calendar.leaves"].create(
            [
                {
                    "name": "Absence",
                    "company_id": self.company.id,
                    "calendar_id": self.employee.resource_calendar_id.id,
                    "resource_id": self.employee.resource_id.id,
                    "holiday_id": self.leave.id,
                    "date_from": datetime(2021, 1, 2, 8, 0, 0),
                    "date_to": datetime(2021, 1, 2, 17, 0, 0),
                    "time_type": "leave",
                }
            ]
        )

        self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime(2021, 1, 4, 8, 0),
                "check_out": datetime(2021, 1, 4, 20, 0),
            }
        )
        self.env["hr.attendance.overtime"].create(
            {"employee_id": self.employee.id, "duration": 3.0}
        )

        data = {"date_from": "2021-01-02", "date_until": "2021-01-04"}
        values = self.report._get_report_values(docids=[self.employee.id], data=data)
        summary = values["summary"].get(self.employee.id)
        leave_allocations = values["leave_allocations"].get(self.employee.id)
        self.assertEqual(summary.get("worked_hours"), 11.0)
        self.assertEqual(summary.get("overtime_total"), 6.0)
        self.assertEqual(summary.get("leave_hours"), 16.0)
        self.assertEqual(summary.get("overtime"), 3.0)
        self.assertTrue(self.allocation in leave_allocations)
