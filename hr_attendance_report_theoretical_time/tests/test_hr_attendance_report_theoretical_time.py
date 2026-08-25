# Copyright 2017-2019 Tecnativa - Pedro M. Baeza
# Copyright 2021 Landoo Sistemas de Informacion SL
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from freezegun import freeze_time

from odoo import Command
from odoo.tools import SQL, mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestHrAttendanceReportTheoreticalTimeBase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.HrLeave = cls.env["hr.leave"]
        cls.CalendarHolidaysPublic = cls.env["calendar.public.holiday"]
        cls.HrLeaveType = cls.env["hr.leave.type"]
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "Test Calendar", "attendance_ids": False, "tz": "UTC"}
        )
        for day in range(5):  # From monday to friday
            cls.calendar.attendance_ids = [
                Command.create(
                    {
                        "name": "Attendance",
                        "dayofweek": str(day),
                        "hour_from": "08",
                        "hour_to": "12",
                    },
                ),
                Command.create(
                    {
                        "name": "Attendance",
                        "dayofweek": str(day),
                        "hour_from": "14",
                        "hour_to": "18",
                    },
                ),
            ]
        cls.address_1 = cls.env["res.partner"].create(
            {"name": "Address 1", "country_id": cls.env.ref("base.uk").id}
        )
        cls.address_2 = cls.env["res.partner"].create(
            {
                "name": "Address 1",
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_cr").id,
            }
        )
        cls.env.company.resource_calendar_id = cls.calendar
        cls.employee_1 = cls.env["hr.employee"].create(
            {
                "name": "Employee 1",
                "resource_calendar_id": cls.calendar.id,
                "address_id": cls.address_1.id,
            }
        )
        cls.employee_2 = cls.env["hr.employee"].create(
            {
                "name": "Employee 2",
                "resource_calendar_id": cls.calendar.id,
                "address_id": cls.address_2.id,
            }
        )
        # Use a very old year for avoiding to collapse with current data
        cls.public_holiday_global = cls.CalendarHolidaysPublic.create(
            {
                "year": 1946,
                "line_ids": [
                    Command.create({"name": "Christmas", "date": "1946-12-25"})
                ],
            }
        )
        cls.public_holiday_country = cls.CalendarHolidaysPublic.create(
            {
                "year": 1946,
                "country_id": cls.address_2.country_id.id,
                "line_ids": [
                    Command.create({"name": "Before Christmas", "date": "1946-12-24"}),
                    Command.create(
                        {
                            "name": "Even More Before Christmas",
                            "date": "1946-12-23",
                            "state_ids": [Command.set(cls.address_2.state_id.ids)],
                        },
                    ),
                ],
            }
        )
        cls.leave_type = cls.HrLeaveType.create(
            {
                "name": "Leave Type Test",
                "exclude_public_holidays": True,
                "requires_allocation": False,
            }
        )
        # Force employee create_date for having auto-generated report entries
        cls.env.cr.execute(
            SQL(
                "UPDATE hr_employee SET create_date = %s WHERE id IN (%s, %s)",
                "1946-12-23 12:00:00",
                cls.employee_1.id,
                cls.employee_2.id,
            )
        )
        # Leave for employee 1
        cls.leave = cls.HrLeave.with_context(
            partner=cls.employee_1.address_id.id
        ).create(
            {
                "request_date_from": "1946-12-26",
                "request_date_to": "1946-12-26",
                "employee_id": cls.employee_1.id,
                "holiday_status_id": cls.leave_type.id,
            }
        )
        cls.leave.action_approve()
        attendances_vals = []
        for employee in (cls.employee_1, cls.employee_2):
            for day in range(23, 27):
                attendances_vals.append(
                    {
                        "employee_id": employee.id,
                        "check_in": f"1946-12-{day} 08:00:00",
                        "check_out": f"1946-12-{day} 12:00:00",
                    }
                )
                attendances_vals.append(
                    {
                        "employee_id": employee.id,
                        "check_in": f"1946-12-{day} 14:00:00",
                        "check_out": f"1946-12-{day} 18:00:00",
                    }
                )
        cls.attendances = cls.env["hr.attendance"].create(attendances_vals)


