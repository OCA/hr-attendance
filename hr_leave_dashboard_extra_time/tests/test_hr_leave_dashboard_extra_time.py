# Copyright 2023 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from odoo import fields
from odoo.tests.common import TransactionCase


class TestHrLeaveDashboardExtraTime(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_id = cls.env.user
        cls.company = cls.env.company
        cls.company.write(
            {
                "hr_attendance_overtime": True,
                "overtime_start_date": date(2024, 5, 25),
            }
        )

        cls.user_id.company_id = cls.company
        cls.user_id.tz = "UTC"
        cls.user_id.company_id.resource_calendar_id.tz = "UTC"
        cls.extra_hours_leave_type = cls.env.ref(
            "hr_holidays_attendance.holiday_status_extra_hours",
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": cls.company.id,
                "user_id": cls.user_id.id,
            }
        )
        cls.env["hr.attendance"].create(
            [
                {
                    "employee_id": cls.employee.id,
                    "check_in": datetime(2024, 5, 28, 8, 0),
                    "check_out": datetime(2024, 5, 28, 20, 0),
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": datetime(2024, 5, 29, 8, 0),
                    "check_out": datetime(2024, 5, 29, 20, 0),
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": datetime(2024, 5, 30, 8, 0),
                    "check_out": datetime(2024, 5, 30, 20, 0),
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": datetime(2024, 5, 31, 8, 0),
                    "check_out": datetime(2024, 5, 31, 20, 0),
                },
            ]
        )
        context = cls.env.context.copy()
        context["allowed_company_ids"] = [cls.company.id]
        cls.env.context = context

    def test_get_allocation_data_request(self):
        self.assertEqual(self.employee.total_overtime, 12)
        leave = self.env["hr.leave"].create(
            {
                "request_date_from": date(2024, 5, 30),
                "request_date_to": date(2024, 5, 30),
                "employee_id": self.employee.id,
                "holiday_status_id": self.extra_hours_leave_type.id,
            }
        )
        self.assertEqual(leave.number_of_hours_display, 8)
        target_date = fields.Date.today()
        result = self.extra_hours_leave_type.get_allocation_data_request(target_date)
        self.assertEqual(result[0][0], self.extra_hours_leave_type.name)
        self.assertEqual(result[0][2], "no")
        self.assertEqual(result[0][3], self.extra_hours_leave_type.id)
        lt_values = result[0][1]
        self.assertEqual(lt_values["leaves_requested"], 1)
        self.assertEqual(lt_values["leaves_taken"], 0)
        self.assertEqual(lt_values["request_unit"], "hour")
