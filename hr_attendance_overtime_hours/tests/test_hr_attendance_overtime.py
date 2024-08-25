# Copyright 2023 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, time

from odoo import fields
from odoo.tests.common import TransactionCase


class TestHRAttendanceOvertime(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Test Calendar",
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Monday Morning",
                            "dayofweek": "0",
                            "hour_from": 8,
                            "hour_to": 12,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Monday Afternoon",
                            "dayofweek": "0",
                            "hour_from": 13,
                            "hour_to": 17,
                        },
                    ),
                ],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "resource_calendar_id": cls.calendar.id,
            }
        )
        cls.overtime = cls.env["hr.attendance.overtime"].create(
            {
                "employee_id": cls.employee.id,
                "date": fields.Date.today(),
            }
        )

    def test_compute_planned_hours(self):
        self.overtime._compute_planned_hours()
        self.assertEqual(self.overtime.planned_hours, 8.0)

    def test_compute_worked_hours(self):
        self.env["hr.attendance"].create(
            [
                {
                    "employee_id": self.employee.id,
                    "check_in": datetime.combine(self.overtime.date, time(8, 0)),
                    "check_out": datetime.combine(self.overtime.date, time(12, 0)),
                },
                {
                    "employee_id": self.employee.id,
                    "check_in": datetime.combine(self.overtime.date, time(13, 0)),
                    "check_out": datetime.combine(self.overtime.date, time(17, 0)),
                },
            ]
        )
        self.overtime._compute_worked_hours()
        self.assertEqual(self.overtime.worked_hours, 8.0)