class TestHrAttendanceReportTheoreticalTime(TestHrAttendanceReportTheoreticalTimeBase):
    def test_theoretical_hours(self):
        # EMPLOYEE 1
        # 1946-12-23
        self.assertEqual(self.attendances[0].theoretical_hours, 8)
        self.assertEqual(self.attendances[1].theoretical_hours, 8)
        # 1946-12-24
        self.assertEqual(self.attendances[2].theoretical_hours, 8)
        self.assertEqual(self.attendances[3].theoretical_hours, 8)
        # 1946-12-25 - Global public holiday
        self.assertEqual(self.attendances[4].theoretical_hours, 0)
        self.assertEqual(self.attendances[5].theoretical_hours, 0)
        # 1946-12-26 - Employee on Holidays
        self.assertEqual(self.attendances[6].theoretical_hours, 0)
        self.assertEqual(self.attendances[7].theoretical_hours, 0)
        # EMPLOYEE 2
        # 1946-12-23 - Public holidays for state of employee 2
        self.assertEqual(self.attendances[8].theoretical_hours, 0)
        self.assertEqual(self.attendances[9].theoretical_hours, 0)
        # 1946-12-24 - Public holiday for country of employee 2
        self.assertEqual(self.attendances[10].theoretical_hours, 0)
        self.assertEqual(self.attendances[11].theoretical_hours, 0)
        # 1946-12-25 - Global public holiday
        self.assertEqual(self.attendances[12].theoretical_hours, 0)
        self.assertEqual(self.attendances[13].theoretical_hours, 0)
        # 1946-12-26 - Employee 2 leave
        self.assertEqual(self.attendances[14].theoretical_hours, 8)
        self.assertEqual(self.attendances[15].theoretical_hours, 8)

    @mute_logger("odoo.models.unlink")
    def test_theoretical_hours_recompute(self):
        """Change calendar, and then recompute with the wizard"""
        # Get rid of 4 hours per day so the theoretical should be 4.
        self.employee_1.resource_calendar_id.attendance_ids.filtered(
            lambda x: x.hour_from == 14.0
        ).unlink()
        # The attendances theoretical hours remain at 8 if not recomputed
        self.assertEqual(self.attendances[0].theoretical_hours, 8)
        self.assertEqual(self.attendances[1].theoretical_hours, 8)
        # Then we run the wizard just for day 23
        wizard = self.env["recompute.theoretical.attendance"].create(
            {
                "employee_ids": [Command.link(self.employee_1.id)],
                "date_from": "1946-12-23 00:00:00",
                "date_to": "1946-12-23 23:59:59",
            }
        )
        wizard.action_recompute()
        # Attendances for day 23 are recomputed
        self.assertEqual(self.attendances[0].theoretical_hours, 4)
        self.assertEqual(self.attendances[1].theoretical_hours, 4)
        # Attendances for day 24 remaine as they were
        self.assertEqual(self.attendances[2].theoretical_hours, 8)
        self.assertEqual(self.attendances[3].theoretical_hours, 8)

    def test_hr_attendance_read_group(self):
        # TODO: Test when having theoretical_hours_start_date set
        # Group by employee
        self.env["hr.attendance"].action_create_empty_attendance(
            limit_date_from=datetime.date(1946, 12, 23),
            limit_date_to=datetime.date(1947, 1, 1),
        ).flush_recordset()
        aggregates = ["worked_hours:sum", "theoretical_hours:sum", "difference:sum"]
        res = self.env[
            "hr.attendance.theoretical.time.report"
        ].formatted_read_grouping_sets(
            [
                ("date", ">=", "1946-12-23"),
                ("date", "<", "1946-12-31"),
                ("employee_id", "in", (self.employee_1.id, self.employee_2.id)),
            ],
            # It's important to add "date:day" so that it filters correctly
            [["employee_id", "date:day"]],
            aggregates,
        )[0]
        # It should include 4 working days (25 is holiday and 26 is leave)
        employee_data = {}
        for item in res:
            employee_id = item["employee_id"][0]
            if employee_id not in employee_data:
                employee_data[employee_id] = {f_name: 0 for f_name in aggregates}
            for f_name in aggregates:
                employee_data[employee_id][f_name] += item[f_name]
        employee_data_1 = employee_data[self.employee_1.id]
        self.assertEqual(employee_data_1["theoretical_hours:sum"], 32)
        self.assertEqual(employee_data_1["worked_hours:sum"], 32)
        self.assertEqual(employee_data_1["difference:sum"], 0)
        # It should include 5 working days (25 is holiday)
        employee_data_2 = employee_data[self.employee_2.id]
        self.assertEqual(employee_data_2["theoretical_hours:sum"], 24)
        self.assertEqual(employee_data_2["worked_hours:sum"], 32)
        self.assertEqual(employee_data_2["difference:sum"], 8)
        # Group by day
        res = self.env[
            "hr.attendance.theoretical.time.report"
        ].formatted_read_grouping_sets(
            [
                ("date", ">=", "1946-12-23"),
                ("date", "<", "1946-12-31"),
                ("employee_id", "=", self.employee_1.id),
            ],
            [["employee_id", "date:day"]],
            ["theoretical_hours:sum"],
        )[0]
        self.assertEqual(res[0]["theoretical_hours:sum"], 8)  # 1946-12-23
        self.assertEqual(res[1]["theoretical_hours:sum"], 8)  # 1946-12-24
        self.assertEqual(res[2]["theoretical_hours:sum"], 0)  # 1946-12-25
        self.assertEqual(res[3]["theoretical_hours:sum"], 0)  # 1946-12-26
        self.assertEqual(res[4]["theoretical_hours:sum"], 8)  # 1946-12-27(virtual)
        self.assertEqual(res[5]["theoretical_hours:sum"], 8)  # 1946-12-30(virtual)

    @mute_logger("odoo.models.unlink")
    @freeze_time("1947-01-01")
    def test_hr_attendance_cron_theoretical_hours_start_date(self):
        self.env["hr.attendance"].action_create_empty_attendance(
            limit_date_from=datetime.date(1946, 12, 23),
            limit_date_to=datetime.date(1947, 1, 1),
        ).flush_recordset()
        domain = [
            ("employee_id", "=", self.employee_1.id),
            ("active", "=", False),
            ("check_in", ">=", "1946-12-23"),
            ("check_in", "<=", "1947-01-01"),
        ]
        attendance_model = self.env["hr.attendance"].with_context(active_test=False)
        total_items = attendance_model.search_count(domain)
        self.assertEqual(total_items, 4)
        self.employee_1.write({"theoretical_hours_start_date": "1946-12-28"})
        total_items = attendance_model.search_count(domain)
        self.assertEqual(total_items, 3)
        # Remove attendances
        attendance_model.search(domain).unlink()
        self.employee_1.write({"theoretical_hours_start_date": "1946-12-28"})
        total_items = attendance_model.search_count(domain)
        self.assertEqual(total_items, 3)

    @mute_logger("odoo.models.unlink")
    @freeze_time("1947-01-01")
    def test_hr_attendance_cron_theoretical_hours_start_date_multi_date(self):
        attendance_model = self.env["hr.attendance"]
        attendance_model.search([("employee_id", "=", self.employee_1.id)]).unlink()
        attendance = attendance_model.create(
            {
                "employee_id": self.employee_1.id,
                "check_in": "1946-12-23 08:00:00",
                "check_out": "1946-12-25 12:00:00",
            }
        )
        attendance_model.action_create_empty_attendance(
            limit_date_from=datetime.date(1946, 12, 23),
            limit_date_to=datetime.date(1946, 12, 26),
        ).flush_recordset()
        domain = [
            ("employee_id", "=", self.employee_1.id),
            ("active", "=", False),
            ("check_in", ">=", "1946-12-23"),
            ("check_in", "<=", "1946-12-26"),
        ]
        attendance_model = self.env["hr.attendance"].with_context(active_test=False)
        total_items = attendance_model.search_count(domain)
        self.assertEqual(total_items, 1)
        # Fix wrong check_out date
        attendance.write({"check_out": "1946-12-23 12:00:00"})
        attendance_model.action_create_empty_attendance(
            limit_date_from=datetime.date(1946, 12, 23),
            limit_date_to=datetime.date(1946, 12, 26),
        ).flush_recordset()
        total_items = attendance_model.search_count(domain)
        self.assertEqual(total_items, 3)

    def test_change_hr_holidays_public(self):
        self.public_holiday_global.line_ids[0].write({"date": "1946-12-23"})
        # 1946-12-23
        self.assertEqual(self.attendances[0].theoretical_hours, 0)
        self.assertEqual(self.attendances[8].theoretical_hours, 0)
        # 1946-12-25
        self.assertEqual(self.attendances[4].theoretical_hours, 8)
        self.assertEqual(self.attendances[12].theoretical_hours, 8)

    @mute_logger("odoo.models.unlink")
    def test_change_hr_holidays(self):
        self.leave.action_refuse()
        # 1946-12-26 - Employee 2
        self.assertEqual(self.attendances[14].theoretical_hours, 8)

    def test_hr_holidays_status_include_in_theoretical(self):
        obj = self.env["hr.attendance.theoretical.time.report"]
        self.leave.holiday_status_id.include_in_theoretical = True
        # 1946-12-26 - Employee 1
        a = self.attendances[6]
        self.assertEqual(obj._theoretical_hours(a.employee_id, a.check_in), 8)

    def test_wizard_theoretical_time(self):
        department = self.env["hr.department"].create({"name": "Department"})
        tag = self.env["hr.employee.category"].create({"name": "Tag"})
        self.employee_1.write(
            {"department_id": department.id, "category_ids": [Command.link(tag.id)]}
        )
        wizard = self.env["wizard.theoretical.time"].create(
            {"department_id": department.id, "category_ids": [Command.link(tag.id)]}
        )
        wizard.populate()
        report = wizard.view_report()
        self.assertTrue(wizard.employee_ids)
        self.assertEqual(wizard.employee_ids[0].name, self.employee_1.name)
        self.assertEqual(
            report["domain"], [("employee_id", "in", [self.employee_1.id])]
        )

    @mute_logger("odoo.models.unlink")
    def test_theoretical_recompute_on_unactive(self):
        self.assertEqual(self.attendances[0].theoretical_hours, 8)
        self.attendances[0].active = False
        leave = self.env["hr.leave"].create(
            {
                "date_from": "1946-12-23 00:00:00",
                "date_to": "1946-12-23 23:59:59",
                "request_date_from": "1946-12-23",
                "request_date_to": "1946-12-23",
                "employee_id": self.employee_1.id,
                "holiday_status_id": self.leave_type.id,
            }
        )
        leave.action_approve()
        self.assertEqual(self.attendances[0].theoretical_hours, 0)
        self.leave_type.include_in_theoretical = True
        self.env["recompute.theoretical.attendance"].create(
            {
                "employee_ids": [Command.link(self.employee_1.id)],
                "date_from": "1946-12-23 00:00:00",
                "date_to": "1946-12-23 23:59:59",
            }
        ).action_recompute()
        self.assertEqual(self.attendances[0].theoretical_hours, 8)


