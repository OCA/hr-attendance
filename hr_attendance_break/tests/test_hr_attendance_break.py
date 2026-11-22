# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from datetime import datetime

from freezegun import freeze_time

from odoo.tests import common


class TestHrAttendanceBreak(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company.attendance_break_rounding_minutes = 0
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "Break Test Calendar", "tz": "UTC"}
        )
        # Monday 08:00-17:00 with a lunch break from 12:00 to 13:00
        cls.calendar.attendance_ids = [(5, 0, 0)] + [
            (0, 0, vals)
            for vals in (
                {
                    "name": "Monday Morning",
                    "dayofweek": "0",
                    "hour_from": 8,
                    "hour_to": 12,
                    "day_period": "morning",
                },
                {
                    "name": "Monday Lunch",
                    "dayofweek": "0",
                    "hour_from": 12,
                    "hour_to": 13,
                    "day_period": "lunch",
                },
                {
                    "name": "Monday Afternoon",
                    "dayofweek": "0",
                    "hour_from": 13,
                    "hour_to": 17,
                    "day_period": "afternoon",
                },
            )
        ]
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Break Tester",
                "tz": "UTC",
                "resource_calendar_id": cls.calendar.id,
            }
        )
        cls.paid_type = cls.env.ref("hr_attendance_break.break_type_paid")
        cls.unpaid_type = cls.env.ref("hr_attendance_break.break_type_unpaid")
        Reason = cls.env["hr.attendance.reason"]
        cls.coffee_reason = Reason.create(
            {
                "name": "Test Coffee",
                "code": "TCOF",
                "action_type": "sign_out",
                "break_type_id": cls.paid_type.id,
            }
        )
        cls.lunch_reason = Reason.create(
            {
                "name": "Test Lunch",
                "code": "TLUN",
                "action_type": "sign_out",
                "break_type_id": cls.unpaid_type.id,
            }
        )
        cls.sick_reason = Reason.create(
            {"name": "Test Sick", "code": "TSICK", "action_type": "sign_out"}
        )

    def _action(self, when, reason=None):
        employee = self.employee
        if reason:
            employee = employee.with_context(attendance_reason_id=reason.id)
        with freeze_time(when):
            return employee._attendance_action_change()

    def test_check_out_with_break_reason_starts_break(self):
        attendance = self._action(datetime(2026, 1, 5, 8, 0))
        self._action(datetime(2026, 1, 5, 10, 0), self.coffee_reason)
        self.assertEqual(self.employee.attendance_state, "checked_out")
        self.assertEqual(len(attendance.break_ids), 1)
        brk = attendance.break_ids
        self.assertEqual(brk.break_start, datetime(2026, 1, 5, 10, 0))
        self.assertFalse(brk.break_stop)
        self.assertEqual(brk.break_type_id, self.paid_type)
        self.assertIn(self.coffee_reason, attendance.attendance_reason_ids)

    def test_check_in_ends_break_and_reopens_attendance(self):
        attendance = self._action(datetime(2026, 1, 5, 8, 0))
        self._action(datetime(2026, 1, 5, 10, 0), self.coffee_reason)
        resumed = self._action(datetime(2026, 1, 5, 10, 15))
        self.assertEqual(resumed, attendance)
        self.assertFalse(attendance.check_out)
        self.assertEqual(self.employee.attendance_state, "checked_in")
        self.assertEqual(attendance.break_ids.break_stop, datetime(2026, 1, 5, 10, 15))
        self.assertAlmostEqual(attendance.break_ids.duration, 0.25)
        self.assertEqual(
            self.env["hr.attendance"].search_count(
                [("employee_id", "=", self.employee.id)]
            ),
            1,
        )

    def test_check_out_without_break_reason(self):
        attendance = self._action(datetime(2026, 1, 5, 8, 0))
        self._action(datetime(2026, 1, 5, 12, 0), self.sick_reason)
        self.assertFalse(attendance.break_ids)
        attendance = self._action(datetime(2026, 1, 5, 13, 0))
        self.assertFalse(attendance.break_ids)
        self.assertEqual(attendance.check_in, datetime(2026, 1, 5, 13, 0))

    def test_full_day_paid_and_unpaid_breaks(self):
        attendance = self._action(datetime(2026, 1, 5, 8, 0))
        self._action(datetime(2026, 1, 5, 10, 0), self.coffee_reason)
        self._action(datetime(2026, 1, 5, 10, 15))
        self._action(datetime(2026, 1, 5, 13, 0), self.lunch_reason)
        self._action(datetime(2026, 1, 5, 13, 30))
        self._action(datetime(2026, 1, 5, 15, 0), self.coffee_reason)
        self._action(datetime(2026, 1, 5, 15, 15))
        self._action(datetime(2026, 1, 5, 17, 0))
        self.assertEqual(len(attendance.break_ids), 3)
        self.assertEqual(attendance.check_out, datetime(2026, 1, 5, 17, 0))
        # The schedule lunch (12:00-13:00) is already excluded by Odoo
        self.assertAlmostEqual(attendance.worked_hours, 8.0)
        self.assertAlmostEqual(attendance.break_hours, 1.0)
        self.assertAlmostEqual(attendance.unpaid_break_hours, 0.5)
        self.assertAlmostEqual(attendance.net_worked_hours, 7.5)

    def test_unpaid_break_during_schedule_lunch_not_deducted_twice(self):
        attendance = self._action(datetime(2026, 1, 5, 8, 0))
        # 11:30 -> 13:00: only the 30 minutes before the schedule lunch count
        self._action(datetime(2026, 1, 5, 11, 30), self.lunch_reason)
        self._action(datetime(2026, 1, 5, 13, 0))
        self._action(datetime(2026, 1, 5, 17, 0))
        self.assertAlmostEqual(attendance.worked_hours, 8.0)
        self.assertAlmostEqual(attendance.break_hours, 1.5)
        self.assertAlmostEqual(attendance.unpaid_break_hours, 0.5)
        self.assertAlmostEqual(attendance.net_worked_hours, 7.5)

    def test_break_left_open_previous_day(self):
        attendance = self._action(datetime(2026, 1, 5, 8, 0))
        self._action(datetime(2026, 1, 5, 16, 0), self.coffee_reason)
        new_attendance = self._action(datetime(2026, 1, 6, 8, 0))
        self.assertNotEqual(new_attendance, attendance)
        self.assertEqual(attendance.check_out, datetime(2026, 1, 5, 16, 0))
        self.assertFalse(attendance.break_ids)
        self.assertEqual(new_attendance.check_in, datetime(2026, 1, 6, 8, 0))

    def test_break_not_resumed_after_manual_change(self):
        attendance = self._action(datetime(2026, 1, 5, 8, 0))
        self._action(datetime(2026, 1, 5, 12, 0), self.lunch_reason)
        attendance.check_out = datetime(2026, 1, 5, 12, 5)
        new_attendance = self._action(datetime(2026, 1, 5, 12, 30))
        self.assertNotEqual(new_attendance, attendance)
        self.assertFalse(attendance.break_ids)

    def test_break_rounding(self):
        self.company.attendance_break_rounding_minutes = 15
        attendance = self._action(datetime(2026, 1, 5, 8, 0))
        self._action(datetime(2026, 1, 5, 14, 0), self.lunch_reason)
        self._action(datetime(2026, 1, 5, 14, 37))
        self._action(datetime(2026, 1, 5, 17, 0))
        self.assertAlmostEqual(attendance.break_ids.duration, 0.5)
        self.assertAlmostEqual(attendance.unpaid_break_hours, 0.5)

    def test_reason_added_on_resume(self):
        sign_in_reason = self.env["hr.attendance.reason"].create(
            {"name": "Test Back", "code": "TBACK", "action_type": "sign_in"}
        )
        attendance = self._action(datetime(2026, 1, 5, 8, 0))
        self._action(datetime(2026, 1, 5, 10, 0), self.coffee_reason)
        self._action(datetime(2026, 1, 5, 10, 15), sign_in_reason)
        self.assertIn(sign_in_reason, attendance.attendance_reason_ids)
