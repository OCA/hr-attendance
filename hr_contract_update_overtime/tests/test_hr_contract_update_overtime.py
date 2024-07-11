# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime, timedelta

from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


@freeze_time("2024-01-19")
class HRContractUpdateOvertime(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        tz = "UTC"
        cls.env.user.tz = tz
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Overtime Employee",
                "gender": "male",
                "country_id": cls.env.ref("base.es").id,
                "tz": tz,
            }
        )
        today = fields.Date.today()

        def make_dtt(days_before, h=0, m=0, to_date=False):
            dat = datetime.combine(
                today - timedelta(days=days_before), datetime.min.time()
            ).replace(hour=h, minute=m)
            if to_date:
                return dat.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
            return dat.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # Configure overtime
        company = cls.employee.company_id
        company.hr_attendance_overtime = True
        company.overtime_start_date = make_dtt(7, 0, 0, to_date=True)
        company.overtime_company_threshold = 0.0
        company.overtime_employee_threshold = 0.0
        company.resource_calendar_id.tz = tz
        # Create attendances

        cls.env["hr.attendance"].create(
            [
                {
                    "employee_id": cls.employee.id,
                    "check_in": make_dtt(4, h=8, m=30),
                    "check_out": make_dtt(4, h=9, m=30),
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": make_dtt(3, h=8, m=30),
                    "check_out": make_dtt(3, h=11, m=30),
                },
                {
                    "employee_id": cls.employee.id,
                    "check_in": make_dtt(2, h=8, m=30),
                    "check_out": make_dtt(2, h=15, m=30),
                },
            ]
        )
        # Create Resource Calendars
        rc_2h_day = cls.env["resource.calendar"].create(
            [
                {
                    "name": "Test Calendar: 10h week",
                    "company_id": company.id,
                    "tz": tz,
                    "two_weeks_calendar": False,
                    "attendance_ids": [(5, 0, 0)]
                    + [
                        (
                            0,
                            0,
                            {
                                "name": "Attendance",
                                "dayofweek": dayofweek,
                                "hour_from": hour_from,
                                "hour_to": hour_to,
                                "day_period": day_period,
                            },
                        )
                        for dayofweek, hour_from, hour_to, day_period in [
                            ("0", 8.0, 10.0, "morning"),
                            ("1", 8.0, 10.0, "morning"),
                            ("2", 8.0, 10.0, "morning"),
                            ("3", 8.0, 10.0, "morning"),
                            ("4", 8.0, 10.0, "morning"),
                        ]
                    ],
                }
            ]
        )
        rc_4h_day = cls.env["resource.calendar"].create(
            [
                {
                    "name": "Test Calendar: 20h week",
                    "company_id": company.id,
                    "tz": tz,
                    "two_weeks_calendar": False,
                    "attendance_ids": [(5, 0, 0)]
                    + [
                        (
                            0,
                            0,
                            {
                                "name": "Attendance",
                                "dayofweek": dayofweek,
                                "hour_from": hour_from,
                                "hour_to": hour_to,
                                "day_period": day_period,
                            },
                        )
                        for dayofweek, hour_from, hour_to, day_period in [
                            ("0", 8.0, 12.0, "morning"),
                            ("1", 8.0, 12.0, "morning"),
                            ("2", 8.0, 12.0, "morning"),
                            ("3", 8.0, 12.0, "morning"),
                            ("4", 8.0, 12.0, "morning"),
                        ]
                    ],
                }
            ]
        )
        rc_8h_day = cls.env["resource.calendar"].create(
            [
                {
                    "name": "Test Calendar: 40h week",
                    "company_id": company.id,
                    "tz": tz,
                    "two_weeks_calendar": False,
                    "attendance_ids": [(5, 0, 0)]
                    + [
                        (
                            0,
                            0,
                            {
                                "name": "Attendance",
                                "dayofweek": dayofweek,
                                "hour_from": hour_from,
                                "hour_to": hour_to,
                                "day_period": day_period,
                            },
                        )
                        for dayofweek, hour_from, hour_to, day_period in [
                            ("0", 8.0, 16.0, "morning"),
                            ("1", 8.0, 16.0, "morning"),
                            ("2", 8.0, 16.0, "morning"),
                            ("3", 8.0, 16.0, "morning"),
                            ("4", 8.0, 16.0, "morning"),
                        ]
                    ],
                }
            ]
        )
        # Create Contracts
        cls.env["hr.contract"].create(
            [
                {
                    "name": "Contract 2h",
                    "employee_id": cls.employee.id,
                    "hr_responsible_id": cls.env.user.id,
                    "resource_calendar_id": rc_2h_day.id,
                    "state": "close",
                    "wage": 1,
                    "date_start": make_dtt(4, to_date=True),
                    "date_end": make_dtt(4, to_date=True),
                },
                {
                    "name": "Contract 4h",
                    "employee_id": cls.employee.id,
                    "hr_responsible_id": cls.env.user.id,
                    "resource_calendar_id": rc_4h_day.id,
                    "state": "close",
                    "wage": 2,
                    "date_start": make_dtt(3, to_date=True),
                    "date_end": make_dtt(3, to_date=True),
                },
                {
                    "name": "Contract 8h",
                    "employee_id": cls.employee.id,
                    "hr_responsible_id": cls.env.user.id,
                    "resource_calendar_id": rc_8h_day.id,
                    "state": "open",
                    "wage": 4,
                    "date_start": make_dtt(2, to_date=True),
                },
            ]
        )
        cls.contract_history = cls.env["hr.contract.history"].search(
            [
                ("employee_id", "=", cls.employee.id),
            ]
        )
        cls.overtime_model = cls.env["hr.attendance.overtime"]

    def test_overtime(self):
        self.assertEqual(self.contract_history.contract_count, 3)
        self.contract_history.action_update_overtime()
        total_overtime = (
            self.env["hr.attendance.overtime"]
            .search(
                [
                    ("employee_id", "=", self.employee.id),
                ]
            )
            .mapped("duration")
        )
        self.assertEqual(sum(total_overtime), -3.0)