class TestHrAttendanceReportTheoreticalTimeResource(BaseCommon):
    @classmethod
    def _define_calendar_2_weeks(cls, name, attendances, tz):
        return cls.env["resource.calendar"].create(
            {
                "name": name,
                "tz": tz,
                "two_weeks_calendar": True,
                "attendance_ids": [
                    Command.create(
                        {
                            "name": f"{name}_{index}",
                            "hour_from": att[0],
                            "hour_to": att[1],
                            "dayofweek": str(att[2]),
                            "week_type": att[3],
                            "display_type": att[4],
                            "sequence": att[5],
                        },
                    )
                    for index, att in enumerate(attendances)
                ],
            }
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar_jules = cls._define_calendar_2_weeks(
            "Week 1: Monday 8 Hours - Week 2: Monday 4 Hours",
            [
                (0, 0, 0, "0", "line_section", 0),
                (8, 12, 0, "0", False, 1),
                (0, 0, 0, "1", "line_section", 10),
                (8, 12, 0, "1", False, 11),
                (16, 20, 0, "1", False, 12),
            ],
            "Europe/Brussels",
        )
        cls.env.company.resource_calendar_id = cls.calendar_jules
        cls.employee = cls.env["hr.employee"].create(
            [{"name": "Employee", "resource_calendar_id": cls.calendar_jules.id}]
        )

    def test_theoretical_time_report_two_weeks(self):
        obj = self.env["hr.attendance.theoretical.time.report"]
        hours = obj._theoretical_hours(self.employee, datetime.date(2022, 1, 10))
        self.assertEqual(hours, 4)
        hours = obj._theoretical_hours(self.employee, datetime.date(2022, 1, 17))
        self.assertEqual(hours, 8)
