# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, datetime, timedelta

from odoo.tests.common import TransactionCase


class TestOvertimeCalculation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "tz": "Europe/Amsterdam",
                "name": "workdays morning",
                "attendance_ids": [
                    # every morning 4h
                    (
                        0,
                        0,
                        {
                            "name": "mon morning",
                            "dayofweek": "0",
                            "hour_from": 8,
                            "hour_to": 12,
                            "day_period": "morning",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "tue morning",
                            "dayofweek": "1",
                            "hour_from": 8,
                            "hour_to": 12,
                            "day_period": "morning",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "wed morning",
                            "dayofweek": "2",
                            "hour_from": 8,
                            "hour_to": 12,
                            "day_period": "morning",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "thu morning",
                            "dayofweek": "3",
                            "hour_from": 8,
                            "hour_to": 12,
                            "day_period": "morning",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "fri morning",
                            "dayofweek": "4",
                            "hour_from": 8,
                            "hour_to": 12,
                            "day_period": "morning",
                        },
                    ),
                ],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "testemployee",
                "resource_calendar_id": cls.calendar.id,
            }
        )
        cls.employee.company_id.overtime_start_date = datetime(2023, 7, 31)

    def _sum_overtime(self):
        return sum(
            self.env["hr.attendance.overtime"]
            .search(
                [
                    ("employee_id", "=", self.employee.id),
                    ("adjustment", "=", False),
                ]
            )
            .mapped("duration")
        )

    def test_calculation_standard(self):
        """Test that the calculation works as expected for standard cases"""
        self.env["hr.attendance.overtime"]._compute_missing_overtime(
            end_date=date(2023, 8, 13)
        )
        self.assertEqual(self._sum_overtime(), -40)

        start_date = datetime(
            2023, 7, 30, 22
        )  # monday 31st 00:00 from pov of europe/amsterdam

        self.env["hr.attendance"].create(
            {
                # monday, nearly exactly working time
                "employee_id": self.employee.id,
                "check_in": start_date + timedelta(hours=8),
                "check_out": start_date + timedelta(hours=12, minutes=30),
            }
        )

        self.assertEqual(self._sum_overtime(), -35.5)

        self.env["hr.attendance"].create(
            {
                # saturday, all overtime
                "employee_id": self.employee.id,
                "check_in": start_date + timedelta(days=5, hours=8),
                "check_out": start_date + timedelta(days=5, hours=12, minutes=30),
            }
        )

        self.assertEqual(self._sum_overtime(), -31)

        self.env["hr.attendance"].create(
            {
                # monday, all out of working times, but less time than expected that day
                "employee_id": self.employee.id,
                "check_in": start_date + timedelta(days=7, hours=22),
                "check_out": start_date + timedelta(days=7, hours=24),
            }
        )

        self.assertEqual(self._sum_overtime(), -29)

        self.env["hr.attendance"].create(
            [
                {
                    # tuesday, all out of working times, but less time than expected that day
                    "employee_id": self.employee.id,
                    "check_in": start_date + timedelta(days=8, hours=22),
                    "check_out": start_date + timedelta(days=8, hours=24),
                },
                {
                    # tuesday, all out of working times, but less time than expected that day
                    "employee_id": self.employee.id,
                    "check_in": start_date + timedelta(days=8, hours=19),
                    "check_out": start_date + timedelta(days=8, hours=20),
                },
            ]
        )

        self.assertEqual(self._sum_overtime(), -26)
