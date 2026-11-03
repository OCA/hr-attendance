# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon

# 2026-11-02 is a Monday of week type "1" (second week),
# 2026-11-09 is a Monday of week type "0" (first week).
MONDAY = "2026-11-02"
MONDAY_FIRST_WEEK = "2026-11-09"
SUNDAY = "2026-11-01"


class TestHrEmployeeAttendance(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.restriction_working_schedules = True
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Test calendar",
                "tz": "UTC",
                "attendance_before": 0.25,
                "attendance_ids": [
                    (5, 0, 0),
                    cls._line_vals("0", "morning", 8.0, 12.0),
                    cls._line_vals("0", "lunch", 12.0, 13.0),
                    cls._line_vals("0", "afternoon", 13.0, 17.0),
                ],
            }
        )
        cls.user = new_test_user(cls.env, "att_user", groups="base.group_user")
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Employee test",
                "resource_calendar_id": cls.calendar.id,
                "user_id": cls.user.id,
            }
        )

    @classmethod
    def _line_vals(cls, dayofweek, day_period, hour_from, hour_to, **extra):
        return (
            0,
            0,
            {
                "name": f"{day_period} {dayofweek}",
                "dayofweek": dayofweek,
                "day_period": day_period,
                "hour_from": hour_from,
                "hour_to": hour_to,
                **extra,
            },
        )

    @freeze_time(f"{SUNDAY} 10:00:00")
    def test_no_attendance_lines(self):
        with self.assertRaisesRegex(UserError, "unable to register"):
            self.employee._valid_attendance_working_hours()

    @freeze_time(f"{MONDAY} 10:00:00")
    def test_within_working_hours(self):
        self.employee._valid_attendance_working_hours()

    @freeze_time(f"{MONDAY} 07:50:00")
    def test_before_working_hours_with_margin(self):
        self.employee._valid_attendance_working_hours()

    @freeze_time(f"{MONDAY} 07:30:00")
    def test_before_working_hours_without_margin(self):
        with self.assertRaisesRegex(UserError, "hasn't started yet"):
            self.employee._valid_attendance_working_hours()

    @freeze_time(f"{MONDAY} 12:30:00")
    def test_lunch_break(self):
        with self.assertRaisesRegex(UserError, "hasn't started yet"):
            self.employee._valid_attendance_working_hours()

    @freeze_time(f"{MONDAY} 12:50:00")
    def test_lunch_break_with_margin(self):
        self.employee._valid_attendance_working_hours()

    @freeze_time(f"{MONDAY} 18:00:00")
    def test_after_working_hours(self):
        with self.assertRaisesRegex(UserError, "already ended") as error:
            self.employee._valid_attendance_working_hours()
        self.assertIn("Morning: 07:45 - 12:00", str(error.exception))
        self.assertIn("Afternoon: 12:45 - 17:00", str(error.exception))
        self.assertNotIn("Lunch", str(error.exception))

    @freeze_time(f"{MONDAY} 02:00:00")
    def test_schedule_starting_at_midnight(self):
        self.calendar.attendance_ids = [
            (5, 0, 0),
            self._line_vals("0", "morning", 0.0, 1.0),
        ]
        with self.assertRaisesRegex(UserError, "already ended") as error:
            self.employee._valid_attendance_working_hours()
        self.assertIn("Morning: 00:00 - 01:00", str(error.exception))

    @freeze_time(f"{MONDAY} 05:00:00")
    def test_schedules_sorted_by_start_time(self):
        self.calendar.attendance_ids = [
            self._line_vals("0", "morning", 0.0, 1.0, sequence=99),
        ]
        with self.assertRaisesRegex(UserError, "hasn't started yet") as error:
            self.employee._valid_attendance_working_hours()
        message = str(error.exception)
        self.assertLess(
            message.index("Morning: 00:00 - 01:00"),
            message.index("Morning: 07:45 - 12:00"),
        )
        self.assertLess(
            message.index("Morning: 07:45 - 12:00"),
            message.index("Afternoon: 12:45 - 17:00"),
        )

    def test_two_weeks_calendar(self):
        self.calendar.write(
            {
                "two_weeks_calendar": True,
                "attendance_ids": [
                    (5, 0, 0),
                    self._line_vals(
                        "0",
                        "morning",
                        0.0,
                        0.0,
                        display_type="line_section",
                        week_type="0",
                        sequence=0,
                    ),
                    self._line_vals(
                        "0", "morning", 8.0, 12.0, week_type="0", sequence=1
                    ),
                    self._line_vals(
                        "0",
                        "morning",
                        0.0,
                        0.0,
                        display_type="line_section",
                        week_type="1",
                        sequence=10,
                    ),
                    self._line_vals(
                        "1", "morning", 8.0, 12.0, week_type="1", sequence=11
                    ),
                ],
            }
        )
        with freeze_time(f"{MONDAY_FIRST_WEEK} 10:00:00"):
            self.employee._valid_attendance_working_hours()
        with freeze_time(f"{MONDAY} 10:00:00"):
            with self.assertRaisesRegex(UserError, "unable to register"):
                self.employee._valid_attendance_working_hours()

    @freeze_time(f"{MONDAY} 18:00:00")
    def test_check_in_restricted(self):
        with self.assertRaisesRegex(UserError, "already ended"):
            self.employee._attendance_action_change()

    @freeze_time(f"{MONDAY} 10:00:00")
    def test_check_in_allowed(self):
        attendance = self.employee._attendance_action_change()
        self.assertEqual(attendance.employee_id, self.employee)
        self.assertEqual(self.employee.attendance_state, "checked_in")

    @freeze_time(f"{MONDAY} 18:00:00")
    def test_check_in_without_restriction(self):
        self.company.restriction_working_schedules = False
        attendance = self.employee._attendance_action_change()
        self.assertEqual(attendance.employee_id, self.employee)

    @freeze_time(f"{MONDAY} 18:00:00")
    def test_check_out_not_restricted(self):
        self.company.restriction_working_schedules = False
        self.employee._attendance_action_change()
        self.company.restriction_working_schedules = True
        attendance = self.employee._attendance_action_change()
        self.assertTrue(attendance.check_out)
        self.assertEqual(self.employee.attendance_state, "checked_out")

    @freeze_time(f"{MONDAY} 18:00:00")
    def test_restriction_is_per_company(self):
        other_company = self.env["res.company"].create({"name": "Other company"})
        self.calendar.company_id = False
        employee = self.env["hr.employee"].create(
            {
                "name": "Other company employee",
                "company_id": other_company.id,
                "resource_calendar_id": self.calendar.id,
            }
        )
        attendance = employee._attendance_action_change()
        self.assertEqual(attendance.employee_id, employee)

    @freeze_time(f"{MONDAY} 18:00:00")
    def test_check_in_restricted_as_user(self):
        employee = self.user.employee_id
        self.assertEqual(employee, self.employee.with_user(self.user))
        with self.assertRaisesRegex(UserError, "already ended"):
            employee._attendance_action_change()
